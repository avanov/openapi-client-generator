""" A collection of functions that transform OpenAPI spec to data structures convenient for codegen.
"""
import re
from pathlib import Path
from string import digits
from functools import reduce
from typing import NamedTuple, Mapping, Sequence, Generator, Optional, Callable, Any, Tuple

from typeit.utils import normalize_name
import openapi_type as oas
from inflection import underscore, camelize, singularize
from pyrsistent.typing import PVector, PMap
from pyrsistent import pmap, pvector
import deepmerge


class EndpointSegment(NamedTuple):
    """ Represents a single endpoint segment, a.k.a. a thing between '/' symbols
    """
    original: str
    """ original value
    """
    segment: str
    """ normalized value
    """
    placeholder: Optional[str] = None
    """ if used as a placeholder, the value contains a string representation of it
    """


class EndpointSegments(NamedTuple):
    segments: Sequence[EndpointSegment]

    def as_fs_path(self) -> Path:
        """ Represent the segments as a filesystem path
        """
        return Path('/'.join(x.segment for x in self.segments))

    def as_endpoint_url(self) -> str:
        """ Represent the segments as a endpoint url
        """
        return '/'.join(x.placeholder if x.placeholder else x.original for x in self.segments)


class Params(NamedTuple):
    query_params: Sequence[oas.OperationParameter]
    path_params: Sequence[oas.OperationParameter]
    header_params: Sequence[oas.OperationParameter]
    cookie_params: Sequence[oas.OperationParameter]


class TypeAttr(NamedTuple):
    name: str
    datatype: str
    is_required: bool
    default: Optional[str]
    docstring: str = ''

    @property
    def datatype_repr(self) -> str:
        if not self.is_required:
            # trying to reduce redundant Optional wrapper
            if self.default not in (None, 'None'):
                return self.datatype
            return f'Optional[{self.datatype}]'
        return self.datatype

    @property
    def default_repr(self) -> Optional[str]:
        if self.default:
            return self.default
        if not self.is_required:
            # optional values always have None as the default value
            return 'None'
        return None


class TypeDescr(NamedTuple):
    name: str
    default_value: Optional[str] = None
    docstring: str = ''


class TypeContext(NamedTuple):
    name: str
    docstring: str = ''
    attrs: PVector[TypeAttr] = pvector()
    is_enum: bool = False
    common_reference_as: Optional[str] = None
    """ if a type is a reference to a common (shared) type, it will be imported from a common domain
    and referenced as this name
    """
    overrides: PMap[str, str] = pmap()
    """ Attribute name overrides between Python and JSON
    """
    @property
    def ordered_attrs(self) -> Sequence[TypeAttr]:
        return sorted(self.attrs, key=lambda x: (x.is_required, x.name), reverse=True)


DEFAULT_QUERY_PARAMS_TYPE = TypeContext(name='Query', docstring='Parameters for the endpoint query string')
DEFAULT_PATH_PARAMS_TYPE  = TypeContext(name='Params', docstring='Parameters for the endpoint path placeholders')
DEFAULT_REQUEST_TYPE      = TypeContext(name='Request')
DEFAULT_RESPONSE_TYPE     = TypeContext(name='Response')
DEFAULT_HEADERS_TYPE      = TypeContext(
    name='Headers',
    attrs=pvector([
        TypeAttr(
            name='accept',
            datatype='str',
            default="'application/json'",
            is_required=True
        ),
        TypeAttr(
            name='accept_charset',
            datatype='str',
            default="'utf-8'",
            is_required=True
        ),
        TypeAttr(
            name='authorization',
            datatype='str',
            default="None",
            is_required=False
        ),
    ])
)


class EndpointMethod(NamedTuple):
    name:               str
    method:             oas.Operation
    params:             Params
    path_params_type:   TypeContext = DEFAULT_PATH_PARAMS_TYPE
    query_types:        Sequence[TypeContext] = pvector([DEFAULT_QUERY_PARAMS_TYPE])
    request_types:      Sequence[TypeContext] = pvector([DEFAULT_REQUEST_TYPE])
    response_types:     Sequence[TypeContext] = pvector([DEFAULT_RESPONSE_TYPE])
    headers_types:      Sequence[TypeContext] = pvector([DEFAULT_HEADERS_TYPE])
    response_is_stream: bool = False


SupportedMethods = Generator[EndpointMethod, None, None]


class Endpoint(NamedTuple):
    path_item: oas.PathItem
    """ original PathItem from OpenAPI spec
    """
    supported_methods: SupportedMethods


ResolvedTypesMap = PMap[str, TypeContext]
ResolvedTypesVec = PVector[TypeContext]  # needed for ordering


class SpecMeta(NamedTuple):
    """ A post-processed OpenAPI specification that is convenient to use for codegen
    """
    spec: oas.OpenAPI
    """ original spec
    """
    paths: Mapping[EndpointSegments, Endpoint]
    common_types: ResolvedTypesVec


def openapi_to_codegen_metadata(spec: oas.OpenAPI) -> SpecMeta:
    paths = {}
    common_types = resolve_schemas(spec.components.schemas, common_types=pmap())
    common_types_ = pmap((x.name, x) for x in common_types)

    for path, item in spec.paths.items():
        pth = api_path_to_filepath(path)
        endpoint = Endpoint(
            path_item=item,
            supported_methods=iter_supported_methods(common_types_, item)
        )
        paths[pth] = endpoint

    return SpecMeta(
        spec=spec,
        paths=paths,
        common_types=common_types
    )


def resolve_schemas(
    schemas: Mapping[str, oas.SchemaType],
    common_types: ResolvedTypesMap
) -> ResolvedTypesVec:
    resolved_types: PVector[TypeContext] = pvector()
    for type_name, schema in schemas.items():
        py_name, default, resolved = recursive_resolve_schema(
            registry=schemas,
            suggested_type_name=type_name,
            schema=schema,
            attr_name_normalizer=underscore,
            common_types=common_types,
        )
        if resolved:
            resolved_types = resolved_types.extend(resolved)
            common_types = common_types.set(type_name, resolved[-1])
        else:
            typ = TypeContext(
                name=type_name,
                attrs=pvector(),
                common_reference_as=py_name
            )
            resolved_types = resolved_types.append(typ)
            common_types = common_types.set(type_name, typ)

    return resolved_types


PYTHONIC = re.compile('/')


class Parsed(NamedTuple):
    actual_type_name: str
    """ name of the valid python type
    """
    default_value: Optional[str] = None
    final_types: PVector[TypeContext] = pvector()


def recursive_resolve_schema(
    registry: Mapping[str, oas.SchemaType],
    suggested_type_name: str,
    schema: oas.SchemaType,
    attr_name_normalizer: Callable[[str], str] = lambda x: x,
    common_types: ResolvedTypesMap = pmap()
) -> Parsed:
    final_types: PVector[TypeContext] = pvector()
    if isinstance(schema, oas.StringValue):
        if schema.enum:
            actual_type_name = camelize(suggested_type_name)
            enum_options = pvector(
                TypeAttr(
                    name=underscore(PYTHONIC.sub('_', x)).upper(),
                    datatype='str',
                    default=f"'{x}'",
                    is_required=True
                )
                for x in schema.enum
            )
            final_types = final_types.append(
                TypeContext(
                    name=actual_type_name,
                    docstring='',
                    attrs=enum_options,
                    is_enum=True
                )
            )
            if schema.default is None:
                default_value = None
            else:
                # construct enum value from the provided default string
                default_value = f"{actual_type_name}('{schema.default}')"
        else:
            actual_type_name = 'str'
            if schema.default is None:
                default_value = None
            else:
                default_value = f"'{schema.default}'"
        return Parsed(
            actual_type_name=actual_type_name,
            final_types=final_types,
            default_value=default_value
        )

    elif isinstance(schema, oas.IntegerValue):
        return Parsed(
            actual_type_name='int',
            default_value=f"{schema.default}" if schema.default is not None else None,
            final_types=pvector()
        )
    elif isinstance(schema, oas.FloatValue):
        return Parsed(
            actual_type_name='float',
            default_value=str(schema.default) if schema.default is not None else None,
            final_types=pvector()
        )
    elif isinstance(schema, oas.BooleanValue):
        return Parsed(
            actual_type_name='bool',
            default_value=None if schema.default is None else str(schema.default),
            final_types=pvector()
        )

    elif isinstance(schema, oas.ObjectValue):
        attrs: PVector[TypeAttr] = pvector()
        for attr_name, attr_schema_type in schema.properties.items():
            attr_type_suggested_name = camelize('_'.join([suggested_type_name, attr_name]))
            attr_type_actual_name, default, new_types = recursive_resolve_schema(
                registry=registry,
                suggested_type_name=attr_type_suggested_name,
                schema=attr_schema_type,
                attr_name_normalizer=attr_name_normalizer,
                common_types=common_types
            )
            final_types = final_types.extend(new_types)
            attrs = attrs.append(TypeAttr(
                # TODO: propagate overrides
                name=normalize_name(attr_name_normalizer(attr_name)),
                datatype=attr_type_actual_name,
                default=default,
                is_required=attr_name in schema.required
            ))
        final_types = final_types.append(
            TypeContext(
                name=suggested_type_name,
                docstring='',
                attrs=attrs
            )
        )
        return Parsed(
            actual_type_name=suggested_type_name,
            default_value=None,
            final_types=final_types
        )

    elif isinstance(schema, oas.Reference):
        # Represents a reference to an object in common types domain
        if schema.ref.location is not oas.custom_types.RefTo.SCHEMAS:
            raise NotImplementedError(
                f'This reference location is not supported yet: {schema.ref.location}'
            )

        # TODO: replace with a distinct alias type representation
        if schema.ref.name in common_types:
            typ = common_types[schema.ref.name]
            return Parsed(
                actual_type_name=typ.name,
                default_value=None,
                final_types=final_types
            )
        else:
            to_resolve = registry[schema.ref.name]
            actual_type_name, default, resolved_types = recursive_resolve_schema(
                registry=registry,
                suggested_type_name=schema.ref.name,
                schema=to_resolve,
                attr_name_normalizer=attr_name_normalizer,
                common_types=common_types
            )
            final_types = final_types.extend(resolved_types)
        return Parsed(
            actual_type_name=actual_type_name,
            default_value=default,
            final_types=final_types
        )

    elif isinstance(schema, oas.ArrayValue):
        sequence_type_literal = 'Sequence[{T}]'
        to_resolve = schema.items
        name = singularize(suggested_type_name)
        actual_type_name, default, resolved_types = recursive_resolve_schema(
            registry=registry,
            suggested_type_name=name,
            schema=to_resolve,
            attr_name_normalizer=attr_name_normalizer,
            common_types=common_types,
        )
        sequence_type_literal = sequence_type_literal.format(T=actual_type_name)
        final_types = final_types.extend(resolved_types)
        return Parsed(
            actual_type_name=sequence_type_literal,
            default_value=None,
            final_types=final_types,
        )

    elif isinstance(schema, oas.ObjectWithAdditionalProperties):
        if schema.additional_properties is None:
            return Parsed(
                actual_type_name='Mapping[Any, Any]',
                default_value=None,
                final_types=final_types
            )
        else:
            return recursive_resolve_schema(
                registry=registry,
                suggested_type_name=suggested_type_name,
                schema=schema.additional_properties,
                attr_name_normalizer=attr_name_normalizer,
                common_types=common_types,
            )

    elif isinstance(schema, oas.ProductSchemaType):
        to_merge = (
            find_reference(x, registry) if isinstance(x, oas.Reference) else x for x in schema.all_of  # type: ignore
        )
        to_merge = (x._asdict() for x in to_merge)
        red: Mapping[str, Any] = reduce(merge_strategy.merge, to_merge, {})
        schema_ = oas.ObjectValue(**red)
        return recursive_resolve_schema(
            registry=registry,
            suggested_type_name=suggested_type_name,
            schema=schema_,
            attr_name_normalizer=attr_name_normalizer,
            common_types=common_types
        )

    elif isinstance(schema, (oas.UnionSchemaTypeAny, oas.UnionSchemaTypeOne)):
        if isinstance(schema, oas.UnionSchemaTypeAny):
            items = schema.any_of
        else:
            items = schema.one_of
        options: PVector[str] = pvector()
        for schema_ in items:
            variant_name = camelize(f'{suggested_type_name}_var{len(options) + 1}')
            actual_variant_py_name, default, resolved_types = recursive_resolve_schema(
                registry=registry,
                suggested_type_name=variant_name,
                schema=schema_,
                attr_name_normalizer=attr_name_normalizer,
                common_types=common_types,
            )
            options = options.append(actual_variant_py_name)

            # We don't need to append aliases to the final types as they are already there
            # either as primitive types, or as types that have been parsed already
            if actual_variant_py_name == variant_name:
                final_types = final_types.extend(resolved_types)

        return Parsed(
            actual_type_name=f'Union[{", ".join(options)}]',
            default_value=None,
            final_types=final_types
        )

    elif isinstance(schema, oas.EmptyValue):
        return Parsed(
            actual_type_name='Any',
            default_value='None',
            final_types=pvector(),
        )

    elif isinstance(schema, oas.InlinedObjectValue):
        schema_ = oas.ObjectValue(
            type='object',
            properties=schema.properties,
            required=schema.required,
            description=schema.description,
        )
        return recursive_resolve_schema(
            registry=registry,
            suggested_type_name=suggested_type_name,
            schema=schema_,
            attr_name_normalizer=attr_name_normalizer,
            common_types=common_types,
        )

    raise NotImplementedError(f'Unsupported recursive type: {schema}')



def api_path_to_filepath(api_path: str, sep: str = '/') -> EndpointSegments:
    """
    :param api_path: URL path
    :param sep: separator symbol used in API path
    """
    segments = [pythonize_path_segment(x) for x in api_path.split(sep) if x.strip()]
    if not segments:
        segments = [EndpointSegment('/', 'root', None)]
    return EndpointSegments(pvector(segments))


def pythonize_path_segment(seg: str) -> EndpointSegment:
    placeholder = {'{', '}'}
    remove = {'.', ','} | placeholder
    is_placeholder = False
    final = []
    for char in seg:
        if char in placeholder:
            is_placeholder = True
            continue
        if char in remove:
            continue
        final.append(char)

    final_underscored = underscore(''.join(final))
    rv = final_underscored
    if is_placeholder:
        rv = f'by_{rv}'
    else:
        # version tags are usually numeric
        if rv[0] in digits:
            rv = f'v{rv}'

    return EndpointSegment(
        original=seg,
        segment=rv,
        placeholder=f'{{{final_underscored}}}' if is_placeholder else None
    )


PARAM_CONTAINERS: PMap[oas.ParamLocation, PVector[oas.OperationParameter]] = pmap(
    { oas.ParamLocation.QUERY:  pvector()  # type: ignore
    , oas.ParamLocation.PATH:   pvector()
    , oas.ParamLocation.HEADER: pvector()
    , oas.ParamLocation.COOKIE: pvector()
    }
)


def iter_supported_methods(common_types: ResolvedTypesMap, path: oas.PathItem) -> SupportedMethods:
    """
    :param spec: reference to the rest of the spec that may be useful for parsing
    :param path: current path
    """
    methods = ( path.head
              , path.get
              , path.post
              , path.put
              , path.patch
              , path.delete
              , path.trace
              )
    supported_methods = ((nam, met) for nam, met in path._asdict().items() if met and met in methods)
    for name, (method) in supported_methods:
        containers = PARAM_CONTAINERS
        for param in method.parameters:
            try:
                container = containers[param.in_]
            except KeyError:
                raise NotImplementedError(f'Param parsing is not supported for parameters in {param.in_}')
            else:
                containers = containers.set(param.in_, container.append(param))

        params = Params(
            query_params=containers[oas.ParamLocation.QUERY],
            path_params=containers[oas.ParamLocation.PATH],
            header_params=containers[oas.ParamLocation.HEADER],
            cookie_params=containers[oas.ParamLocation.COOKIE],
        )

        if method.request_body:
            for content_type, meta in method.request_body.content.items():
                if content_type.format in (oas.ContentTypeFormat.JSON,
                                           oas.ContentTypeFormat.ANYTHING,
                                           oas.ContentTypeFormat.FORM_URLENCODED):
                    request_schema = meta.schema
                    break
            else:
                request_schema = list(method.request_body.content.items())[-1][1].schema

            required_name = 'Request'
            actual_request_type_name, default, request_types = recursive_resolve_schema(
                registry={},
                suggested_type_name=required_name,
                schema=request_schema,
                attr_name_normalizer=underscore,
                common_types=common_types
            )
            if actual_request_type_name != required_name:
                request_types = request_types.append(
                    DEFAULT_REQUEST_TYPE._replace(
                        name=actual_request_type_name,
                        attrs=pvector(),
                        common_reference_as=required_name
                    )
                )

        else:
            request_types = pvector([DEFAULT_REQUEST_TYPE])

        response_is_stream = False
        required_response_name = 'Response'
        if method.responses:
            supported_status = '200'
            try:
                response = method.responses[supported_status]
            except KeyError:
                supported_status, response = list(method.responses.items())[0]

            if not response.content:
                response_types = pvector([DEFAULT_RESPONSE_TYPE._replace(
                    name='None',
                    common_reference_as=required_response_name
                )])
            else:

                for content_type, meta in response.content.items():
                    if content_type.format in (oas.ContentTypeFormat.JSON,
                                               oas.ContentTypeFormat.ANYTHING,
                                               oas.ContentTypeFormat.FORM_URLENCODED,
                                               oas.ContentTypeFormat.EVENT_STREAM):
                        response_schema: Optional[oas.SchemaType] = meta.schema
                        response_is_stream = content_type.format in (oas.ContentTypeFormat.EVENT_STREAM, oas.ContentTypeFormat.BINARY_STREAM)
                        break
                else:
                    last_response = list(response.content.items())[-1][1]
                    response_schema = last_response.schema

                if response_schema is None:
                    response_types = pvector([DEFAULT_RESPONSE_TYPE._replace(
                        name='Any',
                        common_reference_as=required_response_name
                    )])
                else:
                    actual_response_type_name, default, response_types = recursive_resolve_schema(
                        registry={},
                        suggested_type_name=required_response_name,
                        schema=response_schema,
                        attr_name_normalizer=underscore,
                        common_types=common_types,
                    )
                    if actual_response_type_name != required_response_name:
                        response_types = response_types.append(
                            DEFAULT_RESPONSE_TYPE._replace(
                                name=actual_response_type_name,
                                attrs=pvector(),
                                common_reference_as=required_response_name
                            )
                        )

        else:
            response_types = pvector([DEFAULT_RESPONSE_TYPE])

        query_type, query_types = infer_params_type(
            params.query_params,
            name_normalizer=underscore,
            default=DEFAULT_QUERY_PARAMS_TYPE
        )
        path_params_type, _types    = infer_params_type(params.path_params)
        headers_type, headers_types = infer_params_type(params.header_params,
                                                        name_normalizer=lambda x: underscore(x.lower()),
                                                        default=DEFAULT_HEADERS_TYPE)

        yield EndpointMethod(
            name=name,
            method=method,
            params=params,
            path_params_type=path_params_type,
            query_types=query_types,
            request_types=request_types,
            response_types=response_types,
            headers_types=headers_types,
            response_is_stream=response_is_stream
        )


def infer_params_type(params: Sequence[oas.OperationParameter],
                      name_normalizer: Callable[[str], str] = lambda x: x,
                      default: TypeContext = DEFAULT_PATH_PARAMS_TYPE) -> Tuple[TypeContext, PVector[TypeContext]]:
    final_types: PVector[TypeContext] = pvector()
    if not params:
        return default, final_types.append(default)

    rv = default
    overrides = default.overrides
    for param in params:
        actual_type_name, default_value, resolved_types = recursive_resolve_schema(
            registry={},
            suggested_type_name=name_normalizer(f'{default.name}_{param.name}'),
            schema=param.schema,
            attr_name_normalizer=name_normalizer,
            common_types=pmap()
        )
        final_types = final_types.extend(resolved_types)
        datatype = TypeDescr(
            name=actual_type_name,
            default_value=default_value,
        )

        # Checking for required attribute name overrides
        case_normalized = name_normalizer(param.name)
        valid_python_normalized = normalize_name(case_normalized)
        if case_normalized != valid_python_normalized:
            overrides = overrides.set(f'{rv.name}.{valid_python_normalized}', param.name)

        rv = rv._replace(
            attrs=rv.attrs.append(
                TypeAttr(
                    name=valid_python_normalized,
                    datatype=datatype.name,
                    docstring=datatype.docstring,
                    is_required=param.required,
                    default=default_value,
                )
            )
        )
    rv = rv._replace(overrides=overrides)
    final_types = final_types.append(rv)
    return rv, final_types


def python_type_from_openapi_schema(schema: oas.SchemaType) -> TypeDescr:
    if isinstance(schema, oas.StringValue):
        if schema.enum:
            docstring = ', '.join(schema.enum)
        else:
            docstring = schema.description
        return TypeDescr('str', docstring=docstring)
    elif isinstance(schema, oas.IntegerValue):
        return TypeDescr('int')
    elif isinstance(schema, oas.BooleanValue):
        return TypeDescr('bool')
    return TypeDescr('str')


def add_to_set(config, path, base: frozenset, nxt: frozenset) -> frozenset:
    return base | nxt


def find_reference(ref: oas.Reference, components: ResolvedTypesMap) -> oas.ObjectValue:
    if ref.ref.name not in components:
        raise NotImplementedError('Reference is not found in the registry')
    obj = components[ref.ref.name]
    assert isinstance(obj, oas.ObjectValue), "Referenced object is not of type ObjectValue"
    return obj


merge_strategy = deepmerge.Merger(
    [
        (list, "append"),
        (dict, "merge"),
        (frozenset, add_to_set),
    ],
    ["override"],
    ["override"]
)
