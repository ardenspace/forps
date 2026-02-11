import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { ROUTES } from '@/constants';

export function LoginPage() {
  const { login, isLoading, error } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    login({ email, password });
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-yellow-50 p-4">
      <div className="border-2 border-black shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] bg-white p-8 w-full max-w-md">
        <div className="mb-6 text-center">
          <span className="font-black text-3xl border-b-4 border-yellow-400 pb-1">forps</span>
        </div>
        <h1 className="font-black text-2xl mb-1">로그인</h1>
        <p className="text-sm text-muted-foreground mb-6">계정에 로그인하세요</p>

        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label htmlFor="email" className="font-bold text-sm block mb-1">
                이메일
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="email@example.com"
                required
                className="border-2 border-black rounded-none w-full px-3 py-2 text-sm focus:outline-none focus:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]"
              />
            </div>

            <div>
              <label htmlFor="password" className="font-bold text-sm block mb-1">
                비밀번호
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                className="border-2 border-black rounded-none w-full px-3 py-2 text-sm focus:outline-none focus:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]"
              />
            </div>

            {error && (
              <p className="text-sm font-bold text-red-600 border-2 border-red-500 bg-red-50 px-3 py-2">
                로그인에 실패했습니다. 이메일과 비밀번호를 확인해주세요.
              </p>
            )}
          </div>

          <div className="flex flex-col gap-4 mt-6">
            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-black text-white border-2 border-black font-bold py-2 hover:bg-yellow-400 hover:text-black transition-colors shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] disabled:opacity-50"
            >
              {isLoading ? '로그인 중...' : '로그인'}
            </button>

            <p className="text-center text-sm text-muted-foreground">
              계정이 없으신가요?{' '}
              <Link to={ROUTES.REGISTER} className="font-bold underline hover:text-yellow-600">
                회원가입
              </Link>
            </p>
          </div>
        </form>
      </div>
    </div>
  );
}
