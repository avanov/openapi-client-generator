from typing import NamedTuple, Callable
from typeit import TypeConstructor

from example_client.common import *


__all__ = ('Params', 'Request', 'Response', 'request')


class PathParams(NamedTuple):
    """ 
    """
    

class QueryParams(NamedTuple):
    """ 
    """
    

class Request(NamedTuple):
    """ 
    """
    

class Response(NamedTuple):
    """ 
    """
    

class Headers(NamedTuple):
    """ 
    """
    accept: str = 'application/json'
    accept_charset: str = 'utf-8'
    

METHOD = http.Method(__name__.split('.')[-1])
URL = "user/logout"


parse_request, serialize_request = TypeConstructor ^ Request
parse_response, serialize_response = TypeConstructor ^ Response


def request(r: Request) -> None:
    return None