from typing import Any, Optional
from nest.core import Controller, Get, Post, Put, Patch  # adjust to your decorators
from src.ai.tenant.entity import AiTenantEntity
from src.ai.tenant.service import AiTenantService

@Controller("tenant")
class AiTenantController:
    def __init__(self, service: AiTenantService):
        self.service = service

    # Sample (your example kept)
    @Get("/")
    async def get_tenant_info(self) -> Any:
        return await self.service.get_tenant(1)

    # CREATE: POST /tenant  body: { "name": "Acme" }
    @Post("/")
    async def create(self, body: AiTenantEntity) -> Any:
        name = body.name
        if not isinstance(name, str) or not name.strip():
            return {"ok": False, "error": "name is required"}
        return await self.service.create_tenant(name)

    # READ: GET /tenant/{tenant_id}
    @Get("/{tenant_id}")
    async def get_by_id(self, tenant_id: int) -> Any:
        return await self.service.get_tenant(tenant_id)

    # SEARCH: GET /tenant/search?name=Acme
    @Get("/search")
    async def search_by_name(self, name: Optional[str] = None) -> Any:
        if not name:
            return []
        return await self.service.search_tenants_by_name(name)

    # UPDATE NAME: PUT /tenant/{tenant_id}/name   body: { "name": "New Name" }
    @Put("/{tenant_id}/name")
    async def update_name(self, tenant_id: int, body: AiTenantEntity) -> Any:
        new_name = body.name
        if not isinstance(new_name, str) or not new_name.strip():
            return {"ok": False, "error": "name is required"}
        return await self.service.update_name(tenant_id, new_name)

    # PATCH: PATCH /tenant/{tenant_id}   body: { ...partial fields... }
    @Patch("/{tenant_id}")
    async def patch(self, tenant_id: int, body: AiTenantEntity) -> Any:
        return await self.service.patch_tenant(tenant_id, body)
