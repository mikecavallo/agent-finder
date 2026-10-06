import { useMemo } from 'react';
import { highlightSegments } from '../utils/helpers';

/** Shows the extracted resume text with job-relevant keywords highlighted. */
const ResumeViewer = ({ text, keywords = [] }) => {
  const segments = useMemo(() => highlightSegments(text || '', keywords), [text, keywords]);
  return (
    <pre className="max-h-96 overflow-auto whitespace-pre-wrap rounded-lg border border-slate-200 bg-slate-50 p-4 font-sans text-sm leading-relaxed text-slate-800">
      {segments.map((seg, i) =>
        seg.match ? (
          <mark key={i} className="rounded bg-amber-100 px-0.5 text-slate-900">
            {seg.text}
          </mark>
        ) : (
          <span key={i}>{seg.text}</span>
        ),
      )}
    </pre>
  );
};

export default ResumeViewer;
