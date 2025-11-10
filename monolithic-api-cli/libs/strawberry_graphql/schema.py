# libs/strawberry_graphql/schema.py
from __future__ import annotations

import importlib
import pkgutil
from typing import Iterable, Optional

import strawberry
from strawberry.extensions import DisableIntrospection
from strawberry.tools import merge_types

from libs.strawberry_graphql.decorator import QUERY_ROOTS, MUTATION_ROOTS


class StrawberryGraphQLSchema:
    """
    Auto-imports *.resolver modules under configured packages,
    merges registered Query/Mutation roots, and (optionally) disables introspection.

    Single class; no nested classes/functions.
    """

    def __init__(
        self,
        packages: Optional[Iterable[str]] = None,
        disable_introspection: bool = False,
        logger=None,
    ) -> None:
        self._packages = list(packages or ["src"])
        self._disable_introspection = bool(disable_introspection)
        self._discovered = False
        self._schema: Optional[strawberry.Schema] = None
        self._logger = logger

    def _log(self, msg: str) -> None:
        try:
            if self._logger:
                self._logger.info(msg)
        except Exception:
            pass  # avoid failing if no logger


    def _discover_resolvers(self) -> None:
        if self._discovered:
            return

        self._log(f"[GQL] Scanning packages: {self._packages}")

        for basepkg in self._packages:
            try:
                pkg = importlib.import_module(basepkg)
            except Exception as e:
                self._log(f"[GQL] Could not import base package '{basepkg}': {e}")
                continue

            if not hasattr(pkg, "__path__"):
                self._log(f"[GQL] Package '{basepkg}' has no __path__; skipping walk")
                continue

            for mod in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
                # Convention: any module named "...resolver" is a resolver module
                if mod.name.endswith("resolver"):
                    try:
                        importlib.import_module(mod.name)
                        self._log(f"[GQL] Imported resolver module: {mod.name}")
                        self._discovered = True
                    except Exception as e:
                        self._log(f"[GQL] Failed to import resolver '{mod.name}': {e}")

        
        # After discovery, log what got registered
        self._log(f"[GQL] Registered Query roots: {[cls.__name__ for cls in QUERY_ROOTS]}")
        self._log(f"[GQL] Registered Mutation roots: {[cls.__name__ for cls in MUTATION_ROOTS]}")

    def build(self) -> strawberry.Schema:
        self._discover_resolvers()

        if not QUERY_ROOTS:
            raise RuntimeError("No Query roots registered; add a module with @register_query_root")

        Query = merge_types("Query", tuple(QUERY_ROOTS)) if len(QUERY_ROOTS) > 1 else QUERY_ROOTS[0]
        Mutation = (
            merge_types("Mutation", tuple(MUTATION_ROOTS))
            if len(MUTATION_ROOTS) > 1
            else (MUTATION_ROOTS[0] if MUTATION_ROOTS else None)
        )

        extensions = [DisableIntrospection()] if self._disable_introspection else []
        self._schema = strawberry.Schema(query=Query, mutation=Mutation, extensions=extensions)
        return self._schema

    @property
    def schema(self) -> strawberry.Schema:
        return self._schema or self.build()
