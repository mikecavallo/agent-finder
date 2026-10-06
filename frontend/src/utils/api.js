import axios from 'axios';
import { API_BASE_URL } from './constants';

const api = axios.create({ baseURL: `${API_BASE_URL}/api` });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && !error.config.url.startsWith('/auth/')) {
      localStorage.removeItem('authToken');
      window.location.assign('/login');
    }
    return Promise.reject(error);
  },
);

/** Turn a FastAPI error response into a readable message. */
export function errorMessage(error, fallback = 'Something went wrong.') {
  const detail = error?.response?.data?.detail;
  if (!detail) return error?.message || fallback;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d) => d.detail || (d.loc ? `${d.loc.slice(-1)[0]}: ${d.msg}` : d.msg) || JSON.stringify(d))
      .join(' ');
  }
  return fallback;
}

export default api;
