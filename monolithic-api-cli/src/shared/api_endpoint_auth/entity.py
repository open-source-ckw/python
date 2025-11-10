# src/shared/api_endpoint_auth/entity.py
from typing import TYPE_CHECKING, Optional
from datetime import datetime
import sqlalchemy as sa
from sqlalchemy import DateTime, Identity, Index, CheckConstraint, Integer, String, text, TIMESTAMP, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from libs.crud.constant import IN_INDEX_PREFIX, UN_INDEX_PREFIX
from libs.crud.entity import Entity, col_prefix, prefix_to_any_index, tablename

if TYPE_CHECKING:
    from src.shared.api_endpoint_auth_file.entity import ApiEndpointAuthFileEntity
    
ApiEndpointAuthTable: str = tablename("api_endpoint_auth")
ApiEndpointAuthColPrefix: str = "aepu_"

class ApiEndpointAuthEntity(Entity):
    # table and column prefix
    __tablename__ = ApiEndpointAuthTable
    __col_prefix__ = ApiEndpointAuthColPrefix

    # prefix helper
    _cwp = staticmethod(lambda f, _cp=__col_prefix__: col_prefix(_cp, f))
    _iwp = staticmethod(lambda ip, f, _cp=__col_prefix__: prefix_to_any_index(ip, f, _cp))

    __table_args__ = (
        
        # unique index
        Index(
            _iwp(UN_INDEX_PREFIX, "username"),
            _cwp("username"),
            unique=True,
            postgresql_with={"fillfactor": 100, "deduplicate_items": False},
        ),

        Index(
            _iwp(UN_INDEX_PREFIX, "url_slug"),
            _cwp("url_slug"),
            unique=True,
            postgresql_with={"fillfactor": 100, "deduplicate_items": False},
        ),
        
        # normal index
        Index(
            _iwp(IN_INDEX_PREFIX, "created"), 
            _cwp("created"), 
            postgresql_with={"fillfactor": 100, "deduplicate_items": True}
        ),
        Index(
            _iwp(IN_INDEX_PREFIX, "updated"), 
            _cwp("updated"), 
            postgresql_with={"fillfactor": 100, "deduplicate_items": True}
        ),
        Index(
            _iwp(IN_INDEX_PREFIX, "deleted"), 
            _cwp("deleted"), 
            postgresql_with={"fillfactor": 100, "deduplicate_items": True}
        ),
        Index(
            _iwp(IN_INDEX_PREFIX, "email"), 
            _cwp("email"), 
            postgresql_with={"fillfactor": 100, "deduplicate_items": True}
        ),
        Index(
            _iwp(IN_INDEX_PREFIX, "role_id"), 
            _cwp("role_id"), 
            postgresql_with={"fillfactor": 100, "deduplicate_items": True}
        ),
        Index(
            _iwp(IN_INDEX_PREFIX, "suspended"), 
            _cwp("suspended"), 
            postgresql_with={"fillfactor": 100, "deduplicate_items": True}
        ),

        # check constraint
        # role_id 0..255 like SMALLINT with check
        CheckConstraint(
            f"{_cwp('role_id')} >= 0 AND {_cwp('role_id')} <= 255", 
            name="te_api_endpoint_auth_aepu_role_id_check"
        ),

        # table options
        {
            "schema": "public",
            "comment": "api end point access authentication",
            "postgresql_tablespace": "pg_default",
        },
    )

    id: Mapped[int] = mapped_column(
        Integer,
        name=_cwp('id'),
        primary_key=True,
        autoincrement=True,
        nullable=False,
        comment="Primary key. Auto-incrementing unique identifier of record.",
        info={"extra":""},
    )

    role_id: Mapped[int] = mapped_column(
        Integer,
        name=_cwp("role_id"),
        nullable=False,
        server_default=text("0"),
        comment="User auth role.",
        info={"extra": ""},
    )

    username: Mapped[str] = mapped_column(
        String(128),
        name=_cwp("username"),
        nullable=False,
        comment="Required to gain access to API endpoint.",
        info={"extra":""},
    )

    email: Mapped[str] = mapped_column(
        String(128),
        name=_cwp("email"),
        nullable=False,
        comment="Email address.",
        info={"extra":""},
    )

    identify: Mapped[Optional[str]] = mapped_column(
        Text,
        name=_cwp("identify"),
        default="Hr2wz^BWgaEKPl!ItEesaRP3Z-Ezx+OQhzHSX",
        nullable=False,
        comment="Identity blob/descriptor used to identify the principal.",
        info={"extra":""},
    )

    jwt_access_token: Mapped[Optional[str]] = mapped_column(
        Text,
        name=_cwp("jwt_access_token"),
        nullable=True,
        comment="Last issued access token (optional)",
        info={"extra":""},
    )

    jwt_refresh_token: Mapped[Optional[str]] = mapped_column(
        Text,
        name=_cwp("jwt_refresh_token"),
        nullable=True,
        comment="Last issued refresh token (optional)",
        info={"extra":""},
    )

    url_slug: Mapped[Optional[str]] = mapped_column(
        Text,
        name=_cwp("url_slug"),
        nullable=True,
        comment="URL slug for public profile page.",
        info={"extra":""},
    )

    file_profile_photo: Mapped[Optional[str]] = mapped_column(
        String(255),
        name=_cwp("file_profile_photo"),
        nullable=True,
        comment="Profile photo file name will be saved here",
        info={"extra":""},
    )

    record_position: Mapped[Optional[int]] = mapped_column(
        Integer,
        name=_cwp("record_position"),
        default=0,
        nullable=False,
        comment="Position id of the record in their role group",
        info={"extra":""},
    )

    is_main: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        name=_cwp("is_main"),
        nullable=True,
        comment="null: no | date_time: yes",
        info={"extra":""},
    )

    suspended: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        name=_cwp("suspended"),
        nullable=True,
        comment="null: no | date_time: yes last action at",
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

    fr_api_endpoint_auth_files: Mapped[list["ApiEndpointAuthFileEntity"]] = relationship(
        back_populates="fr_api_endpoint_auth",
        primaryjoin="ApiEndpointAuthEntity.id == ApiEndpointAuthFileEntity.aepu_id",
        foreign_keys="ApiEndpointAuthFileEntity.aepu_id",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
        info={"extra": ""},
    )

    # ████ EXTERNAL RELATIONS ████████████████████████████████████████████████






















