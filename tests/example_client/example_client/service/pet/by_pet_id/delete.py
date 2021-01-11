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
    "Response",
)


class Params(NamedTuple):
    """Parameters for the endpoint path placeholders"""

    petId: int


Response = None


class Headers(NamedTuple):
    """"""

    accept: str = "application/json"

    accept_charset: str = "utf-8"

    authorization: Optional[str] = None

    api_key: Optional[str] = None


METHOD = http.Method(__name__.split(".")[-1])
URL = "pet/{pet_id}"


parse_response, serialize_response = camelized(Response)


def call(
    client: http.Client,
    params: Params,
    headers: Headers = Headers(),
) -> Response:

    url = URL.format(**params._asdict())

    resp = client.make_call(
        method=METHOD,
        url=url,
        headers=headers._asdict(),
        is_stream=False,
    )
    return parse_response(resp.json())
