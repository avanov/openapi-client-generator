from string import digits
from typing import NamedTuple, Optional, Mapping, Any

import openapi_type as oas
from inflection import camelize, underscore
from pyrsistent.typing import PMap
from pyrsistent import pmap


NormalizedSchemas = PMap[str, oas.SchemaType]


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


def normalize_schema(schemas: Mapping[str, oas.SchemaType]) -> NormalizedSchemas:
    return pmap({camelized_python_name(k): v for k, v in schemas.items()})


def camelized_python_name(irregular_source: str) -> str:
    """
    :param irregular_source: source string that resembles a python name but that may contain invalid characters
    :return: regular camelized python name
    """
    return camelize(pythonize_path_segment(irregular_source).segment)


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
