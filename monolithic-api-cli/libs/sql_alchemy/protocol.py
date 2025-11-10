# libs/sql_alchemy/protocol.py
from typing import Optional, AsyncIterator, TypeVar
from contextlib import asynccontextmanager
from pydantic import BaseModel

EntityT = TypeVar("EntityT")
DtoT = TypeVar("DtoT", bound=BaseModel)

class SqlAlchemyProtocol:
    def __init__(self, service, key: str):
        self._service = service
        self._key = key

    def key(self) -> str:
        return self._key

    def engine(self):
        return self._service.engine(self._key)

    def session(self):
        return self._service.session(self._key)

    @asynccontextmanager
    async def session_ctx(self) -> AsyncIterator:
        async with self._service.session_ctx(self._key) as s:
            yield s

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator:
        async with self._service.transaction(self._key) as s:
            yield s

    def default_key(self) -> Optional[str]:
        return self._service.default_key()
