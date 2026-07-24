import React, { useState, useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../App';

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: string[];
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, allowedRoles }) => {
  const { user, login, logout } = useAuth();
  const [localLoading, setLocalLoading] = useState(true);
  const location = useLocation();

  useEffect(() => {
    const verifyAuth = async () => {
      try {
        const response = await axios.get('/api/auth/me', { withCredentials: true });
        login(response.data);
      } catch (err) {
        logout();
      } finally {
        setLocalLoading(false);
      }
    };
    verifyAuth();
  }, [login, logout]);

  if (localLoading) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-zinc-950">
        <div className="flex flex-col items-center gap-4">
          <div className="h-12 w-12 animate-spin rounded-full border-4 border-indigo-500/80 border-t-transparent"></div>
          <p className="font-sans font-medium text-zinc-400 text-sm tracking-wide">Verifying secure session...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    // Redirect to login but save the current location they were trying to access
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    // Role not authorized, redirect to main chat
    return <Navigate to="/chat" replace />;
  }

  return <>{children}</>;
};
