# src/shared/api_endpoint_auth/public/dto.py
from datetime import datetime
from typing import ClassVar, Optional

from pydantic import EmailStr, Field

from libs.crud.dto.dto import Dto
from libs.crud.validation import PyDAJWTFormat, PyDAPassPattern
from libs.pynest_graphql.dto_composition import InputType, ObjectType
from src.shared.api_endpoint_auth.private.dto import ApiEndpointAuthDto

_username_field = ApiEndpointAuthDto.model_fields["username"]
_email_field = ApiEndpointAuthDto.model_fields["email"]
_identify_field = ApiEndpointAuthDto.model_fields["identify"]
_jwt_access_field = ApiEndpointAuthDto.model_fields["jwt_access_token"]
_jwt_refresh_field = ApiEndpointAuthDto.model_fields["jwt_refresh_token"]
_created_field = ApiEndpointAuthDto.model_fields["created"]
_updated_field = ApiEndpointAuthDto.model_fields["updated"]

USERNAME_DESC = _username_field.description or ""
EMAIL_DESC = _email_field.description or ""
IDENTIFY_DESC = _identify_field.description or ""
JWT_ACCESS_DESC = _jwt_access_field.description or ""
JWT_REFRESH_DESC = _jwt_refresh_field.description or ""
CREATED_DESC = _created_field.description or ""
UPDATED_DESC = _updated_field.description or ""

USERNAME_MIN_LEN = 5
USERNAME_MAX_LEN = 128
IDENTIFY_MIN_LEN = 8
EMAIL_MAX_LEN = 128


# █████████████████████████████████████████████████████████████
# █ GRAPH HELLO DTO ███████████████████████████████████████████
# █████████████████████████████████████████████████████████████


class GraphHello(Dto):
    metaname: ClassVar[str] = "GraphHello"
    metadesc: ClassVar[str] = "Testing query"


@ObjectType
class GraphHelloOutput(GraphHello):
    message: str = Field(
        ...,
        title="Greeting message",
        description="Localized hello text with timestamp.",
    )


# █████████████████████████████████████████████████████████████
# █ GRAPH LOGIN DTO ███████████████████████████████████████████
# █████████████████████████████████████████████████████████████


class GraphLogin(Dto):
    metaname: ClassVar[str] = "GraphLogin"
    metadesc: ClassVar[str] = "Authenticate an API user and mint JWT tokens."


# ████ INPUT DTO ██████████████████████████████████████████████


@InputType
class GraphLoginInput(GraphLogin):
    username: str = Field(
        ...,
        min_length=USERNAME_MIN_LEN,
        max_length=USERNAME_MAX_LEN,
        title="User role",
        description=USERNAME_DESC,
    )

    identify: PyDAPassPattern = Field(
        ...,
        min_length=IDENTIFY_MIN_LEN,
        title="Password for signin",
        description=IDENTIFY_DESC,
    )


# ████ OUTPUT DTO █████████████████████████████████████████████


@ObjectType
class GraphLoginOutput(GraphLogin):
    username: Optional[str] = Field(
        default=None,
        min_length=USERNAME_MIN_LEN,
        max_length=USERNAME_MAX_LEN,
        title="User role",
        description=USERNAME_DESC,
    )

    email: Optional[EmailStr] = Field(
        default=None,
        max_length=EMAIL_MAX_LEN,
        title="Email for signin",
        description=EMAIL_DESC,
    )

    jwt_access_token: Optional[PyDAJWTFormat] = Field(
        default=None,
        title="JWT access token",
        description=JWT_ACCESS_DESC,
    )

    jwt_refresh_token: Optional[PyDAJWTFormat] = Field(
        default=None,
        title="JWT refresh token",
        description=JWT_REFRESH_DESC,
    )


# █████████████████████████████████████████████████████████████
# █ GRAPH RESET PASSWORD DTO ██████████████████████████████████
# █████████████████████████████████████████████████████████████


class GraphResetPassword(Dto):
    metaname: ClassVar[str] = "GraphResetPassword"
    metadesc: ClassVar[str] = "Reset an API user's password using their refresh token."


# ████ INPUT DTO ██████████████████████████████████████████████


@InputType
class GraphResetPasswordInput(GraphResetPassword):
    username: str = Field(
        ...,
        min_length=USERNAME_MIN_LEN,
        max_length=USERNAME_MAX_LEN,
        title="User role",
        description=USERNAME_DESC,
    )

    identify: PyDAPassPattern = Field(
        ...,
        min_length=IDENTIFY_MIN_LEN,
        title="Password for signin",
        description=IDENTIFY_DESC,
    )

    jwt_refresh_token: PyDAJWTFormat = Field(
        ...,
        title="JWT refresh token",
        description=JWT_REFRESH_DESC,
    )


# ████ OUTPUT DTO █████████████████████████████████████████████


@ObjectType
class GraphResetPasswordOutput(GraphResetPassword):
    username: Optional[str] = Field(
        default=None,
        min_length=USERNAME_MIN_LEN,
        max_length=USERNAME_MAX_LEN,
        title="User role",
        description=USERNAME_DESC,
    )

    email: Optional[EmailStr] = Field(
        default=None,
        max_length=EMAIL_MAX_LEN,
        title="Email for signin",
        description=EMAIL_DESC,
    )

    created: Optional[datetime] = Field(
        default=None,
        title="Record created",
        description=CREATED_DESC,
    )

    updated: Optional[datetime] = Field(
        default=None,
        title="Record last updated",
        description=UPDATED_DESC,
    )


# █████████████████████████████████████████████████████████████
# █ GRAPH SIGNUP DTO ██████████████████████████████████████████
# █████████████████████████████████████████████████████████████


class GraphSignup(Dto):
    metaname: ClassVar[str] = "GraphSignup"
    metadesc: ClassVar[str] = "Signup to get access to the application data."


# ████ INPUT DTO ██████████████████████████████████████████████


@InputType
class GraphSignupInput(GraphSignup):
    username: str = Field(
        ...,
        min_length=USERNAME_MIN_LEN,
        max_length=USERNAME_MAX_LEN,
        title="User role",
        description=USERNAME_DESC,
    )

    identify: PyDAPassPattern = Field(
        ...,
        min_length=IDENTIFY_MIN_LEN,
        title="Password for signin",
        description=IDENTIFY_DESC,
    )

    email: EmailStr = Field(
        ...,
        max_length=EMAIL_MAX_LEN,
        title="Email for signin",
        description=EMAIL_DESC,
    )


# ████ OUTPUT DTO █████████████████████████████████████████████


@ObjectType
class GraphSignupOutput(GraphSignup):
    username: Optional[str] = Field(
        default=None,
        min_length=USERNAME_MIN_LEN,
        max_length=USERNAME_MAX_LEN,
        title="User role",
        description=USERNAME_DESC,
    )

    email: Optional[EmailStr] = Field(
        default=None,
        max_length=EMAIL_MAX_LEN,
        title="Email for signin",
        description=EMAIL_DESC,
    )

    jwt_access_token: Optional[PyDAJWTFormat | str] = Field(
        default=None,
        title="JWT access token",
        description=JWT_ACCESS_DESC,
    )

    jwt_refresh_token: Optional[PyDAJWTFormat | str] = Field(
        default=None,
        title="JWT refresh token",
        description=JWT_REFRESH_DESC,
    )

    created: Optional[datetime] = Field(
        default=None,
        title="Record created",
        description=CREATED_DESC,
    )


# █████████████████████████████████████████████████████████████
# █ GRAPH REFRESH JWT DTO █████████████████████████████████████
# █████████████████████████████████████████████████████████████


class GraphRefreshJWT(Dto):
    metaname: ClassVar[str] = "GraphRefreshJWT"
    metadesc: ClassVar[str] = "Refresh JWT access token using refresh token."


# █████████████████████████████████████████████████████████████
# █ GRAPH WHO AM I DTO ████████████████████████████████████████
# █████████████████████████████████████████████████████████████


class GraphWhoAmI(Dto):
    metaname: ClassVar[str] = "GraphWhoAmI"
    metadesc: ClassVar[str] = "Get the current user info using JWT access token."


# █████████████████████████████████████████████████████████████
# █ GRAPH SIGNOUT DTO █████████████████████████████████████████
# █████████████████████████████████████████████████████████████


class GraphSignout(Dto):
    metaname: ClassVar[str] = "GraphSignout"
    metadesc: ClassVar[str] = (
        "Signout and remove JWT token for the current state. Next time login to regain access."
    )


__all__ = [
    "GraphHello",
    "GraphHelloOutput",
    "GraphLogin",
    "GraphLoginInput",
    "GraphLoginOutput",
    "GraphResetPassword",
    "GraphResetPasswordInput",
    "GraphResetPasswordOutput",
    "GraphSignup",
    "GraphSignupInput",
    "GraphSignupOutput",
    "GraphRefreshJWT",
    "GraphWhoAmI",
    "GraphSignout",
]
