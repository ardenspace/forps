# Handoff: main — @ardensdevspace

## 2026-04-28

- [x] **Phase 1 완료** — forps 본체 alembic 마이그레이션 + pytest 인프라 (브랜치 `feature/phase-1-models-migrations`)
  - [x] 테스트 인프라: pytest 8.3.4 + pytest-asyncio + testcontainers[postgres] (Docker로 PG 16 띄움) + psycopg, async DB fixture, 격리 패턴 (function-scope CREATE/DROP per-test DB)
  - [x] enum 확장: TaskSource, LogLevel, ErrorGroupStatus, TaskEventAction +4값 (모두 대문자 NAME 박힘 — SQLAlchemy 기본 + 기존 `taskstatus` 패턴 일관)
  - [x] Project +6 필드 (git_repo_url, git_default_branch, plan_path, handoff_dir, last_synced_commit_sha, webhook_secret_encrypted) + CHECK 40자 hex on last_synced_commit_sha
  - [x] Task +4 필드 (source, external_id, last_commit_sha, archived_at) + UNIQUE 부분 인덱스 + CHECK 40자 hex on last_commit_sha
  - [x] 신규 모델 6개: Handoff, GitPushEvent, LogIngestToken, RateLimitWindow (composite PK), ErrorGroup, LogEvent (각 모델 정의 + 모든 SHA 컬럼에 CHECK 제약)
  - [x] pg_trgm extension + log_events 일별 파티션 (PARTITION BY RANGE received_at, PK (id, received_at)) + 다음 30일 pre-create
  - [x] 인덱스 5종 (project_level_received / fingerprint partial / version_sha / unfingerprinted partial / message gin_trgm_ops partial)
  - [x] 단일 alembic revision (`c4dee7f06004_phase1_logs_handoffs_git`)
  - [x] 회귀 테스트: 기존 데이터 보존, alembic up/down roundtrip, CHECK/UNIQUE 동작, ORM round-trip enum, 파티셔닝 검증
  - [x] env.py에 신규 6 모델 import (autogenerate 함정 회피)
  - [x] **41 tests passing** (3 smoke + 3 enum + 4 모델 검증 + 14 신규 모델 + 6 constraint + 4 migration + 3 partitioning + 1 ORM round-trip + 3 기존)

### 마지막 커밋

- forps: `27352db test+fix(phase1): final review fixups (test_partitioning, env.py imports, ORM round-trip)` (브랜치 `feature/phase-1-models-migrations`)
- 브랜치 base: `2d374e9 chore: .worktrees/ 디렉토리 ignore` (main)
- 머지 전 PR 생성 + 사용자 검토 단계

### 다음 (Phase 2 — Webhook 수신만)

- [ ] `POST /api/v1/webhooks/github` endpoint
- [ ] 서명 검증 (프로젝트별 secret, Fernet 복호화)
- [ ] GitPushEvent INSERT 만 (처리 로직 X — Phase 4에서 sync_service)
- [ ] push_event_reaper 부팅 hook (`processed_at IS NULL AND received_at < now() - 5min` 회수)
- [ ] commits_truncated 플래그 처리 (length == 20)

### 블로커

없음

### 메모 (2026-04-28 추가)

- **Subagent-Driven Development 페이스**: 14 task를 묶음 처리 (Task 2-3 / 4-6 / 7-9 / 10-11 / 12 / 13). 단순 모델 정의는 한 implementer에 batch dispatch + spec/quality 묶음 review. 토큰/시간 효율 좋음 (개별 dispatch 대비 ~1/3).
- **enum 케이스 결정**: SQLAlchemy 2.0 + `class Foo(str, enum.Enum): MANUAL = "manual"` 매핑은 DB에 enum **NAME** (대문자) 박음. value 아님. 기존 `taskstatus`/`taskeventaction`이 대문자로 박혀있어서 이 패턴 일관 유지. ORM round-trip 테스트로 검증 완료.
- **`mapped_column(default=X)` Python init-time 미적용**: SQLAlchemy 2.0 `default=`는 INSERT 시점만 주입. Python `__init__` 시점엔 None. 우리 default 검증 테스트(Project/Task/LogIngestToken/ErrorGroup) 통과 위해 `__init__` override 패턴 추가 (`kwargs.setdefault`). plan 작성 시 SQLAlchemy 의미 혼동했던 부분 — 후속 plan 작성 시 주의.
- **pg_partman 미도입**: 30일 pre-create 만. Phase 7 진입 시 일별 자동 GC 도입.
- **Python 3.12.13 venv (homebrew python@3.12)**: 맥미니에 처음 forps 백엔드 셋업. `backend/runtime.txt` 의 `python-3.12.12` 와 정합. `requirements.txt` 핀 그대로 (pydantic 2.5.3 + sqlalchemy 2.0.25 등). Python 3.14 시도 시 pydantic-core/greenlet 빌드 실패 — 3.12 권장.
- **Phase 2 진입 전 Fernet 마스터 키 환경변수**: `FORPS_FERNET_KEY` 셋업 필요 (webhook_secret_encrypted 복호화).
- **task-automation Phase 4 안정화 후** error-log Phase 2(ingest endpoint) 진입 가능 (선행 의존: Handoff/Task의 commit_sha join key 안정 필요).

---

## 2026-04-27

- [x] 두 설계서 + 어제 handoff 파일 git 커밋 (forps `7f7f692`)
- [x] 두 설계서 교차 일관성 보강 — Plan 에이전트 독립 리뷰 후 4개 warning 패치
  - [x] error-log §5.4 wire format 명세 추가 (요청 헤더 + JSON 본문)
  - [x] error-log §4.2 archived task의 git 컨텍스트 join 정책 명시
  - [x] task-automation `commit_sha`/`last_commit_sha` 40자 hex full 계약 명시 + Decision Log 항목 (Phase 1 alembic CHECK 제약 대상)
  - [x] task-automation §13 Open Q #6 — Brief single-flight lock workers=1 가정 + 다중 워커 승격 경로
- [x] **Phase 0 완료 (app-chak 레포)** — PR #1 머지
  - [x] `CLAUDE.md` `## forps 연동 규칙` 섹션
  - [x] `PLAN.md` 초안 (첫 마스터 태스크 = forps 연동 자체, 5/2~5/3 기획 회의 후 추가)
  - [x] `handoffs/README.md` + 본 브랜치 handoff
  - [x] `Dockerfile` + `docker-compose.yml` `APP_VERSION_SHA` build arg 주입
  - [x] `backend/app/utils/forps_log_handler.py` — `PIIFilter` + `ForpsHandler` (배치 큐 / gzip / Bearer / 5xx exponential backoff / 4xx silent drop / 큐 한도 1000건·5MB / `X-Forps-Dropped-Since-Last` 헤더 / atexit 5초)
  - [x] `configure_logging()` 확장 + `main.py` 에서 settings 의 모든 비밀 키를 PIIFilter `exact_secrets` 로 전달
  - [x] 단위 테스트 27개, 전체 backend 127/127 통과 회귀 없음

### 마지막 커밋

- forps: `7f7f692 docs: 에러 로그 설계서 + 두 설계서 교차 일관성 보강` (origin/main)
- app-chak: PR #1 머지 — `feat: forps 에러 로그 핸들러 + 연동 인프라 (Phase 0)` (origin/main)

### 다음 (Phase 1 — forps 본체 alembic 마이그레이션)

- [ ] 신규 테이블 모델
  - [ ] `LogEvent` (PostgreSQL 일별 range partition + DROP PARTITION GC)
  - [ ] `ErrorGroup` (status enum: OPEN/RESOLVED/IGNORED/REGRESSED)
  - [ ] `LogIngestToken` (`<key_id>.<secret>` 포맷, bcrypt secret_hash)
  - [ ] `RateLimitWindow` (PostgreSQL UPSERT 기반)
  - [ ] `Handoff` (project_id, branch, commit_sha UNIQUE)
  - [ ] `GitPushEvent`
- [ ] 기존 모델 확장
  - [ ] `Task` 4 필드 추가: `source`, `external_id`, `last_commit_sha`, `archived_at`
  - [ ] `Project` Git-aware 필드 추가 (`repo_url`, `handoff_dir`, `last_synced_commit_sha`, `webhook_secret_encrypted`)
  - [ ] `external_id` UNIQUE 부분 인덱스
- [ ] CHECK 제약: `commit_sha ~ '^[0-9a-f]{40}$' OR commit_sha IS NULL` (Decision Log 2026-04-26 Rev2)
- [ ] 마이그레이션 회귀 테스트 (CRITICAL — 기존 데이터 무손실)

### 블로커

없음

### 메모 (2026-04-27 추가)

- **archived task join 정책 (PR 리뷰 결정)**: `Task.archived_at IS NOT NULL` row 도 LogEvent git 컨텍스트 join 에 포함, UI 에서 `(archived)` 배지 — Phase 4 GitContextPanel 구현 시 반영.
- **app-chak self-hosted runner Docker 이슈**: `~/.docker/config.json` 의 `credsStore: "desktop"` 가 비대화형 launchd 세션에서 keychain unlock 실패. 제거 + URL inline `x-access-token:$GITHUB_TOKEN` 으로 우회. forps 본체도 self-hosted runner 가면 동일 함정 — 운영 노트 참고.
- **forps_log_handler `exact_secrets` 패턴**: app-chak 은 `JWT_SECRET_KEY` + Google/Kakao/OpenWeather/Solar/Places API 키 6종을 통째로 PIIFilter 에 넣음. forps 본체도 동일 패턴 적용 권고.
- **forps 측 ingest endpoint** (`/api/v1/log-ingest`) 미구현 상태 — app-chak 은 `FORPS_LOG_ENDPOINT` 비워둬서 핸들러 자동 비활성. Phase 2 진입 후 e2e 검증.
- **2026-05-02~03 주말 확장 기획 회의** — 회의 후 app-chak `PLAN.md` 에 마스터 태스크 추가, forps 측에서 sync 동작 실제 테스트 가능.

---

## 2026-04-26

- [x] AI 태스크 자동화 설계서 v2 (`docs/superpowers/specs/2026-04-26-ai-task-automation-design.md`)
  - [x] 그래뉼래리티 분리 (마스터 = 0.5~3일, handoff 서브 체크박스 = 자유 영역)
  - [x] Task 상태 모델 통합 (`status` enum 재사용, 별도 `checked_at` 신설 X)
  - [x] `TaskEventAction` enum 확장 4종
  - [x] `Task.archived_at` (PLAN 삭제 soft-delete)
  - [x] `external_id` 프로젝트 내 UNIQUE 제약
  - [x] `Project.webhook_secret_encrypted` per-project (Fernet)
  - [x] Background task 부팅 reaper
  - [x] Webhook commits 길이>20 fallback (Compare API)
  - [x] handoff 누락 정책 강화 (silent → 항상 가시화)
  - [x] Phase 0 (app-chak 선행 작업) 분리
  - [x] 마이그레이션 회귀 테스트 CRITICAL

- [x] 에러 로그 + Git 상관관계 설계서 v3 (`docs/superpowers/specs/2026-04-26-error-log-design.md`)
  - [x] `LogEvent.fingerprinted_at` + 부팅 reaper
  - [x] `version_sha` 형식 검증 + `unknown` 비율 헬스체크
  - [x] 토큰 포맷 `<key_id>.<secret>` (bcrypt hot path 회피)
  - [x] `RateLimitWindow` PostgreSQL UPSERT (다중 워커 정확)
  - [x] PostgreSQL 일별 range partition + `DROP PARTITION` GC
  - [x] `ErrorGroup` status 전이 ASCII 다이어그램
  - [x] 알림 cooldown 3종 (신규/spike/regression)
  - [x] 핸들러 forps 다운 정책 (큐 1000건/5MB, backoff, atexit, drop_count 헤더)
  - [x] `pg_trgm` 풀텍스트 검색 Phase 5 격상
  - [x] 핸들러 배포 방식 결정 (app-chak 레포 직접 복사)

### 마지막 커밋

아직 커밋 X — 두 설계서 + 본 handoff 파일이 untracked 상태.
직전 main HEAD: `3daf363 refactor: 사용하지 않는 agents 파일 정리`

### 다음 (내일 이어서)

- [ ] 두 설계서 + handoff 파일 git 커밋
- [ ] **Phase 0 시작 (app-chak 레포 측)** — `/Users/arden/Documents/ardensdevspace/app-chak/`
  - [ ] `CLAUDE.md`에 forps 연동 규칙 추가 (task-automation §11.1)
  - [ ] 초기 `PLAN.md` 작성 (마스터 태스크 목록, 골디락스 룰 0.5~3일 적용)
  - [ ] `handoffs/` 디렉토리 + 사용 가이드 README
  - [ ] `APP_VERSION_SHA` 환경변수 주입 메커니즘 (Docker build arg)
  - [ ] `backend/app/utils/forps_log_handler.py` 단일 모듈 작성
    - [ ] `logging.Handler` 서브클래스 + 배치 큐
    - [ ] `PIIFilter` (이메일/JWT/password/Bearer 패턴)
    - [ ] HTTP backoff (1s/5s/30s/5min)
    - [ ] atexit 5초 타임아웃
    - [ ] drop_count 헤더 (`X-Forps-Dropped-Since-Last`)
- [ ] Phase 0 끝나면 forps Phase 1 (alembic 마이그레이션) 진입

### 블로커

없음

### 메모

- 두 설계서 진행 순서: **task-automation 먼저 Phase 4 안정화 → error-log 진입.** error-log는 task-automation의 `Handoff.commit_sha` / `Task.last_commit_sha`를 join key로 사용하므로 선행 의존.
- forps 운영 가정: **uvicorn `workers=1`** (맥미니 단일 머신). 다중 워커 필요해지면 spike 감지 부정확 — 운영 문서에 박아둘 것.
- PII 필터 패턴 셋은 Phase 0 시점에 app-chak 코드 실제로 보고 확정 (현재 미정).
- 두 문서 모두 한국어, 14개 섹션 구조, Decision Log로 끝나는 동일 포맷 유지.
- `/plan-eng-review` 2회 거치며 발견된 가장 큰 함정: **task-automation에서 잡은 reaper 패턴을 error-log 초안에서 또 빼먹었음.** 새 백그라운드 작업 추가할 때마다 reaper 체크리스트화 필요.
