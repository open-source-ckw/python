# libs/sql_alchemy/service.py
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, Optional
from urllib.parse import quote_plus

from nest.core import Injectable
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from libs.conf.service import ConfService
from libs.log.service import LogService

from libs.sql_alchemy.configuration import SqlAlchemyConfiguration
from libs.sql_alchemy.protocol import SqlAlchemyProtocol


@Injectable
class SqlAlchemyService:
    def __init__(self, conf: ConfService, log: LogService):
        self.conf = conf
        self.log = log

        self._cfg = SqlAlchemyConfiguration(conf, log)
        self._cfg.configure()

        self._engines: Dict[str, Any] = {}
        self._makers: Dict[str, Any] = {}

    def default_key(self) -> Optional[str]:
        return self._cfg.get_default_key()

    def set_default_key(self, name: str) -> None:
        snap = self._cfg.reconfigure(default_key=name)
        if self.log:
            self.log.info(f"[SqlAlchemyService] default connection set to '{snap.get('default_key')}'")

    def use(self, name: str) -> SqlAlchemyProtocol:
        return SqlAlchemyProtocol(self, name)

    def engine(self, name: Optional[str] = None):
        key = name or self._cfg.get_default_key()
        if not key:
            raise ValueError("No default connection configured.")
        if key in self._engines:
            return self._engines[key]
        cfg = self._cfg.get_connections().get(key)
        if not cfg:
            raise KeyError(f"Connection '{key}' not found.")
        pool = self._cfg.get_pool()
        self._build_engine(key, cfg, pool)
        return self._engines[key]

    def session(self, name: Optional[str] = None) -> AsyncSession:
        key = name or self._cfg.get_default_key()
        if not key:
            raise ValueError("No default connection configured.")
        if key not in self._makers:
            self.engine(key)
        return self._makers[key]()

    @asynccontextmanager
    async def session_ctx(self, name: Optional[str] = None) -> AsyncIterator[AsyncSession]:
        s = self.session(name)
        try:
            yield s
            await s.commit()
        except Exception:
            await s.rollback()
            raise
        finally:
            await s.close()

    @asynccontextmanager
    async def transaction(self, name: Optional[str] = None) -> AsyncIterator[AsyncSession]:
        async with self.session_ctx(name) as s:
            yield s

    async def dispose(self, name: Optional[str] = None, *, all: bool = False) -> None:
        if all:
            keys = list(self._engines.keys())
        else:
            if not name:
                name = self._cfg.get_default_key()
            keys = [name] if name else []
        for k in keys:
            eng = self._engines.pop(k, None)
            self._makers.pop(k, None)
            if eng is not None:
                try:
                    await eng.dispose()
                except Exception:
                    if self.log:
                        self.log.exception(f"[SqlAlchemyService] dispose failed for '{k}'")

    async def reconfigure(
        self,
        *,
        connections: Optional[Dict[str, Dict[str, Any]]] = None,
        pool: Optional[Dict[str, Any]] = None,
        default_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        before = self._cfg.snapshot()
        snap = self._cfg.reconfigure(connections=connections, pool=pool, default_key=default_key)

        old_conns = before["connections"]
        new_conns = snap["connections"]

        removed = set(old_conns) - set(new_conns)
        changed = [k for k in new_conns if new_conns[k] != old_conns.get(k)]
        for k in removed:
            await self.dispose(k)
        for k in changed:
            await self.dispose(k)
            self._build_engine(k, new_conns[k], snap["pool"])

        if self.log:
            self.log.info(
                f"[SqlAlchemyService] reconfigured: removed={list(removed)} changed={changed} default={snap.get('default_key')}"
            )
        return snap

    def _build_engine(self, name: str, conn: Dict[str, Any], pool: Dict[str, Any]) -> None:
        url = self._build_url(conn)
        kwargs: Dict[str, Any] = {
            "echo": bool(pool.get("echo", False)),
            "pool_pre_ping": bool(pool.get("pre_ping", True)),
        }
        size = pool.get("size")
        if size is not None:
            kwargs["pool_size"] = int(size)
        max_overflow = pool.get("max_overflow")
        if max_overflow is not None:
            kwargs["max_overflow"] = int(max_overflow)
        use_lifo = pool.get("use_lifo")
        if use_lifo is not None:
            kwargs["pool_use_lifo"] = bool(use_lifo)
        recycle = pool.get("recycle")
        if recycle:
            kwargs["pool_recycle"] = int(recycle)

        engine = create_async_engine(url, **kwargs)
        maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False, autoflush=False, autocommit=False)

        self._engines[name] = engine
        self._makers[name] = maker
        if self.log:
            self.log.debug(f"[SqlAlchemyService] engine created for '{name}' -> {url}")

    def _build_url(self, conn: Dict[str, Any]) -> str:
        ctype = str(conn.get("type") or "sqlite").lower()
        user = quote_plus(str(conn.get("user") or ""))
        pwd = quote_plus(str(conn.get("password") or ""))
        host = str(conn.get("host") or "")
        port = str(conn.get("port") or "")
        db = str(conn.get("db") or "")
        src = str(conn.get("source_path") or "")

        if ctype in ("pgsql", "postgres", "postgresql"):
            return f"postgresql+asyncpg://{user}:{pwd}@{host}:{port}/{db}"
        if ctype in ("mysql", "mariadb"):
            return f"mysql+aiomysql://{user}:{pwd}@{host}:{port}/{db}"
        if ctype == "sqlite":
            path = src or db or ":memory:"
            if path == ":memory:":
                return "sqlite+aiosqlite://"
            if "://" in path:
                return path
            return f"sqlite+aiosqlite:///{path}"
        raise ValueError(f"Unsupported database type: {ctype}")
