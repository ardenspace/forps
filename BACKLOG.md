## 목적
이 문서는 MVP를 구현 가능한 작업 단위로 쪼개고, 각 항목의 Acceptance Criteria(완료 조건)를 정의한다.

## Epic 0 — 프로젝트 골격/표준
### Story 0.1 — 표준 응답/에러 규격 적용
- AC
  - 성공 응답이 일관된 형태를 갖는다(예: data/message).
  - 에러 응답이 일관된 형태를 갖는다(예: detail/code).
  - 권한 에러/인증 에러가 명확히 구분된다.

## Epic 1 — 인증(Auth)
### Story 1.1 — 회원가입
- AC
  - 이메일/비밀번호로 가입 가능
  - 중복 가입 방지
  - 가입 후 로그인 가능

### Story 1.2 — 로그인/세션
- AC
  - 로그인 성공 시 토큰 발급 및 프론트 저장
  - 보호 라우트에서 미인증 시 로그인으로 리다이렉트
  - /me로 현재 사용자 확인 가능

## Epic 2 — 프로젝트/기본 데이터
### Story 2.1 — 프로젝트 생성/조회
- AC
  - 로그인 사용자가 프로젝트를 생성할 수 있다
  - 프로젝트 리스트를 조회할 수 있다
  - 프로젝트가 없을 때의 빈 상태 UI가 있다

(워크스페이스를 MVP에서 명시적으로 다루지 않으면: “기본 워크스페이스 자동 할당” 같은 단순 정책을 DECISIONS에 기록)

## Epic 3 — 태스크(Task) 핵심 수직 슬라이스
### Story 3.1 — 태스크 생성
- AC
  - 프로젝트에서 태스크 생성 가능(title 필수)
  - default: status=todo, assignee=생성자
  - 생성 후 Board에 즉시 표시

### Story 3.2 — 태스크 목록 조회(프로젝트 단위)
- AC
  - 프로젝트 id로 태스크 조회 가능
  - 응답에 status/assignee/due_date 포함
  - “내 태스크만” 필터를 지원(서버/클라 중 한 방식으로 고정)

### Story 3.3 — 상태 변경(드롭다운/버튼)
- AC
  - todo/doing/done/blocked로 변경 가능
  - Viewer는 변경 불가(서버에서 차단 + UI도 비활성)
  - 변경 즉시 Board에서 컬럼 이동 반영

### Story 3.4 — TaskEvent 기록
- AC
  - 태스크 생성 시 task.created 이벤트가 1건 기록된다
  - 상태 변경 시 task.status_changed 이벤트가 1건 기록된다(from/to 포함)
  - 이벤트 누락이 없고, 실패 시 전체 트랜잭션 처리가 일관된다(정책은 구현에서 결정)

## Epic 4 — UI: Dashboard(Board 메인)
### Story 4.1 — Board 화면(4컬럼) 렌더
- AC
  - 4컬럼(todo/doing/done/blocked)이 보인다
  - 태스크가 컬럼별로 그룹핑되어 렌더링된다
  - 태스크 0개일 때 빈 상태가 있다

### Story 4.2 — 내 태스크만 토글/필터
- AC
  - 토글 on 시 assignee=current_user만 보인다
  - 토글 off 시 전체가 보인다
  - 상태 변경/생성 후에도 필터 동작이 일관된다

### Story 4.3 — 태스크 상세(모달/패널) + 최소 편집
- AC
  - 카드 클릭 시 상세가 열린다
  - (Editor 이상) 상태 변경 UI가 있다
  - (Viewer) 읽기 전용 UI만 보이고 편집 불가

## Epic 5 — Week(보조 탭)
### Story 5.1 — Week 탭 조회
- AC
  - 동일 태스크를 주간 기준으로 표시한다(week_start=월요일)
  - due_date가 없는 태스크 처리 규칙이 문서화되어 있다(표시/숨김/별도 그룹 중 택1)
  - “내 태스크만” 토글이 일관되게 동작한다

## Epic 6 — 공유 링크(External Viewer)
### Story 6.1 — 공유 링크 생성/철회
- AC
  - 권한자만 생성 가능(Owner만 또는 Editor 포함 여부는 DECISIONS 따름)
  - 링크를 복사할 수 있다
  - 철회 시 기존 링크는 더 이상 접근 불가

### Story 6.2 — /share/:token read-only Board
- AC
  - 로그인 없이 접근 가능
  - Board가 read-only로 렌더링된다(편집 UI 없음)
  - 잘못된/철회된 토큰은 명확한 에러 화면을 보여준다

## 릴리즈 플랜(권장 순서)
- (1) Auth + Project + Task(생성/조회/상태변경) + Board 메인
- (2) 권한(Viewer read-only) 완성도 올리기 + TaskEvent 기록
- (3) ShareLink + /share 뷰
- (4) Week 보조 탭