import { STATUS_META, formatScore, formatYears, scoreClasses } from '../utils/helpers';

const CandidateTable = ({ candidates, onSelect }) => {
  if (!candidates.length) {
    return <p className="px-5 py-10 text-center text-sm text-slate-500">No candidates match this view yet.</p>;
  }
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50 text-left text-xs font-medium uppercase tracking-wide text-slate-500">
          <tr>
            <th scope="col" className="px-4 py-3">#</th>
            <th scope="col" className="px-4 py-3">Candidate</th>
            <th scope="col" className="px-4 py-3">Score</th>
            <th scope="col" className="px-4 py-3">Licenses</th>
            <th scope="col" className="px-4 py-3">Sales</th>
            <th scope="col" className="px-4 py-3">Location</th>
            <th scope="col" className="px-4 py-3">Status</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 bg-white">
          {candidates.map((c) => (
            <tr
              key={c.id}
              onClick={() => onSelect(c.id)}
              onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && onSelect(c.id)}
              tabIndex={0}
              className="cursor-pointer hover:bg-indigo-50/50 focus:bg-indigo-50 focus:outline-none"
            >
              <td className="px-4 py-3 text-slate-500">{c.rank ?? '—'}</td>
              <td className="px-4 py-3">
                <div className="font-medium text-slate-900">{c.name}</div>
                <div className="text-xs text-slate-500">{c.current_title || c.source_filename}</div>
              </td>
              <td className="px-4 py-3">
                <span className={`inline-flex min-w-[2.5rem] justify-center rounded-full px-2 py-0.5 text-xs font-semibold ${scoreClasses(c.score)}`}>
                  {formatScore(c.score)}
                </span>
              </td>
              <td className="px-4 py-3 text-slate-700">{c.licenses.length ? c.licenses.join(', ') : <span className="text-slate-400">None</span>}</td>
              <td className="px-4 py-3 text-slate-700">{formatYears(c.years_sales)}</td>
              <td className="px-4 py-3 text-slate-700">{c.location || <span className="text-slate-400">Unknown</span>}</td>
              <td className="px-4 py-3">
                <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_META[c.status].classes}`}>
                  {STATUS_META[c.status].label}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default CandidateTable;
