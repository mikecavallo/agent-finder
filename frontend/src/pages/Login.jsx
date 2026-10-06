import { ShieldCheck } from 'lucide-react';
import { useState } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import useAuth from '../hooks/useAuth';
import { useHealth } from '../hooks/useCandidates';
import { errorMessage } from '../utils/api';

const inputClass =
  'mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500';

const Login = () => {
  const [mode, setMode] = useState('login');
  const [form, setForm] = useState({ username: '', email: '', password: '' });
  const [error, setError] = useState(null);
  const [notice, setNotice] = useState(null);
  const [busy, setBusy] = useState(false);
  const { login, register, status } = useAuth();
  const { data: health } = useHealth();
  const navigate = useNavigate();

  if (status === 'authenticated') return <Navigate to="/" replace />;

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setNotice(null);
    setBusy(true);
    try {
      if (mode === 'register') {
        await register(form.username, form.email, form.password);
        setNotice('Account created. Signing you in…');
      }
      await login(form.username, form.password);
      navigate('/');
    } catch (err) {
      setError(errorMessage(err, mode === 'login' ? 'Invalid username or password.' : 'Registration failed.'));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="mb-6 text-center">
          <ShieldCheck className="mx-auto h-10 w-10 text-indigo-600" aria-hidden="true" />
          <h1 className="mt-2 text-2xl font-semibold text-slate-900">Agent Finder</h1>
          <p className="mt-1 text-sm text-slate-600">AI resume screening for insurance agency hiring</p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="mb-5 grid grid-cols-2 rounded-lg bg-slate-100 p-1 text-sm">
            {['login', 'register'].map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => setMode(m)}
                className={`rounded-md py-1.5 font-medium ${mode === m ? 'bg-white shadow text-slate-900' : 'text-slate-600'}`}
              >
                {m === 'login' ? 'Sign in' : 'Create account'}
              </button>
            ))}
          </div>
          <form onSubmit={handleSubmit} className="space-y-4">
            <label className="block text-sm font-medium text-slate-700">
              Username
              <input className={inputClass} value={form.username} onChange={update('username')} autoComplete="username" required />
            </label>
            {mode === 'register' && (
              <label className="block text-sm font-medium text-slate-700">
                Email
                <input type="email" className={inputClass} value={form.email} onChange={update('email')} autoComplete="email" required />
              </label>
            )}
            <label className="block text-sm font-medium text-slate-700">
              Password
              <input
                type="password"
                className={inputClass}
                value={form.password}
                onChange={update('password')}
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                minLength={mode === 'register' ? 8 : undefined}
                required
              />
            </label>
            {error && <p className="text-sm text-rose-600">{error}</p>}
            {notice && <p className="text-sm text-emerald-700">{notice}</p>}
            <button
              type="submit"
              disabled={busy}
              className="w-full rounded-md bg-indigo-600 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-60"
            >
              {busy ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Create account'}
            </button>
          </form>
          {health?.demo_mode && mode === 'login' && (
            <div className="mt-5 rounded-md bg-slate-50 p-3 text-xs text-slate-600">
              Demo mode is on. Sign in with <code className="font-semibold">demo</code> /{' '}
              <code className="font-semibold">demo-password</code> to explore a sample opening with fictional resumes.
              <button
                type="button"
                className="ml-1 font-semibold text-indigo-600 hover:underline"
                onClick={() => setForm({ ...form, username: 'demo', password: 'demo-password' })}
              >
                Fill in
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Login;
