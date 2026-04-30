# Handoff: main — @ardensdevspace

## 2026-04-30 (Phase 5a)

- [x] **Phase 5a 완료** — Backend endpoints + 자동 webhook 등록 (브랜치 `feature/phase-5a-backend-endpoints`)
  - [x] `GitPushEvent.before_commit_sha` 컬럼 + CHECK 제약 (alembic `a1b2c3d4e5f6`, vanity SHA 수동 작성). `record_push_event` 가 payload.before 저장 (40자 hex 만), `sync_service._collect_changed_files` 가 base 우선 사용 (priority chain: before → last_synced → commits[-1] → head). `0*40` null-sha 는 skip (I-5 fix).
  - [x] `GET /api/v1/projects/{id}/git-settings` (멤버) — `git_repo_url / plan_path / handoff_dir / last_synced_commit_sha / has_webhook_secret / has_github_pat / public_webhook_url`. 평문 secret 절대 노출 안 함 (raw_text assertion 으로 검증).
  - [x] `PATCH /api/v1/projects/{id}/git-settings` (OWNER) — 부분 갱신, github_pat 입력 시 즉시 Fernet encrypt + `extra="forbid"` 스키마.
  - [x] `POST /api/v1/projects/{id}/git-settings/webhook` (OWNER) — `github_hook_service.list_hooks/create_hook/update_hook` (admin:repo_hook 권한 사용). 같은 callback url 의 hook 매칭 시 PATCH (secret rotate), 없으면 POST. URL 매칭은 lowercase + trailing `/` strip (I-3 fix). `_raise_for_status` 가 Authorization 헤더 sanitize (I-1 fix — PAT exc.request.headers leak 차단).
  - [x] `GET /api/v1/projects/{id}/handoffs?branch=...&limit=...` (멤버) — pushed_at desc, raw_content 제외, limit clamp 1~200.
  - [x] `POST /api/v1/projects/{id}/git-events/{event_id}/reprocess` (OWNER) — 처리 실패 이벤트 reset + Phase 4 의 `_run_sync_in_new_session` BackgroundTask 재호출.
  - [x] `forps_public_url` settings + `.env` (기본값 `http://localhost:8000` — prod 는 Cloudflare Tunnel URL).
  - [x] code review (opus) APPROVED — fixed I-1/I-3/I-5 + missing 404 tests. **169 tests passing** (Phase 1+2+3+4 137 + Phase 5a 32).

### 마지막 커밋

- forps: `<sha> docs(handoff): Phase 5a 완료 + Phase 5b 다음 할 일`
- 브랜치 base: `44590c6` (main, Phase 4 머지 직후)

### 다음 (Phase 5b — Frontend UI)

- [ ] `frontend/src/services/githubApi.ts` — git-settings / handoffs / reprocess axios 호출 (Phase 5a endpoint 호출)
- [ ] `frontend/src/hooks/useGithubSettings.ts` — TanStack Query 훅 (GET 캐시 + PATCH/POST mutation)
- [ ] `frontend/src/pages/ProjectGitSettings.tsx` — repo URL / PAT / plan_path / handoff_dir 입력 폼 + "Webhook 등록" / "재등록" 버튼. PAT 발급 가이드 (admin:repo_hook 스코프).
- [ ] `frontend/src/pages/HandoffHistory.tsx` — 브랜치별 이력 + 재처리 버튼 (sync 실패 이벤트)
- [ ] `frontend/src/components/TaskCard.tsx` 수정 — `source` 배지 (`MANUAL` / `SYNCED_FROM_PLAN`) + handoff 누락 ⚠️ 표시. **데이터 정의 필요** (Phase 5b 진입 시 결정).
- [ ] dev server (vite) + 브라우저 수동 검증

### 블로커

없음

### 메모 (2026-04-30 Phase 5a 추가)

- **`forps_public_url` 기본값 localhost**: prod 배포 시 Cloudflare Tunnel URL 로 환경변수 override 필수. 자동 webhook 등록이 localhost 로 callback 등록하면 GitHub 이 호출 못 함 — 수동 e2e 검증 시 주의.
- **PAT 권한 범위**: GitHub PAT 는 `admin:repo_hook` 스코프 필요 (자동 webhook 등록용). Phase 5b ProjectGitSettings UI 에 도움말 텍스트 필수.
- **webhook 자동 등록 = secret rotate**: 매 호출마다 새 secret 생성. 기존 hook 있으면 PATCH 로 secret 갱신 — UI 에서 "재등록" 버튼이 사실상 "secret rotate" 효과 임을 명시.
- **Vanity revision id `a1b2c3d4e5f6`**: 수동 작성 SHA. autogen 의 random hex 와 다른 패턴이지만 chain 정상 (`down_revision = '274c0ed55105'`). 후속 마이그레이션은 다시 autogen 으로.
- **code review followup (Phase 5b/6 트래킹)**:
  - **I-2 (concurrent webhook registration race)**: 두 OWNER 가 동시 `POST /webhook` 호출 → DB 의 webhook_secret 가 stale 될 수 있음 (call A 의 secret 이 commit 마지막에 들어가지만 GitHub side 는 call B 의 secret). 현재는 narrow window. Phase 5b UI 에서 button debounce + post-merge 에 SELECT FOR UPDATE 적용 검토.
  - **I-4 (reprocess race)**: 사용자가 in-flight sync 와 동시에 재처리 트리거 → 두 process_event 동시 실행. UNIQUE 제약이 일부 보호하지만 TaskEvent 중복 가능. Phase 5b UI 에서 "처리 중" 상태 표시 + post-merge 에 CAS 가드 검토.
  - **M-6 (last_synced_commit_sha 미사용)**: Phase 1 에서 컬럼 추가됐지만 어디서도 write 안 함. sync_service 가 처리 완료 시 update 해야 하는데 누락. Phase 5b 또는 별도 fix PR.
  - **M-10 (private import from git_repo_service)**: `github_hook_service` 가 `_auth_headers / _parse_repo / _raise_for_status` (underscore = module-private 위배) 를 import. 후속 refactor 에서 promote 또는 두 모듈 합치기 검토.

---

## 2026-04-30 (Phase 4)

- [x] **Phase 4 완료** — sync_service + git fetch (브랜치 `feature/phase-4-sync-service`)
  - [x] `Project.github_pat_encrypted` 컬럼 추가 (alembic `274c0ed55105`, Phase 1 누락분 보강) + 회귀 테스트
  - [x] `git_repo_service` — `fetch_file` (Contents API + base64 decode + 404→None) + `fetch_compare_files` (Compare API). httpx mock 으로 8 단위 테스트 (httpx.Response `_request` 누락 회피로 explicit Request + `_raise_for_status` 헬퍼 채택)
  - [x] `sync_service.process_event(db, event, *, fetch_file, fetch_compare)` — 의존 주입 / 멱등 가드 / 변경 파일 검사 (commits[*].modified ∪ added 또는 truncated 시 Compare API)
  - [x] PLAN: 신규 task INSERT (`SYNCED_FROM_PLAN`), 체크 → DONE (`CHECKED_BY_COMMIT`), 언체크 (DONE→TODO 롤백 — `UNCHECKED_BY_COMMIT`), PLAN 에서 사라진 task → `archived_at` (`ARCHIVED_FROM_PLAN`), **PLAN 에 다시 등장 → un-archive (히스토리 보존)**
  - [x] handoff: `Handoff` INSERT 1행 (UNIQUE `(project_id, commit_sha)` SAVEPOINT 멱등 — Phase 2 패턴), `parsed_tasks` / `free_notes` / `raw_content` 보존, `MalformedHandoffError` 시 `event.error` 기록
  - [x] webhook endpoint: `BackgroundTasks.add_task(_run_sync_in_new_session, event.id)` — 자체 세션 + 실제 fetcher 주입, 예외는 `logger.exception` 로 보존
  - [x] reaper callback: lifespan 에서 **이벤트마다 fresh session** 으로 sync_service 호출 (한 이벤트 poison 이 다음 이벤트로 전파 안 되게)
  - [x] **plan_parser 하드닝** (Phase 3 code review I-2/I-3): title 안의 em-dash / 백틱 / `@` 가 잘못 추출되지 않게 positional 파싱 (`_TITLE_DELIMITER_RE = " — (?=@|\`)"`)
  - [x] **code review 3-bug fix** (final review): I-1 (un-archive on PLAN re-add), I-2 (poisoned session 후 commit 실패 — `rollback` + `autoflush=False` + `event` mutate + commit), I-3 (reaper 공유 세션 → per-event session)
  - [x] **137 tests passing** (Phase 1 41 + Phase 2 32 + Phase 3 30 + Phase 4 34)

### 마지막 커밋

- forps: `<sha> docs(handoff): Phase 4 완료 + Phase 5 다음 할 일` (브랜치 `feature/phase-4-sync-service`)
- 브랜치 base: `3525a21` (main, Phase 3 머지 직후)
- 머지 전 PR 생성 + 사용자 검토 단계

### 다음 (Phase 5 — UI + 자동 webhook 등록)

- [ ] `ProjectGitSettings.tsx` — repo URL / PAT / plan_path / handoff_dir 입력 폼
- [ ] 자동 webhook 등록 (GitHub API `POST /repos/{owner}/{repo}/hooks`, 프로젝트별 secret 자동 생성)
- [ ] `TaskCard.tsx` — `source` 배지 + handoff 누락 ⚠️ 표시
- [ ] `HandoffHistory.tsx` — 브랜치별 handoff 이력
- [ ] `POST /api/v1/projects/{id}/git-events/{id}/reprocess` — 사용자 수동 재처리 (sync 실패 이벤트)
- [ ] commits_truncated base 정확화 — `GitPushEvent.before_commit_sha` 컬럼 추가 (현재 fallback `commits[-1].id` 는 head 와 동일 — 빈 diff. 실제 영향은 truncated push 가 PLAN/handoff 변경한 케이스로 한정)

### 블로커

없음

### 메모 (2026-04-30 Phase 4 추가)

- **GitHub PAT NULL 처리**: PAT 없으면 unauthenticated 호출. 공개 repo 만 가능, rate limit 60/h. app-chak 같은 private repo 에선 PAT 필수. Phase 5 UI 에서 PAT 입력 강제 유도.
- **commits_truncated base fallback**: 정확한 `before` 가 webhook payload 에 있지만 GitPushEvent 컬럼에 저장 안 함 (Phase 2 plan 누락). 본 phase 에선 `Project.last_synced_commit_sha or commits[-1].id` fallback. `commits[-1]` 은 GitHub webhook 규칙상 head 와 같아 빈 diff — Phase 5 에서 `before_commit_sha` 추가로 보강.
- **BackgroundTask vs reaper**: webhook endpoint 가 BackgroundTask 로 sync 시작 → 정상 흐름. 컨테이너 재시작 시 in-flight 손실 → reaper 가 5분 grace 후 회수. **reaper 가 sync_service.process_event 를 callback 으로 받음 — 같은 코드 경로**. processed_at 가드로 idempotent.
- **error 정책 (자동 재시도 안 함)**: sync 실패 시 `event.error` 기록 + `processed_at = now()`. 사용자 수동 재처리 endpoint 는 Phase 5. 그동안 reaper 는 `processed_at IS NULL` 만 픽업 — 자동 무한 retry 회피.
- **poisoned session 패턴**: `_apply_plan` 안에서 IntegrityError 가 나면 SQLAlchemy 가 session 을 rollback-required 상태로 마킹. 그 위에서 `event.error` 세팅 후 commit 시도 → `PendingRollbackError`. 해결: rollback → `autoflush=False` → event mutate → commit. autoflush 잠금은 commit 직전 stale state 자동 flush 회피용.
- **un-archive 정책**: spec §4.1 은 archived → re-add 케이스 명시 안 함. forps 에서는 history 보존 (TaskEvent / Comment / assignee) 위해 같은 row 의 `archived_at = None` 으로 처리. 재 INSERT 안 함. partial UNIQUE `(project_id, external_id) WHERE external_id IS NOT NULL` 가 자동으로 catch 했음 — 이걸 발견해 정책 명문화.
- **plan_parser title 파싱 변경**: `_TITLE_DELIMITER_RE = re.compile(r" — (?=@|\`)")` lookahead. title 안에 단독 ` — ` 또는 백틱 가능. assignee/path 는 delimiter 이후 영역에서만 검색. Phase 3 spec 의 §6.1 라인 형식과 호환 유지 — 13 기존 테스트 무회귀.
- **Handoff `parsed_tasks` 형식**: `[{external_id, checked, extra}]` (sections[0] 만). `free_notes = {last_commit, next, blockers, subtasks: [{parent_external_id, checked, text}]}`. 다중 날짜 history 는 `raw_content` 에 보존 — Phase 7 brief_service 가 활용.
- **Handoff UNIQUE conflict 테스트 deviation**: 원안의 "다른 GitPushEvent + 같은 head_sha" 케이스가 Phase 1 의 `uq_git_push_project_head` UNIQUE 에 막힘. 대신 Handoff row 를 미리 seed 하고 process_event 가 SAVEPOINT silent skip 하는지 직접 검증 — 더 직접적.

---

## 2026-04-30

- [x] **Phase 3 완료** — PLAN/handoff 파서 (브랜치 `feature/phase-3-parsers`)
  - [x] `ParsedPlan` / `ParsedTask` Pydantic 스키마 (`extra="forbid"`)
  - [x] `ParsedHandoff` / `HandoffSection` / `CheckItem` / `Subtask` / `FreeNotes` Pydantic 스키마
  - [x] `plan_parser_service.parse_plan()` — `## 태스크` 섹션 제한, `[task-XXX]` 형식 + `@user` + `` `path` `` 추출, `DuplicateExternalIdError` raise
  - [x] `handoff_parser_service.parse_handoff()` — 헤더 / `## YYYY-MM-DD` 섹션 / 들여쓰기 0 체크박스 / 들여쓰기 ≥ 2 서브태스크 / `### 마지막 커밋·다음·블로커` 자유 영역, `MalformedHandoffError`
  - [x] sections date desc 정렬 (sections[0] = active)
  - [x] `---` HR 구분선 처리 (실제 handoff 관례 — date 섹션간 분리자가 trailing whitespace 로 들어가지 않게)
  - [x] 알 수 없는 `### 헤더` 아래 체크박스 leak 차단 (code review I-1)
  - [x] **103 tests passing** (Phase 1 41 + Phase 2 32 + Phase 3 30: 13 plan_parser + 17 handoff_parser)

### 마지막 커밋

- forps: `<sha> docs(handoff): Phase 3 완료 + Phase 4 다음 할 일` (브랜치 `feature/phase-3-parsers`)
- 브랜치 base: `c3a2817` (main, Phase 2 머지 직후)
- 머지 전 PR 생성 + 사용자 검토 단계

### 다음 (Phase 4 — sync_service + git fetch)

- [ ] `git_repo_service` (GitHub Contents API + Compare API) — PAT Fernet 복호화 재사용
- [ ] `sync_service` — webhook → fetch → parse → DB 반영 + TaskEvent 생성
- [ ] `push_event_reaper` callback 주입 (Phase 2 stub 교체)
- [ ] 멱등성 (CRITICAL — 같은 webhook 2번 → 1번 반영)
- [ ] PLAN 에서 사라진 task → `archived_at` soft-delete
- [ ] 체크 → 언체크 (DONE → TODO 회귀) 처리
- [ ] **Phase 3 파서 하드닝 (code review I-2 / I-3)**: title 안의 em-dash 가 잘리는 문제 + assignee/path 정규식이 title 영역까지 스캔하는 문제. 위치 기반 (positional) 파싱으로 sync_service 작성과 함께 보강.

### 블로커

없음

### 메모 (2026-04-30 Phase 3 추가)

- **파서는 순수 함수**: DB / 외부 API 의존 없음 — 테스트는 testcontainers 미사용 (pytest 기본). 0.08s 만에 30 tests 완료.
- **들여쓰기 인식**: `(?:    |\t|  )+` — 스페이스 2/4 또는 탭. code review M-1 에서 3-space 들여쓰기는 silent drop 됨 지적. PLAN 작성 가이드에 들여쓰기 규약(2 또는 4 스페이스, 또는 탭) lint 추가 검토.
- **`---` HR 처리**: 실제 `handoffs/main.md` 가 date 섹션 사이에 `---` 구분선 사용 (3 occurrences). 이게 마지막 free-note 영역 (`### 블로커`) 의 raw 에 trailing 으로 따라붙어 `"없음\n\n---"` 문제 발생. `_parse_section_body` 에서 `---` 만나면 `current_free_key = None` 으로 reset.
- **알 수 없는 ### 헤더 leak (I-1 fix)**: `_FREE_NOTE_HEADERS` dict 외의 H3 (예: `### 회의록`) 가 등장하면 `current_free_key = None` 이 되어 그 아래 체크박스가 다시 `_TOP_CHECK_RE` 매칭으로 빠져 `checks` 에 leak되던 문제. `in_h3_zone` 플래그로 H3 진입 후 체크박스 매칭 차단. 회귀 테스트 추가.
- **Em-dash 전용 헤더 RE**: `_HEADER_RE` 가 `—` (U+2014) 만 허용 — `--` ASCII 허용 안 함. Phase 4 sync_service 의 에러 메시지에 명시 필요.
- **에러 분류 결정**: 형식 깨짐 라인은 skip (parsing-resilient), 결정적 fail (헤더/날짜 부재, ID 중복) 만 예외. Phase 4 sync_service 가 예외 잡아 `GitPushEvent.error` 기록.

---

## 2026-04-29

- [x] **Phase 2 완료** — webhook 수신 endpoint + 서명 검증 + reaper (브랜치 `feature/phase-2-webhook-receive`)
  - [x] Fernet 마스터 키 (`FORPS_FERNET_KEY`) + `app/core/crypto.py` (encrypt_secret / decrypt_secret / generate_webhook_secret)
  - [x] `cryptography==44.0.0` 의존성 핀
  - [x] `GitHubPushPayload` Pydantic 스키마 (6 nested models, `extra="ignore"`, `branch` property, `to_commits_json()`)
  - [x] github_webhook_service: HMAC-SHA256 (constant-time) + repo URL 정규화 매칭 (.git/trailing-slash/case 흡수) + GitPushEvent INSERT (UNIQUE 충돌 SAVEPOINT silent skip)
  - [x] commits_truncated 플래그 (len >= 20, `GITHUB_WEBHOOK_COMMITS_CAP` 상수)
  - [x] discord-summary endpoint 분리 → `app/api/v1/endpoints/discord.py` (URL 변동 없음)
  - [x] `webhooks.py`는 GitHub 전용으로 정리, `POST /api/v1/webhooks/github` 마운트
  - [x] 응답 정책: 401 (서명 실패/secret 없음), 200 (정상/unknown repo silent ACK/중복 멱등), 500 (Fernet 복호화 실패)
  - [x] `push_event_reaper` (`REAPER_GRACE = 5min`, callback pluggable — Phase 4 sync 주입), `run_reaper_once()` lifespan hook
  - [x] alembic `fileConfig(disable_existing_loggers=True)` 함정 conftest 회피 (`_reenable_app_loggers` + `caplog` autouse handler)
  - [x] **73 tests passing** (Phase 1 41 + Phase 2 신규 32: 3 crypto + 4 schema + 13 service + 8 endpoint + 4 reaper)

### 마지막 커밋

- forps: `6ed9053 feat(phase2): startup hook — reaper 1회 호출 (DB 실패 시 부팅 진행)` (브랜치 `feature/phase-2-webhook-receive`)
- 브랜치 base: `e1aa4f1` (main, Phase 1 머지 직후)
- 머지 전 PR 생성 + 사용자 검토 단계

### 다음 (Phase 3 — PLAN/handoff 파서)

- [ ] `plan_parser_service` (PLAN.md → `[{external_id, title, assignee, paths}]`, 정규식)
- [ ] `handoff_parser_service` (체크박스 + `### 마지막 커밋`/`### 다음`/`### 블로커` 자유 영역)
- [ ] 들여쓰기 0인 최상위 체크박스만 DB 반영, 들여쓰기 ≥ 2는 `free_notes.subtasks`로 보존
- [ ] `external_id` 중복 reject (PLAN 단계 + DB UNIQUE 2차 방어)
- [ ] 텍스트 입력만으로 단위 테스트 — 파일 fetch는 Phase 4

### 블로커

없음

### 메모 (2026-04-29 추가)

- **`record_push_event` SAVEPOINT 패턴**: UNIQUE 충돌 시 plan 의 flat rollback 대신 `async with db.begin_nested()` 채택. 이유: 테스트의 함수-스코프 `async_session` 이 외부 ORM 객체(`proj` 등)를 보존해야 함. flat rollback 시 `MissingGreenlet` 발생. 프로덕션은 `Depends(get_db)` 가 요청별 fresh 세션이라 둘 다 정상이지만 SAVEPOINT 가 더 일반적이고 안전함.
- **Fernet 키 회전 운영 절차 미정**: `FORPS_FERNET_KEY` 회전 시 모든 `webhook_secret_encrypted` 가 복호화 불가 → 운영 문서 별도 작성 필요. 첫 프로덕션 배포 전 잠금.
- **`InvalidToken` 핸들러**: 현재 endpoint 가 `cryptography` 직접 import. Phase 4 sync_service 진입 시 service 레이어로 wrapper 옮길지 검토 (router 가 외부 라이브러리에 직접 의존하지 않게).
- **알림 정책**: Phase 2 는 webhook 수신만. unknown repo 200 ACK 는 GitHub 재전송 방지 의도 — 운영 시 unknown repo 가 빈번하면 webhook 등록 실수 의심. log 모니터링 기준 추가 필요.
- **alembic + python logging 함정**: `alembic.ini` 의 `[loggers]` 섹션은 `disable_existing_loggers=True` 기본값 — `app.*` 로거 silent disable. 본 phase 에서 conftest 회피 추가. 후속 plan 작성 시 logging 단위 테스트는 이 패턴 주의.

---

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
