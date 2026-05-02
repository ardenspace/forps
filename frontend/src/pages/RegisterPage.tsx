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
    <div className="min-h-screen flex items-center justify-center bg-brand-cream p-4 sm:p-6 md:p-8">
      <div className="bg-white/60 backdrop-blur-xl rounded-3xl shadow-xl border border-brand-blue/10 p-6 sm:p-10 w-full max-w-md mx-auto">
        <div className="mb-6 sm:mb-8 text-center">
          <span className="font-bold text-3xl sm:text-4xl text-brand-blue border-b-4 border-brand-orange pb-1">forps</span>
        </div>
        <h1 className="font-bold text-xl sm:text-2xl mb-2 text-brand-blue">회원가입</h1>
        <p className="text-sm text-brand-blue/60 mb-6 sm:mb-8">새 계정을 만들어 시작하세요</p>

        <form onSubmit={handleSubmit}>
          <div className="space-y-5">
            <div>
              <label htmlFor="name" className="font-bold text-sm block mb-1.5 text-brand-blue">
                이름
              </label>
              <input
                id="name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="홍길동"
                required
                className="bg-white/80 border border-brand-blue/20 rounded-xl w-full px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-blue/20 transition-all text-brand-blue"
              />
            </div>

            <div>
              <label htmlFor="email" className="font-bold text-sm block mb-1.5 text-brand-blue">
                이메일
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="email@example.com"
                required
                className="bg-white/80 border border-brand-blue/20 rounded-xl w-full px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-blue/20 transition-all text-brand-blue"
              />
            </div>

            <div>
              <label htmlFor="password" className="font-bold text-sm block mb-1.5 text-brand-blue">
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
                className="bg-white/80 border border-brand-blue/20 rounded-xl w-full px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-blue/20 transition-all text-brand-blue"
              />
            </div>

            <div>
              <label htmlFor="confirmPassword" className="font-bold text-sm block mb-1.5 text-brand-blue">
                비밀번호 확인
              </label>
              <input
                id="confirmPassword"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••"
                required
                className="bg-white/80 border border-brand-blue/20 rounded-xl w-full px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-blue/20 transition-all text-brand-blue"
              />
            </div>

            {(error || passwordError) && (
              <p className="text-sm font-bold text-brand-orange border border-brand-orange/30 bg-brand-orange/10 rounded-xl px-4 py-3">
                {passwordError || '회원가입에 실패했습니다. 다시 시도해주세요.'}
              </p>
            )}
          </div>

          <div className="flex flex-col gap-4 mt-8">
            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-brand-blue text-white rounded-xl font-bold py-3 hover:bg-brand-neon hover:text-brand-blue transition-colors shadow-sm disabled:opacity-50"
            >
              {isLoading ? '가입 중...' : '회원가입'}
            </button>

            <p className="text-center text-sm text-brand-blue/70">
              이미 계정이 있으신가요?{' '}
              <Link to={ROUTES.LOGIN} className="font-bold underline hover:text-brand-orange transition-colors">
                로그인
              </Link>
            </p>
          </div>
        </form>
      </div>
    </div>
  );
}
