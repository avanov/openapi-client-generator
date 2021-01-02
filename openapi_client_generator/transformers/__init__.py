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


class TypeContext(NamedTuple):
    name: str
    docstring: str = ''
    attrs: Sequence[TypeAttr] = pvector()


class EndpointMethod(NamedTuple):
    name: str
    method: oas.Operation
    params: Params
    path_params_type: TypeContext = TypeContext(name='PathParams', attrs=[])
    query_params_type: TypeContext = TypeContext(name='QueryParams', attrs=[])
    request_type: TypeContext = TypeContext(name='Request', attrs=[])
    response_type: TypeContext = TypeContext(name='Response', attrs=[])
    headers_type: TypeContext = TypeContext(
        name='Headers', attrs=[
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
        ]
    )


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

        yield EndpointMethod(
            name=name,
            method=method,
            params=Params(
                query_params=containers[oas.ParamLocation.QUERY],
                path_params=containers[oas.ParamLocation.PATH],
                header_params=containers[oas.ParamLocation.HEADER],
                cookie_params=containers[oas.ParamLocation.COOKIE],
            )
        )
