from typing import NamedTuple, Callable

from example_client.common import http, types


__all__ = (
    'call',
    )










class Headers(NamedTuple):
    """ 
    """
    accept: str = 'application/json'
    accept_charset: str = 'utf-8'

METHOD = http.Method(__name__.split('.')[-1])
URL = "pet/{pet_id}"





def call(
    client: http.Client,
    
    headers: Headers = Headers(),
) -> None:
    url = '/'.join([client.service_url.rstrip('/'), URL.lstrip('/')])
    response = client.make_call(
        method=METHOD, url=url,
        headers=headers._asdict()
    )
    return None