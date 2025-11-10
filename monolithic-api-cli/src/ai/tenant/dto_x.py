from typing import Optional, List
import strawberry
from strawberry.types import Info
from pydantic import BaseModel, Field, ConfigDict

# Reuse your SQLModel entity directly (Pydantic model under the hood)
from src.ai.tenant.entity import AiTenantEntity  # <-- your class shown in the prompt

# ───────────────────────────────────────────────────────────────────────────────
# Minimal Pydantic DTOs for inputs (no duplication of entity fields)
# ───────────────────────────────────────────────────────────────────────────────

class TenantCreateDTO(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)

class TenantUpdateNameDTO(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)

class TenantPatchDTO(BaseModel):
    # add more optional fields later as needed; for now this matches your REST usage
    name: Optional[str] = Field(None, min_length=2, max_length=255)

    # Let Pydantic ignore unknowns so you can pass partials safely
    model_config = ConfigDict(extra='ignore')  # v2 config style :contentReference[oaicite:2]{index=2}


# ───────────────────────────────────────────────────────────────────────────────
# Strawberry types generated from Pydantic / SQLModel (no field duplication)
# ───────────────────────────────────────────────────────────────────────────────

# OUTPUT TYPE: include ALL fields from AiTenantEntity (id, name, created, updated, deleted, ...)
@strawberry.experimental.pydantic.type(model=AiTenantEntity, all_fields=True)  # :contentReference[oaicite:3]{index=3}
class GraphTenant:
    # no fields here on purpose (all_fields=True)
    pass

# INPUTS: use tiny Pydantic DTOs and generate matching Strawberry inputs
@strawberry.experimental.pydantic.input(model=TenantCreateDTO, all_fields=True)  # :contentReference[oaicite:4]{index=4}
class GraphTenantCreateInput: ...
@strawberry.experimental.pydantic.input(model=TenantUpdateNameDTO, all_fields=True)
class GraphTenantUpdateNameInput: ...
@strawberry.experimental.pydantic.input(model=TenantPatchDTO, all_fields=True)
class GraphTenantPatchInput: ...

# Payload for mutations (mirrors your REST `{ ok, error, tenant }`)
@strawberry.type
class GraphTenantPayload:
    ok: bool
    error: Optional[str] = None
    tenant: Optional[GraphTenant] = None


# ───────────────────────────────────────────────────────────────────────────────
# Helpers
# ───────────────────────────────────────────────────────────────────────────────

def _svc(info: Info):
    """
    Resolve AiTenantService from your DI container / context.
    Adjust if your container exposes a different API.
    """
    ctx = getattr(info, "context", {}) or {}
    container = ctx.get("container")
    if container:
        if hasattr(container, "get"):
            svc = container.get("AiTenantService")
            if svc: return svc
        if hasattr(container, "resolve"):
            svc = container.resolve("AiTenantService")
            if svc: return svc
    if "tenant_service" in ctx:  # direct injection fallback
        return ctx["tenant_service"]
    raise RuntimeError("AiTenantService not available in GraphQL context")

