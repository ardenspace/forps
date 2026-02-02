# Backend Setup

## 개발 환경 설정

### 1. Python 가상환경 생성

```bash
python3.12 -m venv venv
source venv/bin/activate
```

### 2. 패키지 설치

```bash
pip install -r requirements.txt
```

### 3. 환경변수 설정

`.env` 파일 생성:

```bash
cp .env.example .env
# .env 파일을 열어서 필요한 값 수정
```

### 4. 서버 실행

```bash
uvicorn app.main:app --reload --port 8000
```

## API 문서

서버 실행 후:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 유용한 명령어

```bash
# 서버 실행
uvicorn app.main:app --reload

# 마이그레이션 생성
alembic revision --autogenerate -m "메시지"

# 마이그레이션 적용
alembic upgrade head

# 롤백
alembic downgrade -1

# Python 셸 실행 (모델 테스트용)
python -i -c "from app.database import SessionLocal; from app.models import *; db = SessionLocal()"
```
