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

    content_type: str = "application/json"

    accept_charset: str = "utf-8"

    accept: str = "application/json"

    authorization: Optional[str] = None


METHOD = http.Method(__name__.split(".")[-1])
URL = "/"


parse_headers, dump_headers = dasherized ^ Headers


response_overrides: AttrOverrides = {}
parse_response, dump_response = camelized & response_overrides ^ Response


IS_STREAMING_RESPONSE = False


def call(
    client: http.Client,
    headers: Headers,
) -> Response:

    url = URL

    resp = client.make_call(
        method=METHOD,
        url=url,
        headers=http.only_provided_values(dump_headers(headers).items()),
        is_stream=IS_STREAMING_RESPONSE,
    )

    return parse_response(resp.json())
