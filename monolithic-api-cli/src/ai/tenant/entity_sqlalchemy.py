from typing import Optional
from datetime import datetime
import sqlalchemy as sa
from sqlalchemy import Index, Integer, String, text, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from libs.crud.entity_sqlmodel import Entity, EntityPrefixHandler, col_prefix, prefix_to_any_index
from libs.crud.protocol import InIndexPrefix

class AiTenantEntitySalAlc(EntityPrefixHandler, Entity):
    # set defaults for entity
    __entity_tablename__ = 'ai_tenant'
    __column_prefix__ = "tnt_"

    # wcp - with column prefix in name _acp("field")
    _wcp = staticmethod(lambda f, _cp=__column_prefix__: col_prefix(_cp, f))

    # wip - with index prefix in name _aip("in", "field", "col_") or _aip("in", "field") or _aip("in", "field", "") column prefix is optional
    _wip = staticmethod(lambda ip, f, _cp=__column_prefix__: prefix_to_any_index(ip, f, _cp))

    __table_args__ = (
        # primary
        # PrimaryKeyConstraint("id", name="pk_tenant"),

        # indexes
        Index(_wip(InIndexPrefix, 'created'), _wcp('created')),
        Index(_wip(InIndexPrefix, 'updated'), _wcp('updated')),
        Index(_wip(InIndexPrefix, 'deleted'), _wcp('deleted')),
        # Index("in_tenant_active_name", "name", postgresql_where=text("deleted IS NULL")),
        # Index("in_tenant_name_ci", func.lower(text("name"))),

        # unique
        # UniqueConstraint("name", name="un_tenant_name"),  # single column unique constraint
        # UniqueConstraint("id", "email", name="un_user_tenant_email"), # multi column unique constraint
        
        # check constraint
        # CheckConstraint("(deleted IS NULL) OR (deleted >= created)", name="ck_deleted_after_created"),

        # foreign key constraint
        # ForeignKeyConstraint(
        #     ["owner_id"], ["app_user.id"],
        #     name="fk_tenant_owner",
        #     ondelete="SET NULL",
        #     onupdate="CASCADE",
        # ),

        # Table options (dict must be last)
        {
            "schema": "public",
            "comment": "Represents a tenant (organization or account) in the AI platform. Each tenant has its own models, policies, and projects.",
            # "info": {"any":"metadata"},
            # "extend_existing": True,
            # "implicit_returning": False,
            # "prefixes": ["TEMPORARY"], # for CREATE TABLE query prefixes
            # PostgreSQL
            # "postgresql_with": {"fillfactor": 80},
            "postgresql_tablespace": "fastspace",
            # "postgresql_partition_by": "RANGE (created)",
            # "postgresql_on_commit": "PRESERVE ROWS",
            # "postgresql_include": ["col_a", "col_b"], # for INCLUDE columns on unique indexes
            # MySQL
            # "mysql_engine": "InnoDB",
            # "mysql_charset": "utf8mb4",
            # "mysql_collate": "utf8mb4_general_ci",
            # "mysql_row_format": "DYNAMIC"
            # "mysql_partition_by": "RANGE COLUMNS(created)"
            # "mysql_comment": "..."
            # SQLite
            # "sqlite_autoincrement": True,
        },
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        name=_wcp('id'),
        comment="Primary key. Auto-incrementing unique identifier for the tenant.",
        nullable=False,
        doc="Primary key. Auto-incrementing unique identifier for the tenant."
    )

    name: Mapped[str] = mapped_column(
        String(255),
        name=_wcp('name'),
        nullable=False,
        comment="Tenant name (e.g., company or organization name). Must be unique and descriptive.",
    )

    created: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        name=_wcp('created'),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
        comment="Timestamp of tenant creation. Defaults to CURRENT_TIMESTAMP.",
    )

    updated: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True),
        name=_wcp('updated'),
        nullable=True,
        onupdate=sa.func.now(),
        comment="Timestamp of the last tenant update (nullable).",
    )

    deleted: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True),
        name=_wcp('deleted'),
        nullable=True,
        comment="Timestamp when tenant was soft-deleted (nullable). If NULL, tenant is active.",
    )
