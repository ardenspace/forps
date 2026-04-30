# forps dev 환경 자동화
# app-chak (운영 서버, 8000/5432) 는 절대 안 건드림 — 모든 target 은 forps 자원만 대상.

PG_CONTAINER := forps-postgres
PG_USER := forps
PG_PASSWORD := forps123
PG_DB := forps
PG_PORT ?= 5433
BACKEND_PORT ?= 8081

BACKEND_HOST := http://localhost:$(BACKEND_PORT)
BACKEND_API_URL := $(BACKEND_HOST)/api/v1

VENV := backend/venv
VENV_PIP := $(VENV)/bin/pip
VENV_ALEMBIC := $(VENV)/bin/alembic
VENV_PYTEST := $(VENV)/bin/pytest
VENV_UVICORN := $(VENV)/bin/uvicorn

.PHONY: help setup env venv backend frontend db-up db-down stop clean migrate test test-backend test-frontend

help:
	@echo "forps dev targets:"
	@echo "  make setup        # 첫 setup: venv + deps + .env + .env.local + db-up + migrate"
	@echo "  make backend      # uvicorn $(BACKEND_PORT) (auto reload)"
	@echo "  make frontend     # vite (5173 -> backend $(BACKEND_PORT))"
	@echo "  make db-up        # forps-postgres $(PG_PORT) (app-chak 안 건드림)"
	@echo "  make db-down      # forps-postgres 만 stop"
	@echo "  make migrate      # alembic upgrade head"
	@echo "  make test         # backend pytest + frontend build/lint"
	@echo "  make clean        # forps-postgres 컨테이너 삭제"
	@echo ""
	@echo "포트 override:"
	@echo "  make backend BACKEND_PORT=8000"
	@echo "  make db-up PG_PORT=5432"

# 첫 setup — 한 번만
setup: env venv db-up migrate
	cd frontend && bun install
	@echo ""
	@echo "✓ setup 완료. 두 터미널에서 'make backend' / 'make frontend' 로 실행."

env:
	@if [ ! -f backend/.env ]; then \
		echo "DATABASE_URL=postgresql+asyncpg://$(PG_USER):$(PG_PASSWORD)@localhost:$(PG_PORT)/$(PG_DB)" > backend/.env; \
		echo "SECRET_KEY=$$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')" >> backend/.env; \
		echo "FORPS_FERNET_KEY=$$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')" >> backend/.env; \
		echo "FORPS_PUBLIC_URL=$(BACKEND_HOST)" >> backend/.env; \
		echo "ALLOWED_ORIGINS=http://localhost:5173" >> backend/.env; \
		echo "✓ backend/.env 생성 (SECRET_KEY / FORPS_FERNET_KEY 자동 생성)"; \
	else \
		echo "ℹ backend/.env 이미 있음 — 보존"; \
	fi
	@if [ ! -f frontend/.env.local ]; then \
		echo "VITE_API_URL=$(BACKEND_API_URL)" > frontend/.env.local; \
		echo "✓ frontend/.env.local 생성"; \
	else \
		echo "ℹ frontend/.env.local 이미 있음 — 보존"; \
	fi

venv:
	@if [ ! -d $(VENV) ]; then \
		python3.12 -m venv $(VENV); \
		echo "✓ venv 생성"; \
	fi
	@$(VENV_PIP) install --quiet --upgrade pip
	@$(VENV_PIP) install --quiet -r backend/requirements-dev.txt
	@echo "✓ backend deps 설치"

backend:
	$(VENV_UVICORN) --app-dir backend app.main:app --reload --port $(BACKEND_PORT)

frontend:
	cd frontend && bun run dev

db-up:
	@if docker ps --format '{{.Names}}' | grep -q '^$(PG_CONTAINER)$$'; then \
		echo "ℹ $(PG_CONTAINER) 이미 실행 중"; \
	elif docker ps -a --format '{{.Names}}' | grep -q '^$(PG_CONTAINER)$$'; then \
		docker start $(PG_CONTAINER) >/dev/null; \
		echo "✓ $(PG_CONTAINER) start"; \
	else \
		docker run -d --name $(PG_CONTAINER) \
			-e POSTGRES_USER=$(PG_USER) \
			-e POSTGRES_PASSWORD=$(PG_PASSWORD) \
			-e POSTGRES_DB=$(PG_DB) \
			-p $(PG_PORT):5432 \
			postgres:16-alpine >/dev/null; \
		echo "✓ $(PG_CONTAINER) created on port $(PG_PORT)"; \
	fi
	@for i in 1 2 3 4 5 6 7 8 9 10; do \
		docker exec $(PG_CONTAINER) pg_isready -U $(PG_USER) >/dev/null 2>&1 && echo "✓ $(PG_CONTAINER) ready" && exit 0; \
		sleep 1; \
	done; \
	echo "✗ $(PG_CONTAINER) 가 10초 안에 ready 안 됨" && exit 1

db-down:
	@if docker ps --format '{{.Names}}' | grep -q '^$(PG_CONTAINER)$$'; then \
		docker stop $(PG_CONTAINER) >/dev/null; \
		echo "✓ $(PG_CONTAINER) stopped"; \
	else \
		echo "ℹ $(PG_CONTAINER) 가 실행 중 아님"; \
	fi

stop: db-down
	@echo "ℹ uvicorn / vite 는 ctrl-c 로 직접 종료"

clean: db-down
	@if docker ps -a --format '{{.Names}}' | grep -q '^$(PG_CONTAINER)$$'; then \
		docker rm $(PG_CONTAINER) >/dev/null; \
		echo "✓ $(PG_CONTAINER) 컨테이너 삭제"; \
	fi
	@echo "ℹ volume 도 삭제하려면 'docker volume prune'"

migrate:
	cd backend && ../$(VENV_ALEMBIC) upgrade head

test: test-backend test-frontend

test-backend:
	cd backend && ../$(VENV_PYTEST) -q

test-frontend:
	cd frontend && bun run build
	-cd frontend && bun run lint
