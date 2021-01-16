""" Auto-generated by openapi-client-generator
https://github.com/avanov/openapi-client-generator
"""
from enum import Enum
from typing import NamedTuple, Callable, Optional, Type, Mapping, Union

from api_with_examples.common import http
from api_with_examples.common.types import *


__all__ = (
    "call",
    "Response",
)


Response = Any


class Headers(NamedTuple):
    """"""

    accept_charset: str = "utf-8"

    accept: str = "application/json"

    authorization: Optional[str] = None


METHOD = http.Method(__name__.split(".")[-1])
URL = "v2"


parse_headers, dump_headers = dasherized ^ Headers


parse_response, dump_response = camelized & {} ^ Response


def call(
    client: http.Client,
    headers: Headers,
) -> Response:

    url = URL

    resp = client.make_call(
        method=METHOD,
        url=url,
        headers=dump_headers(headers),
        is_stream=False,
    )
    return parse_response(resp.json())
