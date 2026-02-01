from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

app = FastAPI(
    title="for-ps API",
    description="B2B Task Management & Collaboration Tool",
    version="0.1.0"
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
    return {"message": "for-ps API is running"}


@app.get("/health")
async def health():
    return {"status": "ok"}


# TODO: Add routers
# from app.api import auth, workspaces, projects, tasks
# app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
# app.include_router(workspaces.router, prefix="/api/workspaces", tags=["workspaces"])
# app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
# app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
