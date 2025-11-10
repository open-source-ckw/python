from nest.core import Controller, Get
from src.ai.tenant_user.service import AiTenantUserService

@Controller("tenant-user")
class AiTenantUserController:
    def __init__(self, service: AiTenantUserService):
        self.service = service
    
    @Get("/")
    def hello(self):
        self.service.hello()
