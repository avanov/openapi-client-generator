""" A collection of functions that transform OpenAPI spec to data structures convenient for codegen.
"""
from pathlib import Path
from string import digits
from typing import NamedTuple, Mapping, Sequence, Generator, Any, Optional

import openapi_type as oas
from inflection import underscore
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


class EndpointMethod(NamedTuple):
    name: str
    method: oas.Operation
    params_type: Mapping[str, Any] = pmap()
    request_type: Mapping[str, Any] = pmap()
    response_type: Mapping[str, Any] = pmap()
    headers_type: Mapping[str, Any] = pmap()


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


def iter_supported_methods(path: oas.PathItem) -> SupportedMethods:
    methods = (path.head,
               path.get,
               path.post,
               path.put,
               path.patch,
               path.delete,
               path.trace)
    for name, method in path._asdict().items():
        if not method or method not in methods:
            continue
        yield EndpointMethod(
            name=name,
            method=method,
        )
