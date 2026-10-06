import { useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import useAuth from '../hooks/useAuth';
import LoadingSpinner from './LoadingSpinner';

const AuthGuard = ({ children }) => {
  const { status, checkAuth } = useAuth();

  useEffect(() => {
    if (status === 'unknown') checkAuth();
  }, [status, checkAuth]);

  if (status === 'unknown') {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }
  if (status === 'anonymous') return <Navigate to="/login" replace />;
  return children;
};

export default AuthGuard;
