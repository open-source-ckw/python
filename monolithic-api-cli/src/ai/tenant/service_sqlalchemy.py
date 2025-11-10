from nest.core import Injectable
from typing import List, Optional, AsyncIterator
from contextlib import asynccontextmanager
from libs.conf.service import ConfService
from libs.log.service import LogService
from sqlalchemy import (
    select, update as sa_update, delete as sa_delete, func,
    asc, desc, String
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert  # for ON CONFLICT upsert (Postgres only)
from sqlalchemy.exc import IntegrityError

from libs.sql_alchemy_old.service import SqlAlchemyService
from src.ai.tenant.entity_sqlalchemy import AiTenantEntitySalAlc


@Injectable
class AiTenantService:
    """
    Business service for te_ai_tenant with explicit CRUD-style operations:

    - Create
    - Upsert
    - Update
    - SoftRemove (alias of SoftDelete)
    - Remove (alias of Delete)
    - SoftDelete
    - Delete
    - Recover (clear soft-delete flag)
    - Restore (alias of Recover)
    - Find (filter/sort/paginate)
    - FindOneById
    """

    def __init__(self, db: SqlAlchemyService, conf: ConfService, log: LogService):
        # If you want to pin this service to a specific connection:
        # self._db = db.use("your-connection-name")
        self._db = db
        self._conf = conf
        self_log = log

    # ------------------------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------------------------

    @asynccontextmanager
    async def _session(self) -> AsyncIterator[AsyncSession]:
        async with self._db.session() as s:
            yield s

    # ------------------------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------------------------

    async def Create(self, *, name: str) -> AiTenantEntitySalAlc:
        """
        Insert a new tenant. Returns the created row.
        """
        async with self._session() as s:
            row = AiTenantEntitySalAlc(name=name)
            s.add(row)
            await s.flush()
            await s.refresh(row)  # pull server defaults (created)
            await s.commit()
            return row

    async def Upsert(self, *, name: str) -> AiTenantEntitySalAlc:
        """
        Insert or update by name.
        - If you have a UNIQUE constraint on name, uses ON CONFLICT DO UPDATE (atomic).
        - If not, falls back to find-or-create (two-step, best-effort).
        """
        async with self._session() as s:
            # Try to use Postgres ON CONFLICT if possible
            try:
                stmt = (
                    pg_insert(AiTenantEntitySalAlc)
                    .values(name=name)
                    .on_conflict_do_update(
                        index_elements=["name"],   # requires a UNIQUE index/constraint on name
                        set_={
                            "name": name,
                            "updated": func.now(),
                            "deleted": None,  # if previously soft-deleted, restore on upsert
                        },
                    )
                    .returning(
                        AiTenantEntitySalAlc.id,
                        AiTenantEntitySalAlc.name,
                        AiTenantEntitySalAlc.created,
                        AiTenantEntitySalAlc.updated,
                        AiTenantEntitySalAlc.deleted,
                    )
                )
                res = await s.execute(stmt)
                await s.commit()
                row = res.first()
                if row is None:
                    # extremely unlikely; fallback
                    return await self.FindOneById(-1)  # will be None
                # hydrate entity-like object
                entity = AiTenantEntitySalAlc(
                    id=row.id,
                    name=row.name,
                    created=row.created,
                    updated=row.updated,
                    deleted=row.deleted,
                )
                return entity
            except Exception:
                # Fallback path for non-Postgres or missing unique constraint on name:
                # 1) try to find existing (including soft-deleted)
                q = select(AiTenantEntitySalAlc).where(AiTenantEntitySalAlc.name == name)
                existing = (await s.execute(q)).scalar_one_or_none()
                if existing:
                    existing.name = name
                    existing.updated = func.now()
                    existing.deleted = None  # restore if soft-deleted
                    await s.flush()
                    await s.refresh(existing)
                    await s.commit()
                    return existing
                # 2) create new
                row = AiTenantEntitySalAlc(name=name)
                s.add(row)
                await s.flush()
                await s.refresh(row)
                await s.commit()
                return row

    async def Update(self, *, tenant_id: int, name: Optional[str] = None) -> Optional[AiTenantEntitySalAlc]:
        """
        Update fields on an active tenant (not soft-deleted). Returns updated entity or None.
        """
        async with self._session() as s:
            q = select(AiTenantEntitySalAlc).where(
                AiTenantEntitySalAlc.id == tenant_id,
                AiTenantEntitySalAlc.deleted.is_(None),
            )
            row = (await s.execute(q)).scalar_one_or_none()
            if row is None:
                return None

            if name is not None:
                row.name = name
            row.updated = func.now()

            await s.flush()
            await s.refresh(row)
            await s.commit()
            return row

    async def SoftDelete(self, *, tenant_id: int) -> bool:
        """
        Soft-delete (mark as deleted) an active tenant.
        """
        async with self._session() as s:
            stmt = (
                sa_update(AiTenantEntitySalAlc)
                .where(
                    AiTenantEntitySalAlc.id == tenant_id,
                    AiTenantEntitySalAlc.deleted.is_(None),
                )
                .values(deleted=func.now(), updated=func.now())
            )
            res = await s.execute(stmt)
            await s.commit()
            return bool(res.rowcount)

    async def SoftRemove(self, *, tenant_id: int) -> bool:
        """
        Alias for SoftDelete.
        """
        return await self.SoftDelete(tenant_id=tenant_id)

    async def Delete(self, *, tenant_id: int) -> bool:
        """
        Hard delete (remove row).
        """
        async with self._session() as s:
            stmt = sa_delete(AiTenantEntitySalAlc).where(AiTenantEntitySalAlc.id == tenant_id)
            res = await s.execute(stmt)
            await s.commit()
            return bool(res.rowcount)

    async def Remove(self, *, tenant_id: int) -> bool:
        """
        Alias for Delete (hard delete).
        """
        return await self.Delete(tenant_id=tenant_id)

    async def Recover(self, *, tenant_id: int) -> bool:
        """
        Undo soft-delete: set deleted = NULL and update updated.
        Returns True if a row was affected.
        """
        async with self._session() as s:
            stmt = (
                sa_update(AiTenantEntitySalAlc)
                .where(
                    AiTenantEntitySalAlc.id == tenant_id,
                    AiTenantEntitySalAlc.deleted.is_not(None),
                )
                .values(deleted=None, updated=func.now())
            )
            res = await s.execute(stmt)
            await s.commit()
            return bool(res.rowcount)

    async def Restore(self, *, tenant_id: int) -> bool:
        """
        Alias for Recover.
        """
        return await self.Recover(tenant_id=tenant_id)

    # ------------------------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------------------------

    async def FindOneById(self, tenant_id: int, *, include_deleted: bool = False) -> Optional[AiTenantEntitySalAlc]:
        """
        Load a single tenant by id.
        """
        async with self._session() as s:
            conds = [AiTenantEntitySalAlc.id == tenant_id]
            if not include_deleted:
                conds.append(AiTenantEntitySalAlc.deleted.is_(None))
            q = select(AiTenantEntitySalAlc).where(*conds)
            row = (await s.execute(q)).scalar_one_or_none()
            return row

    async def Find(
        self,
        *,
        name_like: Optional[str] = None,
        include_deleted: bool = False,
        order: str = "-created",  # "created" | "-created" | "updated" | "-updated"
        limit: int = 50,
        offset: int = 0,
    ) -> List[AiTenantEntitySalAlc]:
        """
        Flexible list query with filtering, sorting, and pagination.
        """
        async with self._session() as s:
            conds = []
            if not include_deleted:
                conds.append(AiTenantEntitySalAlc.deleted.is_(None))
            if name_like:
                conds.append(AiTenantEntitySalAlc.name.ilike(f"%{name_like}%"))

            q = select(AiTenantEntitySalAlc).where(*conds)

            # ordering
            if order in ("created", "+created"):
                q = q.order_by(asc(AiTenantEntitySalAlc.created))
            elif order in ("-created", "created_desc"):
                q = q.order_by(desc(AiTenantEntitySalAlc.created))
            elif order in ("updated", "+updated"):
                q = q.order_by(asc(AiTenantEntitySalAlc.updated.nulls_last()))
            elif order in ("-updated", "updated_desc"):
                q = q.order_by(desc(AiTenantEntitySalAlc.updated.nulls_last()))
            else:
                q = q.order_by(desc(AiTenantEntitySalAlc.created))

            if offset:
                q = q.offset(offset)
            if limit:
                q = q.limit(limit)

            rows = await s.execute(q)
            return list(rows.scalars().all())