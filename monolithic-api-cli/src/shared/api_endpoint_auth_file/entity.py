# src/shared/api_endpoint_auth_file/entity.py
from datetime import datetime
from typing import TYPE_CHECKING, Optional

import sqlalchemy as sa
from sqlalchemy import BigInteger, DateTime, ForeignKeyConstraint, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from libs.crud.constant import FK_INDEX_PREFIX, IN_INDEX_PREFIX
from libs.crud.entity import Entity, col_prefix, prefix_to_any_index, tablename
from src.shared.api_endpoint_auth.entity import ApiEndpointAuthEntity, ApiEndpointAuthTable

if TYPE_CHECKING:
    from src.shared.api_endpoint_auth.entity import ApiEndpointAuthEntity

ApiEndpointAuthFileTable: str = tablename("api_endpoint_auth_file")
ApiEndpointAuthFileColPrefix: str = "aepuf_"

class ApiEndpointAuthFileEntity(Entity):
    # table and column prefix
    __tablename__ = ApiEndpointAuthFileTable
    __col_prefix__ = ApiEndpointAuthFileColPrefix

    # prefix helper
    _cwp = staticmethod(lambda f, _cp=__col_prefix__: col_prefix(_cp, f))
    _iwp = staticmethod(lambda ip, f, _cp=__col_prefix__: prefix_to_any_index(ip, f, _cp))

    __table_args__ = (
        # normal indexes
        Index(
            _iwp(IN_INDEX_PREFIX, "aepu_id"),
            _cwp("aepu_id"),
            postgresql_with={"fillfactor": 100, "deduplicate_items": True},
            postgresql_using="btree",
            postgresql_tablespace="pg_default",
        ),
        Index(
            _iwp(IN_INDEX_PREFIX, "created"),
            _cwp("created"),
            postgresql_with={"fillfactor": 100, "deduplicate_items": True},
            postgresql_using="btree",
            postgresql_tablespace="pg_default",
        ),
        Index(
            _iwp(IN_INDEX_PREFIX, "updated"),
            _cwp("updated"),
            postgresql_with={"fillfactor": 100, "deduplicate_items": True},
            postgresql_using="btree",
            postgresql_tablespace="pg_default",
        ),
        Index(
            _iwp(IN_INDEX_PREFIX, "deleted"),
            _cwp("deleted"),
            postgresql_with={"fillfactor": 100, "deduplicate_items": True},
            postgresql_using="btree",
            postgresql_tablespace="pg_default",
        ),

        # foreign key constraints
        ForeignKeyConstraint(
            [_cwp("aepu_id")],
            [f"{ApiEndpointAuthTable}.aepu_id"], # use db field name not SQL Alchemy class field name
            name=_iwp(FK_INDEX_PREFIX, "aepu_id"),
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),

        # table options
        {
            "schema": "public",
            "comment": "api endpoint auth file uploads",
            "postgresql_tablespace": "pg_default",
        },
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        name=_cwp('id'),
        primary_key=True,
        autoincrement=True,
        nullable=False,
        comment="Primary key. Auto-incrementing unique identifier of record.",
        info={"extra":""},
    )

    aepu_id: Mapped[int] = mapped_column(
        Integer,
        name=_cwp('aepu_id'),
        nullable=False,
        comment="FK to ApiEndpointAuthEntity.id",
        info={"extra":""},
    )

    file: Mapped[str] = mapped_column(
        String(255),
        name=_cwp('file'),
        nullable=False,
        comment="Stored filename for the uploaded attachment.",
        info={"extra":""},
    )
    
    created: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        name=_cwp("created"),
        default=sa.func.now(),
        server_default=sa.func.now(),
        nullable=False,
        comment="date_time: created at",
        info={"extra":""},
    )

    updated: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        name=_cwp("updated"),
        nullable=True,
        onupdate=sa.func.now(),
        comment="null: no | date_time: yes updated at",
        info={"extra":""},
    )

    deleted: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        name=_cwp("deleted"),
        nullable=True,
        comment="null: no | date_time: yes deleted at",
        info={"extra":""},
    )

    # ████ INTERNAL RELATIONS ████████████████████████████████████████████████

    fr_api_endpoint_auth: Mapped["ApiEndpointAuthEntity"] = relationship(
        back_populates="fr_api_endpoint_auth_files",
        primaryjoin="ApiEndpointAuthFileEntity.aepu_id == ApiEndpointAuthEntity.id",
        foreign_keys="ApiEndpointAuthFileEntity.aepu_id",
        passive_deletes=True,
        lazy="selectin",
        info={"extra": ""},
    )

    # ████ EXTERNAL RELATIONS ████████████████████████████████████████████████
