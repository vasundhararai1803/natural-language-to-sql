"""
FastAPI Application Entrypoint for QueryLens AI.
Uses modern lifespan management, structured logging middleware, explicit CORS origins,
and initializes database storage cleanly.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.api.routes import router
from backend.models.db_models import init_db
from backend.repositories.storage import init_storage
from backend.middleware.logging_middleware import ObservabilityAndRateLimitMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize SQLite analytics DB schema and storage tables
    init_db()
    init_storage()
    yield
    # Shutdown logic (clean up connections if needed)


app = FastAPI(
    title=settings.app_name,
    description="Natural Language to SQL, Analytics & Diagnostics Engine",
    version="1.1.0",
    lifespan=lifespan
)

# Custom Logging, Request ID, and Rate Limiting Middleware
app.add_middleware(ObservabilityAndRateLimitMiddleware)

# Explicit CORS origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"]
)

app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
