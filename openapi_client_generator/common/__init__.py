""" Common utilities shared by all clients

While working on this namespace make sure that it doesn't import
anything from ``openapi_client_generator``, as it will not be available to generated clients.
"""
from . import http
from . import types


__all__ = ('http', 'types')
