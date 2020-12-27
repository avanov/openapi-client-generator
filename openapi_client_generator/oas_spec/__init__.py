from enum import Enum
from pyrsistent import pmap, pvector
from pyrsistent.typing import PVector, PMap

from typing import Literal, NewType
from typing import Mapping
from typing import Any, NamedTuple, Optional, Sequence, FrozenSet, Union
from typeit import TypeConstructor


class IntegerValue(NamedTuple):
    type: Literal['integer']
    format: str = ''


class StringValue(NamedTuple):
    type: Literal['string']
    format: str = ''
    description: str = ''
    enum: PVector[str] = pvector()
    example: str = ''


class RefValue(NamedTuple):
    ref: str


class ObjectValue(NamedTuple):
    type: Literal['object']
    properties: Mapping[str, 'SchemaValue']  # type: ignore


class ArrayValue(NamedTuple):
    type: Literal['array']
    items: 'SchemaValue'  # type: ignore


SchemaValue = Union[StringValue, IntegerValue, RefValue, ObjectValue, ArrayValue]  # type: ignore


class ObjectSchema(NamedTuple):
    type: Literal['object']
    properties: Mapping[str, SchemaValue]
    required: FrozenSet[str] = frozenset()
    description: str = ''


class ArraySchema(NamedTuple):
    type: Literal['array']
    items: SchemaValue


class ResponseRef(NamedTuple):
    """ Values that are referenced as $response.body#/some/path
    """
    operationId: str
    parameters: Mapping[str, str]


class ObjectRef(NamedTuple):
    """ Values that are referenced as #/components/schemas/<SomeType>
    """
    ref: str


class ProductSchemaType(NamedTuple):
    allOf: Sequence['SchemaType']  # type: ignore


SchemaType = Union[ObjectSchema, ArraySchema, ResponseRef, ObjectRef, ProductSchemaType]  # type: ignore


class Components(NamedTuple):
    schemas: Mapping[str, SchemaType]
    links: Mapping[str, SchemaType] = pmap()


class Server(NamedTuple):
    url: str


class InfoLicense(NamedTuple):
    name: str
    url: str = ''


class InfoContact(NamedTuple):
    name: str
    email: str
    url: str


class Info(NamedTuple):
    version: str
    """ API version
    """
    title: str
    license: Optional[InfoLicense]
    contact: Optional[InfoContact]
    termsOfService: str = ''
    description: str = ''


class SpecFormat(Enum):
    V3_0_0 = '3.0.0'
    V3_0_1 = '3.0.1'


class MethodParameter(NamedTuple):
    name: str
    in_: str
    schema: SchemaValue
    required: bool = False
    description: str = ''
    style: str = ''


HTTPCode = NewType('HTTPCode', str)
HeaderName = NewType('HeaderName', str)


class ResponseContentType(Enum):
    """ Response content type
    """
    JSON = 'application/json'


class Header(NamedTuple):
    """ response header
    """
    schema: SchemaValue
    description: str = ''


class ResponseContent(NamedTuple):
    schema: PMap[str, Any] = pmap()
    example: PMap[str, Any] = pmap()


class Response(NamedTuple):
    """ Response of an endpoint
    """
    content: PMap[ResponseContentType, ResponseContent] = pmap()
    headers: PMap[HeaderName, Header] = pmap()
    description: str = ''


class Method(NamedTuple):
    summary: str = ''
    operationId: str = ''
    description: str = ''
    tags: FrozenSet[str] = frozenset()
    parameters: FrozenSet[MethodParameter] = frozenset()
    responses: Mapping[HTTPCode, Response] = pmap()
    callbacks: Mapping[str, Mapping[str, Any]] = pmap()


class Methods(NamedTuple):
    """ Describes endpoint methods
    """
    head: Optional[Method]
    get: Optional[Method]
    post: Optional[Method]
    put: Optional[Method]
    patch: Optional[Method]
    delete: Optional[Method]


class Specification(NamedTuple):
    openapi: SpecFormat
    """ Spec format version
    """
    info: Info
    """ Various metadata
    """
    paths: Mapping[str, Methods] = pmap()
    components: Components = Components(schemas=pmap(), links=pmap())
    servers: Sequence[Server] = pvector()


overrides = { MethodParameter.in_: 'in'
            , RefValue.ref: '$ref'
            , ObjectRef.ref: '$ref'
            }

parse_spec, serialize_spec = TypeConstructor & overrides ^ Specification
