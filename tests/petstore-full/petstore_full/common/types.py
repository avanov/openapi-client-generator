from enum import Enum
from typing import Optional, Sequence, Any, NamedTuple, Mapping, Union, Tuple, Type

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

AttrOverrides = Mapping[Union[property, Tuple[Type, str]], str]


class User(NamedTuple):
    """"""

    username: Optional[str] = None

    user_status: Optional[int] = None

    phone: Optional[str] = None

    password: Optional[str] = None

    last_name: Optional[str] = None

    id: Optional[int] = None

    first_name: Optional[str] = None

    email: Optional[str] = None


class ApiResponse(NamedTuple):
    """"""

    type: Optional[str] = None

    message: Optional[str] = None

    code: Optional[int] = None


class Address(NamedTuple):
    """"""

    zip: Optional[str] = None

    street: Optional[str] = None

    state: Optional[str] = None

    city: Optional[str] = None


class Customer(NamedTuple):
    """"""

    username: Optional[str] = None

    id: Optional[int] = None

    address: Optional[Sequence[Address]] = None


class OrderStatus(Enum):
    PLACED = "placed"
    APPROVED = "approved"
    DELIVERED = "delivered"


class Order(NamedTuple):
    """"""

    status: Optional[OrderStatus] = None

    ship_date: Optional[str] = None

    quantity: Optional[int] = None

    pet_id: Optional[int] = None

    id: Optional[int] = None

    complete: Optional[bool] = None


class Tag(NamedTuple):
    """"""

    name: Optional[str] = None

    id: Optional[int] = None


class Category(NamedTuple):
    """"""

    name: Optional[str] = None

    id: Optional[int] = None


class PetStatus(Enum):
    AVAILABLE = "available"
    PENDING = "pending"
    SOLD = "sold"


class Pet(NamedTuple):
    """"""

    photo_urls: Sequence[str]

    name: str

    tags: Optional[Sequence[Tag]] = None

    status: Optional[PetStatus] = None

    id: Optional[int] = None

    category: Optional[Category] = None
