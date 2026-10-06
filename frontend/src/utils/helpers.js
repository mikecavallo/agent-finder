export function formatScore(score) {
  return score === null || score === undefined ? '—' : Math.round(score).toString();
}

/** Tailwind classes for a 0-100 score badge. */
export function scoreClasses(score) {
  if (score === null || score === undefined) return 'bg-slate-100 text-slate-600';
  if (score >= 75) return 'bg-emerald-100 text-emerald-800';
  if (score >= 50) return 'bg-amber-100 text-amber-800';
  return 'bg-rose-100 text-rose-800';
}

/** Bar color for a 0-1 criterion score. */
export function barClass(score) {
  if (score >= 0.75) return 'bg-emerald-500';
  if (score >= 0.4) return 'bg-amber-500';
  return 'bg-rose-500';
}

export const STATUS_META = {
  new: { label: 'New', classes: 'bg-slate-100 text-slate-700' },
  shortlisted: { label: 'Shortlisted', classes: 'bg-indigo-100 text-indigo-800' },
  contacted: { label: 'Contacted', classes: 'bg-sky-100 text-sky-800' },
  rejected: { label: 'Rejected', classes: 'bg-rose-100 text-rose-700' },
};

export function formatYears(value) {
  if (value === null || value === undefined) return '—';
  return `${Number(value).toFixed(value % 1 ? 1 : 0)} yr${value === 1 ? '' : 's'}`;
}

function escapeRegExp(text) {
  return text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Split text into [{text, match}] segments so matching terms can be highlighted
 * without using dangerouslySetInnerHTML.
 */
export function highlightSegments(text, terms) {
  const cleaned = [...new Set(terms.filter((t) => t && t.trim().length > 1))];
  if (!cleaned.length) return [{ text, match: false }];
  const pattern = new RegExp(`(${cleaned.map(escapeRegExp).join('|')})`, 'gi');
  return text
    .split(pattern)
    .filter((part) => part !== '')
    .map((part) => ({ text: part, match: cleaned.some((t) => t.toLowerCase() === part.toLowerCase()) }));
}

/** Keywords worth highlighting in a resume, based on the job criteria. */
export function resumeKeywords(criteria = {}) {
  const terms = [
    'Property & Casualty',
    'Property and Casualty',
    'Life & Health',
    'Life and Health',
    'P&C',
    'licensed',
    'license',
    'sales',
    'customer service',
    'quota',
    'bilingual',
    'relocat',
  ];
  return [...terms, ...(criteria.required_licenses || []), ...(criteria.bilingual_preferred ? criteria.languages || [] : [])];
}
