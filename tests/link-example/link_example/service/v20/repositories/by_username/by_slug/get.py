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


Response = repository


class Headers(NamedTuple):
    """"""

    accept_charset: str = "utf-8"

    accept: str = "application/json"

    authorization: Optional[str] = None


METHOD = http.Method(__name__.split(".")[-1])
URL = "2.0/repositories/{username}/{slug}"


parse_params, dump_params = underscored ^ Params


parse_headers, dump_headers = dasherized ^ Headers


parse_response, dump_response = camelized & {} ^ Response


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
        is_stream=False,
    )
    return parse_response(resp.json())
