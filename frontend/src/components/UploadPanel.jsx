import { ClipboardPaste, Upload } from 'lucide-react';
import { useRef, useState } from 'react';
import { usePasteResume, useUploadResumes } from '../hooks/useCandidates';
import { errorMessage } from '../utils/api';

const UploadPanel = ({ jobId }) => {
  const [tab, setTab] = useState('files');
  const [files, setFiles] = useState([]);
  const [text, setText] = useState('');
  const [label, setLabel] = useState('');
  const [result, setResult] = useState(null);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef(null);
  const upload = useUploadResumes(jobId);
  const paste = usePasteResume(jobId);
  const busy = upload.isPending || paste.isPending;

  const submitFiles = async () => {
    setResult(null);
    try {
      const data = await upload.mutateAsync(files);
      setResult({ ok: `Screened ${data.created.length} resume${data.created.length === 1 ? '' : 's'}.`, errors: data.errors });
      setFiles([]);
      if (inputRef.current) inputRef.current.value = '';
    } catch (err) {
      setResult({ error: errorMessage(err, 'Upload failed.') });
    }
  };

  const submitText = async () => {
    setResult(null);
    try {
      const data = await paste.mutateAsync({ text, label });
      setResult({ ok: `Screened ${data.name}.`, errors: [] });
      setText('');
      setLabel('');
    } catch (err) {
      setResult({ error: errorMessage(err, 'Could not screen this text.') });
    }
  };

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="font-semibold text-slate-900">Add resumes</h2>
        <div className="flex rounded-lg bg-slate-100 p-1 text-xs">
          {[
            ['files', 'Upload files'],
            ['text', 'Paste text'],
          ].map(([key, name]) => (
            <button
              key={key}
              type="button"
              onClick={() => setTab(key)}
              className={`rounded-md px-3 py-1 font-medium ${tab === key ? 'bg-white text-slate-900 shadow' : 'text-slate-600'}`}
            >
              {name}
            </button>
          ))}
        </div>
      </div>

      {tab === 'files' ? (
        <div className="space-y-3">
          <label
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragging(false);
              setFiles([...e.dataTransfer.files]);
            }}
            className={`flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed px-4 py-6 text-center text-sm ${
              dragging ? 'border-indigo-400 bg-indigo-50' : 'border-slate-300 text-slate-600'
            }`}
          >
            <Upload className="mb-2 h-6 w-6 text-slate-400" aria-hidden="true" />
            <span>
              Drop resumes here or <span className="font-semibold text-indigo-600">browse</span>
            </span>
            <span className="mt-1 text-xs text-slate-500">PDF, DOCX or TXT · up to 20 files, 5 MB each</span>
            <input
              ref={inputRef}
              type="file"
              multiple
              accept=".pdf,.docx,.txt"
              className="sr-only"
              onChange={(e) => setFiles([...e.target.files])}
            />
          </label>
          {files.length > 0 && (
            <ul className="max-h-24 overflow-auto text-xs text-slate-600">
              {files.map((f) => (
                <li key={f.name}>{f.name}</li>
              ))}
            </ul>
          )}
          <button
            type="button"
            disabled={!files.length || busy}
            onClick={submitFiles}
            className="w-full rounded-md bg-indigo-600 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {upload.isPending ? 'Screening…' : `Screen ${files.length || ''} resume${files.length === 1 ? '' : 's'}`}
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          <input
            className="block w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            placeholder="Label (optional), e.g. referral from Pat"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
          />
          <textarea
            className="block w-full rounded-md border border-slate-300 px-3 py-2 font-mono text-xs"
            rows={7}
            placeholder="Paste the resume text here"
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
          <button
            type="button"
            disabled={text.trim().length < 80 || busy}
            onClick={submitText}
            className="inline-flex w-full items-center justify-center gap-1.5 rounded-md bg-indigo-600 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            <ClipboardPaste className="h-4 w-4" aria-hidden="true" />
            {paste.isPending ? 'Screening…' : 'Screen pasted resume'}
          </button>
        </div>
      )}

      {result?.ok && <p className="mt-3 text-sm text-emerald-700">{result.ok}</p>}
      {result?.error && <p className="mt-3 text-sm text-rose-600">{result.error}</p>}
      {result?.errors?.length > 0 && (
        <ul className="mt-2 space-y-1 text-xs text-rose-600">
          {result.errors.map((e) => (
            <li key={e.filename}>{e.detail}</li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default UploadPanel;
