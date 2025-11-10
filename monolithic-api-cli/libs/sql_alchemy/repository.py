from typing import Any, Dict, Generic, Iterable, List, Mapping, Optional, Sequence, Tuple, Type, TypeVar

from .protocol import DtoT, EntityT
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from libs.sql_alchemy.service import SqlAlchemyService

class SqlAlchemyRepository(Generic[EntityT, DtoT]):
    """Generic repository offering basic CRUD helpers for SQLAlchemy entities."""

    entity_cls: Optional[Type[EntityT]] = None
    dto_cls: Optional[Type[DtoT]] = None
    pk_field: str = "id"
    allow_pk_on_create: bool = False

    def __init__(
        self,
        db: SqlAlchemyService,
        *,
        entity_cls: Optional[Type[EntityT]] = None,
        dto_cls: Optional[Type[DtoT]] = None,
        pk_field: Optional[str] = None,
    ) -> None:
        self.db = db
        if entity_cls is not None:
            self.entity_cls = entity_cls
        if dto_cls is not None:
            self.dto_cls = dto_cls
        if pk_field is not None:
            self.pk_field = pk_field

        if self.entity_cls is None or self.dto_cls is None:
            raise ValueError("SqlAlchemyRepository requires both entity_cls and dto_cls to be configured.")

    async def add(self, data: DtoT | Mapping[str, Any] | EntityT) -> DtoT:
        payload = self._prepare_payload(data, allow_pk=self.allow_pk_on_create)
        entity = self.entity_cls(**payload)  # type: ignore[misc]

        async with self.db.transaction() as session:
            session.add(entity)
            await session.flush()
            await session.refresh(entity)

        return self._to_dto(entity)

    async def edit(self, record_id: Any, data: DtoT | Mapping[str, Any] | EntityT) -> Optional[DtoT]:
        payload = self._prepare_payload(data, allow_pk=False)
        if not payload:
            return await self._load_dto_by_id(record_id)

        async with self.db.transaction() as session:
            entity = await self._load_entity(session, record_id)
            if entity is None:
                return None

            for key, value in payload.items():
                setattr(entity, key, value)

            session.add(entity)
            await session.flush()
            await session.refresh(entity)

            return self._to_dto(entity)

    async def delete(self, record_id: Any) -> bool:
        async with self.db.transaction() as session:
            entity = await self._load_entity(session, record_id)
            if entity is None:
                return False

            await session.delete(entity)
            await session.flush()
            return True

    async def search(
        self,
        filters: Optional[Mapping[str, Any]] = None,
        *,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[Sequence[Tuple[str, str]]] = None,
    ) -> List[DtoT]:
        stmt = select(self.entity_cls)

        if filters:
            stmt = self._apply_filters(stmt, filters)

        if order_by:
            stmt = self._apply_order_by(stmt, order_by)

        if limit is not None:
            stmt = stmt.limit(limit)
        if offset:
            stmt = stmt.offset(offset)

        async with self.db.session_ctx() as session:
            result = await session.execute(stmt)
            entities = result.scalars().all()

        return [self._to_dto(entity) for entity in entities]

    def _allowed_fields(self, *, allow_pk: bool) -> Iterable[str]:
        if self.dto_cls is None:
            return []
        allowed = set(getattr(self.dto_cls, "model_fields", {}).keys())
        if not allow_pk and self.pk_field:
            allowed.discard(self.pk_field)
        return allowed

    def _prepare_payload(
        self,
        data: DtoT | Mapping[str, Any] | EntityT,
        *,
        allow_pk: bool,
    ) -> Dict[str, Any]:
        allowed = set(self._allowed_fields(allow_pk=allow_pk))
        if isinstance(data, BaseModel):
            payload = data.model_dump(exclude_unset=True)
        elif isinstance(data, Mapping):
            payload = dict(data)
        else:
            payload = {
                field: getattr(data, field)
                for field in allowed
                if hasattr(data, field)
            }

        return {k: v for k, v in payload.items() if k in allowed}

    def _apply_filters(self, stmt, filters: Mapping[str, Any]):
        for field, value in filters.items():
            attr = getattr(self.entity_cls, field, None)
            if attr is None:
                continue
            if value is None:
                stmt = stmt.where(attr.is_(None))
            elif isinstance(value, (list, tuple, set, frozenset)):
                stmt = stmt.where(attr.in_(list(value)))
            else:
                stmt = stmt.where(attr == value)
        return stmt

    def _apply_order_by(self, stmt, order_by: Sequence[Tuple[str, str]]):
        clauses = []
        for field, direction in order_by:
            attr = getattr(self.entity_cls, field, None)
            if attr is None:
                continue
            direction_value = (direction or "").lower()
            if direction_value in {"desc", "descending", "-1", "-"}:
                clauses.append(attr.desc())
            else:
                clauses.append(attr.asc())
        if clauses:
            stmt = stmt.order_by(*clauses)
        return stmt

    async def _load_entity(self, session: AsyncSession, record_id: Any) -> Optional[EntityT]:
        pk_attr = getattr(self.entity_cls, self.pk_field, None)
        if pk_attr is None:
            raise AttributeError(f"Primary key field '{self.pk_field}' not found on entity '{self.entity_cls}'.")

        stmt = select(self.entity_cls).where(pk_attr == record_id)
        result = await session.execute(stmt)
        return result.scalars().first()

    async def _load_dto_by_id(self, record_id: Any) -> Optional[DtoT]:
        async with self.db.session_ctx() as session:
            entity = await self._load_entity(session, record_id)
            if entity is None:
                return None
            return self._to_dto(entity)

    def _to_dto(self, entity: EntityT) -> DtoT:
        if self.dto_cls is None:
            raise ValueError("dto_cls is not configured.")
        return self.dto_cls.model_validate(entity, from_attributes=True)
