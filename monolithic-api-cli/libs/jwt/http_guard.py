"""HTTP-layer JWT guard helpers for REST controllers."""
from __future__ import annotations

from typing import Any, Iterable, Sequence

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.dependencies.utils import get_parameterless_sub_dependant
from fastapi.routing import APIRoute
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from nest.core.decorators.guards import BaseGuard
from nest.core.pynest_container import PyNestContainer
from starlette.routing import request_response

from libs.conf.service import ConfService
from libs.jwt.guard import JwtGuard
from libs.log.service import LogService


_PUBLIC_FLAG = "__public__"


class JwtAccessGuard(BaseGuard):
    """HTTP bearer guard that reuses :class:`libs.jwt.guard.JwtGuard` verification."""

    security_scheme = HTTPBearer(
        scheme_name="JWTAccess",
        bearerFormat="JWT",
        description="Paste the access token minted by the authentication flow.",
        auto_error=False,
    )

    def __init__(self) -> None:
        container = PyNestContainer()
        self.jwt_guard: JwtGuard = container.get_instance(JwtGuard)
        self.conf: ConfService = container.get_instance(ConfService)
        try:
            self.log: LogService | None = container.get_instance(LogService)
        except Exception:  # pragma: no cover - log service should exist but guard must survive without it
            self.log = None

    async def can_activate(
        self,
        request: Request,
        credentials: HTTPAuthorizationCredentials | None = None,
    ) -> bool:
        endpoint = request.scope.get("endpoint")
        if endpoint is not None and getattr(endpoint, _PUBLIC_FLAG, False):
            request.state.auth = None
            return True

        if credentials is None or not credentials.credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized: missing bearer token",
            )

        if credentials.scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized: invalid auth scheme",
            )

        aud = getattr(self.conf, "jwt_audience", None)
        iss = getattr(self.conf, "jwt_issuer", None)

        result = self.jwt_guard.verify_access(credentials.credentials, aud=aud, iss=iss)
        if not result or not result.get("ok"):
            err = (result or {}).get("error") or {}
            code = err.get("code") or err.get("reason") or "invalid_token"
            msg = err.get("message") or "Unauthorized"
            if self.log:
                self.log.warn(f"[REST][auth] verify_access failed: {code} - {msg}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Unauthorized: {code}",
            )

        request.state.auth = result.get("claims")
        return True


def PublicRoute(target: Any) -> Any:
    """Decorator that marks a controller or handler as public (no JWT required)."""

    if isinstance(target, type):
        setattr(target, _PUBLIC_FLAG, True)
        for _, attr in list(target.__dict__.items()):
            if callable(attr) and hasattr(attr, "__http_method__"):
                setattr(attr, _PUBLIC_FLAG, True)
        return target

    setattr(target, _PUBLIC_FLAG, True)
    return target


def apply_jwt_guard_on_rest_endpoint(
    http_server: FastAPI,
    *,
    guard_cls: type[JwtAccessGuard] = JwtAccessGuard,
    public_routes: Iterable[str] | None = None,
) -> None:
    """Attach ``guard_cls`` to every REST route except those marked as public.

    ``public_routes`` should be an iterable of path strings (e.g. ``"/health"``)
    that match the ``APIRoute.path`` values you want to keep open.  The default
    wiring in :mod:`src.main` passes :pyattr:`libs.conf.service.ConfService.rest_public_routes`,
    so the allow-list can be managed alongside ``gql_public_operations`` in the
    central configuration service.
    """

    public_patterns: set[str] = {route for route in (public_routes or [])}
    guard_dep = guard_cls.as_dependency()
    setattr(guard_dep.dependency, "__pynest_guard__", guard_cls)

    for route in http_server.routes:
        if not isinstance(route, APIRoute):
            continue
        if not route.include_in_schema:
            continue
        if route.path in {"/openapi.json"} or route.path.startswith("/docs") or route.path.startswith("/redoc"):
            continue
        if route.path in public_patterns:
            continue

        endpoint = getattr(route, "endpoint", None)
        if endpoint is not None and getattr(endpoint, _PUBLIC_FLAG, False):
            continue

        if any(getattr(dep.dependency, "__pynest_guard__", None) is guard_cls for dep in route.dependencies):
            continue

        route.dependencies.append(guard_dep)
        route.dependant.dependencies.insert(
            0,
            get_parameterless_sub_dependant(depends=guard_dep, path=route.path_format),
        )
        route.app = request_response(route.get_route_handler())


def iter_protected_routes(http_server: FastAPI) -> Sequence[APIRoute]:
    """Return the list of routes that are currently protected by the JWT guard."""

    protected: list[APIRoute] = []
    for route in http_server.routes:
        if isinstance(route, APIRoute):
            if any(getattr(dep.dependency, "__pynest_guard__", None) is JwtAccessGuard for dep in route.dependencies):
                protected.append(route)
    return protected
