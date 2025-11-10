from nest.core import Controller, Get
from src.ai.tenant.service_sqlalchemy import AiTenantService

@Controller("tenant")
class AiTenantController:
    def __init__(self, service: AiTenantService ):
        self.service = service

    @Get("/")
    async def get_tenant_info(self):
        return await self.service.FindOneById(1)

