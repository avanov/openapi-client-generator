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
    "Response",
)


class Params(NamedTuple):
    """Parameters for the endpoint path placeholders"""

    version: str

    dataset: str


Response = str


class Headers(NamedTuple):
    """"""

    accept_charset: str = "utf-8"

    accept: str = "application/json"

    authorization: Optional[str] = None


METHOD = http.Method(__name__.split(".")[-1])
URL = "{dataset}/{version}/fields"


parse_params, dump_params = underscored ^ Params


parse_headers, dump_headers = dasherized ^ Headers


response_overrides: Mapping[str, Any] = {}
parse_response, dump_response = camelized & response_overrides ^ Response


IS_STREAMING_RESPONSE = False


def call(
    client: http.Client,
    params: Params,
    headers: Headers,
) -> Response:

    url = URL.format(**dump_params(params))

    resp = client.make_call(
        method=METHOD,
        url=url,
        headers=dump_headers(headers),
        is_stream=IS_STREAMING_RESPONSE,
    )
    return parse_response(resp.json())
