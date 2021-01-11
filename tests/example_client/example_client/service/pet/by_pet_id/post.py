""" Auto-generated by openapi-client-generator
https://github.com/avanov/openapi-client-generator
"""
from enum import Enum
from typing import NamedTuple, Callable, Optional

from example_client.common import http
from example_client.common.types import *


__all__ = (
    "call",
    "Params",
    "Query",
)


class Params(NamedTuple):
    """Parameters for the endpoint path placeholders"""

    petId: int


class Query(NamedTuple):
    """Parameters for the endpoint query string"""

    name: Optional[str] = None

    status: Optional[str] = None


class Headers(NamedTuple):
    """"""

    accept: str = "application/json"

    accept_charset: str = "utf-8"

    authorization: Optional[str] = None


METHOD = http.Method(__name__.split(".")[-1])
URL = "pet/{pet_id}"


parse_query, dump_query = dasherized(Query)


def call(
    client: http.Client,
    params: Params,
    query: Query,
    headers: Headers = Headers(),
) -> None:

    url = URL.format(**params._asdict())

    resp = client.make_call(
        method=METHOD,
        url=url,
        headers=headers._asdict(),
        query=dump_query(query),
        is_stream=False,
    )
    return parse_response(resp.json())
