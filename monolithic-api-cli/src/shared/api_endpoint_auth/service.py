from typing import Any, Dict, Mapping, Optional, Sequence, Union

from nest.core import Injectable
from pydantic import BaseModel
from sqlalchemy import select, update

from libs.conf.service import ConfService
from libs.libs_service import LibsService
from libs.log.service import LogService
from libs.pynest_graphql import Context
from libs.sql_alchemy.service import SqlAlchemyService

from src.shared.api_endpoint_auth.entity import ApiEndpointAuthEntity
from src.shared.api_endpoint_auth.factory import ApiEndpointAuthFactory
from src.shared.api_endpoint_auth.public.dto import (
    GraphLoginInput,
    GraphLoginOutput,
    GraphResetPasswordInput,
    GraphResetPasswordOutput,
    GraphSignupInput,
    GraphSignupOutput,
)
from src.shared.api_endpoint_auth.repository import ApiEndpointAuthRepository
from src.shared.api_endpoint_auth.jwt import ApiEndpointAuthJwt
from src.shared.api_endpoint_auth.utils import (
    JWTAuthGuardApiEndpointAuthUserPayload,
    JWTTokenPayload,
)


@Injectable
class ApiEndpointAuthService:
    def __init__(
        self,
        db: SqlAlchemyService,
        conf: ConfService,
        log: LogService,
        repository: ApiEndpointAuthRepository,
        factory: ApiEndpointAuthFactory,
        library: LibsService,
        jwt: ApiEndpointAuthJwt,
    ) -> None:
        self.db = db
        self.conf = conf
        self.log = log
        self.repository = repository
        self.factory = factory
        self.library = library
        self.jwt = jwt

        self.log.bind(service=self.__class__.__name__)

    # ------------------------------------------------------------------
    # Data lookups
    # ------------------------------------------------------------------
    async def find_one_force_select_all(
        self, where: Mapping[str, Any]
    ) -> Optional[ApiEndpointAuthEntity]:
        stmt = select(ApiEndpointAuthEntity)
        for key, value in where.items():
            column = getattr(ApiEndpointAuthEntity, key, None)
            if column is None:
                continue
            if value is None:
                stmt = stmt.where(column.is_(None))
            else:
                stmt = stmt.where(column == value)

        async with self.db.session_ctx() as session:
            result = await session.execute(stmt.limit(1))
            return result.scalars().first()

    async def find_one_for_auth(
        self, by: Union[int, str]
    ) -> ApiEndpointAuthEntity:
        try:
            if isinstance(by, int):
                filters = {"id": by}
            else:
                filters = {"username": str(by)}

            user = await self.find_one_force_select_all(filters)
            if user is not None:
                return user

            raise LookupError("Api endpoint authentication id or username not found.")
        except Exception as err:  # pragma: no cover - defensive logging
            self.log.error("find_one_for_auth_failed", error=str(err))
            raise ValueError(f"Auth searching error. {err}") from err

    async def update_jwt_tokens(
        self,
        record_id: int,
        access_token: Optional[str],
        refresh_token: Optional[str],
    ) -> bool:
        try:
            async with self.db.transaction() as session:
                stmt = (
                    update(ApiEndpointAuthEntity)
                    .where(ApiEndpointAuthEntity.id == record_id)
                    .values(
                        jwt_access_token=access_token,
                        jwt_refresh_token=refresh_token,
                    )
                )
                result = await session.execute(stmt)

            if (result.rowcount or 0) == 1:
                return True

            encoded = self.library.base64_enc(record_id)
            raise ValueError(
                f"Unable to update jwt token for api endpoint authentication id '{encoded}'"
            )
        except Exception as err:  # pragma: no cover - defensive logging
            self.log.error("update_jwt_tokens_failed", error=str(err))
            raise RuntimeError(f"JWT tokens update error. {err}") from err

    def verify_auth_policy(self, user: ApiEndpointAuthEntity) -> bool:
        if user.deleted is None:
            if user.suspended is None:
                if user.identify:
                    return True
                raise LookupError(
                    "Your account password is not set yet, please contact administrator."
                )
            suspended_on = user.suspended.strftime(self.conf.format_date_time)
            raise LookupError(
                f"Your account is suspended on {suspended_on}, please contact administrator."
            )
        raise LookupError(
            f"Account with username '{user.username}' no longer available, please signup"
        )

    async def auth_create(
        self, input: Union[GraphSignupInput, Sequence[GraphSignupInput]]
    ) -> Union[GraphSignupOutput, list[GraphSignupOutput]]:
        try:
            if isinstance(input, Sequence) and not isinstance(input, (str, bytes, bytearray)):
                payloads = [self._prepare_signup_payload(item) for item in input]
                async with self.db.transaction() as session:
                    entities: list[ApiEndpointAuthEntity] = []
                    for payload in payloads:
                        entity = ApiEndpointAuthEntity(**payload)
                        session.add(entity)
                        entities.append(entity)

                    await session.flush()
                    for entity in entities:
                        await session.refresh(entity)

                return [
                    GraphSignupOutput.model_validate(entity, from_attributes=True)
                    for entity in entities
                ]

            payload = self._prepare_signup_payload(input)
            async with self.db.transaction() as session:
                entity = ApiEndpointAuthEntity(**payload)
                session.add(entity)
                await session.flush()
                await session.refresh(entity)

            return GraphSignupOutput.model_validate(entity, from_attributes=True)
        except Exception as err:  # pragma: no cover - defensive logging
            self.log.error("auth_create_failed", error=str(err))
            raise RuntimeError(f"Signup error. {err}") from err

    async def sign_up(
        self, input: Union[GraphSignupInput, Sequence[GraphSignupInput]]
    ) -> Union[GraphSignupOutput, list[GraphSignupOutput]]:
        try:
            created = await self.auth_create(input)

            access_notice = "Login to get JWT access token"
            refresh_notice = "Login to get JWT refresh token"

            if isinstance(created, list):
                for dto in created:
                    dto.jwt_access_token = access_notice
                    dto.jwt_refresh_token = refresh_notice
            else:
                created.jwt_access_token = access_notice
                created.jwt_refresh_token = refresh_notice

            return created
        except Exception as err:  # pragma: no cover - defensive logging
            self.log.error("sign_up_failed", error=str(err))
            raise ValueError(f"Signup error. {err}") from err

    async def sign_in(self, input: GraphLoginInput) -> GraphLoginOutput:
        try:
            user = await self.find_one_for_auth(input.username)
            self.verify_auth_policy(user)

            if not self.library.match_hash(user.identify or "", input.identify):
                raise ValueError("Email/Username and password does not match, try again.")

            tokens = self.jwt.verify_tokens(
                user.jwt_access_token, user.jwt_refresh_token
            )
            if not self.jwt.tokens_are_valid(tokens):
                tokens = self.jwt.generate_tokens(user)
                user.jwt_access_token = tokens["access_token"]
                user.jwt_refresh_token = tokens["refresh_token"]
                await self.update_jwt_tokens(
                    int(user.id),
                    user.jwt_access_token,
                    user.jwt_refresh_token,
                )

            dto = GraphLoginOutput.model_validate(user, from_attributes=True)
            dto.jwt_access_token = user.jwt_access_token
            dto.jwt_refresh_token = user.jwt_refresh_token
            return dto
        except Exception as err:  # pragma: no cover - defensive logging
            self.log.error("sign_in_failed", error=str(err))
            raise ValueError(f"Login error. {err}") from err

    async def jwt_refresh_tokens(self, jwt_refresh_token: str) -> GraphLoginOutput:
        try:
            payload = self.jwt.get_refresh_token_payload(jwt_refresh_token)
            sub = payload.get("sub")
            if not sub:
                raise ValueError(
                    "Invalid refresh token. Refresh token sub is not found or corrupted."
                )

            sub_id = int(self.jwt.decode_sub_id(sub))
            user = await self.find_one_for_auth(sub_id)
            self.verify_auth_policy(user)

            tokens = self.jwt.verify_tokens(
                user.jwt_access_token, user.jwt_refresh_token
            )
            if not self.jwt.tokens_are_valid(tokens):
                tokens = self.jwt.refresh_tokens(payload, user)
                user.jwt_access_token = tokens["access_token"]
                user.jwt_refresh_token = tokens["refresh_token"]
                await self.update_jwt_tokens(
                    int(user.id),
                    user.jwt_access_token,
                    user.jwt_refresh_token,
                )

            if int(user.id) != sub_id:
                raise ValueError("User and refresh token does not match.")

            dto = GraphLoginOutput.model_validate(user, from_attributes=True)
            dto.jwt_access_token = user.jwt_access_token
            dto.jwt_refresh_token = user.jwt_refresh_token
            return dto
        except Exception as err:  # pragma: no cover - defensive logging
            self.log.error("jwt_refresh_tokens_failed", error=str(err))
            raise ValueError(f"JWT Refresh token error. {err}") from err

    async def reset_password(
        self, input: GraphResetPasswordInput
    ) -> GraphResetPasswordOutput:
        try:
            payload = self.jwt.get_refresh_token_payload(input.jwt_refresh_token)
            sub = payload.get("sub")
            username = payload.get("username")
            if not sub:
                raise ValueError(
                    "Invalid refresh token. Refresh token sub is not found or corrupted."
                )

            sub_id = int(self.jwt.decode_sub_id(sub))
            user = await self.find_one_for_auth(sub_id)

            if not (
                user.jwt_refresh_token == input.jwt_refresh_token
                and int(user.id) == sub_id
                and user.username == username
                and user.username == input.username
            ):
                raise ValueError("User identity does not match with refresh token.")

            self.verify_auth_policy(user)

            hashed_password = self.library.get_hash(input.identify)
            async with self.db.transaction() as session:
                stmt = (
                    update(ApiEndpointAuthEntity)
                    .where(ApiEndpointAuthEntity.id == user.id)
                    .values(identify=hashed_password)
                )
                result = await session.execute(stmt)

            if (result.rowcount or 0) != 1:
                raise RuntimeError(
                    f"Unable to reset password for username {user.username}. Please try again or contact administrator."
                )

            updated = await self.find_one_force_select_all({"id": user.id})
            if updated is None:
                raise RuntimeError(
                    f"Unable to load api endpoint authentication id '{user.id}' after password reset."
                )
            return GraphResetPasswordOutput.model_validate(
                updated, from_attributes=True
            )
        except Exception as err:  # pragma: no cover - defensive logging
            self.log.error("reset_password_failed", error=str(err))
            raise ValueError(f"Reset password error. {err}") from err

    async def who_am_i(
        self,
        user: JWTAuthGuardApiEndpointAuthUserPayload,
        context: Optional[Context] = None,
    ) -> GraphSignupOutput:
        try:
            user_id_raw = user.get("id")
            if user_id_raw is None:
                raise ValueError("Invalid JWT payload. Missing subject identifier.")
            user_id = int(user_id_raw)

            stmt = (
                select(ApiEndpointAuthEntity)
                .where(ApiEndpointAuthEntity.id == user_id)
                .where(ApiEndpointAuthEntity.deleted.is_(None))
            )
            async with self.db.session_ctx() as session:
                result = await session.execute(stmt.limit(1))
                entity = result.scalars().first()

            if entity is not None:
                return GraphSignupOutput.model_validate(entity, from_attributes=True)

            encoded = self.library.base64_enc(user_id)
            raise LookupError(
                f"Api endpoint authentication id '{encoded}' not found."
            )
        except Exception as err:  # pragma: no cover - defensive logging
            self.log.error("who_am_i_failed", error=str(err))
            raise ValueError(f"Who am I error. {err}") from err

    async def sign_out(
        self,
        user: JWTAuthGuardApiEndpointAuthUserPayload,
        context: Optional[Context] = None,
    ) -> bool:
        try:
            user_id_raw = user.get("id")
            if user_id_raw is None:
                raise ValueError("Invalid JWT payload. Missing subject identifier.")
            user_id = int(user_id_raw)

            async with self.db.transaction() as session:
                stmt = (
                    update(ApiEndpointAuthEntity)
                    .where(ApiEndpointAuthEntity.id == user_id)
                    .values(jwt_access_token=None, jwt_refresh_token=None)
                )
                result = await session.execute(stmt)

            if (result.rowcount or 0) == 1:
                return True

            encoded = self.library.base64_enc(user_id)
            raise LookupError(
                f"Signout failed. Api endpoint authentication id '{encoded}' not found. Invalid JWT token."
            )
        except Exception as err:  # pragma: no cover - defensive logging
            self.log.error("sign_out_failed", error=str(err))
            raise ValueError(f"Signout error. {err}") from err

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _prepare_signup_payload(
        self, data: Union[GraphSignupInput, Mapping[str, Any]]
    ) -> Dict[str, Any]:
        if isinstance(data, BaseModel):
            payload = data.model_dump(exclude_unset=True)
        elif isinstance(data, Mapping):
            payload = dict(data)
        else:  # pragma: no cover - defensive path
            table = getattr(ApiEndpointAuthEntity, "__table__", None)
            if table is None:
                payload = {}
            else:
                payload = {
                    column.name: getattr(data, column.name)
                    for column in table.columns
                    if hasattr(data, column.name)
                }

        identify = payload.get("identify")
        if not identify:
            raise ValueError("Issue with required field identify/password")

        payload["identify"] = self.library.get_hash(str(identify))
        return payload

__all__ = ["ApiEndpointAuthService"]

