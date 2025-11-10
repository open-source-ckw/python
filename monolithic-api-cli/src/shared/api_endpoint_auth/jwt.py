import json
from typing import Any, Mapping, Optional, cast

from nest.core import Injectable

from libs.jwt.exceptions import JwtVerificationError
from libs.jwt.service import JwtService
from libs.libs_service import LibsService

from src.shared.api_endpoint_auth.entity import ApiEndpointAuthEntity
from src.shared.api_endpoint_auth.utils import (
    JWTTokens,
    JWTTokenPayload,
    JWTAuthGuardApiEndpointAuthUserPayload,
)


@Injectable
class ApiEndpointAuthJwt:
    """Encapsulates JWT-specific operations for API endpoint auth."""

    def __init__(self, jwt: JwtService, libs: LibsService) -> None:
        self._jwt: JwtService = jwt
        self._libs: LibsService = libs

    def generate_tokens(self, user: ApiEndpointAuthEntity) -> JWTTokens:
        """Generate and return JWT access and refresh token pair for a user."""
        sub = self.encode_sub_id(user.id)
        overrides = self.token_payload_overrides(user)
        access = self._jwt.sign_access(sub=sub, payload_overrides=overrides)
        refresh = self._jwt.sign_refresh(sub=sub, payload_overrides=overrides)
        return {"access_token": access, "refresh_token": refresh}

    def refresh_tokens(
        self, _payload: JWTTokenPayload, user: ApiEndpointAuthEntity
    ) -> JWTTokens:
        """Refresh tokens based on payload and user metadata."""
        return self.generate_tokens(user)

    def verify_tokens(
        self,
        access_token: Optional[str],
        refresh_token: Optional[str],
    ) -> JWTTokens:
        """Verify stored tokens and invalidate the one that fails verification."""
        tokens: JWTTokens = {"access_token": None, "refresh_token": None}

        if access_token:
            try:
                self._jwt.verify(access_token, expected_use="access")
                tokens["access_token"] = access_token
            except JwtVerificationError:
                tokens["access_token"] = None

        if refresh_token:
            try:
                self._jwt.verify(refresh_token, expected_use="refresh")
                tokens["refresh_token"] = refresh_token
            except JwtVerificationError:
                tokens["refresh_token"] = None

        return tokens

    @staticmethod
    def tokens_are_valid(tokens: Mapping[str, Optional[str]]) -> bool:
        """Return True when both tokens are present and verified."""
        return bool(tokens.get("access_token")) and bool(tokens.get("refresh_token"))

    def get_refresh_token_payload(self, token: str) -> JWTTokenPayload:
        """Return the decoded refresh token payload or raise ValueError."""
        try:
            return cast(JWTTokenPayload, self._jwt.verify(token, expected_use="refresh"))
        except JwtVerificationError as err:
            raise ValueError(str(err)) from err

    @staticmethod
    def token_payload_overrides(user: ApiEndpointAuthEntity) -> dict[str, Any]:
        overrides: dict[str, Any] = {}
        if user.username is not None:
            overrides["username"] = user.username
        if user.email is not None:
            overrides["email"] = user.email
        if user.role_id is not None:
            overrides["role"] = user.role_id
        return overrides

    def encode_sub_id(self, sub_id: Any) -> str:
        """Encode the provided subject identifier."""
        return self._libs.base64_enc(sub_id)

    def decode_sub_id(self, sub: str) -> str:
        """Decode the provided subject identifier and guard against errors."""
        try:
            return self._libs.base64_dec(sub)
        except Exception as err:  # pragma: no cover - defensive logging
            raise ValueError("Invalid refresh token. Unable to decode subject.") from err

    def current_api_user(
        self,
        ctx: Mapping[str, Any],
    ) -> JWTAuthGuardApiEndpointAuthUserPayload:
        """Extract the authenticated user payload from the GraphQL context."""

        claims: Any = (ctx or {}).get("auth")
        if isinstance(claims, str):
            try:
                claims = json.loads(claims)
            except json.JSONDecodeError as exc:  # pragma: no cover - defensive
                raise ValueError("Invalid JWT payload. Corrupted context claims.") from exc
        if not isinstance(claims, Mapping):
            raise ValueError("Authentication required.")

        subject = claims.get("sub") # this is themain id of the api user
        if subject is None:
            raise ValueError("Invalid JWT payload. Missing subject identifier.")

        if isinstance(subject, str):
            try:
                subject = self.decode_sub_id(subject)
            except ValueError:
                # Subject may already be a numeric string; keep original value.
                pass

        try:
            api_user_id = int(subject)
        except (TypeError, ValueError) as exc:
            raise ValueError("Invalid JWT payload. Corrupted subject identifier.") from exc

        role_raw = (
            claims.get("role")
        )
        if role_raw is None:
            raise ValueError("Invalid JWT payload. Missing role information.")

        try:
            role_value: int | str = int(role_raw)  # type: ignore[assignment]
        except (TypeError, ValueError):
            role_value = str(role_raw)

        return JWTAuthGuardApiEndpointAuthUserPayload(id=api_user_id, role=role_value)


__all__ = ["ApiEndpointAuthJwt"]
