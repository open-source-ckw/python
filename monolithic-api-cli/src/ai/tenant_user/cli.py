from nest.core.decorators.cli.cli_decorators import CliCommand, CliController
from src.ai.tenant_user.service import AiTenantUserService

@CliController("tenant-user")
class AiTenantUserCli:
    def __init__(self, service: AiTenantUserService):
        self.service = service

    @CliCommand("hello")
    def hello(self):
        
        self.service.hello()