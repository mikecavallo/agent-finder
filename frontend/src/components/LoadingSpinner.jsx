const LoadingSpinner = ({ label = 'Loading' }) => (
  <div className="flex items-center justify-center gap-3 text-slate-500" role="status">
    <div className="h-6 w-6 animate-spin rounded-full border-2 border-slate-300 border-t-indigo-600" />
    <span className="text-sm">{label}…</span>
  </div>
);

export default LoadingSpinner;
