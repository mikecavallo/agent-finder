import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import useAuth from '../hooks/useAuth';

const AuthGuard = ({ children }) => {
  const { isAuthenticated, checkAuth, loading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  if (loading) {
    console.log("AuthGuard: Loading...");
    return <div>Loading authentication...</div>; // Or a proper loading spinner
  }

  if (!isAuthenticated) {
    console.log("AuthGuard: Not authenticated, navigating to /login");
    navigate('/login');
    return null;
  }

  console.log("AuthGuard: Authenticated, rendering children");
  return <>{children}</>;
};

export default AuthGuard;
