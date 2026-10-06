import { Briefcase, MapPin, Plus, Trash2, Users } from 'lucide-react';
import { useState } from 'react';
import { Link } from 'react-router-dom';
import JobForm from '../components/JobForm';
import LoadingSpinner from '../components/LoadingSpinner';
import { useCreateJob, useDeleteJob, useJobs } from '../hooks/useCandidates';
import { errorMessage } from '../utils/api';

const Home = () => {
  const { data: jobs, isLoading, error } = useJobs();
  const createJob = useCreateJob();
  const deleteJob = useDeleteJob();
  const [showForm, setShowForm] = useState(false);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Openings</h1>
          <p className="text-sm text-slate-600">Create an opening, upload resumes, and review a ranked shortlist.</p>
        </div>
        {!showForm && (
          <button
            type="button"
            onClick={() => setShowForm(true)}
            className="inline-flex items-center gap-1.5 rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700"
          >
            <Plus className="h-4 w-4" aria-hidden="true" /> New opening
          </button>
        )}
      </div>

      {showForm && (
        <JobForm
          onSubmit={async (payload) => {
            await createJob.mutateAsync(payload);
            setShowForm(false);
          }}
          onCancel={() => setShowForm(false)}
        />
      )}

      {isLoading && <LoadingSpinner label="Loading openings" />}
      {error && <p className="text-sm text-rose-600">{errorMessage(error)}</p>}
      {jobs && jobs.length === 0 && !showForm && (
        <div className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center text-slate-600">
          <Briefcase className="mx-auto h-8 w-8 text-slate-400" aria-hidden="true" />
          <p className="mt-2">No openings yet. Create one to start screening resumes.</p>
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {jobs?.map((job) => (
          <div key={job.id} className="group relative rounded-xl border border-slate-200 bg-white p-5 transition hover:border-indigo-300 hover:shadow-sm">
            <Link to={`/jobs/${job.id}`} className="block">
              <h2 className="pr-8 font-semibold text-slate-900 group-hover:text-indigo-700">{job.title}</h2>
              {job.location && (
                <p className="mt-1 flex items-center gap-1 text-sm text-slate-600">
                  <MapPin className="h-3.5 w-3.5" aria-hidden="true" /> {job.location}
                </p>
              )}
              <div className="mt-3 flex flex-wrap gap-1.5">
                {job.criteria.required_licenses.map((lic) => (
                  <span key={lic} className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-700">
                    {lic}
                  </span>
                ))}
                {job.criteria.bilingual_preferred &&
                  job.criteria.languages.map((lang) => (
                    <span key={lang} className="rounded-full bg-sky-50 px-2 py-0.5 text-xs text-sky-700">
                      {lang}
                    </span>
                  ))}
              </div>
              <p className="mt-4 flex items-center gap-1.5 text-sm text-slate-600">
                <Users className="h-4 w-4" aria-hidden="true" />
                {job.candidate_count} candidate{job.candidate_count === 1 ? '' : 's'} · {job.shortlisted_count} shortlisted
              </p>
            </Link>
            <button
              type="button"
              aria-label={`Delete ${job.title}`}
              onClick={() => {
                if (window.confirm(`Delete "${job.title}" and all of its candidates?`)) deleteJob.mutate(job.id);
              }}
              className="absolute right-3 top-3 rounded p-1 text-slate-400 opacity-0 hover:bg-rose-50 hover:text-rose-600 group-hover:opacity-100"
            >
              <Trash2 className="h-4 w-4" aria-hidden="true" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Home;
