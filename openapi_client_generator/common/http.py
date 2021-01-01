from enum import Enum
from typing import Mapping, NamedTuple, TypeVar, Callable, Optional, Type
from typing import Protocol

import urllib3
from pyrsistent import pmap


__all__ = ('Client', 'make_call', 'Method')


http = urllib3.PoolManager()


Req = TypeVar('Req')
Resp = TypeVar('Resp')
Param = TypeVar('Param')
Headrs = TypeVar('Headrs')


class Endpoint(Protocol[Req, Resp, Param, Headrs]):
    Request: Req
    Response: Resp
    Params: Param
    Headers: Headrs


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


Headers = Mapping[str, str]


class Client(NamedTuple):
    service_url: str

    def call(self,
                 endpoint: Endpoint[Type[Req], Type[Resp], Type[Param], Type[Headrs]],
                 request: Req,
                 params: Param,
                 headers: Headrs
                 ) -> Resp:
        return endpoint.Response()

    def make_call(
        self,
        method: Method,
        url: str,
        headers: Headers = pmap()
    ) -> Mapping:
        url = '/'.join([self.service_url.rstrip('/'), url.lstrip('/')])
        return http.request(method.value.upper(), url, headers=headers)
