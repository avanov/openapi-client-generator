from typing import NamedTuple
from typeit import TypeConstructor

from example_client.common import *


__all__ = ('Params', 'Request', 'Response', 'request')


class Params(NamedTuple):
    pass


class Request(NamedTuple):
    pass


class Response(NamedTuple):
    pass


METHOD = http.Method(__name__.split('.')[-1])
URL = __name__.replace('.', '/')


parse_request, serialize_request = TypeConstructor ^ Request
parse_response, serialize_response = TypeConstructor ^ Response


def request(r: Request) -> Response:
    result = http.make_call(METHOD, URL)
    return parse_response(result)