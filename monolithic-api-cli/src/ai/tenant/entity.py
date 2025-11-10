from datetime import datetime
from typing import Optional
from pydantic import ConfigDict
from sqlmodel import Field, Column, Index, Integer, text, String, TIMESTAMP, CheckConstraint
from libs.crud.entity_sqlmodel import Entity, col_prefix, prefix_to_any_index
from libs.crud.constant import IN_INDEX_PREFIX

class AiTenantEntity(Entity, table=True):
    __entity_tablename__ = 'ai_tenant'
    __column_prefix__ = "tnt_"

    # validate on creation (default) AND on later attribute assignment
    model_config = ConfigDict(validate_assignment=True)

    # wcp - with column prefix in name _acp("field")
    _wcp = staticmethod(lambda f, _cp=__column_prefix__: col_prefix(_cp, f))

    # wip - with index prefix in name _aip("in", "field", "col_") or _aip("in", "field") or _aip("in", "field", "") column prefix is optional
    _wip = staticmethod(lambda ip, f, _cp=__column_prefix__: prefix_to_any_index(ip, f, _cp))
    
    # The __table_args__ tuple and options dictionary can be included directly in SQLModel
    __table_args__ = (
        # Indexes are defined using the SQLAlchemy Index class
        Index(_wip(IN_INDEX_PREFIX, 'created'), _wcp('created')),
        Index(_wip(IN_INDEX_PREFIX, 'updated'), _wcp('updated')),
        Index(_wip(IN_INDEX_PREFIX, 'deleted'), _wcp('deleted')),
        # Table options as a dictionary
        {
            "schema": "public",
            "comment": "Represents a tenant (organization or account) in the AI platform. Each tenant has its own models, policies, and projects.",
            "postgresql_tablespace": "fastspace",
        },
    )

    # Primary key column. Use Field with default=None to enable autoincrement.
    id: Optional[int] = Field(
        default = None,
        # primary_key = True,
        # The sa_column argument is used to pass a custom SQLAlchemy Column object for advanced options
        sa_column = Column(
            Integer,
            primary_key = True,
            name = _wcp('id'),
            comment = "Primary key. Auto-incrementing unique identifier for the tenant.",
            nullable = False
        ),
        # doc is a Pydantic field option, not a database column attribute
        description = "Primary key. Auto-incrementing unique identifier for the tenant."
    )

    # String column for the tenant name
    name: Optional[str] = Field(
        max_length = 255,
        sa_column = Column(
            String(255),
            name = _wcp('name'),
            nullable = False,
            comment = "Tenant name (e.g., company or organization name). Must be unique and descriptive.",
        )
    )

    # Created timestamp
    created: Optional[datetime] = Field(
        sa_column = Column(
            TIMESTAMP,
            name = _wcp('created'),
            default=datetime.now(),
            server_default=text("CURRENT_TIMESTAMP"),
            nullable = False,
            comment = "Timestamp of tenant creation. Defaults to CURRENT_TIMESTAMP.",
        )
    )

    # Updated timestamp (optional/nullable)
    updated: Optional[datetime] = Field(
        sa_column = Column(
            TIMESTAMP,
            name = _wcp('updated'),
            onupdate = text("CURRENT_TIMESTAMP"),  # Use text for database function
            nullable = True,
            comment = "Timestamp of the last tenant update (nullable).",
        )
    )

    # Deleted timestamp (optional/nullable)
    deleted: Optional[datetime] = Field(
        sa_column = Column(
            TIMESTAMP,
            name = _wcp('deleted'),
            nullable = True,
            comment = "Timestamp when tenant was soft-deleted (nullable). If NULL, tenant is active.",
        )
    )