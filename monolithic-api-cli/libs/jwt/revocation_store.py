# libs/jwt/revocation_store.py
import time
from datetime import datetime
from typing import Dict, Optional, Union

from libs.conf.service import ConfService
from libs.log.service import LogService
from nest.core import Injectable

@Injectable
class JwtRevocationStore:
    """
    Simple in-memory revocation store (JTI -> expires_at).
    Swap with Redis/Postgres by implementing the same methods.
    """

    def __init__(self, conf: ConfService, log: LogService):
        self.conf = conf
        self.log = log
        self._revoked: Dict[str, int] = {}

    def revoke(self, jti_or_token: str, *, until: Optional[Union[int, float, datetime]] = None) -> None:
        jti = jti_or_token
        if isinstance(until, datetime):
            exp = int(until.timestamp())
        elif isinstance(until, (int, float)):
            exp = int(until)
        else:
            exp = int(time.time()) + 3600
        self._revoked[jti] = exp

    def is_revoked(self, jti: str) -> bool:
        now = int(time.time())
        exp = self._revoked.get(jti)
        if exp is None:
            return False
        if exp <= now:
            self._revoked.pop(jti, None)
            return False
        return True
