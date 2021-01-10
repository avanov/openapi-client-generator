""" Auto-generated by openapi-client-generator
https://github.com/avanov/openapi-client-generator
"""
from typing import NamedTuple, Callable, Optional

from example_client.common import http
from example_client.common.types import *


__all__ = (
    "call",
    "Params",
)


class Params(NamedTuple):
    """Parameters for the endpoint path placeholders"""

    orderId: int


class Headers(NamedTuple):
    """"""

    accept: str = "application/json"

    accept_charset: str = "utf-8"

    authorization: Optional[str] = None


METHOD = http.Method(__name__.split(".")[-1])
URL = "store/order/{order_id}"


def call(
    client: http.Client,
    params: Params,
    headers: Headers = Headers(),
) -> None:

    url = URL.format(**params._asdict())

    response = client.make_call(
        method=METHOD,
        url=url,
        headers=headers._asdict(),
    )
    return None
