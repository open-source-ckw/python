# libs/sql_alchemy/configuration.py
from typing import Any, Dict, List, Optional, Union


class SqlAlchemyConfiguration:
    def __init__(self, conf, log):
        self.conf = conf
        self.log = log
        self._connections: Dict[str, Dict[str, Any]] = {}
        self._pool: Dict[str, Any] = {}
        self._default_key: Optional[str] = None

    def configure(
        self,
        *,
        default_key: Optional[str] = None,
        override_connections: Optional[Union[Dict[str, Dict[str, Any]], List[Dict[str, Any]]]] = None,
        override_pool: Optional[Dict[str, Any]] = None,
    ) -> None:
        conns = override_connections if override_connections is not None else self.connections()
        if conns is None:
            conns = {}
        if isinstance(conns, list):
            normalized: Dict[str, Dict[str, Any]] = {}
            for i, c in enumerate(conns):
                key = str(c.get("key") or c.get("name") or f"conn{i}")
                normalized[key] = dict(c)
                normalized[key]["key"] = key
            conns = normalized
        else:
            for k, v in list(conns.items()):
                v = dict(v or {})
                v["key"] = v.get("key") or k
                conns[k] = v

        pool = override_pool if override_pool is not None else self.pool()
        pool = dict(pool or {})

        dkey = default_key or getattr(self.conf, "db_default_key", None)
        if not dkey:
            dkey = "main" if "main" in conns else (next(iter(conns.keys())) if conns else None)

        self._connections = conns
        self._pool = pool
        self._default_key = dkey
        if self.log:
            self.log.debug(f"[SqlAlchemyConfiguration] configured connections={list(conns.keys())} default={dkey}")

    def connections(self) -> Optional[Union[Dict[str, Dict[str, Any]], List[Dict[str, Any]]]]:
        """
        "main" is default if present in connections(), else
        the first defined connection.
        """
        return {
            "pgsql": {
                "type": getattr(self.conf, "pgsql_database_type", "pgsql"),
                "host": getattr(self.conf, "pgsql_host", "localhost"),
                "port": getattr(self.conf, "pgsql_port", 5432),
                "user": getattr(self.conf, "pgsql_user", "postgres"),
                "password": getattr(self.conf, "pgsql_pass", ""),
                "db": getattr(self.conf, "pgsql_dbname", "postgres"),
            },
            "local": {
                "type": getattr(self.conf, "sqlite_database_type", "sqlite"),
                "host": getattr(self.conf, "sqlite_host", ""),
                "port": getattr(self.conf, "sqlite_port", 0),
                "user": getattr(self.conf, "sqlite_user", ""),
                "password": getattr(self.conf, "sqlite_pass", ""),
                "db": getattr(self.conf, "sqlite_dbname", ""),
                "source_path": getattr(self.conf, "sqlite_source_path", "./local.db"),
            },
        }

    def pool(self) -> Dict[str, Any]:
        return {
            "size": getattr(self.conf, "db_pool_size", 5),
            "max_overflow": getattr(self.conf, "db_pool_max_overflow", 10),
            "pre_ping": getattr(self.conf, "db_pool_per_ping", True),
            "use_lifo": getattr(self.conf, "db_pool_use_lifo", True),
            "echo": getattr(self.conf, "db_pool_echo", False),
            "recycle": getattr(self.conf, "db_pool_recycle", 0),
        }

    def reconfigure(
        self,
        *,
        connections: Optional[Union[Dict[str, Dict[str, Any]], List[Dict[str, Any]]]] = None,
        pool: Optional[Dict[str, Any]] = None,
        default_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        self.configure(
            default_key=default_key if default_key is not None else self._default_key,
            override_connections=connections if connections is not None else self._connections,
            override_pool=pool if pool is not None else self._pool,
        )
        return self.snapshot()

    def snapshot(self) -> Dict[str, Any]:
        return {
            "connections": {k: dict(v) for k, v in self._connections.items()},
            "pool": dict(self._pool),
            "default_key": self._default_key,
        }

    def get_connections(self) -> Dict[str, Dict[str, Any]]:
        return self._connections

    def get_pool(self) -> Dict[str, Any]:
        return self._pool

    def get_default_key(self) -> Optional[str]:
        return self._default_key
