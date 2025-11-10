from typing import Any, Optional, List, Dict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.ai.tenant.entity import AiTenantEntity
from libs.sql_alchemy.service import SqlAlchemyService

class AiTenantRepository:
    def __init__(self, db: SqlAlchemyService):
        self.db = db  # optionally: db.use("main")

    async def create(self, name: str) -> AiTenantEntity:
        async with self.db.transaction() as s:  # s: AsyncSession
            tenant = AiTenantEntity(name=name)
            s.add(tenant)
            await s.flush()
            await s.refresh(tenant)
            return tenant

    async def find_one_by_id(self, tenant_id: int) -> Optional[AiTenantEntity]:
        async with self.db.session_ctx() as s:
            stmt = select(AiTenantEntity).where(AiTenantEntity.id == tenant_id)
            result = await s.execute(stmt)
            return result.scalars().first()  # -> Tenant | None

    async def find_many_by_name(self, name: str) -> List[AiTenantEntity]:
        async with self.db.session_ctx() as s:
            stmt = select(AiTenantEntity).where(AiTenantEntity.name == name)
            result = await s.execute(stmt)
            return list(result.scalars().all())  # -> list[Tenant]

    async def update_name_by_id(self, tenant_id: int, new_name: str) -> Optional[AiTenantEntity]:
        async with self.db.transaction() as s:  # s: AsyncSession
            stmt = select(AiTenantEntity).where(AiTenantEntity.id == tenant_id)
            result = await s.execute(stmt)
            row = result.scalars().first()
            if not row:
                return None
            row.name = new_name
            # row is already tracked; add() not required but harmless
            s.add(row)
            await s.flush()
            await s.refresh(row)
            return row

    async def patch_by_id(self, tenant_id: int, data: Dict[str, Any]) -> Optional[AiTenantEntity]:
        allowed = {"name"}  # extend as needed (e.g., "secret_name", "age")
        changes = {k: v for k, v in data.items() if k in allowed}

        if not changes:
            return await self.find_one_by_id(tenant_id)

        async with self.db.transaction() as s:
            stmt = select(AiTenantEntity).where(AiTenantEntity.id == tenant_id)
            result = await s.execute(stmt)
            row = result.scalars().first()
            if not row:
                return None

            for k, v in changes.items():
                setattr(row, k, v)

            s.add(row)
            await s.flush()
            await s.refresh(row)
            return row

    async def find_one_by_id(self, tenant_id: int) -> Optional[AiTenantEntity]:
        async with self.db.session_ctx() as s:
            stmt = select(AiTenantEntity).where(AiTenantEntity.id == tenant_id)
            result = await s.execute(stmt)
            return result.scalars().first()
