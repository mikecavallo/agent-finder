"""Agent Finder API: AI resume screening for insurance agency hiring."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .ai.providers import get_provider
from .api import auth, candidates, jobs
from .config import get_settings
from .database import init_db
from .schemas import HealthOut

__version__ = "0.2.0"
logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    init_db()
    if settings.demo_mode:
        from .demo.seed import seed_demo

        await seed_demo(settings)
    yield


app = FastAPI(title="Agent Finder API", version=__version__, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(candidates.router, prefix="/api", tags=["candidates"])


@app.get("/api/health", response_model=HealthOut, tags=["meta"])
def health():
    settings = get_settings()
    return HealthOut(
        status="ok",
        provider=get_provider(settings).label,
        demo_mode=settings.demo_mode,
        version=__version__,
    )
