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


class user(NamedTuple):
    """"""

    uuid: Optional[str] = None

    username: Optional[str] = None


class repository(NamedTuple):
    """"""

    slug: Optional[str] = None

    owner: Optional[user] = None


class pullrequest(NamedTuple):
    """"""

    title: Optional[str] = None

    repository: Optional[repository] = None

    id: Optional[int] = None

    author: Optional[user] = None
