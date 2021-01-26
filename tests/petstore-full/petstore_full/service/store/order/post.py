""" Auto-generated by openapi-client-generator
https://github.com/avanov/openapi-client-generator
"""
from enum import Enum
from typing import NamedTuple, Callable, Optional, Type, Mapping, Union

from petstore_full.common import http
from petstore_full.common.types import *


__all__ = (
    "call",
    "Request",
    "Response",
)


Request = Order

Response = Order


class Headers(NamedTuple):
    """"""

    accept_charset: str = "utf-8"

    accept: str = "application/json"

    authorization: Optional[str] = None


METHOD = http.Method(__name__.split(".")[-1])
URL = "store/order"


parse_headers, dump_headers = dasherized ^ Headers


request_overrides: AttrOverrides = {}
parse_request, dump_request = camelized & request_overrides ^ Request


response_overrides: AttrOverrides = {}
parse_response, dump_response = camelized & response_overrides ^ Response


IS_STREAMING_RESPONSE = False


def call(
    client: http.Client,
    request: Request,
    headers: Headers,
) -> Response:

    url = URL

    resp = client.make_call(
        method=METHOD,
        url=url,
        headers=http.only_provided_values(dump_headers(headers).items()),
        payload=dump_request(request),
        is_stream=IS_STREAMING_RESPONSE,
    )

    return parse_response(resp.json())
