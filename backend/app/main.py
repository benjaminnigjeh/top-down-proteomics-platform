from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.config import settings
from app.database import create_all_tables
from app.api.routes import uploads, jobs, results, engines, exports, conversions


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    settings.JOB_DIR.mkdir(parents=True, exist_ok=True)
    create_all_tables()
    yield
    # Shutdown (nothing needed)


app = FastAPI(
    title="TDPortal-OS",
    description="Open-source top-down proteomics web platform. Not affiliated with official TDPortal.",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api/v1"
app.include_router(uploads.router, prefix=API_PREFIX)
app.include_router(jobs.router, prefix=API_PREFIX)
app.include_router(results.router, prefix=API_PREFIX)
app.include_router(engines.router, prefix=API_PREFIX)
app.include_router(exports.router, prefix=API_PREFIX)
app.include_router(conversions.router, prefix=API_PREFIX)


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "version": settings.APP_VERSION}
