import { LogOut, ShieldCheck } from 'lucide-react';
import { Link, Outlet, useNavigate } from 'react-router-dom';
import { useHealth } from '../hooks/useCandidates';
import useAuth from '../hooks/useAuth';

const Layout = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { data: health } = useHealth();
  const isMock = health?.provider === 'mock';

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
          <Link to="/" className="flex items-center gap-2">
            <ShieldCheck className="h-6 w-6 text-indigo-600" aria-hidden="true" />
            <span className="text-lg font-semibold text-slate-900">Agent Finder</span>
            <span className="hidden text-sm text-slate-500 sm:inline">Resume screening for insurance agencies</span>
          </Link>
          <div className="flex items-center gap-3 text-sm">
            {health && (
              <span
                className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                  isMock ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'
                }`}
                title="Scoring provider configured on the server"
              >
                {isMock ? 'Offline mock scorer' : health.provider}
              </span>
            )}
            <span className="text-slate-600">{user?.username}</span>
            <button
              type="button"
              onClick={() => {
                logout();
                navigate('/login');
              }}
              className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-slate-600 hover:bg-slate-100"
            >
              <LogOut className="h-4 w-4" aria-hidden="true" /> Sign out
            </button>
          </div>
        </div>
        {isMock && (
          <div className="border-t border-amber-200 bg-amber-50 px-4 py-2 text-center text-xs text-amber-900">
            Demo mode: scores come from a deterministic keyword-based scorer, not an LLM. Set ANTHROPIC_API_KEY to
            screen with Claude.
          </div>
        )}
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6">
        <Outlet />
      </main>
    </div>
  );
};

export default Layout;
