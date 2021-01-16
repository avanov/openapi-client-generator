""" Auto-generated by openapi-client-generator
https://github.com/avanov/openapi-client-generator
"""
from enum import Enum
from typing import NamedTuple, Callable, Optional, Type, Mapping, Union

from petstore_full.common import http
from petstore_full.common.types import *


__all__ = (
    "call",
    "Params",
    "Query",
    "Response",
)


class Params(NamedTuple):
    """Parameters for the endpoint path placeholders"""

    petId: int


class Query(NamedTuple):
    """Parameters for the endpoint query string"""

    status: Optional[str] = None

    name: Optional[str] = None


Response = Type[None]


class Headers(NamedTuple):
    """"""

    accept_charset: str = "utf-8"

    accept: str = "application/json"

    authorization: Optional[str] = None


METHOD = http.Method(__name__.split(".")[-1])
URL = "pet/{pet_id}"


parse_params, dump_params = underscored ^ Params


query_overrides = {}
parse_query, dump_query = dasherized & query_overrides ^ Query


parse_headers, dump_headers = dasherized ^ Headers


response_overrides = {}
parse_response, dump_response = camelized & response_overrides ^ Response


def call(
    client: http.Client,
    params: Params,
    query: Query,
    headers: Headers,
) -> Response:

    url = URL.format(**dump_params(params))

    resp = client.make_call(
        method=METHOD,
        url=url,
        headers=dump_headers(headers),
        query=dump_query(query),
        is_stream=False,
    )
    return parse_response(resp.json())
