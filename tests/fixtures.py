"""
Pytest fixtures for the URL Shortener test suite.

Usage in any test file::

    from tests.fixtures import test_db, seeded_db, sample_link, sample_click_event

Or add ``conftest.py`` that imports these fixtures so pytest auto-discovers them::

    # tests/conftest.py
    from tests.fixtures import *  # noqa: F401,F403
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from src.database.models import Base, ClickEvent, Link


# ---------------------------------------------------------------------------
# Engine / session fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def test_db() -> Session:
    """
    Provide an in-memory SQLite session for a single test function.

    * Creates all tables before yielding the session.
    * Rolls back any uncommitted changes and drops all tables after the test
      to guarantee full isolation between tests.

    Yields:
        A bound SQLAlchemy ``Session`` backed by an in-memory SQLite database.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    # Enable FK enforcement on SQLite (mirrors production behaviour)
    @event.listens_for(engine, "connect")
    def _fk_pragma(dbapi_conn, _record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db: Session = SessionLocal()

    yield db

    db.close()
    Base.metadata.drop_all(engine)
    engine.dispose()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _utc(days_ago: int = 0, hours_ago: int = 0) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=days_ago, hours=hours_ago)


# ---------------------------------------------------------------------------
# Individual model fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_link(test_db: Session) -> Link:
    """
    Insert and return a single active, auto-code ``Link``.

    The link points to ``https://example.com`` with the short code ``abc123``.
    """
    link = Link(
        id=uuid.uuid4(),
        short_code="abc123",
        original_url="https://example.com",
        is_active=True,
        is_custom_code=False,
        created_at=_utc(days_ago=7),
        updated_at=_utc(days_ago=7),
    )
    test_db.add(link)
    test_db.commit()
    test_db.refresh(link)
    return link


@pytest.fixture
def custom_link(test_db: Session) -> Link:
    """
    Insert and return an active ``Link`` with a human-chosen short code.

    Short code: ``gh``  →  ``https://github.com``
    """
    link = Link(
        id=uuid.uuid4(),
        short_code="gh",
        original_url="https://github.com",
        is_active=True,
        is_custom_code=True,
        created_at=_utc(days_ago=30),
        updated_at=_utc(days_ago=30),
    )
    test_db.add(link)
    test_db.commit()
    test_db.refresh(link)
    return link


@pytest.fixture
def inactive_link(test_db: Session) -> Link:
    """
    Insert and return a soft-disabled ``Link`` (``is_active=False``).

    Useful for testing that disabled links return 404 on redirect.
    """
    link = Link(
        id=uuid.uuid4(),
        short_code="old-sale",
        original_url="https://www.example.com/promo/blackfriday-2024",
        is_active=False,
        is_custom_code=True,
        created_at=_utc(days_ago=90),
        updated_at=_utc(days_ago=60),
    )
    test_db.add(link)
    test_db.commit()
    test_db.refresh(link)
    return link


@pytest.fixture
def sample_click_event(test_db: Session, sample_link: Link) -> ClickEvent:
    """
    Insert and return a ``ClickEvent`` associated with ``sample_link``.

    Uses a typical desktop Chrome user-agent and a documentation IPv4 address.
    """
    event_ = ClickEvent(
        id=uuid.uuid4(),
        link_id=sample_link.id,
        clicked_at=_utc(hours_ago=2),
        ip_address="203.0.113.42",
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0.0.0 Safari/537.36"
        ),
    )
    test_db.add(event_)
    test_db.commit()
    test_db.refresh(event_)
    return event_


@pytest.fixture
def anonymous_click_event(test_db: Session, sample_link: Link) -> ClickEvent:
    """
    Insert and return a privacy-scrubbed ``ClickEvent`` with null IP and user-agent.

    Models traffic coming through a privacy proxy or from clients that opted out
    of analytics.
    """
    event_ = ClickEvent(
        id=uuid.uuid4(),
        link_id=sample_link.id,
        clicked_at=_utc(hours_ago=1),
        ip_address=None,
        user_agent=None,
    )
    test_db.add(event_)
    test_db.commit()
    test_db.refresh(event_)
    return event_


# ---------------------------------------------------------------------------
# Fully-seeded database fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def seeded_db(test_db: Session) -> Session:
    """
    Populate the in-memory database with a representative set of links and
    click events, then return the same session.

    Schema
    ------
    Links (12 total):
        - 5 custom-code active links  (gh, docs, yt, so, sa-promo)
        - 5 auto-code active links    (x7q2p, m3nkR, Zp9wL, t4Rqx, Kw2vN)
        - 2 inactive links            (old-sale, qX5mY)

    Click events (27 total):
        - Spread across 10 of the 12 links
        - Variety of user-agents: desktop Chrome/Firefox/Safari, mobile iOS/Android, curl, httpx
        - IPv4, IPv6, and null (privacy-scrubbed) addresses

    Returns:
        The seeded ``Session`` (same object as ``test_db``).
    """
    # --- Links ---
    links_data = [
        # custom, active
        dict(short_code="gh",       original_url="https://github.com",                                            is_active=True,  is_custom_code=True,  created_at=_utc(30), updated_at=_utc(30)),
        dict(short_code="docs",     original_url="https://docs.python.org/3/",                                    is_active=True,  is_custom_code=True,  created_at=_utc(25), updated_at=_utc(25)),
        dict(short_code="yt",       original_url="https://www.youtube.com",                                       is_active=True,  is_custom_code=True,  created_at=_utc(20), updated_at=_utc(20)),
        dict(short_code="so",       original_url="https://stackoverflow.com/questions",                          is_active=True,  is_custom_code=True,  created_at=_utc(18), updated_at=_utc(18)),
        dict(short_code="sa-promo", original_url="https://www.amazon.com/deals/storefront?tag=example-20",       is_active=True,  is_custom_code=True,  created_at=_utc(10), updated_at=_utc(10)),
        # auto, active
        dict(short_code="x7q2p",   original_url="https://www.bbc.com/news/technology/article/2026-ai",           is_active=True,  is_custom_code=False, created_at=_utc(15), updated_at=_utc(15)),
        dict(short_code="m3nkR",   original_url="https://medium.com/@dev/building-a-url-shortener",              is_active=True,  is_custom_code=False, created_at=_utc(12), updated_at=_utc(12)),
        dict(short_code="Zp9wL",   original_url="https://www.npmjs.com/package/zod",                             is_active=True,  is_custom_code=False, created_at=_utc(8),  updated_at=_utc(8)),
        dict(short_code="t4Rqx",   original_url="https://docs.sqlalchemy.org/en/20/orm/quickstart.html",         is_active=True,  is_custom_code=False, created_at=_utc(5),  updated_at=_utc(5)),
        dict(short_code="Kw2vN",   original_url="https://hub.docker.com/_/postgres",                             is_active=True,  is_custom_code=False, created_at=_utc(3),  updated_at=_utc(3)),
        # inactive
        dict(short_code="old-sale",original_url="https://www.example.com/promo/blackfriday-2024",                is_active=False, is_custom_code=True,  created_at=_utc(90), updated_at=_utc(60)),
        dict(short_code="qX5mY",   original_url="https://pastebin.com/raw/deprecated-snippet",                   is_active=False, is_custom_code=False, created_at=_utc(45), updated_at=_utc(20)),
    ]

    link_map: dict[str, Link] = {}
    for data in links_data:
        link = Link(id=uuid.uuid4(), **data)
        test_db.add(link)
        test_db.flush()
        link_map[data["short_code"]] = link

    # --- Click events: (short_code, hours_ago, ip, user_agent) ---
    _UA_CHROME_WIN = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    _UA_SAFARI_MAC = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15"
    _UA_FIREFOX    = "Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0"
    _UA_IOS        = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"
    _UA_ANDROID    = "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.144 Mobile Safari/537.36"
    _UA_CURL       = "curl/8.4.0"
    _UA_HTTPX      = "python-httpx/0.26.0"

    clicks: list[tuple[str, int, str | None, str | None]] = [
        # gh — popular, varied traffic
        ("gh",       1,   "203.0.113.42",  _UA_CHROME_WIN),
        ("gh",       3,   "198.51.100.7",  _UA_SAFARI_MAC),
        ("gh",       6,   "192.0.2.88",    _UA_FIREFOX),
        ("gh",       12,  "2001:db8::1",   _UA_IOS),
        ("gh",       18,  "203.0.113.5",   _UA_CURL),
        ("gh",       24,  "198.51.100.22", _UA_CHROME_WIN),
        ("gh",       30,  "192.0.2.10",    _UA_HTTPX),
        # docs
        ("docs",     2,   "203.0.113.99",  _UA_CHROME_WIN),
        ("docs",     8,   "198.51.100.3",  _UA_FIREFOX),
        ("docs",     20,  "192.0.2.55",    _UA_FIREFOX),
        # yt
        ("yt",       1,   "203.0.113.17",  _UA_IOS),
        ("yt",       4,   "198.51.100.44", _UA_ANDROID),
        ("yt",       10,  "192.0.2.200",   _UA_CHROME_WIN),
        # sa-promo — marketing burst
        ("sa-promo", 1,   "203.0.113.50",  _UA_CHROME_WIN),
        ("sa-promo", 1,   "198.51.100.71", _UA_SAFARI_MAC),
        ("sa-promo", 2,   "192.0.2.130",   _UA_IOS),
        ("sa-promo", 2,   "203.0.113.88",  _UA_ANDROID),
        ("sa-promo", 3,   "198.51.100.9",  _UA_CHROME_WIN),
        # news article
        ("x7q2p",   5,   "192.0.2.77",    _UA_SAFARI_MAC),
        ("x7q2p",   14,  "203.0.113.33",  _UA_FIREFOX),
        # blog post
        ("m3nkR",   7,   "198.51.100.60", _UA_CHROME_WIN),
        # npm
        ("Zp9wL",   2,   "192.0.2.44",    _UA_CURL),
        ("Zp9wL",   9,   "203.0.113.21",  _UA_CHROME_WIN),
        # sqlalchemy docs — anonymous (privacy-scrubbed)
        ("t4Rqx",   1,   None,            None),
        # inactive link historical clicks
        ("old-sale", 80 * 24, "198.51.100.15", _UA_CHROME_WIN),
        ("old-sale", 85 * 24, "192.0.2.66",    _UA_SAFARI_MAC),
        # so — one click
        ("so",       5,   "192.0.2.11",    _UA_FIREFOX),
    ]

    for short_code, hours_ago, ip, ua in clicks:
        link = link_map[short_code]
        test_db.add(ClickEvent(
            id=uuid.uuid4(),
            link_id=link.id,
            clicked_at=_utc(hours_ago=hours_ago),
            ip_address=ip,
            user_agent=ua,
        ))

    test_db.commit()
    return test_db
