from nest.core import Module
from src.ai.tenant_user.cli import AiTenantUserCli
from src.ai.tenant_user.controller import AiTenantUserController
from src.ai.tenant_user.service import AiTenantUserService


@Module(
    controllers=[AiTenantUserController],
    providers=[AiTenantUserService],
)
class AiTenantUserModule:
    pass


@Module(
    controllers=[AiTenantUserCli],
    providers=[AiTenantUserService],
)
class AiTenantUserCliModule:
    pass
