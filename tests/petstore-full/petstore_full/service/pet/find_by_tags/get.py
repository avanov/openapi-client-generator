""" Auto-generated by openapi-client-generator
https://github.com/avanov/openapi-client-generator
"""
from enum import Enum
from typing import NamedTuple, Callable, Optional, Type, Mapping, Union

from petstore_full.common import http
from petstore_full.common.types import *


__all__ = (
    "call",
    "Query",
    "Response",
)


class Query(NamedTuple):
    """Parameters for the endpoint query string"""

    tags: Optional[Sequence[str]] = None


Response = Sequence[Pet]


class Headers(NamedTuple):
    """"""

    accept_charset: str = "utf-8"

    accept: str = "application/json"

    authorization: Optional[str] = None


METHOD = http.Method(__name__.split(".")[-1])
URL = "pet/findByTags"


query_overrides = {}
parse_query, dump_query = dasherized & query_overrides ^ Query


parse_headers, dump_headers = dasherized ^ Headers


response_overrides = {}
parse_response, dump_response = camelized & response_overrides ^ Response


def call(
    client: http.Client,
    query: Query,
    headers: Headers,
) -> Response:

    url = URL

    resp = client.make_call(
        method=METHOD,
        url=url,
        headers=dump_headers(headers),
        query=dump_query(query),
        is_stream=False,
    )
    return parse_response(resp.json())
