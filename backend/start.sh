#!/bin/bash
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting FastAPI server..."
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

**Step 2: start.sh 실행 권한 부여**

```bash
chmod +x backend/start.sh