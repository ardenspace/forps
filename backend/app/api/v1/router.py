from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.tasks import router as tasks_router
from app.api.v1.endpoints.workspaces import router as workspaces_router
from app.api.v1.endpoints.projects import router as projects_router
from app.api.v1.endpoints.share_links import router as share_links_router
from app.api.v1.endpoints.webhooks import router as webhooks_router

api_v1_router = APIRouter()
api_v1_router.include_router(auth_router)
api_v1_router.include_router(tasks_router)
api_v1_router.include_router(workspaces_router)
api_v1_router.include_router(projects_router)
api_v1_router.include_router(share_links_router)
api_v1_router.include_router(webhooks_router)
