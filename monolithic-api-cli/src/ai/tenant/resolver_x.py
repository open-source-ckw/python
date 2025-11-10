from typing import Optional, List
from fastapi import Depends
from nest.core import Injectable
import strawberry
from strawberry.types import Info
from libs.strawberry_graphql.decorator import register_mutation_root, register_query_root
from src.ai.tenant.dto_x import _svc, GraphTenant, GraphTenantCreateInput, GraphTenantPatchInput, GraphTenantPayload, GraphTenantUpdateNameInput
from src.ai.tenant.entity import AiTenantEntity
from src.ai.tenant.service import AiTenantService
from strawberry.fastapi import BaseContext


# ───────────────────────────────────────────────────────────────────────────────
# Queries — parity with REST
# ───────────────────────────────────────────────────────────────────────────────

@register_query_root
@strawberry.type
class AiTenantQuery:
    def __init__(self):
        pass

    # GET /tenant/{tenant_id}
    @strawberry.field
    async def tenant(self, info: Info, tenant_id: int) -> Optional[GraphTenant]:
        info = info
        container = info.context['pynest_container']
        service: AiTenantService = container.get_instance(AiTenantService)
        obj = await service.get_tenant(tenant_id)
        return GraphTenant.from_pydantic(obj) if obj else None
    
    # GET /tenant/ -> your REST sample that returns tenant 1
    @strawberry.field
    async def tenant_info(self, info: Info) -> Optional[GraphTenant]:
        obj = await _svc(info).get_tenant(1)
        return GraphTenant.from_pydantic(obj) if obj else None  # :contentReference[oaicite:5]{index=5}

    # GET /tenant/search?name=Acme
    @strawberry.field
    async def tenants_by_name(self, info: Info, name: Optional[str] = None) -> List[GraphTenant]:
        if not name:
            return []
        rows = await _svc(info).search_tenants_by_name(name)
        return [GraphTenant.from_pydantic(r) for r in rows or []]  # handles datetime serialization via Strawberry DateTime  :contentReference[oaicite:6]{index=6}


# ───────────────────────────────────────────────────────────────────────────────
# Mutations — parity with REST
# ───────────────────────────────────────────────────────────────────────────────

@register_mutation_root
@strawberry.type
class AiTenantMutation:
    # POST /tenant  body: { name }
    @strawberry.mutation
    async def create_tenant(self, info: Info, input: GraphTenantCreateInput) -> GraphTenantPayload:
        dto = input.to_pydantic()  # runs Pydantic validation as advised by Strawberry docs :contentReference[oaicite:7]{index=7}
        if not dto.name.strip():
            return GraphTenantPayload(ok=False, error="name is required")
        created = await _svc(info).create_tenant(dto.name)
        return GraphTenantPayload(ok=True, tenant=GraphTenant.from_pydantic(created))

    # PUT /tenant/{tenant_id}/name  body: { name }
    @strawberry.mutation
    async def update_tenant_name(self, info: Info, tenant_id: int, input: GraphTenantUpdateNameInput) -> GraphTenantPayload:
        dto = input.to_pydantic()
        if not dto.name.strip():
            return GraphTenantPayload(ok=False, error="name is required")
        updated = await _svc(info).update_name(tenant_id, dto.name)
        return GraphTenantPayload(ok=True, tenant=GraphTenant.from_pydantic(updated))

    # PATCH /tenant/{tenant_id}  body: partial
    @strawberry.mutation
    async def patch_tenant(self, info: Info, tenant_id: int, input: GraphTenantPatchInput) -> GraphTenantPayload:
        dto = input.to_pydantic()
        partial = dto.model_dump(exclude_unset=True)
        patched = await _svc(info).patch_tenant(tenant_id, partial)
        return GraphTenantPayload(ok=True, tenant=GraphTenant.from_pydantic(patched))