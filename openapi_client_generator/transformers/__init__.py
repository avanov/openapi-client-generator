""" A collection of functions that transform OpenAPI spec to data structures convenient for codegen.
"""
import re
from pathlib import Path
from string import digits
from functools import reduce
from typing import NamedTuple, Mapping, Sequence, Generator, Optional, Union, Callable

import openapi_type as oas
from inflection import underscore, camelize
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
    @property
    def ordered_attrs(self) -> Sequence[TypeAttr]:
        return sorted(self.attrs, key=lambda x: x.is_required, reverse=True)


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
    query_params_type:  TypeContext = DEFAULT_QUERY_PARAMS_TYPE
    request_types:      Sequence[TypeContext] = pvector([DEFAULT_REQUEST_TYPE])
    response_types:     Sequence[TypeContext] = pvector([DEFAULT_RESPONSE_TYPE])
    headers_type:       TypeContext = DEFAULT_HEADERS_TYPE
    response_is_stream: bool = False


SupportedMethods = Generator[EndpointMethod, None, None]


class Endpoint(NamedTuple):
    path_item: oas.PathItem
    """ original PathItem from OpenAPI spec
    """
    supported_methods: SupportedMethods


ResolvedTypes = Mapping[str, TypeContext]


class SpecMeta(NamedTuple):
    """ A post-processed OpenAPI specification that is convenient to use for codegen
    """
    spec: oas.OpenAPI
    """ original spec
    """
    paths: Mapping[EndpointSegments, Endpoint]
    common_types: ResolvedTypes


def openapi_to_codegen_metadata(spec: oas.OpenAPI) -> SpecMeta:
    paths = {}
    common_types = resolve_schemas(spec.components.schemas, common_types=pmap())

    for path, item in spec.paths.items():
        pth = api_path_to_filepath(path)
        endpoint = Endpoint(
            path_item=item,
            supported_methods=iter_supported_methods(common_types, item)
        )
        paths[pth] = endpoint

    return SpecMeta(
        spec=spec,
        paths=paths,
        common_types=common_types
    )


def resolve_schemas(
    schemas: Mapping[str, oas.SchemaType],
    common_types: ResolvedTypes
) -> ResolvedTypes:
    resolved_types: PVector[TypeContext] = pvector()
    for type_name, schema in schemas.items():
        resolved_types = resolved_types.extend(
            recursive_resolve_schema(
                schemas,
                type_name,
                schema,
                attr_name_normalizer=underscore,
                common_types=common_types,
            )
        )
    return {x.name: x for x in resolved_types}


PYTHONIC = re.compile('/')


def recursive_resolve_schema(
    registry: Mapping[str, oas.SchemaType],
    type_name: str,
    schema: oas.SchemaType,
    attr_name_normalizer: Callable[[str], str] = lambda x: x,
    common_types: ResolvedTypes = pmap()
) -> PVector[TypeContext]:
    final_types: PVector[TypeContext] = pvector()
    if isinstance(schema, oas.StringValue):
        final_types = final_types.append(
            TypeContext(
                name='str',
                docstring='',
                attrs=pvector(),
                common_reference_as=type_name
            )
        )
    elif isinstance(schema, oas.IntegerValue):
        final_types = final_types.append(
            TypeContext(
                name='int',
                docstring='',
                attrs=pvector(),
                common_reference_as=type_name
            )
        )
    elif isinstance(schema, oas.ObjectValue):
        attrs: PVector[TypeAttr] = pvector()
        for attr_name, attr_meta in schema.properties.items():
            to_resolve: Union[None, oas.SchemaType, oas.RecursiveAttrs] = None
            default = None
            if isinstance(attr_meta, oas.StringValue):
                if attr_meta.enum:
                    attr_datatype = camelize(f'{type_name}_{attr_name}')
                    final_types = final_types.append(
                        TypeContext(
                            name=attr_datatype,
                            docstring='',
                            attrs=pvector(TypeAttr(
                                name=underscore(PYTHONIC.sub('_', x)).upper(),
                                datatype='str',
                                default=f"'{x}'",
                                is_required=True
                            ) for x in attr_meta.enum),
                            is_enum=True
                        )
                    )
                else:
                    attr_datatype = 'str'
                default = f"'{attr_meta.default}'" if attr_meta.default is not None else None

            elif isinstance(attr_meta, oas.IntegerValue):
                attr_datatype = 'int'
                default = f'{attr_meta.default}' if attr_meta.default is not None else None

            elif isinstance(attr_meta, oas.FloatValue):
                attr_datatype = 'float'
                default = f'{attr_meta.default}' if attr_meta.default is not None else None

            elif isinstance(attr_meta, oas.BooleanValue):
                attr_datatype = 'bool'
                default = f'{attr_meta.default}' if attr_meta.default is not None else None

            elif isinstance(attr_meta, oas.Reference):
                if attr_meta.ref.location is oas.custom_types.RefTo.SCHEMAS:
                    attr_meta_ = registry[attr_meta.ref.name]
                    attr_datatype = camelize(f'{type_name}_{attr_name}')
                    resolved_types = recursive_resolve_schema(
                        registry,
                        attr_datatype,
                        attr_meta_,
                        attr_name_normalizer,
                        common_types=common_types
                    )
                    final_types = final_types.extend(resolved_types)
                else:
                    raise NotImplementedError('Reference Value')

            elif isinstance(attr_meta, oas.ArrayValue):
                attr_datatype = 'Sequence[{T}]'
                to_resolve = attr_meta.items

            elif isinstance(attr_meta, oas.ObjectValue):
                attr_datatype = camelize(f'{type_name}_{attr_name}')
                resolved_types = recursive_resolve_schema(
                    registry,
                    attr_datatype,
                    attr_meta,
                    attr_name_normalizer,
                    common_types=common_types
                )
                final_types = final_types.extend(resolved_types)

            elif isinstance(attr_meta, oas.ObjectWithAdditionalProperties):
                pass

            elif isinstance(attr_meta, oas.ProductSchemaType):
                to_merge = (x._asdict() for x in attr_meta.all_of)
                attr_meta_ = oas.ObjectValue(**reduce(merge_strategy.merge, to_merge, {}))
                attr_datatype = camelize(f'{type_name}_{attr_name}')
                resolved_types = recursive_resolve_schema(
                    registry,
                    attr_datatype,
                    attr_meta_,
                    attr_name_normalizer,
                    common_types=common_types
                )
                final_types = final_types.extend(resolved_types)
                if attr_name in attr_meta_.required:
                    default = None
                else:
                    default = 'None'

            elif isinstance(attr_meta, (oas.UnionSchemaTypeAny, oas.UnionSchemaTypeOne)):
                attr_datatype = camelize(f'{type_name}_{attr_name}')
                resolved_types = recursive_resolve_schema(
                    registry,
                    attr_datatype,
                    attr_meta,
                    attr_name_normalizer,
                    common_types=common_types
                )
                final_types = final_types.extend(resolved_types)

            elif isinstance(attr_meta, oas.EmptyValue):
                attr_datatype = 'Any'
                default = 'None'

            else:
                raise TypeError(f'Unrecognised schema type: {attr_meta}')

            if to_resolve:
                T = 'Any'
                if isinstance(to_resolve, oas.StringValue):
                    T = 'str'
                elif isinstance(to_resolve, oas.FloatValue):
                    T = 'float'
                elif isinstance(to_resolve, oas.BooleanValue):
                    T = 'bool'
                attr_datatype = attr_datatype.format(T=T)

            attrs = attrs.append(TypeAttr(
                name=attr_name_normalizer(attr_name),
                datatype=attr_datatype,
                default=default,
                is_required=attr_name in schema.required
            ))
        final_types = final_types.append(
            TypeContext(
                name=type_name,
                docstring='',
                attrs=attrs
            )
        )

    elif isinstance(schema, oas.ArrayValue):
        schema_ = schema.items
        array_type = TypeContext(
            name=type_name,
            docstring=schema.description,
        )

        final_types = final_types.append(array_type)
        resolved_types = recursive_resolve_schema(
            registry,
            type_name,
            schema_,
            attr_name_normalizer,
            common_types=common_types
        )
        final_types = final_types.extend(resolved_types)

    elif isinstance(schema, oas.Reference):
        if schema.ref.location is oas.custom_types.RefTo.SCHEMAS:
            if schema.ref.name in common_types:
                final_types = final_types.append(
                    TypeContext(
                        name=schema.ref.name,
                        attrs=pvector(),
                        common_reference_as=type_name
                    )
                )
            else:
                to_resolve = registry[schema.ref.name]
                resolved_types = recursive_resolve_schema(
                    registry,
                    schema.ref.name,
                    to_resolve,
                    attr_name_normalizer,
                    common_types=common_types
                )
                final_types = final_types.extend(resolved_types)
        else:
            raise NotImplementedError('Reference Value 2')

    elif isinstance(schema, oas.ProductSchemaType):
        to_merge = (x._asdict() for x in schema.all_of)
        attr_meta_ = oas.ObjectValue(**reduce(merge_strategy.merge, to_merge, {}))
        resolved_types = recursive_resolve_schema(
            registry,
            type_name,
            attr_meta_,
            attr_name_normalizer,
            common_types=common_types
        )
        final_types = final_types.extend(resolved_types)

    elif isinstance(schema, (oas.UnionSchemaTypeAny, oas.UnionSchemaTypeOne)):
        if isinstance(schema, oas.UnionSchemaTypeAny):
            items = schema.any_of
        else:
            items = schema.one_of
        options = []
        for var_num, schema_ in enumerate(items, start=1):
            variant_name = camelize(f'{type_name}_var{var_num}')
            options.append(variant_name)
            resolved_types = recursive_resolve_schema(
                registry,
                variant_name,
                schema_,
                attr_name_normalizer,
                common_types=common_types,
            )
            final_types = final_types.extend(resolved_types)

        final_types.append(
            TypeContext(
                name=f'Union[{", ".join(options)}]',
                attrs=pvector(),
                common_reference_as=type_name
            )
        )

    elif isinstance(schema, oas.ObjectWithAdditionalProperties):
        pass

    else:
        raise NotImplementedError(f'Unsupported recursive type: {schema}')

    return final_types


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


def iter_supported_methods(common_types: ResolvedTypes, path: oas.PathItem) -> SupportedMethods:
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

            if isinstance(request_schema, oas.Reference):
                request_types = [common_types[request_schema.ref.name]._replace(common_reference_as='Request')]
            else:
                request_types = recursive_resolve_schema(
                    {}, 'Request', request_schema,
                    attr_name_normalizer=underscore,
                    common_types=common_types
                )
        else:
            request_types = [DEFAULT_REQUEST_TYPE]


        response_is_stream = False
        if method.responses:
            supported_status = '200'
            try:
                response = method.responses[supported_status]
            except KeyError:

                supported_status, response = list(method.responses.items())[0]

            if not response.content:
                response_types = [DEFAULT_RESPONSE_TYPE]
            else:

                for content_type, meta in response.content.items():
                    if content_type.format in (oas.ContentTypeFormat.JSON,
                                               oas.ContentTypeFormat.ANYTHING,
                                               oas.ContentTypeFormat.FORM_URLENCODED,
                                               oas.ContentTypeFormat.EVENT_STREAM):
                        response_schema = meta.schema
                        response_is_stream = content_type.format in (oas.ContentTypeFormat.EVENT_STREAM, oas.ContentTypeFormat.BINARY_STREAM)
                        break
                else:
                    last_response = list(response.content.items())[-1][1]
                    response_schema = last_response.schema
                if isinstance(response_schema, oas.Reference):
                    response_types = [common_types[response_schema.ref.name]._replace(common_reference_as='Response')]
                else:
                    response_types = recursive_resolve_schema(
                        {}, 'Response', response_schema,
                        attr_name_normalizer=underscore,
                        common_types=common_types,
                    )
        else:
            response_types = [DEFAULT_RESPONSE_TYPE]

        query_params_type = infer_params_type(
            params.query_params,
            name_normalizer=underscore,
            default=DEFAULT_QUERY_PARAMS_TYPE
        )
        path_params_type  = infer_params_type(params.path_params)
        header_type       = infer_params_type(params.header_params,
                                              name_normalizer=lambda x: underscore(x.lower()),
                                              default=DEFAULT_HEADERS_TYPE)

        yield EndpointMethod(
            name=name,
            method=method,
            params=params,
            path_params_type=path_params_type,
            query_params_type=query_params_type,
            request_types=request_types,
            response_types=response_types,
            headers_type=header_type,
            response_is_stream=response_is_stream
        )


def infer_params_type(params: Sequence[oas.OperationParameter],
                      name_normalizer: Callable[[str], str] = lambda x: x,
                      default: TypeContext = DEFAULT_PATH_PARAMS_TYPE) -> TypeContext:
    if not params:
        return default

    rv = default
    for param in params:
        if param.required:
            default_value: Optional[str] = None
        else:
            default_value = 'None'

        datatype = python_type_from_openapi_schema(param.schema)

        normalized_name = name_normalizer(param.name)

        rv = rv._replace(
            attrs=rv.attrs.append(
                TypeAttr(
                    name=normalized_name,
                    datatype=datatype.name,
                    docstring=datatype.docstring,
                    is_required=param.required,
                    default=default_value,
                )
            )
        )
    return rv


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


merge_strategy = deepmerge.Merger(
    [
        (list, "append"),
        (dict, "merge"),
        (frozenset, add_to_set),
    ],
    ["override"],
    ["override"]
)
