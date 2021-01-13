""" Auto-generated by openapi-client-generator
https://github.com/avanov/openapi-client-generator
"""
from enum import Enum
from typing import NamedTuple, Callable, Optional, Type

from example_client.common import http
from example_client.common.types import *


__all__ = (
    "call",
    "Request",
    "Response",
)


Request = Sequence[User]

Response = User


class Headers(NamedTuple):
    """"""

    accept_charset: str = "utf-8"

    accept: str = "application/json"

    authorization: Optional[str] = None


METHOD = http.Method(__name__.split(".")[-1])
URL = "user/createWithList"


parse_request, dump_request = camelized(Request)


parse_response, serialize_response = camelized(Response)


def call(
    client: http.Client,
    request: Request,
    headers: Headers = Headers(),
) -> Response:

    url = URL

    resp = client.make_call(
        method=METHOD,
        url=url,
        headers=headers._asdict(),
        payload=dump_request(request),
        is_stream=False,
    )
    return parse_response(resp.json())
