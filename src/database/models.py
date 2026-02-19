"""
SQLAlchemy ORM models for the URL Shortener application.

Tables:
    links        — Short link records (short_code → original_url)
    click_events — Per-click analytics records (ip, user_agent, timestamp)
"""

import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class Link(Base):
    """
    Represents a shortened URL.

    Columns:
        id             — UUID primary key.
        short_code     — The unique code appended to the base URL (e.g. ``abc123``).
                         3–32 characters: alphanumeric, hyphens, underscores.
        original_url   — The full destination URL.
        is_active      — When False the redirect returns 404 without deleting data.
        is_custom_code — True when the caller explicitly chose the short_code.
        created_at     — Row creation timestamp (UTC, server-set).
        updated_at     — Last modification timestamp (UTC, server-set, auto-updated).
    """

    __tablename__ = "links"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    short_code = Column(
        String(32),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique slug used in the short URL path",
    )
    original_url = Column(
        Text,
        nullable=False,
        comment="Full destination URL including scheme and query string",
    )
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        comment="Soft-disable: False causes redirects to return 404",
    )
    is_custom_code = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="True when the caller explicitly chose the short_code",
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="UTC timestamp of record creation",
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="UTC timestamp of last modification",
    )

    # Relationships
    click_events = relationship(
        "ClickEvent",
        back_populates="link",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # Composite indexes
    __table_args__ = (
        Index("ix_links_is_active_created_at", "is_active", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Link code={self.short_code!r} active={self.is_active}>"


class ClickEvent(Base):
    """
    Records a single redirect (click) on a short link.

    Columns:
        id         — UUID primary key.
        link_id    — FK → links.id (cascades on delete).
        clicked_at — UTC timestamp of the redirect request (server-set).
        ip_address — Client IP address; supports IPv4 and IPv6 (max 45 chars).
        user_agent — Raw ``User-Agent`` header value from the redirect request.
    """

    __tablename__ = "click_events"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    link_id = Column(
        UUID(as_uuid=True),
        ForeignKey("links.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="FK to the short link that was clicked",
    )
    clicked_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="UTC timestamp of the redirect request",
    )
    ip_address = Column(
        String(45),
        nullable=True,
        comment="Client IP (IPv4 max 15 chars, IPv6 max 45 chars)",
    )
    user_agent = Column(
        Text,
        nullable=True,
        comment="Raw User-Agent header from the redirect request",
    )

    # Relationships
    link = relationship("Link", back_populates="click_events")

    # Composite index for analytics queries: all clicks for a link ordered by time
    __table_args__ = (
        Index("ix_click_events_link_id_clicked_at", "link_id", "clicked_at"),
    )

    def __repr__(self) -> str:
        return f"<ClickEvent link_id={self.link_id} at={self.clicked_at}>"
