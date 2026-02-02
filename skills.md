# for-ps Development Skills

B2B Task Management & Collaboration Tool - AI 개발 가이드

## 핵심 원칙

### 1. DRY (Don't Repeat Yourself)
- 같은 코드를 2번 이상 쓰지 않는다
- 공통 로직은 **즉시** 별도 함수/컴포넌트로 분리
- 하드코딩 금지 - 모든 상수는 constants 파일에

### 2. 모듈화 & 재사용성
- 작은 단위로 쪼개서 조합 가능하게
- 한 파일은 하나의 책임만
- 컴포넌트/함수는 독립적으로 테스트 가능하게

### 3. 타입 안전성
- `any` 사용 금지
- 공통 타입은 별도 파일로 관리
- API 응답 타입 정의 필수

---

## 기술 스택

### Backend
- **FastAPI** 0.115+ - Python 웹 프레임워크
- **PostgreSQL** - 데이터베이스
- **SQLAlchemy** 2.0+ - ORM (async 사용)
- **Alembic** - DB 마이그레이션
- **Pydantic** v2 - 데이터 검증

### Frontend
- **React** 19 - UI 라이브러리
- **TypeScript** 5+ - 타입 안전성
- **Vite** - 빌드 도구
- **Tailwind CSS** - 스타일링
- **shadcn/ui** - UI 컴포넌트 (재사용)
- **TanStack Query** - 서버 상태 관리 (예정)
- **Zustand** - 클라이언트 상태 관리 (예정)

---

## Backend 규칙

### 파일 구조
```
backend/app/
├── api/
│   └── v1/
│       ├── endpoints/
│       │   ├── auth.py
│       │   ├── tasks.py
│       │   └── projects.py
│       └── router.py
├── models/              # SQLAlchemy 모델
├── schemas/             # Pydantic 스키마 (request/response)
├── services/            # 비즈니스 로직 (재사용 가능)
├── core/
│   ├── security.py      # JWT, 비밀번호 해싱
│   ├── permissions.py   # 권한 체크
│   └── config.py
├── utils/               # 공통 유틸리티
│   ├── datetime.py      # 날짜 관련 함수
│   └── validators.py
└── constants/           # 상수 관리
    └── messages.py
```

### API 설계 패턴

#### 1. 라우터 구조
```python
# ✅ GOOD: 역할별로 분리
@router.get("/tasks/week", response_model=list[TaskSchema])
async def get_week_tasks(
    week_start: date,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return await TaskService.get_week_tasks(db, week_start, current_user.id)

# ❌ BAD: 라우터에 비즈니스 로직
@router.get("/tasks/week")
async def get_week_tasks(...):
    tasks = db.query(Task).filter(...).all()  # 직접 쿼리 금지
```

#### 2. 응답 형식 (표준화)
```python
# 성공 응답
{
    "data": [...],
    "message": "Success"
}

# 에러 응답
{
    "detail": "Error message",
    "code": "ERROR_CODE"
}
```

#### 3. 에러 핸들링
```python
# utils/exceptions.py - 공통 예외 정의
class NotFoundException(HTTPException):
    def __init__(self, resource: str):
        super().__init__(
            status_code=404,
            detail=f"{resource} not found"
        )

# 사용
if not task:
    raise NotFoundException("Task")
```

### 데이터베이스 규칙

1. **관계 설정**: `back_populates` 양방향 사용
2. **삭제 정책**: `ondelete="CASCADE"` 명시
3. **UUID 사용**: 모든 ID는 UUID
4. **Timestamp**: `created_at`, `updated_at` 필수
5. **마이그레이션**: 변경사항 발생 시 즉시 생성

### 보안 규칙

```python
# 1. 모든 엔드포인트는 인증 필요 (공개 제외)
current_user: User = Depends(get_current_user)

# 2. 권한 체크는 데코레이터 사용
@require_permission("project:write")
async def update_project(...):
    pass

# 3. SQL Injection 방지 - ORM 사용, 직접 쿼리 금지
# ❌ BAD
db.execute(f"SELECT * FROM tasks WHERE id = {task_id}")

# ✅ GOOD
db.query(Task).filter(Task.id == task_id).first()
```

---

## Frontend 규칙

### 파일 구조
```
frontend/src/
├── components/
│   ├── ui/              # shadcn/ui 컴포넌트
│   ├── common/          # 공통 재사용 컴포넌트
│   │   ├── Button.tsx
│   │   ├── Card.tsx
│   │   └── Modal.tsx
│   └── features/        # 도메인별 컴포넌트
│       ├── tasks/
│       └── projects/
├── pages/               # 페이지 컴포넌트
├── hooks/               # 커스텀 훅 (재사용)
│   ├── useWeekTasks.ts
│   └── useAuth.ts
├── services/            # API 클라이언트
│   └── api.ts
├── types/               # 공통 타입 정의
│   ├── task.ts
│   └── project.ts
├── utils/               # 유틸리티 함수
│   ├── date.ts
│   └── format.ts
├── constants/           # 상수
│   └── routes.ts
└── lib/                 # 외부 라이브러리 설정
    └── cn.ts
```

### 컴포넌트 작성 규칙

#### 1. 재사용 가능하게 설계
```tsx
// ✅ GOOD: props로 제어 가능
interface TaskCardProps {
  task: Task;
  onEdit?: (task: Task) => void;
  readOnly?: boolean;
}

export function TaskCard({ task, onEdit, readOnly = false }: TaskCardProps) {
  return (
    <Card>
      <h3>{task.title}</h3>
      {!readOnly && <Button onClick={() => onEdit?.(task)}>Edit</Button>}
    </Card>
  );
}

// ❌ BAD: 하드코딩, 재사용 불가
export function TaskCard() {
  const task = tasks[0]; // 하드코딩
  return <Card>...</Card>;
}
```

#### 2. 커스텀 훅으로 로직 분리
```tsx
// hooks/useWeekTasks.ts
export function useWeekTasks(weekStart: Date) {
  return useQuery({
    queryKey: ['tasks', 'week', weekStart],
    queryFn: () => api.tasks.getWeek(weekStart),
  });
}

// 컴포넌트에서 사용
function MyWeek() {
  const { data: tasks } = useWeekTasks(startOfWeek(new Date()));
  // ...
}
```

#### 3. 상수는 별도 파일로
```tsx
// constants/taskStatus.ts
export const TASK_STATUS = {
  TODO: 'todo',
  DOING: 'doing',
  DONE: 'done',
  BLOCKED: 'blocked',
} as const;

export const TASK_STATUS_LABELS: Record<TaskStatus, string> = {
  todo: 'To Do',
  doing: 'In Progress',
  done: 'Done',
  blocked: 'Blocked',
};

// ❌ BAD: 컴포넌트에서 직접 하드코딩
{status === 'todo' && <Badge>To Do</Badge>}

// ✅ GOOD: 상수 사용
{status === TASK_STATUS.TODO && <Badge>{TASK_STATUS_LABELS[status]}</Badge>}
```

### API 클라이언트 (중앙화)

```tsx
// services/api.ts - 한 곳에서 모든 API 관리
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
});

export const api = {
  tasks: {
    getWeek: (weekStart: Date) =>
      apiClient.get<Task[]>('/tasks/week', { params: { week_start: weekStart } }),
    getById: (id: string) =>
      apiClient.get<Task>(`/tasks/${id}`),
    update: (id: string, data: Partial<Task>) =>
      apiClient.put<Task>(`/tasks/${id}`, data),
  },
  projects: {
    // ...
  },
};

// ❌ BAD: 컴포넌트마다 axios 직접 호출
fetch('/api/tasks/week?week_start=...')
```

### 타입 정의

```tsx
// types/task.ts - 공통 타입
export interface Task {
  id: string;
  title: string;
  status: TaskStatus;
  due_date: string | null;
  project: Project;
}

export type TaskStatus = 'todo' | 'doing' | 'done' | 'blocked';

// types/api.ts - API 응답 타입
export interface ApiResponse<T> {
  data: T;
  message?: string;
}
```

### 스타일링 규칙

```tsx
// ✅ GOOD: Tailwind 유틸리티 + shadcn/ui 재사용
import { cn } from '@/lib/utils';

<Card className={cn(
  "p-4 hover:shadow-lg transition-shadow",
  isSelected && "border-primary"
)}>

// ❌ BAD: 인라인 스타일, 하드코딩
<div style={{ padding: '16px', border: isSelected ? '1px solid blue' : '' }}>
```

---

## 공통 패턴

### 날짜 처리 (통일)
```tsx
// utils/date.ts - 공통 함수
import { startOfWeek, endOfWeek, format } from 'date-fns';

export const getWeekRange = (date: Date) => ({
  start: startOfWeek(date, { weekStartsOn: 1 }), // 월요일 시작
  end: endOfWeek(date, { weekStartsOn: 1 }),
});

export const formatDate = (date: Date) => format(date, 'yyyy-MM-dd');

// ❌ BAD: 컴포넌트마다 다른 방식으로 날짜 처리
```

### 권한 체크 (통일)
```tsx
// hooks/usePermission.ts
export function usePermission(resource: string, action: string) {
  const { user } = useAuth();
  return user.permissions.includes(`${resource}:${action}`);
}

// 사용
function TaskEditButton({ task }: Props) {
  const canEdit = usePermission('task', 'write');
  if (!canEdit) return null;
  return <Button>Edit</Button>;
}
```

---

## 금지 사항 (절대 금지!)

### Backend
- ❌ 라우터에 비즈니스 로직 작성
- ❌ 직접 SQL 쿼리 (ORM 사용)
- ❌ `SELECT *` 사용 (필요한 컬럼만)
- ❌ 에러 메시지에 민감 정보 포함
- ❌ 비밀번호 평문 저장

### Frontend
- ❌ `any` 타입 사용
- ❌ 컴포넌트에서 직접 API 호출 (커스텀 훅 사용)
- ❌ 하드코딩된 URL, 상수
- ❌ 인라인 스타일 (Tailwind 사용)
- ❌ props drilling (Context/Zustand 사용)

### 공통
- ❌ 같은 코드 2번 이상 반복
- ❌ console.log 커밋 (개발 시만 사용)
- ❌ 주석으로 코드 설명 (코드 자체가 명확해야 함)
- ❌ 매직 넘버 (상수로 정의)

---

## 네이밍 컨벤션

### Backend (Python)
- 파일/모듈: `snake_case` (task_service.py)
- 클래스: `PascalCase` (TaskService)
- 함수/변수: `snake_case` (get_week_tasks)
- 상수: `UPPER_SNAKE_CASE` (MAX_TASKS_PER_PAGE)

### Frontend (TypeScript)
- 파일: `PascalCase` (TaskCard.tsx) - 컴포넌트
- 파일: `camelCase` (useWeekTasks.ts) - 훅, 유틸
- 컴포넌트: `PascalCase` (TaskCard)
- 함수/변수: `camelCase` (getWeekTasks)
- 상수: `UPPER_SNAKE_CASE` (API_BASE_URL)
- 타입/인터페이스: `PascalCase` (Task, TaskStatus)

---

## 코딩 시작 전 체크리스트

- [ ] 이미 비슷한 기능이 있는지 확인
- [ ] 재사용 가능한 컴포넌트/함수로 만들 수 있는지 고민
- [ ] 하드코딩 하려는 값이 있다면 constants로
- [ ] 타입 정의 먼저 (types 파일에)
- [ ] 2번 이상 쓸 코드라면 즉시 분리

---

## 참고

이 문서는 프로젝트가 성장하면서 계속 업데이트됩니다.
새로운 패턴이나 규칙이 생기면 즉시 추가하세요.
