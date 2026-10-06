export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const LICENSE_OPTIONS = ['P&C', 'Life & Health', 'Personal Lines', 'Series 6', 'Series 7', 'Series 63'];

export const CRITERIA_LABELS = {
  licenses: 'Insurance licenses',
  sales: 'Sales experience',
  customer_service: 'Customer service',
  bilingual: 'Language skills',
  location: 'Location fit',
};

export const DEFAULT_WEIGHTS = {
  licenses: 30,
  sales: 25,
  customer_service: 20,
  bilingual: 10,
  location: 15,
};

export const STATUSES = ['new', 'shortlisted', 'contacted', 'rejected'];
