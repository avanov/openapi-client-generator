""" A collection of functions that transform OpenAPI spec to data structures convenient for codegen.
"""
from pathlib import Path
from string import digits
from typing import NamedTuple, Mapping

import openapi_type as oas
from inflection import underscore
from pyrsistent import pmap


class SpecMeta(NamedTuple):
    """ A post-processed OpenAPI specification that is convenient to use for codegen
    """
    spec: oas.OpenAPI
    """ original spec
    """
    paths: Mapping[Path, oas.PathItem]


def openapi_to_codegen_metadata(spec: oas.OpenAPI) -> SpecMeta:
    paths = pmap({
        api_path_to_filepath(path): item for path, item in spec.paths.items()
    })
    return SpecMeta(
        spec=spec,
        paths=paths
    )


def api_path_to_filepath(api_path: str, sep: str = '/') -> Path:
    """
    :param api_path: URL path
    :param sep: separator symbol used in API path
    """
    segments = [pythonize_path_segment(x) for x in api_path.split(sep) if x.strip()]
    if not segments:
        segments = ['root']
    return Path('/'.join(segments))


def pythonize_path_segment(seg: str) -> str:
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
    return rv
