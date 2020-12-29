from enum import Enum
from typing import Mapping

import urllib3
from pyrsistent import pmap


__all__ = ('make_call', 'Method')


http = urllib3.PoolManager()


class Method(Enum):
    HEAD = 'head'
    GET = 'get'
    POST = 'post'
    PUT = 'put'
    PATCH = 'patch'
    DELETE = 'delete'
    TRACE = 'trace'
    CONNECT = 'connect'
    OPTIONS = 'options'


def make_call(method: Method, url: str, headers: Mapping[str, str] = pmap()) -> Mapping:
    http.request(method.value.upper(), url, headers=headers)
    return {}
