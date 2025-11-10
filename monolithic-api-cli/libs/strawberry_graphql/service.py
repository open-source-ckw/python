# libs/strawberry_graphql/service.py
import json
from pathlib import Path
from typing import Any, Iterable, Optional

from fastapi import Depends, FastAPI, HTTPException, Request, status
from nest.core import Injectable
from strawberry.printer import print_schema  # export SDL

from libs.conf.service import ConfService
from libs.jwt.guard import JwtGuard
from libs.jwt.service import JwtService
from libs.log.service import LogService
from libs.strawberry_graphql.router import StrawberryGraphQLRouter
from libs.strawberry_graphql.schema import StrawberryGraphQLSchema
from nest.core.pynest_application import PyNestApp
from nest.core.pynest_container import PyNestContainer

@Injectable
class StrawberryGraphQLService:
    """
    Injectable facade for the GraphQL stack.

    Config behavior (no extra envs introduced):
      - If either:
            conf.gql_disable_subgraph_playground == True  OR
            conf.gql_disable_supergraph_playground == True
        → IDE disabled, introspection disabled, IDE HTML not public.
      - Else
        → IDE enabled ("apollo-sandbox"), introspection enabled,
          and the IDE HTML (GET with Accept: text/html) is allowed without JWT.
      - JWT is REQUIRED for all operations except when the GraphQL operationName
        is in conf.graphql_public_operations (public ops list).

    Router/Strawberry notes:
      - graphql_ide/context_getter are official on GraphQLRouter.  (Strawberry FastAPI)
      - Introspection disabling uses Strawberry's DisableIntrospection extension.
      - GraphQL over HTTP: GET queries carry ?query&operationName...; we DO NOT bypass those.
    """

    def __init__(self, conf: ConfService, log: LogService, jwt_service: JwtService, jwt_guard: JwtGuard) -> None:
        # DI preference: names match params
        self.conf = conf
        self.log = log

        # JWT DI slots (resolved during mount)
        self.jwt_service = jwt_service
        self.jwt_guard = jwt_guard

        # Discovery roots
        self._packages: list[str] = ["src"]

        # Decide IDE & HTML policy *once*, from your two flags (simple rule)
        self.gql_disable_subgraph_playground: bool = bool(getattr(self.conf, "gql_disable_subgraph_playground", False))
        self.gql_disable_supergraph_playground: bool = bool(getattr(self.conf, "gql_disable_supergraph_playground", False))

        # IDE is enabled only when BOTH disables are False
        self.ide_enabled: bool = not (self.gql_disable_subgraph_playground or self.gql_disable_supergraph_playground)
        # HTML page of IDE is public only when IDE is enabled
        self.public_ide_html: bool = self.ide_enabled

        # configure scanning root (auto-import *.resolver)
        """
        self.set_scan_packages([
            "src",
            "src.shared",
            "src.shared.api_endpoint_auth",
            "src.shared.api_endpoint_auth.public",
        ])
        """
        self.set_scan_packages(["src"])


    # ---------- Optional knobs ----------
    def set_scan_packages(self, packages: Iterable[str]) -> None:
        self._packages = list(packages)

    # ---------- Main entry ----------
    def mount(self, http_server: FastAPI, app: PyNestApp) -> None:
        """
        Build schema, create router, attach JWT dependency, mount under prefix.
        Optionally pass PyNest app so we can resolve JwtGuard/JwtService via DI.
        """
        # just a precaution as this is starup process
        if self.jwt_service is None and self.jwt_guard is None:
            self.log.error("[GraphQL] Failed to resolve JwtGuard/JwtService from container: {e}")
            return False

        # Decide IDE + introspection based on the simplified flags
        graphql_ide: Optional[str] = "apollo-sandbox" if self.ide_enabled else None  # Strawberry supports this IDE name.  # noqa: E501
        disable_introspection = not self.ide_enabled  # Sandbox needs introspection enabled.  # noqa: E501

        self.log.info(f"[GraphQL] IDE={'on' if graphql_ide else 'off'}; disable_introspection={disable_introspection}")

        # Build schema (DisableIntrospection when needed)
        schema_builder = StrawberryGraphQLSchema(
            packages=self._packages,
            disable_introspection=disable_introspection,  # disables all introspection queries when True
            logger=self.log
        )

        # Router with Strawberry's context_getter (request/auth for resolvers)
        router_builder = StrawberryGraphQLRouter(
            schema_builder=schema_builder,
            context_getter=self._context_getter,
            graphql_ide=graphql_ide,       # "apollo-sandbox" | "graphiql" | None
            allow_get=False,
        )
        gql_router = router_builder.as_router()

        # Normalize prefix from conf.gql_root_slug (leading single "/")
        prefix = self._normalize_prefix(getattr(self.conf, "gql_root_slug", None))

        # Mount and apply router-wide JWT dependency
        http_server.include_router(
            gql_router,
            prefix=prefix,
            dependencies=[Depends(self._jwt_dependency)],  # secure everything by default
        )

        print("GraphQL router mounted and runnin at:", prefix)

        # Optional: write SDL for tooling/clients
        sdl_dir = getattr(self.conf, "gql_schema_dir_path", None)
        if sdl_dir:
            try:
                path = Path(sdl_dir).expanduser().resolve()
                path.mkdir(parents=True, exist_ok=True)
                sdl = print_schema(schema_builder.schema)
                (path / "schema.graphql").write_text(sdl, encoding="utf-8")
                self.log.info(f"[GraphQL] SDL written → {path / 'schema.graphql'}")
            except Exception as e:
                self.log.error(f"[GraphQL] Failed to write SDL: {e}")

    # ---------- Router-wide JWT dependency ----------
    async def _jwt_dependency(self, request: Request) -> Any:
        # Log operationName + whether Authorization header is present
        op_name = await self._extract_operation_name(request)
        auth_hdr = request.headers.get("authorization")
        self.log.info(
            f"[GraphQL][auth] op={op_name or '-'} "
            f"auth={'present' if auth_hdr else 'absent'} "
            f"method={request.method} path={request.url.path}"
        )

        # 1) Public operations (by operationName)
        public_ops: list[str] = list(getattr(self.conf, "gql_public_operations", []) or [])
        if op_name and op_name in public_ops:
            request.state.auth = None
            return None

        # 2) Allow IDE HTML shell (GET + Accept: text/html, no ?query=) when enabled
        if self.public_ide_html:
            accept = (request.headers.get("accept") or "").lower()
            is_get = request.method.upper() == "GET"
            wants_html = "text/html" in accept
            has_query_param = "query" in request.query_params
            if is_get and wants_html and not has_query_param:
                request.state.auth = None
                return None
            
        # 3) Require JwtGuard
        if not self.jwt_guard:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized: guard missing")
        
        # 4) Extract Bearer token
        token = self.jwt_guard.token_from_authorization(auth_hdr)
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized: missing bearer token")
        
        # 5) Verify access token (optionally pass aud/iss if you keep them in conf)
        aud = getattr(self.conf, "jwt_audience", None)
        iss = getattr(self.conf, "jwt_issuer", None)

        try:
            result = self.jwt_guard.verify_access(token, aud=aud, iss=iss)
            # TODO: need to implement DB operation to check JWT with db. for higher security with jti key
        except Exception as e:
            # In case guard.verify_access itself raises unexpectedly
            self.log.warn(f"[GraphQL][auth] verify_access raised: {e}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized: invalid access token")
        
        if not result or not result.get("ok"):
            err = (result or {}).get("error") or {}
            
            # Try to surface a helpful message/code if present
            code = err.get("code") or err.get("reason") or "invalid_token"
            msg = err.get("message") or "Unauthorized"
            self.log.warn(f"[GraphQL][auth] verify_access failed: {code} - {msg}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Unauthorized: {code}")


        claims = result.get("claims") or {}
        request.state.auth = claims
        return claims


    # ---------- Strawberry context ----------
    async def _context_getter(self, request: Request) -> dict:
        """
        Strawberry's documented hook for per-request context:
          - request (FastAPI Request)
          - auth    (claims set by the guard)
        """
        auth = getattr(request.state, "auth", None)
        return {"request": request, "auth": auth, "pynest_container": PyNestContainer()}

    # ---------- Helpers ----------
    async def _extract_operation_name(self, request: Request) -> Optional[str]:
        """
        Parse GraphQL operationName from GET query or POST JSON body.
        If absent, returns None (auth required unless HTML bypass applies).
        """
        try:
            if request.method == "GET":
                return request.query_params.get("operationName")
            
            # POST (application/json, per GraphQL over HTTP)
            body = await request.body()
            if not body:
                return None
            data = json.loads(body.decode("utf-8"))
            # per spec: 'operationName' is optional; if not present, it's None. :contentReference[oaicite:10]{index=10}
            return data.get("operationName")
        except Exception:
            return None

    def _normalize_prefix(self, slug: str | None, default: str = "graphql") -> str:
        s = (str(slug).strip() if slug is not None else "") or default
        return "/" + s.strip("/")
