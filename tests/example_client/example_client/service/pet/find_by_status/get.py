from typing import NamedTuple, Callable

from example_client.common import http, types


__all__ = (
    'request',
    )










class Headers(NamedTuple):
    """ 
    """
    accept: str = 'application/json'
    accept_charset: str = 'utf-8'

METHOD = http.Method(__name__.split('.')[-1])
URL = "pet/findByStatus"





def request(client: http.Client) -> None:
    return None