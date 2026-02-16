# 2026-02-16 Implementation Plan

## Goal

문서와 코드를 일치시키고, 현재 코드베이스에서 바로 구현 가능한 미구현 항목을 우선순위대로 완료한다.

## Scope

### Backend

1. P0 TODO 해결
   - `GET /workspaces/{workspace_id}` 멤버 검증 추가
   - `POST /workspaces/{workspace_id}/projects` 생성 권한 검증 추가
   - `DELETE /share-links/{share_link_id}` 링크 소유 프로젝트 기준 권한 검증 추가
   - `GET /projects/{project_id}`의 `task_count` 실제 값 반영

2. 누락 API 구현
   - Workspace: `PATCH /workspaces/{workspace_id}`, `DELETE /workspaces/{workspace_id}`
   - Workspace Member: `PATCH /workspaces/{workspace_id}/members/{user_id}`
   - Project: `PATCH /workspaces/{workspace_id}/projects/{project_id}`, `DELETE /workspaces/{workspace_id}/projects/{project_id}`
   - Project Member: `GET/POST/PATCH/DELETE /projects/{project_id}/members...`
   - Auth: `POST /auth/logout`

3. Week API 보완
   - `GET /tasks/week`에서 `due_date`가 없는 태스크도 반환되도록 수정

### Frontend

1. 공유 링크 관리 UI
   - 공유 링크 목록 조회
   - 공유 링크 생성
   - 공유 링크 철회
   - Owner만 UI 노출

2. 워크스페이스 멤버 UI 연결
   - 대시보드에 멤버 목록/초대 UI 연결
   - Owner만 초대/제거 UI 활성화

3. Table 뷰 구현
   - Board/Week와 동일 데이터 소스(`useTasks`) 사용
   - Task 클릭 시 기존 상세 모달 재사용

## Implementation Order

1. Backend P0 TODO 해결
2. Backend 누락 API 추가
3. Frontend API 타입/훅 확장
4. Frontend 공유 링크 + 멤버 UI 연결
5. Frontend Table 뷰 추가
6. Week API 보완 반영 확인

## Validation Plan

1. Backend
   - FastAPI import/type check (런타임 에러 없음)
   - 주요 엔드포인트 권한 시나리오 검증 (owner/editor/viewer)

2. Frontend
   - TypeScript 빌드 통과
   - 주요 화면 진입/라우팅 오류 없음

3. Regression Focus
   - 기존 로그인/보드/Week/공유 조회 동작 유지
   - 권한별 버튼 노출 규칙 유지

## Out of Scope

- 결제/Discord Webhook/외부 통합
- 테스트 프레임워크 신규 도입
- 대규모 리팩토링
