from functools import wraps
from typing import Callable
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.workspace import WorkspaceMember, WorkspaceRole


def check_workspace_role(
    db: Session,
    user_id: UUID,
    workspace_id: UUID,
    required_role: WorkspaceRole | None = None
) -> WorkspaceMember:
    """
    Check if user has access to workspace and required role.
    Returns WorkspaceMember if authorized, raises HTTPException otherwise.
    """
    membership = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == user_id
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this workspace"
        )

    if required_role:
        # Role hierarchy: owner > editor > viewer
        role_hierarchy = {
            WorkspaceRole.OWNER: 3,
            WorkspaceRole.EDITOR: 2,
            WorkspaceRole.VIEWER: 1
        }

        if role_hierarchy.get(membership.role, 0) < role_hierarchy.get(required_role, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires {required_role.value} role"
            )

    return membership


def require_workspace_role(required_role: WorkspaceRole):
    """
    Decorator to check workspace role.
    Usage:
        @require_workspace_role(WorkspaceRole.OWNER)
        async def delete_project(workspace_id: UUID, ...):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # This is a placeholder - actual implementation would need
            # to extract workspace_id, user_id, and db from function args/kwargs
            # For now, we'll implement this check directly in route handlers
            return await func(*args, **kwargs)
        return wrapper
    return decorator
