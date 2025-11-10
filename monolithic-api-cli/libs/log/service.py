import logging
import uuid
from contextlib import contextmanager
from typing import Any, Optional

import structlog
from nest.core import Injectable

from libs.conf.service import ConfService
from libs.log.configuration import LogConfiguration

"""
SOME optimisation required regarding console logs level but not much information

Console (dev): shows your app’s TRACE, DEBUG, INFO, WARN, ERROR, CRITICAL;
framework logs (e.g., pynest, uvicorn) appear only WARNING+.

Files: unchanged (trace.log = TRACE+DEBUG, error.log = ERROR+, all.log respects env floor).

Console (dev): you see your app’s TRACE/DEBUG/INFO/WARNING/ERROR, plus WARNING/ERROR from frameworks.

Console (prod): shows ERROR+ by default (override with LOG_CONSOLE_LEVEL).

Files unchanged: trace.log (TRACE+DEBUG), error.log (ERROR+), all.log (INFO+ dev / ERROR+ prod), audit.log.
"""

@Injectable
class LogService:
    """
    Single DI service used across the app.
    Swap sinks (e.g., DB) later by changing this class only.
    """

    _configured = False
    _config: Optional[LogConfiguration] = None

    def __init__(self, conf: ConfService):
        logConf: LogConfiguration = LogConfiguration(conf)
        
        self.conf = conf
        self._log = logConf.logger
        self._levels = LogConfiguration.LEVELS
        # if not LogService._configured:
        #     LogService._config = logConf # LogConfiguration()
        #     LogService._configured = True
        # self._log: structlog.stdlib.BoundLogger = LogService._config.logger  # type: ignore[union-attr]
        # self._levels = LogConfiguration.LEVELS

    # ---- Context helpers ----
    def bind(self, **ctx: Any) -> "LogService":
        child = LogService.__new__(LogService)
        child._log = self._log.bind(**ctx)          # type: ignore[attr-defined]
        child._levels = self._levels                # type: ignore[attr-defined]
        return child

    def unbind(self, *keys: str) -> "LogService":
        self._log = self._log.unbind(*keys)
        return self

    @contextmanager
    def ctx(self, **ctx: Any):
        """
        Temporarily bind context for a block (works in CLI, REST, jobs, etc.).
        """
        bound = self.bind(**ctx)
        try:
            yield bound
        finally:
            bound.unbind(*ctx.keys())

    @contextmanager
    def job(self, name: str, **ctx: Any):
        """
        Standardized job unit with job_id + start/finish logs.
        Great for CLI commands and background tasks.
        """
        jid = str(uuid.uuid4())
        with self.ctx(job=name, job_id=jid, **ctx) as log:
            log.info("job_started")
            try:
                yield log
                log.info("job_finished")
            except Exception:
                log.exception("job_failed")
                raise

    # ---- Logging API ----
    def trace(self, event: str, **kw):
      kw.setdefault("level_alias", "TRACE")  # optional tag
      self._log.debug(event, **kw)

    def debug(self, event: str, **kw: Any) -> None:
        self._log.debug(event, **kw)

    def info(self, event: str, **kw: Any) -> None:
        self._log.info(event, **kw)

    # def notice(self, event: str, **kw: Any) -> None:
    #     self._log.log(self._levels["notice"], event, **kw)

    def notice(self, event: str, **kw):
        kw.setdefault("level_alias", "NOTICE")
        self._log.info(event, **kw) 

    def warn(self, event: str, **kw: Any) -> None:
        self._log.warning(event, **kw)

    def error(self, event: str, **kw: Any) -> None:
        self._log.error(event, **kw)

    def crit(self, event: str, **kw: Any) -> None:
        self._log.critical(event, **kw)

    def fatal(self, event: str, **kw):
        kw.setdefault("level_alias", "FATAL")
        self._log.critical(event, **kw)

    # def alert(self, event: str, **kw: Any) -> None:
    #     self._log.log(self._levels["alert"], event, **kw)

    def alert(self, event: str, **kw):
        kw.setdefault("level_alias", "ALERT")
        self._log.critical(event, **kw)

    # def emerg(self, event: str, **kw: Any) -> None:
    #     self._log.log(self._levels["emerg"], event, **kw)
    def emerg(self, event: str, **kw):
        kw.setdefault("level_alias", "EMERG")
        self._log.critical(event, **kw)

    def exception(self, event: str, **kw: Any) -> None:
        self._log.exception(event, **kw)

    # ---- Audit channel helper ----
    def audit(self, event: str, **kw: Any) -> None:
        """
        Dedicated audit sink: prefix event with 'audit_' and log at INFO.
        e.g., log.audit('user_role_changed', actor=..., target=...)
        """
        if not event.startswith("audit_"):
            event = f"audit_{event}"
        self._log.info(event, **kw)

    # ---- Interop ----
    def std_logger(self) -> logging.Logger:
        """
        std_logger() gives you a plain stdlib logging.Logger that still goes through your same structlog pipeline (PII redaction, JSON, files, console). Use it when a library expects a logging.Logger.
        Usage:
        pylog = self.log.std_logger()
        pylog.info("plain stdlib message", extra={"order_id": "o_123"})
        """
        return logging.getLogger("app")

    # ---- Lifecycle ----
    def shutdown(self) -> None:
        if LogService._config:
            LogService._config.shutdown()
