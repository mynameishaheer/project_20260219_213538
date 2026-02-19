# Database Schema — URL Shortener

**Database:** PostgreSQL (SQLite supported for local development via `DATABASE_URL`)
**ORM:** SQLAlchemy (Declarative)
**Last updated:** 2026-02-19

---

## Tables

### `links`

Stores every short URL record.

| Column          | Type                        | Nullable | Default        | Description |
|-----------------|-----------------------------|----------|----------------|-------------|
| `id`            | `UUID`                      | NO       | `gen_random_uuid()` | Primary key |
| `short_code`    | `VARCHAR(32)`               | NO       | —              | Unique slug used in the short URL path (3–32 chars: `[A-Za-z0-9_-]`) |
| `original_url`  | `TEXT`                      | NO       | —              | Full destination URL including scheme and query string |
| `is_active`     | `BOOLEAN`                   | NO       | `TRUE`         | Soft-disable: `FALSE` causes redirects to return 404 without deleting data |
| `is_custom_code`| `BOOLEAN`                   | NO       | `FALSE`        | `TRUE` when the caller explicitly chose the short_code |
| `created_at`    | `TIMESTAMP WITH TIME ZONE`  | NO       | `NOW()`        | UTC timestamp of record creation |
| `updated_at`    | `TIMESTAMP WITH TIME ZONE`  | NO       | `NOW()`        | UTC timestamp of last modification (auto-updated) |

**Constraints:**
- `PK` on `id`
- `UNIQUE` on `short_code`

---

### `click_events`

Records one row per redirect (click) on a short link.

| Column       | Type                        | Nullable | Default   | Description |
|--------------|-----------------------------|----------|-----------|-------------|
| `id`         | `UUID`                      | NO       | `gen_random_uuid()` | Primary key |
| `link_id`    | `UUID`                      | NO       | —         | FK → `links.id` (CASCADE DELETE) |
| `clicked_at` | `TIMESTAMP WITH TIME ZONE`  | NO       | `NOW()`   | UTC timestamp of the redirect request |
| `ip_address` | `VARCHAR(45)`               | YES      | `NULL`    | Client IP; 45 chars covers full IPv6 notation |
| `user_agent` | `TEXT`                      | YES      | `NULL`    | Raw `User-Agent` header from the redirect request |

**Constraints:**
- `PK` on `id`
- `FK` on `link_id` → `links.id` with `ON DELETE CASCADE`

---

## Relationships (ERD)

```
links
 ├── id            (PK)
 ├── short_code    (UNIQUE)
 ├── original_url
 ├── is_active
 ├── is_custom_code
 ├── created_at
 └── updated_at
       │
       │  1 ──── N
       ▼
click_events
 ├── id            (PK)
 ├── link_id       (FK → links.id, CASCADE DELETE)
 ├── clicked_at
 ├── ip_address
 └── user_agent
```

- One `Link` has zero or more `ClickEvent` records.
- Deleting a `Link` cascades and removes all associated `ClickEvent` rows (satisfies US-04).

---

## Indexes

| Index name                              | Table          | Columns                    | Purpose |
|-----------------------------------------|----------------|----------------------------|---------|
| `ix_links_short_code`                   | `links`        | `short_code`               | O(log n) lookup on every redirect request — the hottest read path |
| `ix_links_is_active_created_at`         | `links`        | `is_active`, `created_at`  | Paginated "list active links" queries (US-06) |
| `ix_click_events_link_id`               | `click_events` | `link_id`                  | FK index; speeds up joins and cascade deletes |
| `ix_click_events_clicked_at`            | `click_events` | `clicked_at`               | Time-range analytics queries |
| `ix_click_events_link_id_clicked_at`    | `click_events` | `link_id`, `clicked_at`    | Composite: analytics for a single link ordered by time (US-03) |

---

## Key Design Decisions

### UUID primary keys
All tables use UUID PKs (`uuid4`) instead of sequential integers to:
- avoid enumeration attacks on the short-code namespace,
- allow distributed generation without a central sequence, and
- keep IDs opaque in API responses.

### Soft-delete via `is_active`
Setting `is_active = FALSE` deactivates a link without purging analytics history (Maya's use case, US-06). Hard deletion via `DELETE /api/links/{code}` removes the row and cascades to `click_events`.

### `updated_at` auto-update
SQLAlchemy's `onupdate=func.now()` keeps `updated_at` current on every ORM `UPDATE`. For raw SQL patches, add a trigger:

```sql
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_links_updated_at
BEFORE UPDATE ON links
FOR EACH ROW EXECUTE FUNCTION set_updated_at();
```

### IPv6-safe `ip_address`
`VARCHAR(45)` covers the longest possible IPv6 address in full notation (`xxxx:xxxx:xxxx:xxxx:xxxx:xxxx:xxxx:xxxx` = 39 chars) plus the IPv4-mapped form (`::ffff:192.168.100.228` = 22 chars, max 45).

### SQLite compatibility
The `DATABASE_URL` environment variable selects the backend.
- Development: `sqlite:///./app.db` (default)
- Production: `postgresql+psycopg2://user:pass@host/dbname`

SQLite uses `VARCHAR` / `DATETIME` fallbacks for UUID and timezone-aware timestamp columns respectively. `PRAGMA foreign_keys=ON` and `PRAGMA journal_mode=WAL` are applied automatically via a SQLAlchemy connect event.

---

## Migration Strategy

For production deployments, manage schema changes with **Alembic**:

```bash
# Initialise (one-time)
alembic init alembic

# Generate a migration from model changes
alembic revision --autogenerate -m "initial schema"

# Apply
alembic upgrade head
```

`create_tables()` in `database.py` is provided for test environments and initial bootstrapping only.
