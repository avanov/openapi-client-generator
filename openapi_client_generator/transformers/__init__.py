""" A collection of functions that transform OpenAPI spec to data structures convenient for codegen.
"""
from pathlib import Path
from string import digits
from typing import NamedTuple, Mapping, Sequence, Generator, Tuple

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
    is_placeholder: bool
    """ whether used as a placeholder
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
        return '/'.join(x.original for x in self.segments)


SupportedMethods = Generator[Tuple[str, oas.Operation], None, None]


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
    paths = pmap({
        api_path_to_filepath(path):
            Endpoint(
                path_item=item,
                supported_methods=iter_supported_methods(item)
            )
        for path, item in spec.paths.items()
    })
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
        segments = [EndpointSegment('/', 'root', False)]
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
    rv = underscore(''.join(final))
    if is_placeholder:
        rv = f'by_{rv}'
    else:
        # version tags are usually numeric
        if rv[0] in digits:
            rv = f'v{rv}'

    return EndpointSegment(
        original=seg,
        segment=rv,
        is_placeholder=is_placeholder
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
        yield name, method
