# AI 태스크 자동화 설계서 (forps)

작성일: 2026-04-26

---

## 1. 배경

forps는 현재 수동 Kanban 기반 B2B 태스크 관리 도구다. 본 기능은 forps를 그대로 유지(리팩토링 방식)하면서 다음을 추가한다:

- 외부 프로젝트(예: `app-chak`) 레포의 **PLAN.md**를 forps의 태스크 목록과 자동 동기화
- 팀원의 **git push** 이벤트로 태스크 체크 상태를 자동 갱신
- 팀원이 **다음 작업 재개 시** PLAN과 handoff 이력을 종합한 브리핑을 로컬 Gemma 4로 생성

핵심 원칙: **AI는 합성·요약·추천에만 사용**한다. 태스크 체크 같은 사실(state) 결정은 결정적 파서(마크다운/정규식)로 처리한다.

---

## 2. 사용자 시나리오

### 2.1 새 작업 시작
1. 팀원의 로컬 Claude Code가 forps API의 브리핑 endpoint를 호출
2. forps는 PLAN.md + 최근 handoff 섹션 + TaskEvent를 종합해 Gemma 4로 자연어 브리핑 생성
3. 팀원이 권한을 주면 Claude Code가 실제 코드 수정 진행

### 2.2 git push 발생 (자동 처리)
1. 팀원이 `feature/<branch>`에서 push (handoff 파일 갱신 포함)
2. GitHub → forps webhook → handoff/PLAN 파일 파싱
3. 태스크 체크 상태 갱신, Discord 알림 발송
4. 작업 이력은 Handoff/TaskEvent 테이블에 보존

### 2.3 Project 최초 git 연동
1. forps UI에서 GitHub repo URL, PLAN 경로, handoff 디렉토리 입력
2. forps가 GitHub Webhook 자동 등록
3. PLAN.md 1회 fetch → 초기 Task 일괄 생성

---

## 3. 아키텍처 결정

| 결정 | 선택 | 이유 |
|---|---|---|
| 리팩토링 vs 신규 프로젝트 | **리팩토링** | 기존 인증·권한·Project·Task·Discord 자산 재사용 |
| AI 위치 | **forps 외부(팀원의 Claude) + 내부(Gemma 4 보조)** | 결정적 파이프라인 + 합성만 AI |
| AI 모델 (forps 내부) | **로컬 Gemma 4 26B MoE (llama.cpp)** | API 비용 0, 사용자 머신에 이미 존재 |
| Git 통합 메커니즘 | **GitHub Webhook (모든 브랜치)** | 모든 push 캡처, GitHub Actions와 독립 |
| 외부 노출 | **Cloudflare Tunnel (기존 사용 중)** | 추가 인프라 불필요 |
| 계획서 형식 | **PLAN.md (마스터) + handoff-{branch}.md (팀원별 상태)** | 머지 충돌 회피 + 팀원별 분리 |
| 데이터 모델 접근법 | **Task 모델 확장(접근 2) + Project Git-aware(접근 3 일부)** | 단일 태스크 모델, UI 자연스러움 |
| 태스크 ↔ 커밋 매칭 | **handoff 체크박스 우선, 보조로 커밋 메시지 컨벤션 + 파일 경로** | 결정적, AI 의존 없음 |

---

## 4. 데이터 모델

### 4.1 기존 모델 확장

**`Project`** (4 필드 추가)
```python
git_repo_url: str | None              # "https://github.com/foo/app-chak"
git_default_branch: str = "main"
plan_path: str = "PLAN.md"
handoff_dir: str = "handoffs/"
last_synced_commit_sha: str | None
```

**`Task`** (3 필드 추가)
```python
source: TaskSource                    # "manual" | "synced_from_plan"
external_id: str | None               # "task-001"
last_commit_sha: str | None
```

기존 데이터는 모두 유효 (`source` 기본값 = `"manual"`).

### 4.2 신규 모델

**`Handoff`** — push마다 1행 INSERT
```python
id: UUID
project_id: UUID                      # FK
branch: str                           # "feature/login-redesign"
author_user_id: UUID | None           # forps User 매칭 (nullable)
author_git_login: str
commit_sha: str
pushed_at: datetime
raw_content: text                     # 파싱 전 원본 마크다운
parsed_tasks: JSON                    # [{"external_id": "task-001", "checked": true}, ...]
free_notes: JSON                      # {"last_commit": "...", "next": "...", "blockers": "..."}

UNIQUE (project_id, commit_sha)       # 멱등성
```

**`GitPushEvent`** — webhook raw 보존
```python
id: UUID
project_id: UUID
branch: str
commits: JSON                         # webhook payload의 commits 배열
pusher: str
received_at: datetime
processed_at: datetime | None
error: text | None

UNIQUE (project_id, head_commit_sha)
```

**`TaskEvent`** — 새 이벤트 타입 추가
- `task.synced_from_plan`
- `task.checked_by_commit`
- `task.unchecked_by_commit`

---

## 5. 컴포넌트 / 서비스

### 5.1 신규 백엔드 서비스

```
backend/app/services/
  github_webhook_service.py    ① 서명 검증 + GitPushEvent INSERT
  git_repo_service.py           ② 파일 fetch (GitHub API or 로컬 clone 캐시)
  plan_parser_service.py        ③ PLAN.md → 태스크 목록 (정규식)
  handoff_parser_service.py     ④ handoff-{branch}.md → 체크 상태 + 자유 영역
  sync_service.py               ⑤ 파싱 결과 → Task/Handoff DB 반영
  brief_service.py              ⑥ Gemma 4로 브리핑 생성
  ollama_client.py              ⑦ Ollama HTTP 클라이언트
```

각 서비스의 책임:

| # | 입력 | 출력 | 외부 의존 |
|---|---|---|---|
| ① | GitHub POST payload | GitPushEvent row | 없음 |
| ② | (project, sha, path) | 파일 내용 (str) | git CLI / GitHub API |
| ③ | PLAN.md 텍스트 | `[{external_id, title, assignee, paths}]` | 없음 |
| ④ | handoff 텍스트 | `{checks, free_notes}` | 없음 |
| ⑤ | webhook 이벤트 | DB 변경 + TaskEvent | ②③④ |
| ⑥ | (project, user) | 자연어 브리핑 | ⑦ |
| ⑦ | prompt | completion | Ollama HTTP |

### 5.2 신규 API 엔드포인트

```
POST   /api/v1/webhooks/github               # GitHub webhook 수신
GET    /api/v1/projects/{id}/git-settings    # 현재 git 설정 조회
PATCH  /api/v1/projects/{id}/git-settings    # repo URL, plan_path 등 수정
GET    /api/v1/projects/{id}/handoffs        # 브랜치별 handoff 이력
GET    /api/v1/projects/{id}/brief           # 작업 재개 브리핑 (Gemma 4)
POST   /api/v1/projects/{id}/git-events/{id}/reprocess  # 수동 재처리
```

### 5.3 신규 프론트엔드

```
frontend/src/
  pages/
    ProjectGitSettings.tsx
    HandoffHistory.tsx
  components/
    TaskCard.tsx                  # 기존, source 배지 추가
    DailyBriefPanel.tsx
  hooks/
    useGithubSettings.ts
    useDailyBrief.ts
  services/
    githubApi.ts
```

---

## 6. 파일 형식 규약

### 6.1 PLAN.md (스프린트 마스터, 1개)

```markdown
# 스프린트: <이름>

## 태스크

- [ ] [task-001] 로그인 UI 리뉴얼 — @alice — `frontend/screens/Login.tsx`, `frontend/components/auth/`
- [ ] [task-002] JWT 토큰 만료 처리 — @bob — `backend/auth/`
- [ ] [task-003] 알림 모달 — @charlie — `frontend/components/Notification.tsx`

## 노트
<자유 메모, forps는 무시>
```

**파싱 규칙**
- `- [ ]` / `- [x]` 체크박스 라인만 태스크로 인식
- `[task-XXX]` 형식의 ID 필수
- `@username` → assignee
- `` `path` `` (백틱) → 영향 파일/폴더
- `## 태스크` 헤더 아래 영역만 파싱, 그 외는 무시

### 6.2 handoff-{branch}.md (브랜치별, 팀원별)

위치: `app-chak/handoffs/feature-login-redesign.md` (브랜치명의 `/`는 `-`로 치환)

```markdown
# Handoff: feature/login-redesign — @alice

## 2026-04-26
- [x] task-001
- [ ] task-007 (60% 완료)

### 마지막 커밋
abc1234 — 로그인 폼 검증 로직

### 다음
- task-007 마무리 후 PR

### 블로커
없음

---

## 2026-04-25
- [x] task-001 시작
...
```

**파싱 규칙**
- 최상위 `# Handoff: <branch> — @<user>` 헤더에서 브랜치/유저 추출
- `## YYYY-MM-DD` 섹션이 일자별 단위. 최신 날짜 섹션이 active
- 각 날짜 섹션 안의 `- [x] task-XXX` / `- [ ] task-XXX` 체크박스가 forps DB에 반영
- `### 마지막 커밋`, `### 다음`, `### 블로커` 자유 영역은 Gemma 4 브리핑 컨텍스트로만 사용

### 6.3 app-chak의 CLAUDE.md 추가 규칙

```markdown
## forps 연동 규칙

### handoff 파일 갱신 (필수)
1. 작업 시작 시 `handoffs/{현재브랜치}.md` 파일 확인. 없으면 생성.
2. 작업 진행하며 해당 파일의 오늘 날짜 섹션을 갱신.
3. **git push 직전 반드시** 해당 파일에 변경사항을 commit.

### PLAN.md 작성
스프린트 시작 시 `PLAN.md`에 마스터 태스크 목록을 작성한다. 형식:
- 체크박스로 시작 (`- [ ]`)
- 태스크 ID는 `[task-NNN]`
- assignee는 `@username`
- 영향 파일은 backtick으로 감싸 명시

### 강제
- handoff 미갱신 push는 PR 머지 거부 (lint hook으로 강제 가능, 추후 도입)
```

---

## 7. 데이터 흐름

### 7.1 git push → 자동 동기화

```
[팀원] git push (handoff 갱신 포함)
   ↓
[GitHub] webhook POST /api/v1/webhooks/github
   ↓
[forps] github_webhook_service
   ├── X-Hub-Signature-256 검증
   ├── repo URL → Project 조회
   └── GitPushEvent INSERT
   ↓
[즉시 200 응답]
   ↓
[FastAPI BackgroundTask] sync_service.process(event)
   ├── git_repo_service: 변경 파일에 handoffs/* / PLAN.md 있는지 확인
   ├── handoff_parser_service.parse(content)
   ├── plan_parser_service.parse(PLAN.md) (변경됐으면)
   ├── DB 업데이트
   │   ├── Task.checked_at, Task.last_commit_sha
   │   ├── Handoff INSERT
   │   └── TaskEvent (task.checked_by_commit 등)
   ├── discord_service.notify (체크 변경 요약)
   └── GitPushEvent.processed_at = now()
```

### 7.2 작업 재개 → 브리핑

```
[팀원의 Claude Code]
   GET /api/v1/projects/{id}/brief?user=alice&branch=feature/login-redesign
   ↓
[forps] brief_service
   ├── PLAN에서 alice의 미완료 태스크
   ├── 최근 N일 handoff 섹션
   ├── 어제~오늘 TaskEvent
   └── 위 컨텍스트 → Gemma 4 프롬프트
   ↓
[Gemma 4] 자연어 브리핑 생성
   ↓
[forps] 5분 캐시 후 응답
   ↓
[Claude Code] 사용자에게 브리핑 표시 + 권한 요청
```

---

## 8. 에러 처리

| 위치 | 케이스 | 대응 |
|---|---|---|
| Webhook | 서명 검증 실패 | 401, 보안 로그 |
| Webhook | 알 수 없는 repo | 200 + 경고 로그 (재전송 방지) |
| Webhook | DB 쓰기 실패 | 500 → GitHub 자동 재시도 |
| Fetch | PLAN.md 없음 | skip + Project에 `plan_missing=true` 마킹 |
| Fetch | handoff 없음 | skip (선택적 Discord 경고) |
| Fetch | API rate limit | exponential backoff (10s/60s/300s) → 실패 시 GitPushEvent.error에 기록, 사용자 재처리 가능 |
| 파싱 | 형식 깨짐 | 파싱 가능한 부분만 처리, raw 보존, error 필드에 사유 |
| 파싱 | task ID가 PLAN에 없음 | Task 미생성, Handoff.parsed_tasks에 orphan 표시. PLAN 추가 후 다음 push 때 매칭 |
| 동기화 | 같은 task 동시 체크 | last-write-wins (commit_sha 시각 기준), 양쪽 TaskEvent 보존 |
| 동기화 | 체크 → 언체크 (롤백) | 정상 처리, Discord에 "되돌림" 알림 |
| Gemma | Ollama 다운 | fallback 텍스트 + DB raw 데이터 |
| Gemma | 타임아웃 (>30s) | 부분 응답 반환, 캐시 안 함 |
| Discord | webhook 무효 | silent (1회) → 3회 연속 실패 시 disable + UI 경고 |

**전체 원칙**
- 외부 의존(GitHub, Gemma, Discord) 실패는 forps 코어를 막지 않는다.
- 모든 push는 GitPushEvent에 raw로 보존 → 코드 수정 후 재처리 가능.
- 사용자가 UI에서 "이 push 다시 처리" 수동 트리거 가능.

---

## 9. 보안

- **Webhook 서명 검증**: `GITHUB_WEBHOOK_SECRET` 환경변수, `X-Hub-Signature-256` HMAC 검증
- **GitHub PAT**: Project별로 암호화 저장 (Fernet, 기존 forps 패턴 따름)
- **Cloudflare Tunnel**: 외부 노출은 기존 터널 재사용, 직접 IP 노출 없음
- **Ollama**: localhost(맥미니) 내부 통신만, 외부 접근 차단
- **Brief API 권한**: 호출자는 Project 멤버여야 함 (기존 permission_service 재활용)

---

## 10. 테스트 전략

### 10.1 파서 단위 테스트 (최우선)
- `plan_parser_service`: 정상 / 형식 어긋남 / 빈 파일 / 노트 영역 무시 검증
- `handoff_parser_service`: 다중 날짜 섹션, 체크박스 diff, 자유 영역 보존

### 10.2 서비스 통합 테스트
- `sync_service`: 가짜 webhook payload + 가짜 git_repo_service → DB 변경 검증
  - 멱등성: 동일 payload 두 번 → 변경 한 번만
  - 부분 실패 시 GitPushEvent 잔존

### 10.3 Gemma 모킹
- `ollama_client`를 인터페이스로, 테스트는 `FakeOllamaClient` 고정 응답
- 실제 호출은 manual smoke test로만

### 10.4 프론트 단위 테스트
- ProjectGitSettings 폼 검증
- DailyBriefPanel 렌더링 (브리핑/로딩/에러)

---

## 11. 단계적 도입 (마이그레이션)

이 설계는 한 번에 다 구현하지 않는다. 단계 분할:

**Phase 1 — 모델/마이그레이션**
- alembic revision: Project/Task 필드 추가, Handoff/GitPushEvent 테이블 신설
- 기존 데이터 무결성 검증 (`source="manual"` 기본값)

**Phase 2 — Webhook 수신만**
- `/webhooks/github` endpoint
- 서명 검증, GitPushEvent INSERT만
- 처리 로직은 아직 없음 (raw 수신 검증)

**Phase 3 — PLAN/handoff 파서**
- `plan_parser_service`, `handoff_parser_service` 단위 테스트와 함께
- 파일 fetch 없이 텍스트 입력으로 검증 가능

**Phase 4 — 동기화**
- `git_repo_service` (GitHub Contents API 우선, 로컬 clone은 후속)
- `sync_service` 조립
- 실제 webhook → DB 반영 E2E 동작

**Phase 5 — UI (설정 페이지)**
- ProjectGitSettings — repo URL, PLAN 경로 입력
- 자동 webhook 등록 (GitHub API 호출)

**Phase 6 — Discord 알림 통합**
- 기존 discord_service 확장: 체크 변경 요약 메시지 템플릿

**Phase 7 — Gemma 브리핑 (선택)**
- `ollama_client`, `brief_service`
- DailyBriefPanel UI
- Phase 7은 핵심이 아니므로 1~6 안정화 후 도입

각 Phase는 독립적으로 머지 가능. 1~4까지가 핵심 가치 전달, 5~6는 사용성, 7은 부가가치.

---

## 12. 비범위 (Out of Scope)

다음은 본 설계에서 제외 (필요시 별도 스펙):

- **에러 로그 + Git 상관관계 (기능 #2)**: 별도 설계 문서로 분리 예정
- **forps에서 PLAN.md 직접 편집 후 git에 commit**: 단방향(읽기) 유지, 양방향 동기화 미고려
- **GitLab/Bitbucket 지원**: GitHub 우선
- **handoff 갱신 강제 lint hook**: 규칙은 CLAUDE.md에 명시하되 자동 강제는 후속
- **PR/Issue 동기화**: push 이벤트만 사용, PR 코멘트/리뷰는 미사용
- **다중 PLAN.md / 모노레포 부분 동기화**: 단일 PLAN.md만 지원

---

## 13. Open Questions

향후 구현 단계에서 확정 필요한 항목:

1. **GitHub 인증**: PAT vs GitHub App. App이 멀티 repo 권한 관리 더 깔끔하나 초기 설정 복잡.
2. **로컬 clone 캐시 위치**: 맥미니 디스크의 어느 경로에 forps가 fetch한 repo를 둘지.
3. **handoff 파일이 없는 push의 Discord 알림 정책**: 기본은 silent, 옵션으로 경고 발송.
4. **Brief API 호출자 인증**: 기존 forps JWT 재사용 vs 별도 토큰 발급.
5. **Gemma 4 프롬프트 구조**: 시스템 프롬프트 + few-shot 예제 포맷 (구현 시점에 튜닝).

---

## 14. 결정 사항 요약 (Decision Log)

- 2026-04-26: 리팩토링 방식 채택 (신규 프로젝트 X)
- 2026-04-26: PLAN + handoff 이원 파일 구조
- 2026-04-26: GitHub Webhook (모든 브랜치)
- 2026-04-26: AI = 합성/브리핑만, 결정적 동작은 파서로
- 2026-04-26: Gemma 4 26B MoE (로컬, llama.cpp) 사용
- 2026-04-26: Task 모델 확장 + Project Git-aware (접근 2+3)
- 2026-04-26: 단계적 도입 (Phase 1~7)
