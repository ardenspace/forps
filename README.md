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

`Makefile` 이 dev 환경 setup 자동화. **app-chak 같은 다른 서비스가 8000/5432 점유 중이어도 충돌 없음** — forps 는 backend 8081 / postgres 5433 default.

### 첫 setup (한 번만)

```bash
make setup
```

이걸로 다음이 한 번에 됨:
- `backend/venv` 생성 + dev deps 설치
- `backend/.env` 자동 생성 (SECRET_KEY / FORPS_FERNET_KEY 랜덤)
- `frontend/.env.local` 자동 생성 (`VITE_API_URL` 가 backend port 가리킴)
- `forps-postgres` Docker 컨테이너 5433 에 띄움
- `alembic upgrade head`
- `frontend` deps 설치 (bun)

기존 `.env` 가 있으면 보존 (시크릿 안 덮음).

### 일상 작업

두 터미널 필요:

```bash
# Terminal 1
make backend     # uvicorn http://localhost:8081 (auto reload)

# Terminal 2
make frontend    # vite http://localhost:5173
```

### 그 외

```bash
make migrate     # alembic upgrade head
make test        # backend pytest + frontend build/lint
make db-down     # forps-postgres 만 stop (app-chak 안 건드림)
make db-up       # 다시 띄움
make clean       # forps-postgres 컨테이너 삭제 (volume 은 prune 별도)
make help        # 전체 target 목록
```

### 포트 override

```bash
make backend BACKEND_PORT=8000
make db-up PG_PORT=5432
```

### 수동 setup (Makefile 안 쓸 때)

```bash
# 1. PostgreSQL — app-chak 과 충돌 없는 5433 사용 권장
docker run -d --name forps-postgres \
  -e POSTGRES_USER=forps -e POSTGRES_PASSWORD=forps123 -e POSTGRES_DB=forps \
  -p 5433:5432 postgres:16-alpine

# 2. backend env (template: backend/.env.example)
cp backend/.env.example backend/.env
# SECRET_KEY / FORPS_FERNET_KEY 채우기

# 3. backend
cd backend
python3.12 -m venv venv && source venv/bin/activate
pip install -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8081

# 4. frontend env + dev server
cp frontend/.env.example frontend/.env.local
cd frontend && bun install && bun run dev
```

서버 실행 후:
- API: http://localhost:8081
- API 문서: http://localhost:8081/docs
- Frontend: http://localhost:5173

### Alembic

```bash
# 새 마이그레이션 생성
cd backend && source venv/bin/activate
alembic revision --autogenerate -m "마이그레이션 메시지"

# 적용
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

전체 템플릿: `backend/.env.example`, `frontend/.env.example`. `make setup` 이 자동 생성 (시크릿은 랜덤).

| 변수 | 위치 | 설명 |
|---|---|---|
| `DATABASE_URL` | backend/.env | PostgreSQL async URL (asyncpg driver) |
| `SECRET_KEY` | backend/.env | JWT 서명. `secrets.token_urlsafe(32)` |
| `FORPS_FERNET_KEY` | backend/.env | Webhook secret / GitHub PAT 암호화. `Fernet.generate_key()` |
| `FORPS_PUBLIC_URL` | backend/.env | webhook callback URL (GitHub 가 호출). 로컬: `http://localhost:8081` / 운영: Cloudflare Tunnel URL |
| `ALLOWED_ORIGINS` | backend/.env | CORS — frontend origin (default `http://localhost:5173`) |
| `VITE_API_URL` | frontend/.env.local | backend API base URL (default `http://localhost:8081/api/v1`) |

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
