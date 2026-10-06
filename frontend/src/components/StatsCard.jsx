const StatsCard = ({ title, value, hint, icon: Icon }) => (
  <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-5">
    <div>
      <p className="text-sm font-medium text-slate-500">{title}</p>
      <p className="mt-1 text-2xl font-semibold text-slate-900">{value}</p>
      {hint && <p className="mt-1 text-xs text-slate-500">{hint}</p>}
    </div>
    {Icon && (
      <div className="rounded-lg bg-indigo-50 p-2.5 text-indigo-600">
        <Icon className="h-5 w-5" aria-hidden="true" />
      </div>
    )}
  </div>
);

export default StatsCard;
