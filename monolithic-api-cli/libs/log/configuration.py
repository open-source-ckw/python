import json
import logging
import os
import re
import shutil
import socket
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, Optional, Any
from nest.core import Injectable
import structlog

from libs.conf.service import ConfService

try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore

# type only; your ConfService provides tz, app_name, log_dir_path, etc.
# from libs.conf.conf_service import ConfService

class LogConfiguration:
    """
    Simple, DI-friendly logging setup:
    - Console (pretty in dev, JSON in prod) with TRACE/DEBUG for your app, WARNING+ for others
    - Files: all.log (env floor), error.log (ERROR+), trace.log (DEBUG+), audit.log (event starts 'audit_')
    - Deep PII redaction, OTEL trace ids, sampling, retention
    """

    # ---------- level numbers (use stdlib where possible) ----------
    LEVELS = {
        "trace": 5,                       # below DEBUG
        "debug": logging.DEBUG,           # 10
        "info": logging.INFO,             # 20
        "notice": 25,                     # between INFO & WARNING
        "warn": logging.WARNING,          # 30
        "error": logging.ERROR,           # 40
        "crit": logging.CRITICAL,         # 50
        "fatal": logging.CRITICAL,        # alias of critical
        "alert": 60,                      # above critical (routes as critical)
        "emerg": 70,                      # above alert (routes as critical)
    }

    # ---------- redaction patterns ----------
    SENSITIVE_KEYS = {
        "password", "passwd", "secret", "token", "access_token", "refresh_token",
        "authorization", "auth", "api_key", "apikey", "email", "phone",
    }
    EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
    BEARER_RE = re.compile(r"\bBearer\s+[A-Za-z0-9\-_\.=]+\b", re.I)
    HEX_TOKEN_RE = re.compile(r"\b[0-9a-f]{24,64}\b", re.I)
    DIGIT_16_RE = re.compile(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b")

    # ---------- paths ----------
    @dataclass(frozen=True)
    class _Paths:
        base: Path
        day_dir: Path
        all_file: Path
        error_file: Path
        trace_file: Path
        audit_file: Path

    # ---------- filters ----------
    class _OnlyLevels(logging.Filter):
        def __init__(self, allowed: Iterable[int]):
            super().__init__()
            self.allowed = set(allowed)
        def filter(self, record: logging.LogRecord) -> int:
            return 1 if record.levelno in self.allowed else 0

    class _MinLevel(logging.Filter):
        def __init__(self, min_level: int):
            super().__init__()
            self.min = min_level
        def filter(self, record: logging.LogRecord) -> int:
            return 1 if record.levelno >= self.min else 0

    class _AuditOnly(logging.Filter):
        """Allow only events whose event name starts with 'audit_'."""
        def filter(self, record: logging.LogRecord) -> int:
            msg = getattr(record, "msg", None)
            if isinstance(msg, dict):
                ev = msg.get("event")
                if isinstance(ev, str) and ev.startswith("audit_"):
                    return 1
            return 0

    class _ConsoleNoiseGate(logging.Filter):
        """
        Let low levels (TRACE/DEBUG/INFO) through only for your app logger(s).
        For others, show WARNING+ so console stays useful.
        """
        def __init__(self, allow_prefixes: Iterable[str], min_foreign: int = logging.WARNING):
            super().__init__()
            self.allow_prefixes = tuple(allow_prefixes)
            self.min_foreign = min_foreign
        def filter(self, record: logging.LogRecord) -> int:
            if any(record.name.startswith(p) for p in self.allow_prefixes):
                return 1
            return 1 if record.levelno >= self.min_foreign else 0

    # ---------- ctor ----------
    def __init__(self, conf: ConfService):
        self.conf = conf
        
        # environment & toggles (prefer ConfService; fall back to OS env for safety)
        self.tz_name = self.conf.tz or os.getenv("TZ") or "UTC"
        try:
            # ConfService exposes py_env and helpers; prefer that
            self.py_env = (self.conf.py_env or "dev").lower()
            self.is_prod = bool(getattr(self.conf, "is_prod_env", False)) or self.py_env == "prod"
        except Exception:
            self.py_env = (os.getenv("py_env") or os.getenv("PY_ENV") or "dev").lower()
            self.is_prod = self.py_env == "prod"

        # File logging controls
        try:
            self.log_to_files = bool(self.conf.log_to_files)
        except Exception:
            self.log_to_files = self._env_bool("LOG_TO_FILES", True)
        try:
            self.files_per_pid = bool(self.conf.log_files_per_pid)
        except Exception:
            self.files_per_pid = self._env_bool("LOG_FILES_PER_PID", False)
        try:
            self.keep_days = int(self.conf.log_keep_days)
        except Exception:
            self.keep_days = int(os.getenv("LOG_KEEP_DAYS", "14"))
        try:
            self.sample_rate = float(self.conf.log_sample_rate)
        except Exception:
            self.sample_rate = self._env_float("LOG_SAMPLE_RATE", 1.0)

        # register display names for custom numbers (purely cosmetic)
        for name, num in self.LEVELS.items():
            if logging.getLevelName(num) != name.upper():
                logging.addLevelName(num, name.upper())

        # compute paths + prune old day folders
        self.paths = self._compute_paths()
        if self.log_to_files and self.keep_days > 0:
            self._prune_old_days(self.keep_days)

        # wire logging
        self._configure_structlog_and_stdlib()

        # bind baseline context once
        self._struct_logger = structlog.get_logger("app").bind(
            service=os.getenv("SERVICE_NAME", self.conf.app_name or "app"),
            env=self.py_env,
            version=os.getenv("APP_VERSION", "dev"),
            host=socket.gethostname(),
            pid=os.getpid(),
        )

    # ---------- public ----------
    @property
    def logger(self) -> structlog.stdlib.BoundLogger:
        return self._struct_logger

    def shutdown(self) -> None:
        for h in list(logging.getLogger().handlers):
            try:
                h.flush(); h.close()
            except Exception:
                pass

    # ---------- helpers ----------
    @staticmethod
    def _env_bool(name: str, default: bool) -> bool:
        val = os.getenv(name)
        return default if val is None else val.strip().lower() in ("1", "true", "yes", "on")

    @staticmethod
    def _env_float(name: str, default: float) -> float:
        try:
            return float(os.getenv(name, str(default)))
        except Exception:
            return default

    def _now(self) -> datetime:
        if self.tz_name and ZoneInfo is not None:
            return datetime.now(ZoneInfo(self.tz_name))  # type: ignore[arg-type]
        return datetime.now().astimezone()

    def _compute_paths(self) -> "_Paths":
        now = self._now()
        root = self.conf.log_dir_path or (Path.cwd() / "log" / "structlog")
        day_dir = root / f"{now:%Y}" / f"{now:%m}" / f"{now:%d}"
        day_dir.mkdir(parents=True, exist_ok=True)
        suffix = f".{os.getpid()}" if self.files_per_pid else ""
        return self._Paths(
            base=root,
            day_dir=day_dir,
            all_file=day_dir / f"all{suffix}.log",
            error_file=day_dir / f"error{suffix}.log",
            trace_file=day_dir / f"trace{suffix}.log",
            audit_file=day_dir / f"audit{suffix}.log",
        )

    # ---------- processors ----------
    def _ts(self, _logger, _name, ed: dict) -> dict:
        ed["ts"] = self._now().isoformat()
        return ed

    def _deep_redact_value(self, v: Any) -> Any:
        if isinstance(v, dict):
            return {k: ("***redacted***" if k.lower() in self.SENSITIVE_KEYS else self._deep_redact_value(val))
                    for k, val in v.items()}
        if isinstance(v, (list, tuple)):
            seq = [self._deep_redact_value(x) for x in v]
            return tuple(seq) if isinstance(v, tuple) else seq
        if isinstance(v, str):
            if self.EMAIL_RE.search(v) or self.BEARER_RE.search(v) or self.HEX_TOKEN_RE.search(v) or self.DIGIT_16_RE.search(v):
                return "***redacted***"
        return v

    def _redact(self, _logger, _name, ed: dict) -> dict:
        out = {}
        for k, v in ed.items():
            if isinstance(k, str) and k.lower() in self.SENSITIVE_KEYS:
                out[k] = "***redacted***"
            else:
                out[k] = self._deep_redact_value(v)
        return out

    def _otel(self, _logger, _name, ed: dict) -> dict:
        try:
            from opentelemetry import trace  # type: ignore
            span = trace.get_current_span()
            ctx = span.get_span_context()
            if getattr(ctx, "is_valid", False):
                ed["trace_id"] = format(ctx.trace_id, "032x")
                ed["span_id"] = format(ctx.span_id, "016x")
        except Exception:
            pass
        return ed

    def _sample(self, _logger, _name, ed: dict):
        if self.sample_rate >= 1.0:
            return ed
        level = ed.get("level")
        if isinstance(level, str) and level.lower() in ("trace", "debug", "info", "notice"):
            import random
            if random.random() > self.sample_rate:
                return structlog.DropEvent
        return ed

    def _apply_level_alias(self, _logger, _name, ed: dict) -> dict:
        """
        If caller set 'level_alias' (e.g., LogService.trace/notice),
        use it for the displayed bracket label & JSON 'level'.
        """
        alias = ed.get("level_alias")
        if isinstance(alias, str) and alias:
            ed["level"] = alias.lower()
        return ed

    # ---------- retention ----------
    def _prune_old_days(self, keep_days: int) -> None:
        cutoff_date = (self._now() - timedelta(days=keep_days)).date()
        base = self.paths.base
        if not base.exists():
            return
        for y in base.iterdir():
            if not (y.is_dir() and y.name.isdigit() and len(y.name) == 4): continue
            for m in y.iterdir():
                if not (m.is_dir() and m.name.isdigit() and len(m.name) == 2): continue
                for d in m.iterdir():
                    if not (d.is_dir() and d.name.isdigit() and len(d.name) == 2): continue
                    try:
                        folder_date = datetime(int(y.name), int(m.name), int(d.name)).date()
                    except Exception:
                        continue
                    if folder_date < cutoff_date:
                        shutil.rmtree(d, ignore_errors=True)

    # ---------- wiring ----------
    def _configure_structlog_and_stdlib(self) -> None:
        root = logging.getLogger()
        root.handlers.clear()
        root.setLevel(logging.DEBUG)

        # files floor: prod -> ERROR+, dev -> INFO+
        file_floor = self.LEVELS["error"] if self.is_prod else self.LEVELS["info"]

        # console: TRACE in dev, ERROR in prod (override via LOG_CONSOLE_LEVEL)
        console = logging.StreamHandler()
        # Prefer ConfService for console level; fallback to env if present
        desired = None
        try:
            desired = getattr(self.conf, "log_console_level", None)
        except Exception:
            desired = None
        desired = desired or os.getenv("LOG_CONSOLE_LEVEL")
        if desired:
            console_level = self.LEVELS.get(str(desired).lower(), self.LEVELS["debug"])
        else:
            console_level = self.LEVELS["error"] if self.is_prod else self.LEVELS["trace"]
        console.setLevel(console_level)

        # show low levels only for your app logger(s); foreign logs threshold comes from conf/env
        allowed_prefixes = tuple(p for p in ("app", self.conf.app_name or "") if p)
        foreign_min = None
        try:
            foreign_min = getattr(self.conf, "log_console_foreign_min_level", None)
        except Exception:
            foreign_min = None
        foreign_min = str(foreign_min or os.getenv("LOG_CONSOLE_FOREIGN_MIN_LEVEL") or "ERROR").upper()
        foreign_floor = getattr(logging, foreign_min, logging.ERROR)
        console.addFilter(self._ConsoleNoiseGate(allow_prefixes=allowed_prefixes, min_foreign=foreign_floor))

        # files
        file_handlers: list[logging.Handler] = []
        if self.log_to_files:
            all_fh = logging.FileHandler(self.paths.all_file, encoding="utf-8")
            all_fh.setLevel(logging.NOTSET)
            all_fh.addFilter(self._MinLevel(file_floor))
            file_handlers.append(all_fh)

            err_fh = logging.FileHandler(self.paths.error_file, encoding="utf-8")
            err_fh.setLevel(self.LEVELS["error"])
            file_handlers.append(err_fh)

            trace_fh = logging.FileHandler(self.paths.trace_file, encoding="utf-8")
            trace_fh.setLevel(logging.NOTSET)
            # NOTE: our trace() delegates to debug(); include DEBUG so both appear
            trace_fh.addFilter(self._OnlyLevels({self.LEVELS["trace"], self.LEVELS["debug"]}))
            file_handlers.append(trace_fh)

            audit_fh = logging.FileHandler(self.paths.audit_file, encoding="utf-8")
            audit_fh.setLevel(logging.NOTSET)
            audit_fh.addFilter(self._AuditOnly())
            file_handlers.append(audit_fh)

        # processors
        pre_chain = [
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,  # sets initial 'level'
            self._apply_level_alias,             # override bracket label from level_alias (trace/notice/etc.)
            self._sample,
            self._ts,
            self._otel,
            self._redact,
        ]

        # renderers
        console_renderers = (
            [structlog.processors.JSONRenderer(serializer=json.dumps)]
            if self.is_prod else
            [structlog.dev.ConsoleRenderer()]
        )
        file_renderers = [structlog.processors.JSONRenderer(serializer=json.dumps)]

        # hook processors into handlers
        console.setFormatter(structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=pre_chain,
            processors=console_renderers,
        ))
        for fh in file_handlers:
            fh.setFormatter(structlog.stdlib.ProcessorFormatter(
                foreign_pre_chain=pre_chain,
                processors=file_renderers,
            ))

        # attach handlers
        root.addHandler(console)
        for fh in file_handlers:
            root.addHandler(fh)

        # capture warnings; quiet frameworks in prod
        logging.captureWarnings(True)
        if self.is_prod:
            for noisy in ("pynest", "nest", "uvicorn", "uvicorn.access", "uvicorn.error", "gunicorn", "asyncio"):
                logging.getLogger(noisy).setLevel(logging.WARNING)

        # structlog global processors (same chain)
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                self._apply_level_alias,
                self._sample,
                self._ts,
                self._otel,
                self._redact,
                structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
            ],
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

