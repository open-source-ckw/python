# libs/jwt/guard.py
from typing import Any, Dict, Iterable, Optional
from nest.core import Injectable
from libs.conf.service import ConfService
from libs.jwt.service import JwtService
from libs.jwt.exceptions import JwtVerificationError
from libs.log.service import LogService
@Injectable
class JwtGuard:
    """
    Thin adapter for controllers/routers: extract bearer/cookie, verify access,
    and run simple scope/tenant checks. Keep policy in JwtService.
    """

    def __init__(self, conf: ConfService, log: LogService, service: JwtService):
        self.conf = conf
        self.log = log
        self.service = service

    # ----- extraction -----

    def token_from_authorization(self, auth_header: Optional[str]) -> Optional[str]:
        if not auth_header:
            return None
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1]
        return None

    def token_from_cookies(self, cookies: Dict[str, str], name: str) -> Optional[str]:
        return cookies.get(name)

    # ----- verification -----

    def verify_access(self, token: str, *, aud: Optional[str] = None, iss: Optional[str] = None) -> Dict[str, Any]:
        #return self.service.verify(token, expected_use="access", aud=aud, iss=iss)
        try:
            claims = self.service.verify(token, expected_use="access", aud=aud, iss=iss)
            return {"ok": True, "claims": claims}
        except JwtVerificationError as e:
            return {"ok": False, "error": e.as_dict()}

    def verify_refresh(self, token: str, *, aud: Optional[str] = None, iss: Optional[str] = None) -> Dict[str, Any]:
        #return self.service.verify(token, expected_use="refresh", aud=aud, iss=iss)
        try:
            claims = self.service.verify(token, expected_use="refresh", aud=aud, iss=iss)
            return {"ok": True, "claims": claims}
        except JwtVerificationError as e:
            return {"ok": False, "error": e.as_dict()}

    # ----- checks -----

    def require_scopes(self, claims: Dict[str, Any], required: Iterable[str]) -> bool:
        if not required:
            return True
        scopes = set(claims.get("scopes") or [])
        return set(required).issubset(scopes)

    def require_au(self, claims: Dict[str, Any], au) -> bool:
        return str(claims.get("au")) == str(au)
