from typing import Dict, List, cast

from .base import BaseObject
from .guild import Guild
from .types import Data

__all__ = ('User',)


class User(BaseObject):
    __slots__ = ('_name', '_guilds', '_id')

    def __init__(self, data: Data) -> None:
        self._process_data(data)

    def _process_data(self, data: Data) -> None:
        self._store_snowflake(cast(int, data.get('id')))

        self._name: str = cast(str, data.get('name'))

        self._guilds: Dict[int, Guild] = {}

        for g in data.get('guilds', []):
            guild = Guild(g)
            self._guilds[guild.id] = guild

        # self._flags = data.get('flags')
        # UserFlag after ferrischat implemented it

    @property
    def name(self) -> str:
        return self._name

    @property
    def guilds(self) -> List[Guild]:
        return list(self._guilds.values())

    def __expr__(self) -> str:
        return f'<User id={self.id} name={self.name!r}>'
