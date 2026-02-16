# forps

B2B 협업 업무 관리 툴 (Task Management & Collaboration Tool)

## 기술 스택

### Backend
- **FastAPI** - Python 웹 프레임워크
- **PostgreSQL** - 데이터베이스 (로컬: Docker, 배포: Railway)
- **SQLAlchemy** - ORM
- **Alembic** - DB 마이그레이션
- **JWT** - 인증

### Frontend
- **Vite + React** - SPA
- **shadcn/ui + Tailwind** - UI 라이브러리

## 프로젝트 구조

```
forps/
├── backend/
│   ├── app/
│   │   ├── models/          # DB 모델
│   │   │   ├── user.py
│   │   │   ├── workspace.py
│   │   │   ├── project.py
│   │   │   ├── task.py
│   │   │   ├── share_link.py
│   │   │   └── task_event.py
│   │   ├── core/            # 핵심 로직
│   │   │   ├── security.py  # JWT, 비밀번호 해싱
│   │   │   └── permissions.py
│   │   ├── api/             # API 라우터
│   │   ├── schemas/         # Pydantic 스키마
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── dependencies.py
│   │   └── main.py
│   ├── alembic/             # DB 마이그레이션
│   ├── requirements.txt
│   └── .env
├── frontend/
└── docker-compose.yml
```

## 시작하기

### 1. PostgreSQL 실행 (Docker)

```bash
docker-compose up -d
```

### 2. 백엔드 실행

```bash
cd backend

# 가상환경 활성화
source venv/bin/activate

# 서버 실행
uvicorn app.main:app --reload --port 8000
```

서버 실행 후:
- API: http://localhost:8000
- API 문서: http://localhost:8000/docs

### 3. 데이터베이스 마이그레이션

```bash
# 새 마이그레이션 생성
alembic revision --autogenerate -m "마이그레이션 메시지"

# 마이그레이션 적용
alembic upgrade head

# 롤백
alembic downgrade -1
```

## 데이터 모델

### 핵심 엔티티

- **User** - 사용자
- **Workspace** - 워크스페이스 (팀/조직)
- **WorkspaceMember** - 워크스페이스 멤버십 (권한: Owner/Editor/Viewer)
- **Project** - 프로젝트
- **ProjectMember** - 프로젝트 참여자
- **Task** - 태스크 (상태: To do/Doing/Done/Blocked)
- **Comment** - 댓글
- **ShareLink** - 공유 링크 (외부 공유)
- **TaskEvent** - 활동 로그

## 환경변수

`.env` 파일 예시:

```bash
# Database
DATABASE_URL=postgresql://forps:forps123@localhost:5432/forps

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# CORS
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# Discord (optional)
DISCORD_WEBHOOK_URL=
```

## 배포 (Railway)

Railway는 환경변수 `DATABASE_URL`을 자동으로 설정합니다.

```bash
# Railway CLI 설치
npm install -g @railway/cli

# 로그인
railway login

# 배포
railway up
```

## 구현 상태 (2026-02 기준)

- [x] API 엔드포인트 기본 구현 (auth, workspaces, projects, tasks, share)
- [x] 프론트엔드 세팅 (Vite + React + TypeScript + Tailwind)
- [x] Kanban 뷰 구현
- [ ] Table 뷰 구현
- [ ] Discord 웹훅 (일일/주간 리포트)

## 남은 주요 미구현 항목

- [ ] Workspace 수정/삭제 API
- [ ] Workspace 멤버 role 변경 API
- [ ] Project 수정/삭제 API
- [ ] Project 멤버 관리 API (조회/추가/수정/삭제)
- [ ] ShareLink 생성/관리 프론트 UI
