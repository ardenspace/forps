import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { ROUTES } from '@/constants';

export function RegisterPage() {
  const { register, isLoading, error } = useAuth();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordError, setPasswordError] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (password !== confirmPassword) {
      setPasswordError('비밀번호가 일치하지 않습니다.');
      return;
    }

    setPasswordError('');
    register({ name, email, password });
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-yellow-50 p-3 sm:p-4">
      <div className="border-2 border-black shadow-[6px_6px_0px_0px_rgba(244,0,4,1)] sm:shadow-[8px_8px_0px_0px_rgba(244,0,4,1)] bg-white p-5 sm:p-8 w-full max-w-md">
        <div className="mb-5 sm:mb-6 text-center">
          <span className="font-black text-2xl sm:text-3xl border-b-4 border-yellow-400 pb-1">forps</span>
        </div>
        <h1 className="font-black text-xl sm:text-2xl mb-1">회원가입</h1>
        <p className="text-xs sm:text-sm text-muted-foreground mb-5 sm:mb-6">새 계정을 만들어 시작하세요</p>

        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label htmlFor="name" className="font-bold text-sm block mb-1">
                이름
              </label>
              <input
                id="name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="홍길동"
                required
                className="border-2 border-black rounded-none w-full px-3 py-2 text-sm focus:outline-none focus:shadow-[2px_2px_0px_0px_rgba(244,0,4,1)]"
              />
            </div>

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
                className="border-2 border-black rounded-none w-full px-3 py-2 text-sm focus:outline-none focus:shadow-[2px_2px_0px_0px_rgba(244,0,4,1)]"
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
                minLength={8}
                className="border-2 border-black rounded-none w-full px-3 py-2 text-sm focus:outline-none focus:shadow-[2px_2px_0px_0px_rgba(244,0,4,1)]"
              />
            </div>

            <div>
              <label htmlFor="confirmPassword" className="font-bold text-sm block mb-1">
                비밀번호 확인
              </label>
              <input
                id="confirmPassword"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••"
                required
                className="border-2 border-black rounded-none w-full px-3 py-2 text-sm focus:outline-none focus:shadow-[2px_2px_0px_0px_rgba(244,0,4,1)]"
              />
            </div>

            {(error || passwordError) && (
              <p className="text-sm font-bold text-red-600 border-2 border-red-500 bg-red-50 px-3 py-2">
                {passwordError || '회원가입에 실패했습니다. 다시 시도해주세요.'}
              </p>
            )}
          </div>

          <div className="flex flex-col gap-4 mt-6">
            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-black text-white border-2 border-black font-bold py-2 hover:bg-yellow-400 hover:text-black transition-colors shadow-[4px_4px_0px_0px_rgba(244,0,4,1)] disabled:opacity-50"
            >
              {isLoading ? '가입 중...' : '회원가입'}
            </button>

            <p className="text-center text-sm text-muted-foreground">
              이미 계정이 있으신가요?{' '}
              <Link to={ROUTES.LOGIN} className="font-bold underline hover:text-yellow-600">
                로그인
              </Link>
            </p>
          </div>
        </form>
      </div>
    </div>
  );
}
