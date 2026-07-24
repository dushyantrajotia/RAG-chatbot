import React, { createContext, useContext, useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import { Login } from './pages/Login';
import { Chat } from './pages/Chat';
import { Admin } from './pages/Admin';
import { ProtectedRoute } from './components/ProtectedRoute';

// Configure Axios defaults to support proxy-based cookie transmissions
axios.defaults.withCredentials = true;

interface UserProfile {
  name: string;
  email: string;
  role: string;
}

interface AuthContextType {
  user: UserProfile | null;
  loading: boolean;
  login: (user: UserProfile) => void;
  logout: () => void;
  checkAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const App: React.FC = () => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  const checkAuth = async () => {
    try {
      const response = await axios.get('/api/auth/me', { withCredentials: true });
      setUser(response.data);
    } catch (err) {
      // Not authenticated or session expired
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkAuth();
  }, []);

  const login = (userData: UserProfile) => {
    setUser(userData);
  };

  const logout = () => {
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, checkAuth }}>
      <BrowserRouter>
        <Routes>
          {/* Public Auth Route */}
          <Route path="/login" element={<Login />} />

          {/* Protected Chat Route */}
          <Route
            path="/chat"
            element={
              <ProtectedRoute>
                <Chat />
              </ProtectedRoute>
            }
          />

          {/* Admin Protected Dashboard Route */}
          <Route
            path="/admin"
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <Admin />
              </ProtectedRoute>
            }
          />

          {/* Root Fallback Redirects */}
          <Route
            path="/"
            element={
              loading ? (
                <div className="flex h-screen w-screen items-center justify-center bg-zinc-950">
                  <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent"></div>
                </div>
              ) : user ? (
                <Navigate to="/chat" replace />
              ) : (
                <Navigate to="/login" replace />
              )
            }
          />

          {/* Catch-all Wildcard Route */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthContext.Provider>
  );
};

export default App;
