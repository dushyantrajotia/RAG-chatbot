import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../App';
import { Bot, Mail, Lock, User, ShieldAlert, ArrowRight, CheckCircle2, AlertCircle } from 'lucide-react';

export const Login: React.FC = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [role, setRole] = useState('user');
  
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const { user, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // If user is already authenticated, redirect them
  useEffect(() => {
    if (user) {
      const from = (location.state as any)?.from?.pathname || '/chat';
      navigate(from, { replace: true });
    }
  }, [user, navigate, location]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setLoading(true);

    if (!email.trim() || !password.trim()) {
      setError('Please fill in all fields.');
      setLoading(false);
      return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters.');
      setLoading(false);
      return;
    }

    try {
      if (isLogin) {
        await axios.post('/api/auth/login', { email, password }, { withCredentials: true });
        setSuccess('Authentication successful! Redirecting...');
        
        // Fetch current user details
        setTimeout(async () => {
          try {
            const meResponse = await axios.get('/api/auth/me', { withCredentials: true });
            login(meResponse.data);
          } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to retrieve profile.');
          } finally {
            setLoading(false);
          }
        }, 800);
      } else {
        // Register
        await axios.post('/api/auth/register', {
          email,
          password,
          name: name.trim() || undefined,
          role
        }, { withCredentials: true });
        setSuccess('Registration successful! You can now log in.');
        setIsLogin(true);
        setPassword('');
        setName('');
        setLoading(false);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'An error occurred. Please try again.');
      setLoading(false);
    }
  };

  return (
    <div className="animated-gradient-bg min-h-screen w-screen flex items-center justify-center p-4 relative overflow-hidden select-none">
      {/* Decorative Blur Orbs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full bg-indigo-500/10 blur-[120px] pointer-events-none"></div>
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 rounded-full bg-purple-500/10 blur-[120px] pointer-events-none"></div>

      {/* Login Card Container */}
      <div className="w-full max-w-md glass-card rounded-3xl shadow-2xl relative z-10 overflow-hidden transform hover:scale-[1.005] transition-all duration-300">
        
        {/* Top Header Section */}
        <div className="px-8 pt-8 pb-4 text-center">
          <div className="inline-flex items-center justify-center p-3.5 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 mb-4 animate-pulse">
            <Bot size={32} />
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-white via-zinc-100 to-zinc-400 bg-clip-text text-transparent">
            RAG Chatbot
          </h1>
          <p className="text-zinc-400 text-sm mt-1.5 font-light">
            Secure, state-of-the-art document RAG agent
          </p>
        </div>

        {/* Auth Mode Tabs */}
        <div className="flex border-b border-zinc-800/60 px-8">
          <button
            onClick={() => { setIsLogin(true); setError(null); setSuccess(null); }}
            className={`flex-1 pb-3 text-sm font-semibold border-b-2 transition-all duration-300 ${
              isLogin 
                ? 'text-indigo-400 border-indigo-500' 
                : 'text-zinc-500 border-transparent hover:text-zinc-300'
            }`}
            id="tab-login"
          >
            Sign In
          </button>
          <button
            onClick={() => { setIsLogin(false); setError(null); setSuccess(null); }}
            className={`flex-1 pb-3 text-sm font-semibold border-b-2 transition-all duration-300 ${
              !isLogin 
                ? 'text-indigo-400 border-indigo-500' 
                : 'text-zinc-500 border-transparent hover:text-zinc-300'
            }`}
            id="tab-register"
          >
            Register
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-8 space-y-5">
          {/* Info Status Banners */}
          {error && (
            <div className="flex items-start gap-3 p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-400 text-sm animate-shake">
              <AlertCircle className="shrink-0 mt-0.5" size={16} />
              <span>{error}</span>
            </div>
          )}
          {success && (
            <div className="flex items-start gap-3 p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-emerald-400 text-sm">
              <CheckCircle2 className="shrink-0 mt-0.5" size={16} />
              <span>{success}</span>
            </div>
          )}

          {/* Registration Extra Fields */}
          {!isLogin && (
            <div className="space-y-1.5">
              <label className="text-zinc-400 text-xs font-semibold uppercase tracking-wider pl-1">Full Name</label>
              <div className="relative">
                <User className="absolute left-3.5 top-1/2 -translate-y-1/2 text-zinc-500" size={18} />
                <input
                  type="text"
                  placeholder="John Doe"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full glass-input pl-11"
                  required={!isLogin}
                  id="reg-name"
                />
              </div>
            </div>
          )}

          {/* Email input */}
          <div className="space-y-1.5">
            <label className="text-zinc-400 text-xs font-semibold uppercase tracking-wider pl-1">Email Address</label>
            <div className="relative">
              <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 text-zinc-500" size={18} />
              <input
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full glass-input pl-11"
                required
                id="auth-email"
              />
            </div>
          </div>

          {/* Password input */}
          <div className="space-y-1.5">
            <label className="text-zinc-400 text-xs font-semibold uppercase tracking-wider pl-1">Password</label>
            <div className="relative">
              <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 text-zinc-500" size={18} />
              <input
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full glass-input pl-11"
                required
                id="auth-password"
              />
            </div>
          </div>

          {/* Registration Role Dropdown (For testing convenience) */}
          {!isLogin && (
            <div className="space-y-1.5">
              <label className="text-zinc-400 text-xs font-semibold uppercase tracking-wider pl-1">Account Role</label>
              <div className="relative">
                <ShieldAlert className="absolute left-3.5 top-1/2 -translate-y-1/2 text-zinc-500" size={18} />
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="w-full glass-input pl-11 appearance-none cursor-pointer"
                  id="reg-role"
                >
                  <option value="user" className="bg-zinc-900 text-zinc-200">Standard User</option>
                  <option value="admin" className="bg-zinc-900 text-zinc-200">Admin Privileges</option>
                </select>
              </div>
            </div>
          )}

          {/* Action Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full btn-primary flex items-center justify-center gap-2 mt-2 group disabled:opacity-50 disabled:cursor-not-allowed"
            id="auth-submit"
          >
            {loading ? (
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
            ) : (
              <>
                <span>{isLogin ? 'Sign In' : 'Register Account'}</span>
                <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform duration-200" />
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
};
