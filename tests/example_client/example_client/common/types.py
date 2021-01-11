from enum import Enum
from typing import Optional, Sequence, Any, NamedTuple

import inflection
from typeit import TypeConstructor, flags


generate_constructor_and_serializer = TypeConstructor


class AttrStyle(Enum):
    CAMELIZED = "camelized"
    DASHERIZED = "dasherized"
    UNDERSCORED = "underscored"


camelized = TypeConstructor & flags.GlobalNameOverride(
    lambda x: inflection.camelize(x, uppercase_first_letter=False)
)
dasherized = TypeConstructor & flags.GlobalNameOverride(inflection.dasherize)
underscored = TypeConstructor


class OrderStatus(Enum):
    PLACED = "placed"
    APPROVED = "approved"
    DELIVERED = "delivered"


class Order(NamedTuple):
    """"""

    id: Optional[int] = None

    pet_id: Optional[int] = None

    quantity: Optional[int] = None

    ship_date: Optional[str] = None

    status: Optional[OrderStatus] = None

    complete: Optional[bool] = None


class Address(NamedTuple):
    """"""

    street: Optional[str] = None

    city: Optional[str] = None

    state: Optional[str] = None

    zip: Optional[str] = None


class Customer(NamedTuple):
    """"""

    id: Optional[int] = None

    username: Optional[str] = None

    address: Optional[Sequence[Address]] = None


class Category(NamedTuple):
    """"""

    id: Optional[int] = None

    name: Optional[str] = None


class User(NamedTuple):
    """"""

    id: Optional[int] = None

    username: Optional[str] = None

    first_name: Optional[str] = None

    last_name: Optional[str] = None

    email: Optional[str] = None

    password: Optional[str] = None

    phone: Optional[str] = None

    user_status: Optional[int] = None


class Tag(NamedTuple):
    """"""

    id: Optional[int] = None

    name: Optional[str] = None


class PetStatus(Enum):
    AVAILABLE = "available"
    PENDING = "pending"
    SOLD = "sold"


class Pet(NamedTuple):
    """"""

    name: str

    photo_urls: Sequence[str]

    id: Optional[int] = None

    category: Optional[Category] = None

    tags: Optional[Sequence[Tag]] = None

    status: Optional[PetStatus] = None


class ApiResponse(NamedTuple):
    """"""

    code: Optional[int] = None

    type: Optional[str] = None

    message: Optional[str] = None
