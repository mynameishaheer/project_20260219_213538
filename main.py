"""
URL Shortener — FastAPI application entry point.

Run locally:
    uvicorn main:app --reload --port 8000

Production (via docker-entrypoint.sh):
    uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from src.database.database import create_tables
from src.health import get_health_status_async


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables exist (Alembic handles migrations in prod)
    create_tables()
    yield
    # Shutdown: nothing to tear down at this level


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="URL Shortener",
    version="1.0.0",
    description="A fast URL shortening service built with FastAPI.",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Health endpoint — no authentication required
# ---------------------------------------------------------------------------

@app.get(
    "/health",
    tags=["ops"],
    summary="Health check",
    response_description="Service health status",
)
async def health():
    """
    Returns the health status of the service and its dependencies.

    Always accessible without authentication.  Returns HTTP 200 when healthy
    and HTTP 503 when one or more checks are degraded.
    """
    payload = await get_health_status_async()
    status_code = 200 if payload["status"] == "healthy" else 503
    return JSONResponse(content=payload, status_code=status_code)


# ---------------------------------------------------------------------------
# Root redirect placeholder
# ---------------------------------------------------------------------------

@app.get("/", include_in_schema=False)
async def root():
    """Placeholder — will serve the web dashboard."""
    return {"message": "URL Shortener API is running. See /docs for the API reference."}
