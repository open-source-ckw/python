# libs/strawberry_graphql/router.py
from typing import Any, Callable, Optional
from fastapi import APIRouter
from strawberry.fastapi import GraphQLRouter
from libs.strawberry_graphql.schema import StrawberryGraphQLSchema

class StrawberryGraphQLRouter:
    """
    Thin wrapper that creates a Strawberry GraphQLRouter (FastAPI APIRouter)
    with optional IDE and context_getter.

    Constraints: one class in file; no nested classes/functions.
    """

    def __init__(
        self,
        schema_builder: StrawberryGraphQLSchema,
        context_getter: Optional[Callable[..., Any]] = None,
        graphql_ide: Optional[str] = "apollo-sandbox",  # "graphiql" | "apollo-sandbox" | "pathfinder" | None
        allow_get: bool = True,
        dependency_overrides_provider = None
    ) -> None:
        self._schema_builder = schema_builder
        self._context_getter = context_getter
        self._graphql_ide = graphql_ide
        self._allow_get = allow_get
        self._dependency_overrides_provider = dependency_overrides_provider

    def as_router(self) -> APIRouter:
        # GraphQLRouter supports graphql_ide, context_getter, allow_queries_via_get, etc. :contentReference[oaicite:3]{index=3}
        return GraphQLRouter(
            self._schema_builder.schema,
            graphql_ide=self._graphql_ide,
            allow_queries_via_get=self._allow_get,
            context_getter=self._context_getter,  # context injection documented in Strawberry FastAPI. :contentReference[oaicite:4]{index=4}
            multipart_uploads_enabled=True,
            dependency_overrides_provider=self._dependency_overrides_provider
        )
