""" A collection of functions that transform OpenAPI spec to data structures convenient for codegen.
"""
from pathlib import Path
from string import digits
from typing import NamedTuple, Mapping, Sequence, Generator, Optional

import openapi_type as oas
from inflection import underscore
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
    default: Optional[str]
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
        ),
        TypeAttr(
            name='accept_charset',
            datatype='str',
            default="'utf-8'"
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


class SpecMeta(NamedTuple):
    """ A post-processed OpenAPI specification that is convenient to use for codegen
    """
    spec: oas.OpenAPI
    """ original spec
    """
    paths: Mapping[EndpointSegments, Endpoint]


def openapi_to_codegen_metadata(spec: oas.OpenAPI) -> SpecMeta:
    paths = {}
    for path, item in spec.paths.items():
        pth = api_path_to_filepath(path)
        endpoint = Endpoint(
            path_item=item,
            supported_methods=iter_supported_methods(item)
        )
        paths[pth] = endpoint

    return SpecMeta(
        spec=spec,
        paths=paths
    )


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
            path_params_type=infer_path_params_type(params.path_params),
            query_params_type=infer_path_params_type(params.query_params, default=DEFAULT_QUERY_PARAMS_TYPE),
            request_type=infer_request_type(),
            response_type=infer_response_type(),
            headers_type=infer_headers_type(),
        )


def infer_path_params_type(params: Sequence[oas.OperationParameter],
                           default: TypeContext = DEFAULT_PATH_PARAMS_TYPE) -> TypeContext:
    if not params:
        return default

    rv = default
    for param in params:
        schema = param.schema
        if param.required:
            datatype = '{T}'
            default_value: Optional[str] = None
        else:
            datatype = 'Optional[{T}]'
            default_value = 'None'

        T = python_type_from_openapi_schema(param.schema)

        rv = rv._replace(
            attrs=rv.attrs.append(
                TypeAttr(
                    name=param.name,
                    datatype=datatype.format(T=T.name),
                    default=default_value,
                    docstring=T.docstring,
                )
            )
        )
    return rv


def infer_query_params_type(params: Sequence[oas.OperationParameter],
                            default: TypeContext = DEFAULT_QUERY_PARAMS_TYPE) -> TypeContext:
    return default


def infer_request_type(default: TypeContext = DEFAULT_REQUEST_TYPE) -> TypeContext:
    return default


def infer_response_type(default: TypeContext = DEFAULT_RESPONSE_TYPE) -> TypeContext:
    return default


def infer_headers_type(default: TypeContext = DEFAULT_HEADERS_TYPE) -> TypeContext:
    return default


class TypeDescr(NamedTuple):
    name: str
    default_value: Optional[str] = None
    docstring: str = ''


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
