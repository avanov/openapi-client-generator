""" Auto-generated by openapi-client-generator
https://github.com/avanov/openapi-client-generator
"""
from enum import Enum
from typing import NamedTuple, Callable, Optional, Type, Mapping, Union

from petstore_expanded.common import http
from petstore_expanded.common.types import *


__all__ = (
    "call",
    "Query",
    "Response",
)


class Query(NamedTuple):
    """Parameters for the endpoint query string"""

    tags: Optional[Sequence[str]] = None

    limit: Optional[int] = None


Response = Sequence[Pet]


class Headers(NamedTuple):
    """"""

    accept_charset: str = "utf-8"

    accept: str = "application/json"

    authorization: Optional[str] = None


METHOD = http.Method(__name__.split(".")[-1])
URL = "pets"


query_overrides: AttrOverrides = {}
parse_query, dump_query = dasherized & query_overrides ^ Query


parse_headers, dump_headers = dasherized ^ Headers


response_overrides: AttrOverrides = {}
parse_response, dump_response = camelized & response_overrides ^ Response


IS_STREAMING_RESPONSE = False


def call(
    client: http.Client,
    query: Query,
    headers: Headers,
) -> Response:

    url = URL

    resp = client.make_call(
        method=METHOD,
        url=url,
        headers=http.only_provided_values(dump_headers(headers).items()),
        query=http.only_provided_values(dump_query(query).items()),
        is_stream=IS_STREAMING_RESPONSE,
    )

    return parse_response(resp.json())
