import { useState } from 'react';
import { CRITERIA_LABELS, DEFAULT_WEIGHTS, LICENSE_OPTIONS } from '../utils/constants';
import { errorMessage } from '../utils/api';

const inputClass =
  'mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500';

const emptyForm = {
  title: '',
  location: '',
  description: '',
  required_licenses: ['P&C'],
  min_sales_years: 2,
  customer_service_required: true,
  bilingual_preferred: false,
  languages: 'Spanish',
  weights: { ...DEFAULT_WEIGHTS },
};

const JobForm = ({ onSubmit, onCancel }) => {
  const [form, setForm] = useState(emptyForm);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  const set = (field, value) => setForm((f) => ({ ...f, [field]: value }));
  const toggleLicense = (lic) =>
    set(
      'required_licenses',
      form.required_licenses.includes(lic)
        ? form.required_licenses.filter((l) => l !== lic)
        : [...form.required_licenses, lic],
    );

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await onSubmit({
        title: form.title,
        location: form.location,
        description: form.description,
        criteria: {
          required_licenses: form.required_licenses,
          min_sales_years: Number(form.min_sales_years) || 0,
          customer_service_required: form.customer_service_required,
          bilingual_preferred: form.bilingual_preferred,
          languages: form.languages
            .split(',')
            .map((l) => l.trim())
            .filter(Boolean),
          weights: Object.fromEntries(Object.entries(form.weights).map(([k, v]) => [k, Number(v) || 0])),
        },
      });
      setForm(emptyForm);
    } catch (err) {
      setError(errorMessage(err, 'Could not create the opening.'));
    } finally {
      setBusy(false);
    }
  };

  return (
    <form onSubmit={submit} className="space-y-4 rounded-xl border border-slate-200 bg-white p-5">
      <h2 className="text-base font-semibold text-slate-900">New opening</h2>
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="text-sm font-medium text-slate-700">
          Job title
          <input className={inputClass} value={form.title} onChange={(e) => set('title', e.target.value)} placeholder="Licensed Insurance Agent" required />
        </label>
        <label className="text-sm font-medium text-slate-700">
          Location (City, ST)
          <input className={inputClass} value={form.location} onChange={(e) => set('location', e.target.value)} placeholder="Wilmington, NC" />
        </label>
      </div>
      <label className="block text-sm font-medium text-slate-700">
        Description <span className="font-normal text-slate-500">(optional, given to the LLM as context)</span>
        <textarea className={inputClass} rows={3} value={form.description} onChange={(e) => set('description', e.target.value)} />
      </label>

      <fieldset>
        <legend className="text-sm font-medium text-slate-700">Required licenses</legend>
        <div className="mt-2 flex flex-wrap gap-2">
          {LICENSE_OPTIONS.map((lic) => (
            <label
              key={lic}
              className={`cursor-pointer rounded-full border px-3 py-1 text-sm ${
                form.required_licenses.includes(lic) ? 'border-indigo-500 bg-indigo-50 text-indigo-700' : 'border-slate-300 text-slate-600'
              }`}
            >
              <input type="checkbox" className="sr-only" checked={form.required_licenses.includes(lic)} onChange={() => toggleLicense(lic)} />
              {lic}
            </label>
          ))}
        </div>
      </fieldset>

      <div className="grid gap-4 sm:grid-cols-3">
        <label className="text-sm font-medium text-slate-700">
          Minimum years in sales
          <input type="number" min="0" step="0.5" className={inputClass} value={form.min_sales_years} onChange={(e) => set('min_sales_years', e.target.value)} />
        </label>
        <label className="flex items-center gap-2 pt-6 text-sm text-slate-700">
          <input type="checkbox" checked={form.customer_service_required} onChange={(e) => set('customer_service_required', e.target.checked)} />
          Customer service experience
        </label>
        <label className="flex items-center gap-2 pt-6 text-sm text-slate-700">
          <input type="checkbox" checked={form.bilingual_preferred} onChange={(e) => set('bilingual_preferred', e.target.checked)} />
          Bilingual preferred
        </label>
      </div>
      {form.bilingual_preferred && (
        <label className="block text-sm font-medium text-slate-700">
          Preferred languages (comma separated)
          <input className={inputClass} value={form.languages} onChange={(e) => set('languages', e.target.value)} />
        </label>
      )}

      <details className="rounded-md bg-slate-50 p-3">
        <summary className="cursor-pointer text-sm font-medium text-slate-700">Rubric weights</summary>
        <div className="mt-3 grid gap-3 sm:grid-cols-5">
          {Object.entries(CRITERIA_LABELS).map(([key, label]) => (
            <label key={key} className="text-xs font-medium text-slate-600">
              {label}
              <input
                type="number"
                min="0"
                max="100"
                className={inputClass}
                value={form.weights[key]}
                onChange={(e) => set('weights', { ...form.weights, [key]: e.target.value })}
              />
            </label>
          ))}
        </div>
        <p className="mt-2 text-xs text-slate-500">
          Weights are relative. Unused criteria (no location, bilingual not preferred) are ignored automatically.
        </p>
      </details>

      {error && <p className="text-sm text-rose-600">{error}</p>}
      <div className="flex justify-end gap-2">
        {onCancel && (
          <button type="button" onClick={onCancel} className="rounded-md px-4 py-2 text-sm text-slate-600 hover:bg-slate-100">
            Cancel
          </button>
        )}
        <button type="submit" disabled={busy} className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-60">
          {busy ? 'Saving…' : 'Create opening'}
        </button>
      </div>
    </form>
  );
};

export default JobForm;
