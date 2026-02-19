# Database Migrations

This project uses [Alembic](https://alembic.sqlalchemy.org/) for managing database schema migrations.

## Prerequisites

- Alembic installed (`pip install alembic`)
- `DATABASE_URL` environment variable set (defaults to `sqlite:///./app.db` for local development)

## Running Migrations

Apply all pending migrations to bring the database up to the latest schema:

```bash
./scripts/migrate.sh
# or directly:
alembic upgrade head
```

## Rolling Back

Undo the most recent migration:

```bash
./scripts/rollback.sh
# or directly:
alembic downgrade -1
```

Downgrade to a specific revision:

```bash
alembic downgrade <revision_id>
```

## Creating a New Migration

After modifying models in `src/database/models.py`, auto-generate a migration:

```bash
alembic revision --autogenerate -m "describe_your_change"
```

Review the generated file in `alembic/versions/` before applying it — autogenerate is not 100% complete for all DDL operations (e.g. column type changes may need manual adjustment).

## Migration History

| Revision | Description | Tables |
|----------|-------------|--------|
| `3b527d7be7fb` | initial_schema | `links`, `click_events` |

### `3b527d7be7fb` — initial_schema

Creates the two core tables:

- **`links`** — Shortened URL records (`short_code` → `original_url`)
  - Indexes: `ix_links_short_code` (unique), `ix_links_is_active_created_at` (composite)
- **`click_events`** — Per-click analytics with FK to `links`
  - Indexes: `ix_click_events_link_id`, `ix_click_events_clicked_at`, `ix_click_events_link_id_clicked_at` (composite)

## Configuration

- **`alembic.ini`** — Alembic configuration; sets default `sqlalchemy.url = sqlite:///./app.db`
- **`alembic/env.py`** — Loads `Base.metadata` from `src.database.models`; overrides URL from `DATABASE_URL` env var
- **`alembic/versions/`** — Migration scripts (one file per revision)
