import { create } from 'zustand';
import api from '../utils/api';

const useAuth = create((set) => ({
  user: null,
  token: localStorage.getItem('authToken') || null,
  isAuthenticated: !!localStorage.getItem('authToken'),

  login: async (username, password) => {
    try {
      const response = await api.post('/auth/token', 
        new URLSearchParams({
          username,
          password,
        }),
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        }
      );
      const { access_token } = response.data;
      localStorage.setItem('authToken', access_token);
      set({ user: { username }, token: access_token, isAuthenticated: true });
      return true;
    } catch (error) {
      console.error("Login failed:", error);
      set({ user: null, token: null, isAuthenticated: false });
      return false;
    }
  },

  logout: () => {
    localStorage.removeItem('authToken');
    set({ user: null, token: null, isAuthenticated: false });
  },

  checkAuth: async () => {
    console.log("useAuth: checkAuth called");
    const token = localStorage.getItem('authToken');
    if (token) {
      try {
        const response = await api.get('/auth/me');
        set({ user: response.data, token, isAuthenticated: true });
        console.log("useAuth: checkAuth success, isAuthenticated: true");
      } catch (error) {
        console.error("useAuth: Auth check failed:", error);
        localStorage.removeItem('authToken');
        set({ user: null, token: null, isAuthenticated: false });
        console.log("useAuth: checkAuth failed, isAuthenticated: false");
      }
    } else {
      console.log("useAuth: No token found, isAuthenticated: false");
      set({ user: null, token: null, isAuthenticated: false });
    }
  },
}));

export default useAuth;
