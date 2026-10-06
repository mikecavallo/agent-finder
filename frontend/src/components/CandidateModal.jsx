import { Check, Copy, Mail, RefreshCw, Trash2, X } from 'lucide-react';
import { useEffect, useState } from 'react';
import {
  useCandidate,
  useDeleteCandidate,
  useOutreachDraft,
  useRescoreCandidate,
  useUpdateCandidate,
} from '../hooks/useCandidates';
import useAuth from '../hooks/useAuth';
import { errorMessage } from '../utils/api';
import { STATUSES } from '../utils/constants';
import { STATUS_META, barClass, formatScore, formatYears, resumeKeywords, scoreClasses } from '../utils/helpers';
import LoadingSpinner from './LoadingSpinner';
import ResumeViewer from './ResumeViewer';

const Section = ({ title, children }) => (
  <section>
    <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">{title}</h3>
    {children}
  </section>
);

const CandidateModal = ({ candidateId, job, onClose }) => {
  const { data: c, isLoading, error } = useCandidate(candidateId);
  const update = useUpdateCandidate(job.id);
  const rescore = useRescoreCandidate(job.id);
  const outreach = useOutreachDraft(job.id);
  const remove = useDeleteCandidate(job.id);
  const username = useAuth((s) => s.user?.username);
  const [notes, setNotes] = useState('');
  const [recruiterName, setRecruiterName] = useState('');
  const [copied, setCopied] = useState(false);
  const [actionError, setActionError] = useState(null);

  useEffect(() => {
    if (c) setNotes(c.notes || '');
  }, [c?.id, c?.notes]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (username && !recruiterName) setRecruiterName(username);
  }, [username]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  const run = async (mutation, args) => {
    setActionError(null);
    try {
      await mutation.mutateAsync(args);
    } catch (err) {
      setActionError(errorMessage(err));
    }
  };

  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-slate-900/40" onClick={onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Candidate details"
        className="h-full w-full max-w-3xl overflow-y-auto bg-white shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 z-10 flex items-start justify-between border-b border-slate-200 bg-white px-6 py-4">
          {c ? (
            <div>
              <h2 className="text-xl font-semibold text-slate-900">{c.name}</h2>
              <p className="text-sm text-slate-600">
                {[c.current_title, c.location, c.email, c.phone].filter(Boolean).join(' · ')}
              </p>
            </div>
          ) : (
            <div />
          )}
          <button type="button" onClick={onClose} aria-label="Close" className="rounded p-1 text-slate-500 hover:bg-slate-100">
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>

        {isLoading && (
          <div className="p-10">
            <LoadingSpinner label="Loading candidate" />
          </div>
        )}
        {error && <p className="p-6 text-sm text-rose-600">{errorMessage(error)}</p>}

        {c && (
          <div className="space-y-7 px-6 py-5">
            <div className="flex flex-wrap items-center gap-4">
              <div className={`rounded-xl px-4 py-2 text-center ${scoreClasses(c.score)}`}>
                <div className="text-3xl font-bold">{formatScore(c.score)}</div>
                <div className="text-xs">of 100{c.rank ? ` · rank #${c.rank}` : ''}</div>
              </div>
              <div className="flex flex-wrap gap-2">
                {STATUSES.map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => run(update, { id: c.id, status: s })}
                    className={`rounded-full border px-3 py-1 text-sm font-medium ${
                      c.status === s ? `${STATUS_META[s].classes} border-transparent` : 'border-slate-300 text-slate-600 hover:bg-slate-50'
                    }`}
                  >
                    {STATUS_META[s].label}
                  </button>
                ))}
              </div>
              <div className="ml-auto flex gap-2">
                <button
                  type="button"
                  onClick={() => run(rescore, c.id)}
                  disabled={rescore.isPending}
                  className="inline-flex items-center gap-1 rounded-md border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                >
                  <RefreshCw className={`h-4 w-4 ${rescore.isPending ? 'animate-spin' : ''}`} aria-hidden="true" /> Rescore
                </button>
                <button
                  type="button"
                  onClick={async () => {
                    if (window.confirm(`Remove ${c.name} from this opening?`)) {
                      await run(remove, c.id);
                      onClose();
                    }
                  }}
                  className="inline-flex items-center gap-1 rounded-md border border-slate-300 px-3 py-1.5 text-sm text-rose-600 hover:bg-rose-50"
                >
                  <Trash2 className="h-4 w-4" aria-hidden="true" /> Remove
                </button>
              </div>
            </div>
            {actionError && <p className="text-sm text-rose-600">{actionError}</p>}

            <Section title="Score breakdown">
              <div className="space-y-3">
                {c.breakdown.map((b) => (
                  <div key={b.key} className={b.weight === 0 ? 'opacity-50' : ''}>
                    <div className="flex items-baseline justify-between text-sm">
                      <span className="font-medium text-slate-800">{b.label}</span>
                      <span className="text-xs text-slate-500">
                        {Math.round(b.score * 100)}% · weight {b.weight}
                      </span>
                    </div>
                    <div className="mt-1 h-2 rounded-full bg-slate-100">
                      <div className={`h-2 rounded-full ${barClass(b.score)}`} style={{ width: `${b.score * 100}%` }} />
                    </div>
                    <p className="mt-1 text-xs text-slate-600">{b.evidence}</p>
                  </div>
                ))}
              </div>
              <p className="mt-3 text-xs text-slate-500">
                Scored by {c.scored_by}. The total is the weighted average of the criteria above. Use it to prioritize
                review, not as a hiring decision.
              </p>
            </Section>

            <div className="grid gap-6 sm:grid-cols-2">
              <Section title="Strengths">
                <ul className="list-disc space-y-1 pl-5 text-sm text-slate-700">
                  {c.strengths.length ? c.strengths.map((s) => <li key={s}>{s}</li>) : <li className="list-none text-slate-400">None noted</li>}
                </ul>
              </Section>
              <Section title="Concerns">
                <ul className="list-disc space-y-1 pl-5 text-sm text-slate-700">
                  {c.concerns.length ? c.concerns.map((s) => <li key={s}>{s}</li>) : <li className="list-none text-slate-400">None noted</li>}
                </ul>
              </Section>
            </div>

            <Section title="Extracted profile">
              <dl className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm sm:grid-cols-3">
                {[
                  ['Licenses', c.licenses.join(', ') || 'None found'],
                  ['Languages', c.languages.join(', ') || '—'],
                  ['Sales experience', formatYears(c.years_sales)],
                  ['Customer service', formatYears(c.years_customer_service)],
                  ['Source', c.source_filename || '—'],
                ].map(([k, v]) => (
                  <div key={k}>
                    <dt className="text-xs text-slate-500">{k}</dt>
                    <dd className="text-slate-800">{v}</dd>
                  </div>
                ))}
              </dl>
              {c.summary && <p className="mt-3 text-sm text-slate-700">{c.summary}</p>}
            </Section>

            <Section title="Notes">
              <textarea
                className="block w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                rows={3}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Interview notes, follow-ups…"
              />
              <button
                type="button"
                disabled={notes === (c.notes || '') || update.isPending}
                onClick={() => run(update, { id: c.id, notes })}
                className="mt-2 rounded-md bg-slate-800 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-900 disabled:opacity-40"
              >
                Save notes
              </button>
            </Section>

            <Section title="Outreach email draft">
              <p className="mb-2 text-xs text-slate-500">
                Generates a draft for you to review, edit and send from your own email. Agent Finder never sends email.
              </p>
              <div className="flex gap-2">
                <input
                  className="flex-1 rounded-md border border-slate-300 px-3 py-1.5 text-sm"
                  value={recruiterName}
                  onChange={(e) => setRecruiterName(e.target.value)}
                  placeholder="Your name"
                />
                <button
                  type="button"
                  disabled={!recruiterName.trim() || outreach.isPending}
                  onClick={() => run(outreach, { id: c.id, recruiterName })}
                  className="inline-flex items-center gap-1 rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
                >
                  <Mail className="h-4 w-4" aria-hidden="true" />
                  {outreach.isPending ? 'Drafting…' : c.outreach_draft ? 'Regenerate' : 'Draft email'}
                </button>
              </div>
              {c.outreach_draft && (
                <div className="relative mt-3">
                  <pre className="whitespace-pre-wrap rounded-lg border border-slate-200 bg-slate-50 p-4 font-sans text-sm text-slate-800">
                    {c.outreach_draft}
                  </pre>
                  <button
                    type="button"
                    onClick={async () => {
                      await navigator.clipboard.writeText(c.outreach_draft);
                      setCopied(true);
                      setTimeout(() => setCopied(false), 1500);
                    }}
                    className="absolute right-2 top-2 inline-flex items-center gap-1 rounded bg-white px-2 py-1 text-xs text-slate-600 shadow hover:bg-slate-100"
                  >
                    {copied ? <Check className="h-3.5 w-3.5" aria-hidden="true" /> : <Copy className="h-3.5 w-3.5" aria-hidden="true" />}
                    {copied ? 'Copied' : 'Copy'}
                  </button>
                </div>
              )}
            </Section>

            <Section title="Resume text">
              <ResumeViewer text={c.resume_text} keywords={resumeKeywords(job.criteria)} />
            </Section>
          </div>
        )}
      </div>
    </div>
  );
};

export default CandidateModal;
