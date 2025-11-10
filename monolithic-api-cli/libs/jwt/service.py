# libs/jwt/service.py
from typing import Any, Dict, Iterable, Optional, Union
import jwt  # PyJWT
from nest.core import Injectable
from libs.conf.service import ConfService
from libs.jwt.utils import JwtUtils
from libs.jwt.keystore import JwtKeyStore
from libs.jwt.revocation_store import JwtRevocationStore
from libs.log.service import LogService
from jwt import (
    InvalidTokenError, DecodeError, InvalidSignatureError, ExpiredSignatureError,
    InvalidAudienceError, InvalidIssuerError, ImmatureSignatureError,
    MissingRequiredClaimError, PyJWTError
)
from .exceptions import JwtVerificationError

@Injectable
class JwtService:
    """
    Single, app-wide service for JWT mint/verify/refresh/revoke/JWKS.

    Claims policy:
      - Service owns registered claims (iss, aud, sub, exp, iat, nbf, jti) and 'typ'.
      - Callers can add optional extras via payload_overrides (e.g., uname, email, role, au, udvc, sess).
      - We pin algorithms per token type and enforce iss/aud + leeway. :contentReference[oaicite:5]{index=5}

      EXTRAS
        it has too many guards
        https://github.com/PythonNest/PyNest/blob/main/examples/guard_examples.py
        can we just create new file pynest_guard.py
        and put all of those extra
    """

    # reserved claims that callers cannot override
    RESERVED: set = {"iss", "aud", "exp", "iat", "nbf", "jti", "typ"}

    def __init__(self, conf: ConfService, log: LogService):
        self.conf = conf
        self.log = log
        self.utils = JwtUtils(conf, log)
        self.keystore = JwtKeyStore(conf, log, self.utils)
        self.revocation = JwtRevocationStore(conf, log)

        # Config (defaults chosen for safety and speed)
        self._issuer: str = getattr(conf, "jwt_issuer", "THATSEND")
        self._audience: Union[str, Iterable[str]] = getattr(conf, "jwt_audience", "Application")

        self._access_ttl = self.utils.parse_duration(getattr(conf, "jwt_accesstoken_expires_in", "15m"))
        self._refresh_ttl = self.utils.parse_duration(getattr(conf, "jwt_refreshtoken_expires_in", "14d"))

        self._alg_access: str = getattr(conf, "jwt_signing_alg_access", "RS256")
        self._alg_refresh: str = getattr(conf, "jwt_signing_alg_refresh", "RS256")

        self._kid_access: str = getattr(conf, "jwt_kid_access", "v1")
        self._kid_refresh: str = getattr(conf, "jwt_kid_refresh", "v1")

        self._leeway = self.utils.parse_duration(getattr(conf, "jwt_leeway", "30s"))
        self._require_exp: bool = bool(getattr(conf, "jwt_require_exp", True))
        self._require_iat: bool = bool(getattr(conf, "jwt_require_iat", True))

        self._jwks_enabled: bool = bool(getattr(conf, "jwt_jwks_enabled", False))
        self._jwks_cache_max_age: int = int(getattr(conf, "jwt_jwks_cache_max_age", 3600))

        # Allowed algorithms (pin one per token type — OWASP guidance). :contentReference[oaicite:6]{index=6}
        self._allowed_access = [self._alg_access]
        self._allowed_refresh = [self._alg_refresh]

    # ---------- public API ----------

    def configure(self, options: Dict[str, Any]) -> None:
        if not options:
            return
        if "issuer" in options:
            self._issuer = options["issuer"]
        if "audience" in options:
            self._audience = options["audience"]
        if "access_expires_in" in options:
            self._access_ttl = self.utils.parse_duration(options["access_expires_in"])
        if "refresh_expires_in" in options:
            self._refresh_ttl = self.utils.parse_duration(options["refresh_expires_in"])
        if "leeway" in options:
            self._leeway = self.utils.parse_duration(options["leeway"])
        if "alg_access" in options:
            self._alg_access = options["alg_access"]
            self._allowed_access = [self._alg_access]
        if "alg_refresh" in options:
            self._alg_refresh = options["alg_refresh"]
            self._allowed_refresh = [self._alg_refresh]
        if "kid_access" in options:
            self._kid_access = options["kid_access"]
        if "kid_refresh" in options:
            self._kid_refresh = options["kid_refresh"]

    def sign_access(
        self,
        sub: str,
        *,
        aud: Optional[Union[str, Iterable[str]]] = None,
        scopes: Optional[Iterable[str]] = None,
        au: Optional[Union[str, int]] = None,
        payload_overrides: Optional[Dict[str, Any]] = None,
        expires_in: Optional[Union[str, int]] = None,
        kid: Optional[str] = None,
        algorithm: Optional[str] = None,
        additional_headers: Optional[Dict[str, Any]] = None,
    ) -> str:
        return self._sign(
            sub=sub,
            typ="access",
            aud=aud,
            ttl=self.utils.parse_duration(expires_in) if expires_in is not None else self._access_ttl,
            kid=kid or self._kid_access,
            algorithm=algorithm or self._alg_access,
            payload_overrides=payload_overrides,
            additional_headers=additional_headers,
            scopes=scopes,
            au=au,
        )

    def sign_refresh(
        self,
        sub: str,
        *,
        aud: Optional[Union[str, Iterable[str]]] = None,
        au: Optional[Union[str, int]] = None,
        payload_overrides: Optional[Dict[str, Any]] = None,
        expires_in: Optional[Union[str, int]] = None,
        kid: Optional[str] = None,
        algorithm: Optional[str] = None,
        additional_headers: Optional[Dict[str, Any]] = None,
    ) -> str:
        return self._sign(
            sub=sub,
            typ="refresh",
            aud=aud,
            ttl=self.utils.parse_duration(expires_in) if expires_in is not None else self._refresh_ttl,
            kid=kid or self._kid_refresh,
            algorithm=algorithm or self._alg_refresh,
            payload_overrides=payload_overrides,
            additional_headers=additional_headers,
            au=au,
        )

    def verify(
        self,
        token: str,
        *,
        expected_use: str,  # "access" or "refresh"
        aud=None,
        iss=None,
        leeway=None,
    ) -> dict:
        try:
            header = jwt.get_unverified_header(token)  # may raise DecodeError if token is malformed
            alg = header.get("alg")

            allowed = self._allowed_access if expected_use == "access" else self._allowed_refresh
            try:
                key = self.keystore.select_verification_key(expected_use, alg)
            except (ValueError, FileNotFoundError, KeyError) as e:
                # Key material missing / misconfigured for this alg/kind
                raise JwtVerificationError("JWT_ERR_KEYCONFIG", f"Key config error for {expected_use}/{alg}: {e}") from e

            options = {
                "require": [],
                "verify_signature": True,
                "verify_exp": True,
                "verify_iat": self._require_iat,
                "verify_aud": True,
                "verify_iss": True,
            }
            if self._require_exp:
                options["require"].append("exp")
            if self._require_iat:
                options["require"].append("iat")

            payload = jwt.decode(
                token,
                key=key,
                algorithms=allowed,
                audience=self.utils.ensure_audience(aud if aud is not None else self._audience),
                issuer=iss if iss is not None else self._issuer,
                options=options,
                leeway=int((self.utils.parse_duration(leeway) if leeway is not None else self._leeway).total_seconds()),
            )  # PyJWT enforces sig + iss/aud/exp/iat/nbf. See docs.  :contentReference[oaicite:2]{index=2}

            if payload.get("typ") != expected_use:
                raise InvalidTokenError("Token 'typ' mismatch")

            jti = payload.get("jti")
            if jti and self.revocation.is_revoked(jti):
                raise InvalidTokenError("Token is revoked")

            return payload

        # ---- PyJWT-specific failures (decode/validation) ----
        except ExpiredSignatureError as e:
            raise JwtVerificationError("JWT_ERR_EXPIRED", "Token has expired") from e
        except InvalidAudienceError as e:
            raise JwtVerificationError("JWT_ERR_AUDIENCE", "Invalid audience") from e
        except InvalidIssuerError as e:
            raise JwtVerificationError("JWT_ERR_ISSUER", "Invalid issuer") from e
        except InvalidSignatureError as e:
            raise JwtVerificationError("JWT_ERR_INVALID", "Invalid signature") from e
        except MissingRequiredClaimError as e:
            # e.g., aud required but missing when audience was supplied to decode
            raise JwtVerificationError("JWT_ERR_CLAIM_MISSING", str(e)) from e
        except (ImmatureSignatureError,) as e:
            raise JwtVerificationError("JWT_ERR_NOT_BEFORE", str(e)) from e
        except (DecodeError, InvalidTokenError, PyJWTError) as e:
            raise JwtVerificationError("JWT_ERR_INVALID", str(e)) from e

        # ---- Everything else (config/attribute mistakes) ----
        except (AttributeError, TypeError) as e:
            # Likely a naming drift (DI fields) or wrong type passed to algorithms/audience
            raise JwtVerificationError("JWT_ERR_CONFIG", f"Verifier configuration error: {e}") from e
        except Exception as e:
            # Keep app state intact but include the concrete class for diagnostics
            cls = e.__class__.__name__
            raise JwtVerificationError("JWT_ERR_INVALID", f"{cls}: {e}") from e

    def introspect(self, token: str) -> Dict[str, Any]:
        header = jwt.get_unverified_header(token)
        payload = jwt.decode(token, options={"verify_signature": False})
        return {"header": header, "payload": payload}

    def refresh(
        self,
        access_token: str,
        refresh_token: str,
        *,
        rotate_refresh: bool = True,
        reuse_detection_handler=None,
    ) -> Dict[str, Optional[str]]:
        try:
            rt = self.verify(refresh_token, expected_use="refresh")
            at_meta = self.introspect(access_token)
            at_sub = at_meta["payload"].get("sub")
            if at_sub and at_sub != rt.get("sub"):
                raise jwt.InvalidTokenError("Subject mismatch between tokens")

            carried = {k: rt[k] for k in ("uname", "email", "role", "udvc", "sess", "scopes") if k in rt}
            new_access = self.sign_access(
                sub=rt["sub"],
                aud=rt.get("aud"),
                au=rt.get("au"),
                payload_overrides=carried,
            )

            new_refresh: Optional[str] = None
            if rotate_refresh:
                old_jti = rt.get("jti")
                if old_jti:
                    self.revocation.revoke(old_jti)
                minimal = {k: rt[k] for k in ("sess", "udvc") if k in rt}
                new_refresh = self.sign_refresh(
                    sub=rt["sub"],
                    aud=rt.get("aud"),
                    au=rt.get("au"),
                    payload_overrides=minimal,
                )
            return {"access": new_access, "refresh": new_refresh}

        # ---- PyJWT-specific failures (decode/validation) ----
        except ExpiredSignatureError as e:
            #raise JwtVerificationError("JWT_ERR_EXPIRED", "Token has expired") from e
            return {"ok": False, "error": e.as_dict()}
        except InvalidAudienceError as e:
            #raise JwtVerificationError("JWT_ERR_AUDIENCE", "Invalid audience") from e
            return {"ok": False, "error": e.as_dict()}
        except InvalidIssuerError as e:
            #raise JwtVerificationError("JWT_ERR_ISSUER", "Invalid issuer") from e
            return {"ok": False, "error": e.as_dict()}
        except InvalidSignatureError as e:
            #raise JwtVerificationError("JWT_ERR_INVALID", "Invalid signature") from e
            return {"ok": False, "error": e.as_dict()}
        except MissingRequiredClaimError as e:
            # e.g., aud required but missing when audience was supplied to decode
            #raise JwtVerificationError("JWT_ERR_CLAIM_MISSING", str(e)) from e
            return {"ok": False, "error": e.as_dict()}
        except (ImmatureSignatureError,) as e:
            #raise JwtVerificationError("JWT_ERR_NOT_BEFORE", str(e)) from e
            return {"ok": False, "error": e.as_dict()}
        except (DecodeError, InvalidTokenError, PyJWTError) as e:
            #raise JwtVerificationError("JWT_ERR_INVALID", str(e)) from e
            return {"ok": False, "error": e.as_dict()}

        # ---- Everything else (config/attribute mistakes) ----
        except (AttributeError, TypeError) as e:
            # Likely a naming drift (DI fields) or wrong type passed to algorithms/audience
            #raise JwtVerificationError("JWT_ERR_CONFIG", f"Verifier configuration error: {e}") from e
            return {"ok": False, "error": e.as_dict()}
        except Exception as e:
            # Keep app state intact but include the concrete class for diagnostics
            cls = e.__class__.__name__
            #raise JwtVerificationError("JWT_ERR_INVALID", f"{cls}: {e}") from e
            return {"ok": False, "error": e.as_dict()}
        

    def revoke(self, jti: str, *, reason: Optional[str] = None, until: Optional[Union[int, float]] = None) -> None:
        self.revocation.revoke(jti, until=until)

    def is_revoked(self, jti: str) -> bool:
        return self.revocation.is_revoked(jti)

    def jwks(self) -> Dict[str, Any]:
        return self.keystore.jwks(self._alg_access, self._kid_access, self._alg_refresh, self._kid_refresh, self._jwks_cache_max_age)

    def current_kids(self) -> Dict[str, str]:
        return {"access": self._kid_access, "refresh": self._kid_refresh}

    def set_active_key(self, kind: str, kid: str, keypair: Dict[str, Optional[bytes]]) -> None:
        self.keystore.set_active_key(kind, kid, keypair)

    # ---------- internal ----------

    def _sign(
        self,
        *,
        sub: str,
        typ: str,
        aud: Optional[Union[str, Iterable[str]]],
        ttl,
        kid: Optional[str],
        algorithm: str,
        payload_overrides: Optional[Dict[str, Any]],
        additional_headers: Optional[Dict[str, Any]],
        scopes: Optional[Iterable[str]] = None,
        au: Optional[Union[str, int]] = None,
    ) -> str:
        now = self.utils.now_utc()
        exp = int((now + ttl).timestamp())
        iat = int(now.timestamp())

        payload: Dict[str, Any] = {
            "iss": self._issuer,
            "aud": aud if aud is not None else self._audience,
            "sub": str(sub),
            "typ": typ,
            "iat": iat,
            "exp": exp,
            "jti": self._gen_jti(),
        }
        if scopes:
            payload["scopes"] = list(scopes)
        if au is not None:
            payload["au"] = au

        if payload_overrides:
            for k, v in payload_overrides.items():
                if k in self.RESERVED:
                    raise ValueError(f"'{k}' is reserved and cannot be overridden")
                payload[k] = v

        headers = {"alg": algorithm, "typ": "JWT"}
        if kid:
            headers["kid"] = kid
        if additional_headers:
            headers.update(additional_headers)

        key = self.keystore.select_signing_key(typ, algorithm)
        return jwt.encode(payload, key, algorithm=algorithm, headers=headers)

    def _gen_jti(self) -> str:
        # keep local to avoid importing uuid just for one call
        import uuid
        return uuid.uuid4().hex
