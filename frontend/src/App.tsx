function App() {
  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto p-8">
        <div className="space-y-8">
          <div>
            <h1 className="text-4xl font-bold text-foreground">for-ps</h1>
            <p className="text-muted-foreground mt-2">
              B2B 협업 업무 관리 툴
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <div className="rounded-lg border bg-card p-6 shadow-sm">
              <h3 className="font-semibold text-card-foreground">
                프로젝트 관리
              </h3>
              <p className="mt-2 text-sm text-muted-foreground">
                워크스페이스와 프로젝트를 체계적으로 관리하세요
              </p>
            </div>

            <div className="rounded-lg border bg-card p-6 shadow-sm">
              <h3 className="font-semibold text-card-foreground">
                태스크 추적
              </h3>
              <p className="mt-2 text-sm text-muted-foreground">
                To do, Doing, Done 상태로 업무를 추적하세요
              </p>
            </div>

            <div className="rounded-lg border bg-card p-6 shadow-sm">
              <h3 className="font-semibold text-card-foreground">
                권한 관리
              </h3>
              <p className="mt-2 text-sm text-muted-foreground">
                Owner, Editor, Viewer 역할로 접근 제어
              </p>
            </div>
          </div>

          <div className="rounded-lg border-2 border-dashed p-8 text-center">
            <p className="text-sm text-muted-foreground">
              🎨 tweakcn에서 테마를 선택하고 CSS 변수를 index.css에 적용하세요!
            </p>
            <p className="mt-2 text-xs text-muted-foreground">
              bold tech / cosmic night / soft pop
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
