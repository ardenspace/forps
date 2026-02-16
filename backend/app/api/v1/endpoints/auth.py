from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CurrentUser
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(data: RegisterRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    return await auth_service.register(db, data)


@router.post("/login", response_model=AuthResponse)
async def login(data: LoginRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    return await auth_service.login(db, data)


@router.get("/me", response_model=UserResponse)
async def me(current_user: CurrentUser):
    return current_user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(current_user: CurrentUser):
    _ = current_user
    return Response(status_code=status.HTTP_204_NO_CONTENT)
