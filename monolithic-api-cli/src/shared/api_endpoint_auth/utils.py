from typing import NotRequired, Optional, TypedDict, Union


class JWTTokenPayload(TypedDict):
    """Claims embedded in minted JWT tokens."""

    type: str
    sub: str
    iat: int
    exp: int
    aud: str
    iss: str
    username: NotRequired[str]
    email: NotRequired[str]
    role: NotRequired[Union[int, str]]


class JWTToken(TypedDict):
    """Token pair returned to API clients."""

    access_token: str
    refresh_token: str


class JWTTokens(TypedDict):
    """Internal representation of mutable access and refresh tokens."""

    access_token: Optional[str]
    refresh_token: Optional[str]


class JWTTokenUser(TypedDict):
    """User entity snapshot associated with stored JWT credentials."""

    id: Union[int, str]
    username: str
    email: str
    role_id: Union[int, str]
    identify: str
    jwt_access_token: Optional[str]
    jwt_refresh_token: Optional[str]


class JWTAuthGuardApiEndpointAuthUserPayload(TypedDict):
    """Subset of JWT payload forwarded by authentication guard."""

    id: Union[int, str]
    role: Union[int, str]


class JWTAuthGuardApiEndpointAuthHeaderPayload(TypedDict):
    """Serialized header payload forwarded by the authentication guard."""

    apiuser: JWTAuthGuardApiEndpointAuthUserPayload


__all__ = [
    "JWTTokenPayload",
    "JWTToken",
    "JWTTokens",
    "JWTTokenUser",
    "JWTAuthGuardApiEndpointAuthUserPayload",
    "JWTAuthGuardApiEndpointAuthHeaderPayload",
]
