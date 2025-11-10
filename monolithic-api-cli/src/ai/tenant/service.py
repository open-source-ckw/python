from nest.core import Injectable
from libs.conf.service import ConfService
from libs.log.service import LogService
from libs.sql_alchemy.service import SqlAlchemyService
from src.ai.tenant.repository import AiTenantRepository

@Injectable
class AiTenantService:
    def __init__(self, db: SqlAlchemyService, conf: ConfService, log: LogService):
        self.db = db  # or db.use("main")
        self.conf = conf
        self.log = log
        self.repo = AiTenantRepository(self.db)

    async def create_tenant(self, name: str):
        return await self.repo.create(name)

    async def get_tenant(self, tenant_id: int):
        return await self.repo.find_one_by_id(tenant_id)

    async def search_tenants_by_name(self, name: str):
        return await self.repo.find_many_by_name(name)
    
    async def update_name(self, tenant_id: int, new_name: str):
        return await self.repo.update_name_by_id(tenant_id, new_name)

    async def patch_tenant(self, tenant_id: int, data: dict):
        return await self.repo.patch_by_id(tenant_id, data)
