from enum import Enum
from typing import Mapping, NamedTuple, TypeVar, Optional, Type, Any, Iterable, Tuple
from typing import Protocol

import requests
from inflection import dasherize
from pyrsistent import pmap


__all__ = ('Client', 'Method')


http = requests.Session()


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


Headers = Mapping[str, Optional[str]]
Seconds = int


class Client(NamedTuple):
    service_url: str
    request_timeout: Seconds = 30

    def call(
        self,
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
        headers: Headers = pmap(),
        query: Optional[Mapping[str, Any]] = None,
        payload: Optional[Mapping[str, Any]] = None,
        is_stream: bool = False
    ) -> requests.Response:
        url = '/'.join([self.service_url.rstrip('/'), url.lstrip('/')])

        req = requests.Request(
            method.value.upper(),
            url,
            params=query,
            data=payload,
            headers={dasherize(k): v for k, v in headers.items() if v is not None}
        ).prepare()

        return http.send(req,
            stream=is_stream,
            timeout=self.request_timeout
        )


NonNullableItems = Iterable[Tuple[str, Any]]


def only_provided_values(xs: NonNullableItems) -> Mapping[str, Any]:
    return {k: v for k, v in xs if v is not None}
