from enum import Enum
from typing import ( Mapping
                   , NamedTuple
                   , TypeVar
                   , Optional
                   , Any
                   , Iterable
                   , Tuple
                   , Generator
                   , Protocol
                   , Callable
                   )
import requests
from inflection import dasherize
from pyrsistent import pmap


__all__ = ('Client', 'Method', 'Stream')


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
            json=payload,
            headers={dasherize(k): v for k, v in headers.items() if v is not None}
        ).prepare()

        return http.send(req,
            stream=is_stream,
            timeout=self.request_timeout
        )


NonNullableItems = Iterable[Tuple[str, Any]]


def only_provided_values(xs: NonNullableItems) -> Mapping[str, Any]:
    return {k: v for k, v in xs if v is not None}


T = TypeVar('T')


class Stream(NamedTuple):
    """ Stream wrapper with a few helper methods
    """
    response: requests.Response
    """ response stream that needs to be closed regardless stream consumption
    strategy
    """
    def byte_chunks(self, size: int) -> Generator[bytes, None, None]:
        """ iterate over bytes of size ``chunk_size`` coming to the receiving socket
        """
        # enter the context as we need to close the stream upon exhaustion or GC
        with self.response:
            for chunk in self.response.iter_content(chunk_size=size):
                yield chunk

    def byte_lines(self) -> Generator[bytes, None, None]:
        """ iterate over byte lines
        """
        # enter the context as we need to close the stream upon exhaustion or GC
        with self.response:
            for line in self.response.iter_lines():
                # filter out keep-alive new lines
                if line:
                    yield line

    def text_lines(self) -> Generator[str, None, None]:
        """ iterate over textual lines
        """
        for line in self.byte_lines():
            yield line.decode('utf-8')

    def map_byte_chunks(self, f: Callable[[bytes], T], size: int) -> Generator[T, None, None]:
        for chunk in self.byte_chunks(size=size):
            yield f(chunk)

    def map_byte_lines(self, f: Callable[[bytes], T]) -> Generator[T, None, None]:
        for line in self.byte_lines():
            yield f(line)

    def map_text_lines(self, f: Callable[[str], T]) -> Generator[T, None, None]:
        for line in self.text_lines():
            yield f(line)
