#!/usr/bin/env python
"""Seed database with initial development data"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta, timezone

from src.database.database import SessionLocal, create_tables
from src.database.models import ClickEvent, Link

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utc(days_ago: int = 0, hours_ago: int = 0) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=days_ago, hours=hours_ago)


# ---------------------------------------------------------------------------
# Seed definitions
# ---------------------------------------------------------------------------

LINKS = [
    # Custom short codes — hand-picked slugs
    dict(
        short_code="gh",
        original_url="https://github.com",
        is_active=True,
        is_custom_code=True,
        created_at=_utc(days_ago=30),
        updated_at=_utc(days_ago=30),
    ),
    dict(
        short_code="docs",
        original_url="https://docs.python.org/3/",
        is_active=True,
        is_custom_code=True,
        created_at=_utc(days_ago=25),
        updated_at=_utc(days_ago=25),
    ),
    dict(
        short_code="yt",
        original_url="https://www.youtube.com",
        is_active=True,
        is_custom_code=True,
        created_at=_utc(days_ago=20),
        updated_at=_utc(days_ago=20),
    ),
    dict(
        short_code="so",
        original_url="https://stackoverflow.com/questions",
        is_active=True,
        is_custom_code=True,
        created_at=_utc(days_ago=18),
        updated_at=_utc(days_ago=18),
    ),
    dict(
        short_code="sa-promo",
        original_url="https://www.amazon.com/deals/storefront?tag=example-20",
        is_active=True,
        is_custom_code=True,
        created_at=_utc(days_ago=10),
        updated_at=_utc(days_ago=10),
    ),
    # Auto-generated short codes — random-looking slugs
    dict(
        short_code="x7q2p",
        original_url="https://www.bbc.com/news/technology/article/2026-ai-breakthrough",
        is_active=True,
        is_custom_code=False,
        created_at=_utc(days_ago=15),
        updated_at=_utc(days_ago=15),
    ),
    dict(
        short_code="m3nkR",
        original_url="https://medium.com/@dev/building-a-url-shortener-with-fastapi-abc123",
        is_active=True,
        is_custom_code=False,
        created_at=_utc(days_ago=12),
        updated_at=_utc(days_ago=12),
    ),
    dict(
        short_code="Zp9wL",
        original_url="https://www.npmjs.com/package/zod",
        is_active=True,
        is_custom_code=False,
        created_at=_utc(days_ago=8),
        updated_at=_utc(days_ago=8),
    ),
    dict(
        short_code="t4Rqx",
        original_url="https://docs.sqlalchemy.org/en/20/orm/quickstart.html",
        is_active=True,
        is_custom_code=False,
        created_at=_utc(days_ago=5),
        updated_at=_utc(days_ago=5),
    ),
    dict(
        short_code="Kw2vN",
        original_url="https://hub.docker.com/_/postgres",
        is_active=True,
        is_custom_code=False,
        created_at=_utc(days_ago=3),
        updated_at=_utc(days_ago=3),
    ),
    # Inactive link — disabled but preserved for analytics history
    dict(
        short_code="old-sale",
        original_url="https://www.example.com/promo/blackfriday-2024",
        is_active=False,
        is_custom_code=True,
        created_at=_utc(days_ago=90),
        updated_at=_utc(days_ago=60),
    ),
    dict(
        short_code="qX5mY",
        original_url="https://pastebin.com/raw/deprecated-snippet",
        is_active=False,
        is_custom_code=False,
        created_at=_utc(days_ago=45),
        updated_at=_utc(days_ago=20),
    ),
]

# click_events: list of (short_code, hours_ago, ip, user_agent)
CLICK_EVENTS = [
    # gh — popular link, many clicks
    ("gh", 1,   "203.0.113.42",  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"),
    ("gh", 3,   "198.51.100.7",  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15"),
    ("gh", 6,   "192.0.2.88",    "Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0"),
    ("gh", 12,  "2001:db8::1",   "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"),
    ("gh", 18,  "203.0.113.5",   "curl/8.4.0"),
    ("gh", 24,  "198.51.100.22", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"),
    ("gh", 30,  "192.0.2.10",    "python-httpx/0.26.0"),
    # docs
    ("docs", 2,  "203.0.113.99", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"),
    ("docs", 8,  "198.51.100.3", "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0"),
    ("docs", 20, "192.0.2.55",   "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0"),
    # yt
    ("yt", 1,  "203.0.113.17",   "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"),
    ("yt", 4,  "198.51.100.44",  "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.144 Mobile Safari/537.36"),
    ("yt", 10, "192.0.2.200",    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"),
    # sa-promo — marketing campaign, burst of clicks
    ("sa-promo", 1,  "203.0.113.50",  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"),
    ("sa-promo", 1,  "198.51.100.71", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15"),
    ("sa-promo", 2,  "192.0.2.130",   "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"),
    ("sa-promo", 2,  "203.0.113.88",  "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.144 Mobile Safari/537.36"),
    ("sa-promo", 3,  "198.51.100.9",  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"),
    # x7q2p — news article
    ("x7q2p", 5,  "192.0.2.77",   "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"),
    ("x7q2p", 14, "203.0.113.33", "Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0"),
    # m3nkR — blog post
    ("m3nkR", 7,  "198.51.100.60", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"),
    # Zp9wL — npm page
    ("Zp9wL", 2,  "192.0.2.44",   "curl/8.4.0"),
    ("Zp9wL", 9,  "203.0.113.21", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"),
    # old-sale — inactive link still has historical click data
    ("old-sale", 80 * 24, "198.51.100.15", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"),
    ("old-sale", 85 * 24, "192.0.2.66",   "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15"),
    # Click with null IP and user-agent (privacy-scrubbed / proxy)
    ("t4Rqx", 1,  None, None),
]


# ---------------------------------------------------------------------------
# Seeding logic
# ---------------------------------------------------------------------------

def seed() -> None:
    create_tables()
    db = SessionLocal()
    try:
        # --- Links ---
        link_map: dict[str, Link] = {}
        for data in LINKS:
            existing = db.query(Link).filter_by(short_code=data["short_code"]).first()
            if existing:
                print(f"  skip existing link: {data['short_code']!r}")
                link_map[data["short_code"]] = existing
                continue
            link = Link(**data)
            db.add(link)
            db.flush()  # populate link.id before inserting click_events
            link_map[data["short_code"]] = link
            print(f"  + link: {data['short_code']!r} → {data['original_url'][:60]}")

        # --- ClickEvents ---
        for short_code, hours_ago, ip, ua in CLICK_EVENTS:
            link = link_map.get(short_code)
            if link is None:
                print(f"  skip click for unknown code: {short_code!r}")
                continue
            event = ClickEvent(
                link_id=link.id,
                clicked_at=_utc(hours_ago=hours_ago),
                ip_address=ip,
                user_agent=ua,
            )
            db.add(event)

        db.commit()
        total_links = len([l for l in LINKS])
        total_clicks = len(CLICK_EVENTS)
        print(f"\n✅ Database seeded successfully! ({total_links} links, {total_clicks} click events)")
    except Exception as e:
        db.rollback()
        print(f"❌ Seeding failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
