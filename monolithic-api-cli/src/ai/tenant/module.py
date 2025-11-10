from nest.core import Module
from libs.sql_alchemy.module import SqlAlchemyModule
from src.ai.tenant.cli import AiTenantCli
from src.ai.tenant.controller import AiTenantController
from src.ai.tenant.service import AiTenantService


@Module(
    imports=[SqlAlchemyModule],
    controllers=[AiTenantController],
    providers=[AiTenantService],
    exports=[AiTenantService],
)
class AiTenantModule:
    pass

@Module(
    imports=[SqlAlchemyModule],
    controllers=[AiTenantCli],
    providers=[AiTenantService],
    exports=[AiTenantService],
)
class AiTenantCliModule:
    pass
