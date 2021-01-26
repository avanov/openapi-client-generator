""" Auto-generated by openapi-client-generator
https://github.com/avanov/openapi-client-generator
"""
from enum import Enum
from typing import NamedTuple, Callable, Optional, Type, Mapping, Union

from link_example.common import http
from link_example.common.types import *


__all__ = (
    "call",
    "Params",
    "Response",
)


class Params(NamedTuple):
    """Parameters for the endpoint path placeholders"""

    username: str

    slug: str

    pid: str


Response = pullrequest


class Headers(NamedTuple):
    """"""

    accept_charset: str = "utf-8"

    accept: str = "application/json"

    authorization: Optional[str] = None


METHOD = http.Method(__name__.split(".")[-1])
URL = "2.0/repositories/{username}/{slug}/pullrequests/{pid}"


parse_params, dump_params = underscored ^ Params


parse_headers, dump_headers = dasherized ^ Headers


response_overrides: AttrOverrides = {}
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
        headers=http.only_provided_values(dump_headers(headers).items()),
        is_stream=IS_STREAMING_RESPONSE,
    )

    return parse_response(resp.json())
