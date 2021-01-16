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


class Pet(NamedTuple):
    """"""

    name: str

    id: int

    tag: Optional[str] = None


class NewPet(NamedTuple):
    """"""

    name: str

    tag: Optional[str] = None

    id: Optional[int] = None


class Error(NamedTuple):
    """"""

    message: str

    code: int
