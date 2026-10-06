import { create } from 'zustand';
import api from '../utils/api';

const useAuth = create((set) => ({
  user: null,
  status: 'unknown', // unknown | authenticated | anonymous

  login: async (username, password) => {
    const response = await api.post('/auth/token', new URLSearchParams({ username, password }), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    localStorage.setItem('authToken', response.data.access_token);
    const me = await api.get('/auth/me');
    set({ user: me.data, status: 'authenticated' });
  },

  register: async (username, email, password) => {
    await api.post('/auth/register', { username, email, password });
  },

  logout: () => {
    localStorage.removeItem('authToken');
    set({ user: null, status: 'anonymous' });
  },

  checkAuth: async () => {
    if (!localStorage.getItem('authToken')) {
      set({ user: null, status: 'anonymous' });
      return;
    }
    try {
      const me = await api.get('/auth/me');
      set({ user: me.data, status: 'authenticated' });
    } catch {
      localStorage.removeItem('authToken');
      set({ user: null, status: 'anonymous' });
    }
  },
}));

export default useAuth;
