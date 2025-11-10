# libs/jwt/keystore.py
from typing import Any, Dict, Optional, Tuple
from libs import conf
from libs.conf.service import ConfService
from libs.jwt.utils import JwtUtils
from libs.log.service import LogService
from nest.core import Injectable
@Injectable
class JwtKeyStore:
    """
    Loads and serves signing/verification key material for access/refresh tokens.
    Handles HMAC secrets and asymmetric PEM keys. Also generates JWKS.
    """

    def __init__(self, conf: ConfService, log: LogService, utils: JwtUtils):
        self.conf = conf
        self.log = log
        self.utils = utils

        # Secrets for HS* (dev/local)
        self._access_secret: Optional[bytes] = self._to_bytes(getattr(conf, "jwt_accesstoken_secret", None))
        self._refresh_secret: Optional[bytes] = self._to_bytes(getattr(conf, "jwt_refreshtoken_secret", None))

        # Paths for asymmetric PEM keys
        self._access_private = self._read_file(getattr(conf, "jwt_private_key_access_path", None))
        self._access_public = self._read_file(getattr(conf, "jwt_public_key_access_path", None))
        self._refresh_private = self._read_file(getattr(conf, "jwt_private_key_refresh_path", None))
        self._refresh_public = self._read_file(getattr(conf, "jwt_public_key_refresh_path", None))

        # kids are owned by JwtService but we mirror for JWKS exposure if needed
        self._kid_access: str = getattr(conf, "jwt_kid_access", "v1")
        self._kid_refresh: str = getattr(conf, "jwt_kid_refresh", "v1")

    # ---------- IO helpers ----------

    def _read_file(self, path: Optional[str]) -> Optional[bytes]:
        if not path:
            return None
        with open(path, "rb") as f:
            return f.read()

    def _to_bytes(self, s: Optional[str]) -> Optional[bytes]:
        if s is None:
            return None
        return s.encode() if isinstance(s, str) else s

    # ---------- key selection ----------

    def select_signing_key(self, typ: str, algorithm: str) -> bytes:
        if typ == "access":
            if algorithm.startswith("HS"):
                if not self._access_secret:
                    raise ValueError("No HMAC secret configured for access tokens")
                return self._access_secret
            if not self._access_private:
                raise ValueError("No private key configured for access tokens")
            return self._access_private
        else:
            if algorithm.startswith("HS"):
                if not self._refresh_secret:
                    raise ValueError("No HMAC secret configured for refresh tokens")
                return self._refresh_secret
            if not self._refresh_private:
                raise ValueError("No private key configured for refresh tokens")
            return self._refresh_private

    def select_verification_key(self, typ: str, algorithm: str) -> bytes:
        if typ == "access":
            if algorithm.startswith("HS"):
                if not self._access_secret:
                    raise ValueError("No HMAC secret configured for access tokens")
                return self._access_secret
            return self._access_public or self._access_private or b""
        else:
            if algorithm.startswith("HS"):
                if not self._refresh_secret:
                    raise ValueError("No HMAC secret configured for refresh tokens")
                return self._refresh_secret
            return self._refresh_public or self._refresh_private or b""

    # ---------- jwks & rotation ----------

    def jwks(self, alg_access: str, kid_access: str, alg_refresh: str, kid_refresh: str, cache_max_age: int) -> Dict[str, Any]:
        """
        Generate a minimal JWK Set for current public keys (skip HS*). RFC7517 compatible. :contentReference[oaicite:4]{index=4}
        """
        keys = []
        for kind, alg, kid, pub, prv in (
            ("access", alg_access, kid_access, self._access_public, self._access_private),
            ("refresh", alg_refresh, kid_refresh, self._refresh_public, self._refresh_private),
        ):
            if alg.startswith("HS"):
                continue
            material = pub or prv
            if not material:
                continue
            try:
                from cryptography.hazmat.primitives import serialization
                from cryptography.hazmat.primitives.asymmetric import rsa, ec, ed25519

                key_obj = (
                    serialization.load_pem_public_key(material)
                    if pub
                    else serialization.load_pem_private_key(material, password=None).public_key()
                )
                if isinstance(key_obj, rsa.RSAPublicKey):
                    numbers = key_obj.public_numbers()
                    keys.append({
                        "kty": "RSA",
                        "n": self.utils.b64url_uint(numbers.n),
                        "e": self.utils.b64url_uint(numbers.e),
                        "alg": alg,
                        "use": "sig",
                        "kid": kid,
                    })
                elif isinstance(key_obj, ec.EllipticCurvePublicKey):
                    numbers = key_obj.public_numbers()
                    curve = key_obj.curve.name
                    crv_map = {"secp256r1": "P-256", "secp384r1": "P-384", "secp521r1": "P-521"}
                    keys.append({
                        "kty": "EC",
                        "crv": crv_map.get(curve, curve),
                        "x": self.utils.b64url_uint(numbers.x),
                        "y": self.utils.b64url_uint(numbers.y),
                        "alg": alg,
                        "use": "sig",
                        "kid": kid,
                    })
                elif isinstance(key_obj, ed25519.Ed25519PublicKey):
                    x = key_obj.public_bytes(
                        encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
                    )
                    keys.append({
                        "kty": "OKP",
                        "crv": "Ed25519",
                        "x": self.utils.b64url_bytes(x),
                        "alg": "EdDSA",
                        "use": "sig",
                        "kid": kid,
                    })
            except Exception:
                # Keep JWKS minimal and fail-closed if public derivation fails
                continue
        return {"keys": keys, "cache_max_age": cache_max_age}

    def current_kids(self) -> Dict[str, str]:
        return {"access": self._kid_access, "refresh": self._kid_refresh}

    def set_active_key(self, kind: str, kid: str, keypair: Dict[str, Optional[bytes]]) -> None:
        if kind == "access":
            self._access_private = keypair.get("private")
            self._access_public = keypair.get("public")
            self._access_secret = keypair.get("secret")
            self._kid_access = kid
        elif kind == "refresh":
            self._refresh_private = keypair.get("private")
            self._refresh_public = keypair.get("public")
            self._refresh_secret = keypair.get("secret")
            self._kid_refresh = kid
        else:
            raise ValueError("kind must be 'access' or 'refresh'")
