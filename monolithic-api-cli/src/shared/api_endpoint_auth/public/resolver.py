from datetime import datetime, timezone
from typing import Annotated
from sqlalchemy import Boolean
from strawberry.types import Info as StrawberryGraphQLResolveInfo
from libs.pynest_graphql import Args, Context, Mutation, Query, Resolver, BodySelection
from src.shared.api_endpoint_auth.jwt import ApiEndpointAuthJwt
from src.shared.api_endpoint_auth.private.dto import ApiEndpointAuthDto
from src.shared.api_endpoint_auth.public.dto import (
    GraphHello,
    GraphHelloOutput,
    GraphLogin,
    GraphLoginInput,
    GraphLoginOutput,
    GraphRefreshJWT,
    GraphResetPassword,
    GraphResetPasswordInput,
    GraphResetPasswordOutput,
    GraphSignout,
    GraphSignup,
    GraphSignupInput,
    GraphSignupOutput,
    GraphWhoAmI,
)
from src.shared.api_endpoint_auth.service import ApiEndpointAuthService


@Resolver(of=ApiEndpointAuthDto)
class ApiEndpointAuthPublicResolver:
    def __init__(
        self,
        service: ApiEndpointAuthService,
        aepujwt: ApiEndpointAuthJwt,
    ) -> None:
        self.service = service
        self.aepujwt = aepujwt

    @Query(name=GraphHello.metaname, description=GraphHello.metadesc)
    async def hello(
        self,
        ctx: Annotated[dict, Context()],
        selection: Annotated[GraphHelloOutput, BodySelection()],
        info: StrawberryGraphQLResolveInfo,
        ) -> GraphHelloOutput:
        timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        return GraphHelloOutput(
            message=(
                "Hello API user, this is the enterprise application, and you are using "
                f"GraphQL API service. Have a nice day! {timestamp}"
            )
        )

    @Mutation(name=GraphSignup.metaname, description=GraphSignup.metadesc)
    async def sign_up(
        self,
        ctx: Annotated[dict, Context()],
        input: Annotated[GraphSignupInput, Args("input")],
        selection: Annotated[GraphSignupOutput, BodySelection()],
        info: StrawberryGraphQLResolveInfo,
    ) -> GraphSignupOutput:
        result = await self.service.sign_up(input)
        if isinstance(result, list) and len(result) == 1:
            return result[0]
        return result

    @Mutation(name=GraphLogin.metaname, description=GraphLogin.metadesc)
    async def sign_in(
        self,
        ctx: Annotated[dict, Context()],
        input: Annotated[GraphLoginInput, Args("input")],
        selection: Annotated[GraphLoginOutput, BodySelection()],
        info: StrawberryGraphQLResolveInfo,
    ) -> GraphLoginOutput:
        return await self.service.sign_in(input)

    @Mutation(name=GraphRefreshJWT.metaname, description=GraphRefreshJWT.metadesc)
    async def jwt_refresh_tokens(
        self,
        ctx: Annotated[dict, Context()],
        jwt_refresh_token: Annotated[str, Args("jwtRefreshToken")],
        selection: Annotated[GraphLoginOutput, BodySelection()],
        info: StrawberryGraphQLResolveInfo,
    ) -> GraphLoginOutput:
        return await self.service.jwt_refresh_tokens(jwt_refresh_token)

    @Mutation(name=GraphResetPassword.metaname, description=GraphResetPassword.metadesc)
    async def reset_password(
        self,
        ctx: Annotated[dict, Context()],
        input: Annotated[GraphResetPasswordInput, Args("input")],
        selection: Annotated[GraphResetPasswordOutput, BodySelection()],
        info: StrawberryGraphQLResolveInfo,
    ) -> GraphResetPasswordOutput:
        return await self.service.reset_password(input)

    @Query(name=GraphWhoAmI.metaname, description=GraphWhoAmI.metadesc)
    async def who_am_i(
        self,
        ctx: Annotated[dict, Context()],
        selection: Annotated[GraphSignupOutput, BodySelection()],
        info: StrawberryGraphQLResolveInfo,
    ) -> GraphSignupOutput:
        user = self.aepujwt.current_api_user(info.context)
        return await self.service.who_am_i(user, ctx)

    @Mutation(name=GraphSignout.metaname, description=GraphSignout.metadesc)
    async def sign_out(
        self,
        ctx: Annotated[dict, Context()],
        selection: Annotated[bool, BodySelection()],
        info: StrawberryGraphQLResolveInfo,
    ) -> bool:
        user = self.aepujwt.current_api_user(info.context)
        return await self.service.sign_out(user, ctx)
