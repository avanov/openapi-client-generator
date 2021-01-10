from enum import Enum
from typing import Optional, Sequence, Any, NamedTuple
from openapi_type.custom_types import TypeGenerator


generate_constructor_and_serializer = TypeGenerator


class OrderStatus(Enum):
    PLACED = "x"
    APPROVED = "x"
    DELIVERED = "x"


class Order(NamedTuple):
    """"""

    id: Optional[int] = None

    petId: Optional[int] = None

    quantity: Optional[int] = None

    shipDate: Optional[str] = None

    status: Optional[OrderStatus] = None

    complete: Optional[bool] = None


class Customer(NamedTuple):
    """"""

    id: Optional[int] = None

    username: Optional[str] = None

    address: Optional[Sequence[Any]] = None


class Address(NamedTuple):
    """"""

    street: Optional[str] = None

    city: Optional[str] = None

    state: Optional[str] = None

    zip: Optional[str] = None


class Category(NamedTuple):
    """"""

    id: Optional[int] = None

    name: Optional[str] = None


class User(NamedTuple):
    """"""

    id: Optional[int] = None

    username: Optional[str] = None

    firstName: Optional[str] = None

    lastName: Optional[str] = None

    email: Optional[str] = None

    password: Optional[str] = None

    phone: Optional[str] = None

    userStatus: Optional[int] = None


class Tag(NamedTuple):
    """"""

    id: Optional[int] = None

    name: Optional[str] = None


class PetCategory(NamedTuple):
    """"""

    id: Optional[int] = None

    name: Optional[str] = None


class PetStatus(Enum):
    AVAILABLE = "x"
    PENDING = "x"
    SOLD = "x"


class Pet(NamedTuple):
    """"""

    name: str

    photoUrls: Sequence[str]

    id: Optional[int] = None

    category: Optional[PetCategory] = None

    tags: Optional[Sequence[Any]] = None

    status: Optional[PetStatus] = None


class ApiResponse(NamedTuple):
    """"""

    code: Optional[int] = None

    type: Optional[str] = None

    message: Optional[str] = None
