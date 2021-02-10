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

    uuid: Optional[str] = None

    username: Optional[str] = None


class Repository(NamedTuple):
    """"""

    slug: Optional[str] = None

    owner: Optional[User] = None


class Pullrequest(NamedTuple):
    """"""

    title: Optional[str] = None

    repository: Optional[Repository] = None

    id: Optional[int] = None

    author: Optional[User] = None
