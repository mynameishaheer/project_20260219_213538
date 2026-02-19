# Product Requirements Document (PRD)
## URL Shortener — FastAPI + SQLite

**Document Version:** 1.0
**Date:** 2026-02-19
**Status:** Draft

---

## Table of Contents

1. [Product Overview](#1-product-overview)
2. [User Personas](#2-user-personas)
3. [User Stories](#3-user-stories)
4. [Feature Requirements](#4-feature-requirements)
5. [Technical Requirements](#5-technical-requirements)
6. [User Interface & Experience](#6-user-interface--experience)
7. [Success Metrics & KPIs](#7-success-metrics--kpis)
8. [Timeline & Milestones](#8-timeline--milestones)
9. [Risks & Mitigation Strategies](#9-risks--mitigation-strategies)
10. [Assumptions & Dependencies](#10-assumptions--dependencies)
11. [Open Questions](#11-open-questions)

---

## 1. Product Overview

### Vision and Mission

**Vision:** To be the simplest, fastest, and most reliable URL shortening service that empowers users to share links with confidence.

**Mission:** Provide a frictionless URL shortening experience backed by transparent analytics, giving individuals and teams full control over the links they share — with no unnecessary complexity.

### Target Audience

- Individual developers and technical users who need quick link shortening via API
- Content creators, marketers, and social media managers who share links frequently
- Small-to-medium businesses that need branded short links and basic analytics
- Internal engineering teams that want a self-hosted, privacy-respecting alternative to commercial services

### Key Value Proposition

- **Instant shortening:** Paste a long URL, get a short one in under a second
- **No black box:** Self-hosted on FastAPI + SQLite — you own the data
- **Click analytics:** Know who is clicking and when, without relying on third parties
- **API-first:** Fully scriptable; integrates into CI/CD pipelines, bots, and automation workflows
- **Zero cost at small scale:** SQLite removes the need for a database server

### Product Goals and Objectives

1. Reduce average long URL character count by ≥ 80% to make links shareable in character-limited contexts (Twitter, SMS)
2. Provide accurate click-through analytics so users can measure link performance
3. Expose a REST API that allows programmatic link creation and management
4. Achieve sub-100 ms response time on redirect for all cached URLs
5. Support custom short codes so brands can maintain identity in shared links

---

## 2. User Personas

### Persona 1 — Alex, the Solo Developer

| Attribute | Detail |
|-----------|--------|
| Age | 28 |
| Role | Freelance full-stack developer |
| Tech comfort | Expert |
| Primary device | macOS laptop + CLI |

**Goals:**
- Automate link creation from scripts and CI pipelines
- Track whether documentation or demo links sent to clients are being visited
- Host a lightweight service without spinning up a dedicated database server

**Pain Points:**
- Commercial shorteners have rate limits or require account creation
- Bitly / TinyURL send data to third parties — clients care about privacy
- Most self-hosted tools require Postgres or MySQL, which is overkill for small projects

**Typical Use Cases:**
- `curl -X POST /shorten` inside a deployment script to generate a short preview URL
- Reviewing the `/analytics/{code}` endpoint in a browser after sending a client a proposal link
- Setting a custom short code like `/d/demo-v2` for a project demo

---

### Persona 2 — Maya, the Content Marketer

| Attribute | Detail |
|-----------|--------|
| Age | 34 |
| Role | Digital marketing manager at a SaaS company |
| Tech comfort | Intermediate |
| Primary device | Windows laptop + Chrome |

**Goals:**
- Shorten affiliate and campaign links before posting to social media
- See which links get the most clicks to prioritize content topics
- Deactivate links from old campaigns that are no longer relevant

**Pain Points:**
- Long URLs break formatting in newsletters and Instagram bios
- Free tiers of commercial shorteners limit history or hide analytics behind paywalls
- No way to deactivate a short link once it has been shared publicly

**Typical Use Cases:**
- Shortening a UTM-tagged landing page URL before scheduling a Twitter post
- Checking the click dashboard weekly to report link performance to the VP of Marketing
- Deleting or disabling a short link when a campaign ends to prevent outdated traffic

---

### Persona 3 — Jordan, the Internal Tools Engineer

| Attribute | Detail |
|-----------|--------|
| Age | 41 |
| Role | Platform engineer at a mid-size e-commerce company |
| Tech comfort | Expert |
| Primary device | Linux workstation + terminal |

**Goals:**
- Deploy a self-hosted URL shortener for internal use so the company controls all redirect data
- Integrate the shortener into Slack bots and internal dashboards
- Ensure the system is observable and easy to maintain without a DBA

**Pain Points:**
- SaaS shorteners are blocked by the company firewall or violate data-residency policies
- Database-heavy self-hosted solutions need dedicated ops care
- Most tools lack a well-documented REST API for bot integration

**Typical Use Cases:**
- Running the FastAPI server on an internal host; integrating `/shorten` with a Slack slash command
- Querying `/api/links` programmatically to audit all active short links company-wide
- Monitoring redirect latency via the health-check endpoint in a Grafana dashboard

---

## 3. User Stories

### Alex (Solo Developer)

#### US-01 — Shorten a URL via API
> As a developer, I want to POST a long URL to an API endpoint and receive a short URL, so that I can automate link creation from scripts and CI pipelines.

**Acceptance Criteria:**
- `POST /api/shorten` accepts `{"url": "<long_url>"}` with `Content-Type: application/json`
- Response returns `{"short_code": "<code>", "short_url": "<base_url>/<code>", "original_url": "<long_url>"}`
- Returns HTTP 422 if the URL is missing or malformed
- Response time ≤ 200 ms for 99th percentile

---

#### US-02 — Custom short code
> As a developer, I want to specify my own short code when shortening a URL, so that the resulting link is memorable and brand-consistent.

**Acceptance Criteria:**
- `POST /api/shorten` accepts optional `"code": "<custom_code>"`
- Short code must be 3–32 alphanumeric characters (hyphens and underscores allowed)
- Returns HTTP 409 if the requested code is already taken
- Auto-generates a code if the `code` field is omitted

---

#### US-03 — View click analytics via API
> As a developer, I want to retrieve click counts and timestamps for a short link via API, so that I can display analytics in my own dashboard.

**Acceptance Criteria:**
- `GET /api/analytics/{code}` returns `{"code": ..., "original_url": ..., "clicks": <int>, "created_at": ..., "click_events": [{"timestamp": ..., "ip": ..., "user_agent": ...}]}`
- Returns HTTP 404 if the code does not exist
- Data reflects all clicks since link creation

---

#### US-04 — Delete a short link via API
> As a developer, I want to DELETE a short link by its code, so that I can clean up expired or incorrect links programmatically.

**Acceptance Criteria:**
- `DELETE /api/links/{code}` removes the link and all associated analytics
- Returns HTTP 204 on success
- Returns HTTP 404 if the code does not exist
- Subsequent redirects to the deleted code return HTTP 404

---

### Maya (Content Marketer)

#### US-05 — Shorten a URL via web form
> As a marketer, I want to paste a URL into a web form and receive a short link, so that I can quickly shorten links without using the command line.

**Acceptance Criteria:**
- Home page (`GET /`) renders a form with a URL input field and a Submit button
- Submitting the form displays the generated short URL inline with a one-click copy button
- Invalid URLs show an inline error message (no full-page reload required)
- Works on mobile screen widths ≥ 375 px

---

#### US-06 — View all my links
> As a marketer, I want to see a list of all short links I have created with their click counts, so that I can monitor link performance at a glance.

**Acceptance Criteria:**
- `GET /dashboard` renders a table with columns: Short Code, Original URL (truncated), Created At, Click Count
- Links are sortable by Created At and Click Count
- Pagination supports pages of 20 rows with next/previous navigation

---

#### US-07 — Disable a short link
> As a marketer, I want to deactivate a short link without deleting it, so that I can stop old campaign links from redirecting while preserving analytics history.

**Acceptance Criteria:**
- Dashboard provides a toggle or Disable button per link
- Disabled links return HTTP 410 Gone on redirect
- Analytics for disabled links remain accessible via the analytics endpoint
- Link status (active/disabled) is visible in the dashboard table

---

#### US-08 — Copy short URL to clipboard
> As a marketer, I want to click a single button to copy the short URL, so that I can paste it into social media without manually selecting text.

**Acceptance Criteria:**
- A "Copy" button appears next to each generated short URL on the result view and dashboard
- Clicking it copies the full short URL to the system clipboard
- Button label changes to "Copied!" for 2 seconds as confirmation feedback

---

### Jordan (Internal Tools Engineer)

#### US-09 — Health check endpoint
> As a platform engineer, I want a `/health` endpoint that confirms the service and database are reachable, so that I can wire it into load-balancer and uptime checks.

**Acceptance Criteria:**
- `GET /health` returns `{"status": "ok", "db": "ok"}` with HTTP 200 when healthy
- Returns `{"status": "error", "db": "unreachable"}` with HTTP 503 when the SQLite file cannot be accessed
- Response time ≤ 50 ms

---

#### US-10 — List all links via API
> As a platform engineer, I want to GET a paginated list of all short links via API, so that I can audit active links and integrate with internal tooling.

**Acceptance Criteria:**
- `GET /api/links?page=1&limit=50` returns an array of link objects with fields: `code`, `original_url`, `created_at`, `clicks`, `is_active`
- Supports `?is_active=true|false` filter query parameter
- Returns HTTP 200 with an empty array (not 404) when no links exist

---

#### US-11 — Redirect to original URL
> As any user clicking a short link, I want to be redirected to the original URL immediately, so that I reach the intended destination without friction.

**Acceptance Criteria:**
- `GET /<code>` returns HTTP 302 redirect to the original URL
- Redirect occurs in ≤ 100 ms for links already in the SQLite in-memory cache
- Each redirect increments the click counter and logs timestamp, IP, and User-Agent
- Inactive or non-existent codes return HTTP 404 or 410 as appropriate

---

#### US-12 — API documentation
> As a developer integrating the service, I want auto-generated interactive API documentation, so that I can explore endpoints and test requests without reading source code.

**Acceptance Criteria:**
- `GET /docs` serves Swagger UI (FastAPI default) listing all endpoints
- `GET /redoc` serves ReDoc documentation
- All endpoints include descriptions, request/response schemas, and example payloads

---

#### US-13 — Rate limiting on shorten endpoint
> As a platform engineer, I want rate limiting on the shorten endpoint, so that the service cannot be abused to flood the database with millions of links.

**Acceptance Criteria:**
- Default limit: 60 requests per minute per IP on `POST /api/shorten`
- Returns HTTP 429 with a `Retry-After` header when limit is exceeded
- Limit is configurable via an environment variable

---

#### US-14 — Link expiry
> As any user, I want to optionally set an expiry date on a short link, so that it automatically stops redirecting after a campaign or event ends.

**Acceptance Criteria:**
- `POST /api/shorten` accepts optional `"expires_at": "<ISO-8601 datetime>"`
- After expiry, the code returns HTTP 410 Gone
- Dashboard shows expiry date in the link table and highlights expired links

---

#### US-15 — QR code generation
> As a marketer, I want to download a QR code for any short link, so that I can embed it in printed materials and presentations.

**Acceptance Criteria:**
- `GET /qr/{code}` returns a PNG image of the QR code pointing to the short URL
- QR code is scannable by standard mobile camera apps
- Accessible as a download link in the dashboard alongside each short link

---

## 4. Feature Requirements

### 4.1 Must-Have Features (MVP)

#### F-01 URL Shortening Engine
**Description:** Core logic that accepts a long URL and produces a unique short code. Uses a collision-resistant random code generator (Base62, 6–8 characters). Validates that the input is a well-formed URL.

**Acceptance Criteria:**
- Generates a unique 6-character Base62 code by default
- Collision rate < 1 in 1,000,000 for the first 100,000 links
- URL validation rejects non-HTTP/HTTPS schemes
- Duplicate long URLs receive new unique codes (no deduplication by default)

---

#### F-02 Redirect Handler
**Description:** Handles `GET /<code>` requests, looks up the original URL in SQLite, logs the click event (timestamp, IP, User-Agent), and issues a 302 redirect.

**Acceptance Criteria:**
- Lookup completes in ≤ 50 ms for a database with up to 100,000 records
- Returns 404 for unknown codes, 410 for disabled/expired codes
- Click event persisted atomically with redirect response

---

#### F-03 REST API
**Description:** FastAPI-based JSON API covering: `POST /api/shorten`, `GET /api/links`, `GET /api/links/{code}`, `DELETE /api/links/{code}`, `GET /api/analytics/{code}`.

**Acceptance Criteria:**
- All endpoints return `application/json`
- Errors follow RFC 7807 Problem Details format
- OpenAPI schema generated automatically at `/openapi.json`

---

#### F-04 SQLite Persistence
**Description:** All link records and click events stored in a local SQLite file. Schema managed with Alembic migrations.

**Acceptance Criteria:**
- `links` table: `id`, `code` (unique index), `original_url`, `created_at`, `expires_at`, `is_active`
- `click_events` table: `id`, `link_id` (FK), `clicked_at`, `ip_address`, `user_agent`
- WAL mode enabled for concurrent read performance
- Database file path configurable via `DATABASE_URL` environment variable

---

#### F-05 Health Check Endpoint
**Description:** `GET /health` returns service status and database connectivity status.

**Acceptance Criteria:**
- Runs a `SELECT 1` query to verify DB is accessible
- Returns 200 when healthy, 503 when DB is unreachable
- Response time ≤ 50 ms

---

### 4.2 Should-Have Features

#### F-06 Web Dashboard
**Description:** Minimal HTML UI at `GET /` and `GET /dashboard` for non-technical users to shorten URLs, view links, and see click counts — without touching the API directly.

**Acceptance Criteria:**
- Built with Jinja2 templates served by FastAPI
- Responsive layout (mobile-first, min-width 375 px)
- Supports shortening, listing, copying, and disabling links

---

#### F-07 Custom Short Codes
**Description:** Allow users to specify their own short code at link creation time.

**Acceptance Criteria:**
- Validated: 3–32 chars, alphanumeric + hyphens + underscores
- Rejected with 409 if code already exists

---

#### F-08 Link Disable / Enable Toggle
**Description:** Soft-delete approach: set `is_active = false` rather than deleting the record, so analytics are preserved.

**Acceptance Criteria:**
- `PATCH /api/links/{code}` with `{"is_active": false}` disables a link
- Disabled links return 410; analytics remain accessible

---

#### F-09 Click Analytics API
**Description:** `GET /api/analytics/{code}` returns total clicks, click events list, and a daily click time-series array.

**Acceptance Criteria:**
- Returns `click_events` array with up to 1,000 most recent events
- Includes `daily_clicks` array: `[{"date": "YYYY-MM-DD", "count": <int>}]` for the last 30 days

---

#### F-10 Rate Limiting
**Description:** SlowAPI (starlette-based) rate limiter on the shorten endpoint.

**Acceptance Criteria:**
- 60 req/min per IP by default
- Configurable via `RATE_LIMIT` env var (e.g., `"30/minute"`)
- Returns 429 with `Retry-After` header

---

#### F-11 Link Expiry
**Description:** Optional `expires_at` field. A background task or on-access check marks expired links as inactive.

**Acceptance Criteria:**
- Expiry checked on every redirect request
- APScheduler job runs every minute to bulk-expire links past their `expires_at`

---

### 4.3 Nice-to-Have Features

#### F-12 QR Code Generation
**Description:** `GET /qr/{code}` returns a PNG QR code for the short URL, generated with the `qrcode` Python library.

#### F-13 Click Geolocation
**Description:** Resolve IP addresses to country/city using a bundled MaxMind GeoLite2 database and include `country` and `city` fields in click event records.

#### F-14 API Key Authentication
**Description:** Optional Bearer token auth for write endpoints (`POST /api/shorten`, `DELETE /api/links/{code}`, `PATCH /api/links/{code}`). Keys stored as hashed values in SQLite.

#### F-15 CSV Analytics Export
**Description:** `GET /api/analytics/{code}/export` returns a CSV file of all click events for a given link, suitable for import into Excel or Google Sheets.

#### F-16 Bulk Shortening
**Description:** `POST /api/shorten/bulk` accepts an array of up to 100 URLs and returns an array of short codes in a single request, useful for batch processing.

#### F-17 Prometheus Metrics Endpoint
**Description:** `GET /metrics` exposes Prometheus-compatible metrics: total links, total clicks, redirect latency histogram, DB query duration.

---

## 5. Technical Requirements

### Technology Stack

| Layer | Technology | Version |
|-------|------------|---------|
| Language | Python | 3.11+ |
| Web Framework | FastAPI | 0.115+ |
| ASGI Server | Uvicorn | 0.32+ |
| ORM | SQLAlchemy | 2.0+ |
| Database | SQLite | 3.39+ (WAL mode) |
| Migrations | Alembic | 1.14+ |
| Validation | Pydantic v2 | 2.9+ |
| Templates | Jinja2 | 3.1+ |
| Rate Limiting | SlowAPI | 0.1.9+ |
| Testing | pytest + httpx | Latest |

### Architecture Considerations

- **Single-process deployment:** FastAPI + Uvicorn with multiple worker processes (`--workers 4`) for vertical scaling
- **Repository pattern:** All database access through repository classes; no raw SQL in route handlers
- **Dependency injection:** FastAPI `Depends()` used for DB sessions, rate limiters, and config
- **Configuration management:** All environment-sensitive values read from environment variables (dotenv supported via `python-dotenv`)
- **Layered structure:**
  ```
  app/
  ├── main.py          # FastAPI app factory, lifespan
  ├── config.py        # Settings via pydantic-settings
  ├── models.py        # SQLAlchemy ORM models
  ├── schemas.py       # Pydantic request/response schemas
  ├── database.py      # Engine, session factory
  ├── routers/
  │   ├── links.py     # /api/shorten, /api/links
  │   ├── analytics.py # /api/analytics
  │   └── redirect.py  # /<code> redirect handler
  ├── services/
  │   ├── shortener.py # Code generation logic
  │   └── analytics.py # Click recording
  ├── repositories/
  │   ├── link_repo.py
  │   └── click_repo.py
  └── templates/
      └── *.html
  ```

### Database Requirements

- **Engine:** SQLite 3 with WAL journaling enabled (`PRAGMA journal_mode=WAL`)
- **Tables:**
  - `links(id, code, original_url, created_at, expires_at, is_active)`
  - `click_events(id, link_id, clicked_at, ip_address, user_agent)`
- **Indexes:** Unique index on `links.code`; composite index on `click_events(link_id, clicked_at)`
- **Connection pool:** `StaticPool` (single connection, thread-safe) for SQLite; `check_same_thread=False`
- **Max DB file size target:** < 1 GB for up to 1 million links + 10 million click events

### API Specifications

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| POST | `/api/shorten` | Create short link | No (MVP) |
| GET | `/api/links` | List all links (paginated) | No (MVP) |
| GET | `/api/links/{code}` | Get link details | No |
| PATCH | `/api/links/{code}` | Update link (enable/disable) | No (MVP) |
| DELETE | `/api/links/{code}` | Delete link + events | No (MVP) |
| GET | `/api/analytics/{code}` | Get click analytics | No |
| GET | `/{code}` | Redirect to original URL | No |
| GET | `/health` | Health check | No |
| GET | `/docs` | Swagger UI | No |

### Performance Requirements

| Metric | Target |
|--------|--------|
| Redirect latency (p50) | ≤ 30 ms |
| Redirect latency (p99) | ≤ 100 ms |
| Shorten endpoint latency (p99) | ≤ 200 ms |
| Health check latency (p99) | ≤ 50 ms |
| Throughput (single process) | ≥ 500 redirects/sec |
| Database file size (1M links) | ≤ 500 MB |

### Security Requirements

- **Input validation:** All URL inputs validated with Pydantic `AnyHttpUrl`; reject `javascript:`, `data:`, `file:` schemes
- **SQL injection:** Not possible via SQLAlchemy ORM parameterized queries
- **XSS:** Jinja2 auto-escaping enabled for all templates; Content-Security-Policy header set
- **Rate limiting:** 60 req/min per IP on write endpoints; 429 response with `Retry-After`
- **Clickjacking:** `X-Frame-Options: DENY` response header
- **Open redirect:** Only stored, validated URLs are redirected to — no user-supplied redirect targets at request time
- **SSRF:** Reject private IP ranges (`10.x.x.x`, `192.168.x.x`, `127.x.x.x`) in submitted URLs (nice-to-have)
- **HTTPS:** Enforce HTTPS in production via reverse proxy (nginx/Caddy); `Strict-Transport-Security` header

### Scalability Considerations

- **Vertical:** Uvicorn multi-worker (`--workers N`) + SQLite WAL supports moderate concurrency
- **Horizontal (future):** SQLite is not horizontally scalable; migration path to PostgreSQL via SQLAlchemy swap (connection string only)
- **Caching (future):** Redis or in-process LRU cache for hot short codes to reduce DB reads on redirects
- **CDN (future):** Short links can be fronted by a CDN edge that caches 302 redirect responses with appropriate `Cache-Control` headers

---

## 6. User Interface & Experience

### Key UI/UX Principles

1. **Speed first:** The homepage should load in < 1 second and the shortening action should complete in under 500 ms total perceived time
2. **Zero learning curve:** A first-time visitor should be able to shorten a URL without reading any instructions
3. **Accessible defaults:** WCAG 2.1 AA compliance — sufficient color contrast, keyboard navigability, screen reader labels
4. **Minimal chrome:** No login walls, no onboarding modals, no cookie banners unless legally required
5. **Feedback immediacy:** Every user action (form submit, copy, disable) provides instant visual feedback

### Main User Flows

#### Flow 1 — Shorten a URL (Web)
```
[Home page] → Paste URL → Click "Shorten"
           → (validation passes) → Short URL displayed inline
           → Click "Copy" → URL in clipboard (toast: "Copied!")
           → Share link
```

#### Flow 2 — Shorten a URL (API)
```
POST /api/shorten {"url": "https://..."}
→ 200 {"short_code": "abc123", "short_url": "https://s.example.com/abc123"}
→ Embed in script / bot
```

#### Flow 3 — Redirect
```
User clicks https://s.example.com/abc123
→ GET /abc123
→ 302 Location: https://original-long-url.example.com/path?query=value
→ Browser follows redirect
```

#### Flow 4 — View Analytics (Dashboard)
```
[Dashboard] → Click link row → [Link Detail page]
           → See total clicks, daily chart, recent click events table
```

### Wireframe Descriptions

#### Screen 1 — Home Page (`GET /`)
- **Header:** Service name + tagline ("Shorten. Share. Track.")
- **Hero section:** Large URL input field (full-width) + "Shorten" CTA button
- **Result area** (appears after submission): Short URL displayed in a highlighted box with a "Copy" button and a "View Analytics" text link
- **Recent links** (optional): Last 5 links created in this browser session (localStorage)
- **Footer:** Link to `/dashboard` and `/docs`

#### Screen 2 — Dashboard (`GET /dashboard`)
- **Header:** "My Links" title + search/filter bar
- **Table columns:** Short Code | Original URL | Created | Expires | Clicks | Status | Actions
- **Actions column:** Copy | Analytics | Disable/Enable | Delete
- **Pagination:** Previous / Next buttons + "Page X of Y"
- **Empty state:** Illustration + "No links yet. Shorten your first URL." CTA

#### Screen 3 — Link Analytics (`GET /dashboard/{code}`)
- **Summary cards:** Total Clicks, Created At, Status, Expiry
- **Click chart:** Simple bar chart (last 30 days) using Chart.js or CSS bars
- **Click events table:** Timestamp | IP | User Agent (paginated, newest first)
- **Actions:** Copy Short URL | Disable Link | Delete Link

### Accessibility Requirements

- All form inputs have associated `<label>` elements
- Color is never the sole means of conveying information (status shown with icon + text)
- Focus indicators visible for all interactive elements
- All images / icons have descriptive `alt` text or `aria-label`
- Keyboard tab order follows visual reading order
- WCAG 2.1 AA color contrast ratio ≥ 4.5:1 for body text, ≥ 3:1 for large text

---

## 7. Success Metrics & KPIs

### User Engagement KPIs

| KPI | Target (3 months post-launch) |
|-----|-------------------------------|
| Total short links created | ≥ 1,000 |
| Weekly active API consumers | ≥ 25 unique IPs |
| Average clicks per link | ≥ 5 |
| Dashboard page sessions per week | ≥ 100 |
| Copy button click-through rate | ≥ 70% of shorten events |

### Technical Performance Metrics

| Metric | Target |
|--------|--------|
| Redirect p99 latency | ≤ 100 ms |
| API uptime | ≥ 99.5% monthly |
| Error rate (5xx) | < 0.1% of requests |
| Health check pass rate | 100% |
| Test coverage | ≥ 85% line coverage |

### Business Metrics (Self-Hosted Context)

| Metric | Target |
|--------|--------|
| Time to first successful shorten | ≤ 2 minutes from `docker run` or `uvicorn` |
| Setup complexity | Zero external dependencies beyond Python |
| Developer adoption (GitHub stars, if open-sourced) | ≥ 100 stars in 6 months |

### How Success Will Be Measured

- Click events recorded in SQLite provide ground-truth data for all engagement KPIs
- Uvicorn access logs parsed for error rate and latency percentiles
- Prometheus metrics endpoint (F-17) feeds optional Grafana dashboard for real-time monitoring
- Weekly automated report generated by querying `/api/analytics` endpoints

---

## 8. Timeline & Milestones

### Phase 1 — Core MVP (Weeks 1–2)

**Goal:** Working redirect service with REST API and SQLite persistence

| Week | Deliverables |
|------|-------------|
| 1 | Project scaffold, SQLAlchemy models, Alembic migrations, `POST /api/shorten`, `GET /<code>` redirect |
| 2 | `GET /api/links`, `DELETE /api/links/{code}`, `GET /health`, unit + integration tests, CI pipeline |

**Milestone:** API fully functional; redirect latency ≤ 100 ms; ≥ 80% test coverage

---

### Phase 2 — Analytics & Web UI (Weeks 3–4)

**Goal:** Click tracking, analytics API, and basic web dashboard

| Week | Deliverables |
|------|-------------|
| 3 | Click event recording, `GET /api/analytics/{code}`, custom short codes (F-07) |
| 4 | Jinja2 home page, dashboard page, link detail/analytics page, copy button |

**Milestone:** Non-technical users can shorten and monitor links without touching the API

---

### Phase 3 — Polish & Should-Haves (Weeks 5–6)

**Goal:** Rate limiting, link expiry, disable/enable, production hardening

| Week | Deliverables |
|------|-------------|
| 5 | Rate limiting (SlowAPI), link expiry (APScheduler), disable/enable toggle |
| 6 | Security headers, input sanitization, Docker image, deployment documentation |

**Milestone:** Production-ready single-container deployment; ≥ 85% test coverage

---

### Phase 4 — Nice-to-Haves (Weeks 7–8, optional)

**Goal:** QR codes, API key auth, bulk shortening, Prometheus metrics

| Week | Deliverables |
|------|-------------|
| 7 | QR code endpoint (F-12), CSV export (F-15), API key auth (F-14) |
| 8 | Bulk shortening (F-16), Prometheus metrics (F-17), performance profiling |

**Milestone:** Feature-complete v1.0 release candidate

---

### Sprint Breakdown (2-week sprints)

| Sprint | Focus | Key Stories |
|--------|-------|-------------|
| Sprint 1 | Core engine + API | US-01, US-11, US-09 |
| Sprint 2 | Analytics + dashboard | US-03, US-06, US-05 |
| Sprint 3 | UX + customization | US-02, US-07, US-08, US-14 |
| Sprint 4 | Hardening + extras | US-13, US-04, US-10, US-12, US-15 |

---

## 9. Risks & Mitigation Strategies

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| SQLite write contention under high concurrent load | Medium | High | Enable WAL mode; use connection pooling; add migration path to PostgreSQL |
| Short code collisions as database grows large | Low | Medium | Pre-check for collision before insert; retry up to 5 times; use 8-char codes when > 50k links |
| Malicious URLs submitted (phishing, malware) | Medium | High | Integrate Google Safe Browsing API (nice-to-have); display original domain before redirect; rate limit |
| Open redirect abuse (SSRF) | Medium | High | Validate submitted URLs against private IP blocklist; restrict to HTTP/HTTPS schemes only |
| Disk space exhaustion from click event logs | Low | Medium | Add TTL purge job for events older than 90 days (configurable); alert when DB > 500 MB |

### Business Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Link rot — broken original URLs behind short codes | Medium | Medium | Periodic background job to HEAD-check original URLs and flag 404s in dashboard |
| Abuse for spam or phishing campaigns | Medium | High | Rate limiting, optional API key auth, referrer logging, easy link deletion |
| Scope creep delaying MVP | High | Medium | Strict MoSCoW prioritization; defer Phase 4 features to post-launch iteration |
| Low adoption if UX is too technical | Low | Medium | Include web UI in MVP (Phase 2); provide one-command Docker setup |

### Mitigation Strategies Summary

1. **Start with WAL mode** from day one — changing SQLite settings post-deployment requires downtime
2. **Write integration tests for the redirect path** before anything else — it's the highest-traffic, most critical path
3. **Keep the schema minimal** — adding columns later via Alembic is cheap; removing them is not
4. **Document the PostgreSQL migration path** in the README before v1.0 so users know the escape hatch

---

## 10. Assumptions & Dependencies

### Key Assumptions

1. The service will initially be deployed on a single server/container; horizontal scaling is not required for MVP
2. All users are trusted in the MVP (no authentication); API key auth is deferred to Phase 4
3. SQLite is sufficient for the anticipated load (< 1,000 links created/day, < 50,000 redirects/day)
4. The operator (self-hoster) is responsible for HTTPS termination via a reverse proxy (nginx, Caddy, Traefik)
5. Short codes are case-sensitive (e.g., `abc123` ≠ `ABC123`)
6. Analytics data does not need GDPR-compliant anonymization for MVP (IP addresses stored as-is)

### External Dependencies

| Dependency | Purpose | Risk if Unavailable |
|-----------|---------|---------------------|
| Python 3.11+ runtime | Application execution | Blocking — required |
| SQLite 3.39+ | Persistence | Blocking — bundled with Python |
| pip packages (FastAPI, SQLAlchemy, etc.) | Framework | Blocking — must be installable |
| Docker (optional) | Containerized deployment | Non-blocking — can run directly with uvicorn |
| Google Safe Browsing API (Phase 4) | Malicious URL detection | Non-blocking — feature disabled if absent |
| MaxMind GeoLite2 DB (Phase 4) | IP geolocation | Non-blocking — feature disabled if absent |

### Resource Requirements

- **Development:** 1 backend developer, 1 sprint (2 weeks) per phase
- **Infrastructure:** Single VPS or container (1 vCPU, 512 MB RAM, 10 GB disk) for MVP deployment
- **Storage:** ≈ 500 MB SQLite file for 1 million links + 10 million click events

---

## 11. Open Questions

1. **Authentication scope:** Should the MVP require any form of authentication, or is a fully open API (relying on rate limiting) acceptable for the initial deployment target?

2. **URL deduplication:** If the same long URL is submitted twice, should the system return the existing short code or generate a new one? Deduplication simplifies management but complicates analytics per-intent.

3. **Redirect type:** Should redirects use HTTP 301 (permanent, browser-cached — reduces server load) or 302 (temporary, always hits server — accurate click counting)? Currently specced as 302; 301 makes click analytics unreliable.

4. **Click event retention:** How long should raw click event data be retained? 30 days? 1 year? Forever? This affects storage planning significantly.

5. **Base URL configuration:** How should the base URL for short links be configured — environment variable, config file, or auto-detected from request `Host` header? Auto-detection is simpler but unreliable behind proxies.

6. **Custom domain support:** Should users be able to configure a custom domain (e.g., `go.company.com`) as the short link base, or is a single configured base URL sufficient?

7. **Branded short code namespace:** If custom codes are allowed, should there be reserved codes (e.g., `api`, `docs`, `health`, `dashboard`) that cannot be claimed by users?

8. **Analytics privacy:** Are there GDPR or CCPA implications for storing IP addresses in click events? Should IP anonymization (last octet masked) be included from day one?

9. **Concurrency model:** Should Uvicorn be configured with multiple worker processes (improves throughput but SQLite WAL mode may need tuning), or is a single async worker sufficient for the target load?

10. **UI framework:** Should the web dashboard use server-rendered Jinja2 templates (simpler, no JS build step) or a lightweight frontend framework like HTMX + Alpine.js (more interactive, still minimal)?

---

*End of PRD — Version 1.0*

*This document should be reviewed and updated at the end of each development phase.*
