"""
Database package — exports models and session utilities.
"""

from .database import SessionLocal, create_tables, drop_tables, engine, get_db, health_check
from .models import Base, ClickEvent, Link

__all__ = [
    # Models
    "Base",
    "Link",
    "ClickEvent",
    # Engine / session
    "engine",
    "SessionLocal",
    # Helpers
    "get_db",
    "create_tables",
    "drop_tables",
    "health_check",
]
