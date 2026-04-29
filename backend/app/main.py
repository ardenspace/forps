import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.v1.router import api_v1_router
from app.services.discord_service import start_weekly_scheduler
from app.services.push_event_reaper import run_reaper_once

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: 미처리 push event 회수 (Phase 2 — Phase 4에 sync 주입)
    try:
        reaped = await run_reaper_once()
        if reaped:
            logger.info("startup reaper picked up %d pending push events", reaped)
    except Exception:
        # 부팅을 막지 않음 — DB 미준비 등
        logger.exception("startup reaper failed")

    # Startup: 주간 리포트 스케줄러 시작
    scheduler_task = asyncio.create_task(start_weekly_scheduler())
    yield
    # Shutdown: 스케줄러 정리
    scheduler_task.cancel()


app = FastAPI(
    title="forps API",
    description="B2B Task Management & Collaboration Tool",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "forps API is running"}


@app.head("/health")
@app.get("/health")
async def health():
    return {"status": "ok"}


app.include_router(api_v1_router, prefix="/api/v1")
