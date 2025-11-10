# libs/jwt/utils.py
import base64
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Optional, Union

from nest.core import Injectable

from libs.conf.service import ConfService
from libs.log.service import LogService

@Injectable
class JwtUtils:
    def __init__(self, conf: ConfService, log: LogService):
        self.conf = conf
        self.log = log

    def parse_duration(self, value: Union[str, int, float]) -> timedelta:
        """
        Supports: 30s, 15m, 1h, 1d, ms; or numeric seconds.
        Simple & fast on purpose (no third-party dependency).
        """
        if isinstance(value, (int, float)):
            return timedelta(seconds=int(value))
        s = str(value).strip().lower()
        if s.endswith("ms"):
            return timedelta(milliseconds=int(s[:-2]))
        if s.endswith("s"):
            return timedelta(seconds=int(s[:-1]))
        if s.endswith("m"):
            return timedelta(minutes=int(s[:-1]))
        if s.endswith("h"):
            return timedelta(hours=int(s[:-1]))
        if s.endswith("d"):
            return timedelta(days=int(s[:-1]))
        return timedelta(seconds=int(s))

    def now_utc(self) -> datetime:
        return datetime.now(timezone.utc)

    def b64url_uint(self, n: int) -> str:
        b = n.to_bytes((n.bit_length() + 7) // 8, "big")
        return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")

    def b64url_bytes(self, b: bytes) -> str:
        return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")

    def ensure_audience(self, aud: Optional[Union[str, Iterable[str]]]) -> Optional[Union[str, Iterable[str]]]:
        # PyJWT accepts str or list for 'audience' — pass through as-is. :contentReference[oaicite:3]{index=3}
        return aud
