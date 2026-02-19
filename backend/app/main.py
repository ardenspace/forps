import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.v1.router import api_v1_router
from app.services.discord_service import start_weekly_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
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


@app.get("/health")
async def health():
    return {"status": "ok"}


app.include_router(api_v1_router, prefix="/api/v1")
