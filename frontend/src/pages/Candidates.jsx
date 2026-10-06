import { ArrowLeft, Award, Check, Star, Users } from 'lucide-react';
import { useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import CandidateModal from '../components/CandidateModal';
import CandidateTable from '../components/CandidateTable';
import LoadingSpinner from '../components/LoadingSpinner';
import StatsCard from '../components/StatsCard';
import UploadPanel from '../components/UploadPanel';
import { useCandidates, useJob } from '../hooks/useCandidates';
import { errorMessage } from '../utils/api';
import { STATUSES } from '../utils/constants';
import { STATUS_META, formatScore } from '../utils/helpers';

const Candidates = () => {
  const { jobId } = useParams();
  const { data: job, isLoading: jobLoading, error: jobError } = useJob(jobId);
  const { data: candidates = [], isLoading } = useCandidates(jobId);
  const [filter, setFilter] = useState('all');
  const [selected, setSelected] = useState(null);

  const stats = useMemo(() => {
    const scored = candidates.filter((c) => c.score !== null);
    const avg = scored.length ? scored.reduce((sum, c) => sum + c.score, 0) / scored.length : null;
    return {
      total: candidates.length,
      strong: scored.filter((c) => c.score >= 75).length,
      avg,
      shortlisted: candidates.filter((c) => c.status === 'shortlisted').length,
    };
  }, [candidates]);

  const visible = filter === 'all' ? candidates : candidates.filter((c) => c.status === filter);

  if (jobLoading) return <LoadingSpinner label="Loading opening" />;
  if (jobError) return <p className="text-sm text-rose-600">{errorMessage(jobError)}</p>;

  const c = job.criteria;
  return (
    <div className="space-y-6">
      <div>
        <Link to="/" className="inline-flex items-center gap-1 text-sm text-slate-600 hover:text-indigo-700">
          <ArrowLeft className="h-4 w-4" aria-hidden="true" /> All openings
        </Link>
        <h1 className="mt-2 text-2xl font-semibold text-slate-900">{job.title}</h1>
        <p className="mt-1 text-sm text-slate-600">
          {[
            job.location,
            c.required_licenses.length ? `Licenses: ${c.required_licenses.join(', ')}` : 'No license requirement',
            `${c.min_sales_years}+ yrs sales`,
            c.customer_service_required && 'Customer service',
            c.bilingual_preferred && `Bilingual: ${c.languages.join(', ')}`,
          ]
            .filter(Boolean)
            .join(' · ')}
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatsCard title="Candidates" value={stats.total} icon={Users} />
        <StatsCard title="Strong matches" value={stats.strong} hint="Score 75 or higher" icon={Star} />
        <StatsCard title="Average score" value={formatScore(stats.avg)} icon={Award} />
        <StatsCard title="Shortlisted" value={stats.shortlisted} icon={Check} />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-1">
          <UploadPanel jobId={jobId} />
        </div>
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white lg:col-span-2">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 px-4 py-3">
            <h2 className="font-semibold text-slate-900">Ranked candidates</h2>
            <div className="flex flex-wrap gap-1 text-xs">
              {['all', ...STATUSES].map((s) => {
                const count = s === 'all' ? candidates.length : candidates.filter((x) => x.status === s).length;
                return (
                  <button
                    key={s}
                    type="button"
                    onClick={() => setFilter(s)}
                    className={`rounded-full px-2.5 py-1 font-medium ${
                      filter === s ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    {s === 'all' ? 'All' : STATUS_META[s].label} ({count})
                  </button>
                );
              })}
            </div>
          </div>
          {isLoading ? (
            <div className="p-10">
              <LoadingSpinner label="Loading candidates" />
            </div>
          ) : (
            <CandidateTable candidates={visible} onSelect={setSelected} />
          )}
        </div>
      </div>

      {selected && <CandidateModal candidateId={selected} job={job} onClose={() => setSelected(null)} />}
    </div>
  );
};

export default Candidates;
