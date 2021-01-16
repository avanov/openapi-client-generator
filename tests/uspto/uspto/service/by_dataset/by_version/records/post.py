""" Auto-generated by openapi-client-generator
https://github.com/avanov/openapi-client-generator
"""
from enum import Enum
from typing import NamedTuple, Callable, Optional, Type, Mapping, Union

from uspto.common import http
from uspto.common.types import *


__all__ = (
    "call",
    "Params",
    "Request",
    "Response",
)


class Params(NamedTuple):
    """Parameters for the endpoint path placeholders"""

    version: str

    dataset: str


class Request(NamedTuple):
    """"""

    criteria: str = "*:*"

    start: Optional[int] = 0

    rows: Optional[int] = 100


Response = Sequence[Mapping[Any, Any]]


class Headers(NamedTuple):
    """"""

    accept_charset: str = "utf-8"

    accept: str = "application/json"

    authorization: Optional[str] = None


METHOD = http.Method(__name__.split(".")[-1])
URL = "{dataset}/{version}/records"


parse_params, dump_params = underscored ^ Params


parse_headers, dump_headers = dasherized ^ Headers


request_overrides = {}
parse_request, dump_request = camelized & request_overrides ^ Request


response_overrides = {}
parse_response, dump_response = camelized & response_overrides ^ Response


def call(
    client: http.Client,
    request: Request,
    params: Params,
    headers: Headers,
) -> Response:

    url = URL.format(**dump_params(params))

    resp = client.make_call(
        method=METHOD,
        url=url,
        headers=dump_headers(headers),
        payload=dump_request(request),
        is_stream=False,
    )
    return parse_response(resp.json())
