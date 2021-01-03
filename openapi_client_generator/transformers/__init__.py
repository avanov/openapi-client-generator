""" A collection of functions that transform OpenAPI spec to data structures convenient for codegen.
"""
from enum import Enum
from pathlib import Path
from string import digits
from typing import NamedTuple, Mapping, Sequence, Generator, Optional, Any, Union

import openapi_type as oas
from inflection import underscore, camelize
from pyrsistent.typing import PVector, PMap
from pyrsistent import pmap, pvector


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

    def datatype_repr(self) -> str:
        if self.is_required:
            return f'Optional[{self.datatype}]'
        return self.datatype


class TypeDescr(NamedTuple):
    name: str
    default_value: Optional[str] = None
    docstring: str = ''


class TypeContext(NamedTuple):
    name: str
    docstring: str = ''
    attrs: PVector[TypeAttr] = pvector()


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
    ])
)


class EndpointMethod(NamedTuple):
    name:              str
    method:            oas.Operation
    params:            Params
    path_params_type:  TypeContext = DEFAULT_PATH_PARAMS_TYPE
    query_params_type: TypeContext = DEFAULT_QUERY_PARAMS_TYPE
    request_type:      TypeContext = DEFAULT_REQUEST_TYPE
    response_type:     TypeContext = DEFAULT_RESPONSE_TYPE
    headers_type:      TypeContext = DEFAULT_HEADERS_TYPE


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
    for path, item in spec.paths.items():
        pth = api_path_to_filepath(path)
        endpoint = Endpoint(
            path_item=item,
            supported_methods=iter_supported_methods(item)
        )
        paths[pth] = endpoint

    common_types = resolve_schemas(spec.components.schemas)

    return SpecMeta(
        spec=spec,
        paths=paths,
        common_types=common_types
    )


def resolve_schemas(schemas: Mapping[str, oas.SchemaType]) -> ResolvedTypes:
    resolved_types = pvector()
    for type_name, schema in schemas.items():
        resolved_types = resolved_types.extend(recursive_resolve_schema(schemas, type_name, schema))
    return {x.name: x for x in resolved_types}


def recursive_resolve_schema(
    registry: Mapping[str, oas.SchemaType],
    type_name: str,
    schema: oas.SchemaType
) -> PVector[TypeContext]:
    final_types = pvector()
    if isinstance(schema, oas.StringValue):
        raise NotImplementedError('String Schema')
    elif isinstance(schema, oas.ObjectSchema):
        attrs = pvector()
        for attr_name, attr_meta in schema.properties.items():
            to_resolve: Union[None, oas.SchemaValue, oas.RecursiveAttrs] = None
            default = None
            if isinstance(attr_meta, oas.StringValue):
                if attr_meta.enum:
                    raise NotImplementedError('String Enum')
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
                        attr_meta_
                    )
                    final_types = final_types.extend(resolved_types)
                else:
                    raise NotImplementedError('Reference Value')

            elif isinstance(attr_meta, oas.ArrayValue):
                attr_datatype = 'Sequence[{T}]'
                to_resolve = attr_meta.items

            elif isinstance(attr_meta, oas.ObjectValue):
                attr_datatype = '{T}'
                to_resolve = attr_meta.properties

            elif isinstance(attr_meta, oas.ObjectWithAdditionalProperties):
                raise NotImplementedError(' Additional properties')
            else:
                raise TypeError(f'Unrecognised schema type: {attr_meta}')

            if to_resolve:
                T = 'Any'
                attr_datatype = attr_datatype.format(T=T)

            attrs = attrs.append(TypeAttr(
                name=attr_name,
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

    elif isinstance(schema, oas.ArraySchema):
        schema

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


def iter_supported_methods(path: oas.PathItem) -> SupportedMethods:
    methods = ( path.head
              , path.get
              , path.post
              , path.put
              , path.patch
              , path.delete
              , path.trace
              )
    supported_methods = ((nam, met) for nam, met in path._asdict().items() if met and met in methods)
    for name, method in supported_methods:
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

        yield EndpointMethod(
            name=name,
            method=method,
            params=params,
            path_params_type=infer_params_type(params.path_params),
            query_params_type=infer_params_type(params.query_params, default=DEFAULT_QUERY_PARAMS_TYPE),
            request_type=infer_request_type(),
            response_type=infer_response_type(),
            headers_type=infer_headers_type(),
        )


def infer_params_type(params: Sequence[oas.OperationParameter],
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

        rv = rv._replace(
            attrs=rv.attrs.append(
                TypeAttr(
                    name=param.name,
                    datatype=datatype.name,
                    docstring=datatype.docstring,
                    is_required=param.required,
                    default=default_value,
                )
            )
        )
    return rv


def infer_request_type(default: TypeContext = DEFAULT_REQUEST_TYPE) -> TypeContext:
    return default


def infer_response_type(default: TypeContext = DEFAULT_RESPONSE_TYPE) -> TypeContext:
    return default


def infer_headers_type(default: TypeContext = DEFAULT_HEADERS_TYPE) -> TypeContext:
    return default


def python_type_from_openapi_schema(schema: oas.SchemaValue) -> TypeDescr:
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
