# Frontend Setup

## 기술 스택

- **Vite** - 빌드 도구
- **React 19** - UI 라이브러리
- **TypeScript** - 타입 안전성
- **Tailwind CSS** - 유틸리티 CSS
- **shadcn/ui** - UI 컴포넌트
- **tweakcn** - 테마 커스터마이징

## 시작하기

### 1. 패키지 설치

```bash
bun install
```

### 2. 개발 서버 실행

```bash
bun run dev
```

서버 실행 후: http://localhost:5173

## tweakcn 테마 적용하기

### 1. tweakcn 사이트 접속

https://tweakcn.com/

### 2. 테마 선택

추천 테마:
- **bold tech** - 프로페셔널한 블루 계열
- **cosmic night** - 다크 모던 느낌
- **soft pop** - 부드러운 파스텔 톤

### 3. CSS 변수 복사

1. tweakcn 사이트에서 원하는 테마 선택
2. "Copy CSS" 버튼 클릭
3. \`src/index.css\` 파일 열기
4. \`:root\`와 \`.dark\` 안의 CSS 변수들을 교체

### 4. 저장 후 자동 새로고침

Vite가 변경사항을 감지하고 자동으로 새로고침됩니다.

## shadcn/ui 컴포넌트 추가하기

```bash
# Button 컴포넌트 추가
bunx shadcn@latest add button

# 여러 컴포넌트 한번에 추가
bunx shadcn@latest add button card input label
```

## 다음 단계

- [ ] 로그인/회원가입 페이지
- [ ] 워크스페이스 선택 화면
- [ ] 프로젝트 대시보드
- [ ] 태스크 관리 (Table + Kanban 뷰)
- [ ] API 연동 (Axios)
