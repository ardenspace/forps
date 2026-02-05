from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from app.schemas.auth import AuthResponse, RegisterRequest, LoginRequest, TokenResponse, UserResponse


async def register(db: AsyncSession, data: RegisterRequest) -> AuthResponse:
    # 1. 기존 사용자 중복 체크
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # 2. 사용자 생성
    user = User(
        email=data.email,
        name=data.name,
        password_hash=get_password_hash(data.password),
    )
    db.add(user)
    await db.flush()

    # 3. 기본 Workspace 자동 생성
    workspace = Workspace(
        name=f"{data.name}의 워크스페이스",
        slug=f"ws-{user.id.hex}",  # 전체 UUID hex 사용 (충돌 방지)
        description=None,
    )
    db.add(workspace)
    await db.flush()

    # 4. 사용자를 Workspace Owner로 추가
    member = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=user.id,
        role=WorkspaceRole.OWNER,
    )
    db.add(member)

    await db.commit()
    await db.refresh(user)

    # 5. 토큰 생성 및 반환
    token = create_access_token(data={"sub": str(user.id)})
    return AuthResponse(
        token=TokenResponse(access_token=token),
        user=UserResponse.model_validate(user),
    )


async def login(db: AsyncSession, data: LoginRequest) -> AuthResponse:
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(data={"sub": str(user.id)})
    return AuthResponse(
        token=TokenResponse(access_token=token),
        user=UserResponse.model_validate(user),
    )
