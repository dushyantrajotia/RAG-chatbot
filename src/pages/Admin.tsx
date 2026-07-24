import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../App';
import { 
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, 
  Cell, AreaChart, Area, CartesianGrid 
} from 'recharts';
import { 
  BarChart3, Users, MessageSquare, ThumbsUp, 
  Search, ArrowLeft, RefreshCw, Briefcase, 
  ArrowUpDown, AlertTriangle, Paperclip
} from 'lucide-react';

interface FeedbackMetrics {
  total_feedback: number;
  up_count: number;
  down_count: number;
  average_rating: number;
}

interface AnalyticsData {
  total_conversations: number;
  total_turns: number;
  intent_breakdown: { [intent: string]: number };
  feedback_metrics: FeedbackMetrics;
  leads_captured_per_day: { [date: string]: number };
}

interface Lead {
  id: string;
  session_id: string;
  name: string | null;
  email: string | null;
  company: string | null;
  intent: string;
  score: number;
  updated_at: string;
}

export const Admin: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  // Enforce role check on render
  useEffect(() => {
    if (!user || user.role !== 'admin') {
      navigate('/chat');
    }
  }, [user, navigate]);

  // Data states
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Table filtering and sorting states
  const [searchQuery, setSearchQuery] = useState('');
  const [sortField, setSortField] = useState<keyof Lead>('score');
  const [sortAsc, setSortAsc] = useState(false);

  // Document upload state
  const [uploadState, setUploadState] = useState<{
    status: 'idle' | 'loading' | 'success' | 'error';
    message: string;
    chunksAdded?: number;
  }>({ status: 'idle', message: '' });
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchDashboardData = async () => {
    setError(null);
    try {
      const [analyticsRes, leadsRes] = await Promise.all([
        axios.get('/api/analytics', { withCredentials: true }),
        axios.get('/api/leads', { withCredentials: true })
      ]);

      setAnalytics(analyticsRes.data);
      setLeads(leadsRes.data);
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to retrieve admin dashboard records.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    if (user && user.role === 'admin') {
      fetchDashboardData();
    }
  }, [user]);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchDashboardData();
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const file = files[0];
    const extension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    
    if (!['.pdf', '.docx', '.txt'].includes(extension)) {
      setUploadState({
        status: 'error',
        message: 'Unsupported format. Use .pdf, .docx, or .txt'
      });
      return;
    }

    setUploadState({ status: 'loading', message: `Uploading "${file.name}"...` });

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await axios.post('/api/documents/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        withCredentials: true
      });

      setUploadState({
        status: 'success',
        message: `Successfully indexed "${file.name}"`,
        chunksAdded: res.data.chunks_added
      });
      
      // Refresh analytics and leads to reflect new state
      fetchDashboardData();

      // Auto clear upload success state after 5 seconds
      setTimeout(() => {
        setUploadState({ status: 'idle', message: '' });
      }, 5000);
    } catch (err: any) {
      setUploadState({
        status: 'error',
        message: err.response?.data?.detail || 'Failed to upload document.'
      });
    } finally {
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  // Sort and filter leads
  const handleSort = (field: keyof Lead) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(true);
    }
  };

  const filteredLeads = leads
    .filter(lead => {
      const searchLower = searchQuery.toLowerCase();
      return (
        (lead.name || '').toLowerCase().includes(searchLower) ||
        (lead.email || '').toLowerCase().includes(searchLower) ||
        (lead.company || '').toLowerCase().includes(searchLower) ||
        (lead.intent || '').toLowerCase().includes(searchLower)
      );
    })
    .sort((a, b) => {
      let valA = a[sortField];
      let valB = b[sortField];

      // Handle null cases
      if (valA === null) valA = '';
      if (valB === null) valB = '';

      if (typeof valA === 'string' && typeof valB === 'string') {
        return sortAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
      }
      if (typeof valA === 'number' && typeof valB === 'number') {
        return sortAsc ? valA - valB : valB - valA;
      }
      return 0;
    });

  // Calculate feedback rating percentage
  const feedbackPercentage = analytics
    ? Math.round(analytics.feedback_metrics.average_rating * 100)
    : 0;

  // Helper for rendering lead score badges
  const getScoreBadgeClass = (score: number) => {
    if (score >= 70) return 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20';
    if (score >= 30) return 'bg-amber-500/10 text-amber-400 border border-amber-500/20';
    return 'bg-zinc-800 text-zinc-400 border border-zinc-700/60';
  };

  const getScoreLabel = (score: number) => {
    if (score >= 70) return 'Hot Lead';
    if (score >= 30) return 'Warm Lead';
    return 'Cold Lead';
  };

  const getIntentBadgeClass = (intent: string) => {
    switch (intent.toLowerCase()) {
      case 'sales': return 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20';
      case 'pricing': return 'bg-purple-500/10 text-purple-400 border border-purple-500/20';
      case 'complaint': return 'bg-rose-500/10 text-rose-400 border border-rose-500/20';
      default: return 'bg-sky-500/10 text-sky-400 border border-sky-500/20'; // Support
    }
  };

  if (!user || user.role !== 'admin') {
    return null;
  }

  if (loading) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-zinc-950">
        <div className="flex flex-col items-center gap-4">
          <div className="h-12 w-12 animate-spin rounded-full border-4 border-indigo-500/80 border-t-transparent"></div>
          <p className="font-sans font-medium text-zinc-400 text-sm tracking-wide">Loading management report...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen w-screen bg-zinc-950 text-zinc-100 font-sans p-6 md:p-8 select-none overflow-y-auto">
      <div className="max-w-7xl mx-auto space-y-6">
        
        {/* Top Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-zinc-900 pb-5">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/chat')}
              className="p-2.5 rounded-xl bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-white hover:bg-zinc-800 transition-colors"
              title="Return to Chat"
              id="btn-back-to-chat"
            >
              <ArrowLeft size={18} />
            </button>
            <div>
              <h1 className="text-3xl font-extrabold tracking-tight text-white flex items-center gap-2">
                <span>RAG Operations Console</span>
                <span className="text-xs bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 px-2 py-0.5 rounded-full font-bold uppercase tracking-wider">
                  Admin
                </span>
              </h1>
              <p className="text-zinc-400 text-sm mt-1">Lead intelligence, conversational intent diagnostics, and agent metrics.</p>
            </div>
          </div>
          
          <div className="flex items-center gap-3 self-end sm:self-center">
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="flex items-center gap-2 py-2.5 px-4 rounded-xl bg-zinc-900 border border-zinc-800 text-zinc-300 hover:text-white hover:bg-zinc-800 transition-all font-semibold text-xs active:scale-[0.98]"
              id="btn-refresh-dashboard"
            >
              <RefreshCw size={14} className={refreshing ? 'animate-spin' : ''} />
              <span>Refresh Metrics</span>
            </button>
          </div>
        </div>

        {error && (
          <div className="flex items-start gap-3 p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-400">
            <AlertTriangle className="shrink-0 mt-0.5" size={18} />
            <div>
              <h4 className="font-bold">Error loading metrics</h4>
              <p className="text-sm text-rose-400/80 mt-1">{error}</p>
            </div>
          </div>
        )}

        {/* STATS OVERVIEW CARDS */}
        {analytics && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {/* Total Conversations */}
            <div className="glass-card rounded-2xl p-5 flex items-center justify-between">
              <div>
                <p className="text-zinc-500 text-xs font-semibold uppercase tracking-wider">Total Sessions</p>
                <h3 className="text-3xl font-extrabold text-white mt-1">{analytics.total_conversations}</h3>
                <p className="text-[10px] text-zinc-400 mt-1">Unique session identifiers</p>
              </div>
              <div className="p-3.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                <MessageSquare size={20} />
              </div>
            </div>

            {/* Total Turns */}
            <div className="glass-card rounded-2xl p-5 flex items-center justify-between">
              <div>
                <p className="text-zinc-500 text-xs font-semibold uppercase tracking-wider">Total Dialogue Turns</p>
                <h3 className="text-3xl font-extrabold text-white mt-1">{analytics.total_turns}</h3>
                <p className="text-[10px] text-zinc-400 mt-1">Total messages sent by users</p>
              </div>
              <div className="p-3.5 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400">
                <BarChart3 size={20} />
              </div>
            </div>

            {/* Feedback Score */}
            <div className="glass-card rounded-2xl p-5 flex items-center justify-between">
              <div>
                <p className="text-zinc-500 text-xs font-semibold uppercase tracking-wider">Avg Feedback Rating</p>
                <h3 className="text-3xl font-extrabold text-white mt-1">
                  {analytics.feedback_metrics.total_feedback > 0 ? `${feedbackPercentage}%` : 'N/A'}
                </h3>
                <p className="text-[10px] text-zinc-400 mt-1">
                  {analytics.feedback_metrics.up_count} up / {analytics.feedback_metrics.down_count} down
                </p>
              </div>
              <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
                <ThumbsUp size={20} />
              </div>
            </div>

            {/* Total Leads */}
            <div className="glass-card rounded-2xl p-5 flex items-center justify-between">
              <div>
                <p className="text-zinc-500 text-xs font-semibold uppercase tracking-wider">Leads Captured</p>
                <h3 className="text-3xl font-extrabold text-white mt-1">{leads.length}</h3>
                <p className="text-[10px] text-zinc-400 mt-1">Sales/Pricing triggers logged</p>
              </div>
              <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400">
                <Users size={20} />
              </div>
            </div>
          </div>
        )}

        {/* DOCUMENT UPLOADER */}
        <div className="glass-card rounded-2xl p-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Paperclip size={18} className="text-indigo-400" />
                <span>RAG Knowledge Base Ingestion</span>
              </h3>
              <p className="text-zinc-500 text-xs mt-0.5">Upload new reference policies (PDF, DOCX, TXT) to split and index into the vector store.</p>
            </div>
            <div>
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileUpload}
                accept=".pdf,.docx,.txt"
                className="hidden"
                id="admin-file-upload-input"
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={uploadState.status === 'loading'}
                className="flex items-center gap-2 py-2.5 px-5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs active:scale-[0.98] transition-all disabled:opacity-50"
                id="btn-admin-file-upload"
              >
                <span>Upload Document</span>
              </button>
            </div>
          </div>

          {/* Upload Status Banner */}
          {uploadState.status !== 'idle' && (
            <div className={`mt-4 p-4 rounded-xl border flex items-center justify-between text-xs font-semibold ${
              uploadState.status === 'loading' ? 'bg-indigo-500/10 border-indigo-500/20 text-indigo-400' :
              uploadState.status === 'success' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' :
              'bg-rose-500/10 border-rose-500/20 text-rose-400'
            }`}>
              <div className="flex items-center gap-2">
                <span>{uploadState.message}</span>
                {uploadState.status === 'success' && uploadState.chunksAdded !== undefined && (
                  <span className="bg-emerald-500/20 px-2 py-0.5 rounded text-[10px]">+{uploadState.chunksAdded} chunks</span>
                )}
              </div>
              {uploadState.status !== 'loading' && (
                <button 
                  onClick={() => setUploadState({ status: 'idle', message: '' })}
                  className="text-zinc-400 hover:text-white"
                >
                  Dismiss
                </button>
              )}
            </div>
          )}
        </div>

        {/* RECHARTS INTENTS & DAILY REGISTRATIONS */}
        {analytics && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            
            {/* Intent breakdown recharts BarChart */}
            <div className="glass-card rounded-2xl p-6 flex flex-col">
              <h3 className="text-md font-bold text-white mb-4 uppercase tracking-wider text-zinc-400 text-xs pl-1">
                Dialogue Intent Distribution
              </h3>
              
              <div className="w-full h-64 mt-auto">
                {Object.keys(analytics.intent_breakdown).length === 0 ? (
                  <div className="flex h-full items-center justify-center">
                    <p className="text-zinc-500 text-sm italic">No intent logs captured yet.</p>
                  </div>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={Object.entries(analytics.intent_breakdown).map(([name, value]) => ({ name, count: value }))}
                      margin={{ top: 10, right: 10, left: -25, bottom: 0 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
                      <XAxis 
                        dataKey="name" 
                        stroke="#71717a" 
                        fontSize={11} 
                        tickLine={false} 
                      />
                      <YAxis 
                        stroke="#71717a" 
                        fontSize={11} 
                        tickLine={false} 
                        allowDecimals={false} 
                      />
                      <Tooltip
                        contentStyle={{ 
                          backgroundColor: '#09090b', 
                          borderColor: '#27272a',
                          borderRadius: '12px',
                          color: '#f4f4f5',
                          fontSize: '11px',
                          fontFamily: 'sans-serif'
                        }}
                      />
                      <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                        {Object.keys(analytics.intent_breakdown).map((_, index) => {
                          const colors = ['#6366f1', '#a855f7', '#f43f5e', '#0ea5e9'];
                          return <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />;
                        })}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </div>
            </div>

            {/* Daily Leads Capture recharts AreaChart */}
            <div className="glass-card rounded-2xl p-6 flex flex-col">
              <h3 className="text-md font-bold text-white mb-4 uppercase tracking-wider text-zinc-400 text-xs pl-1">
                Leads Captured Trend
              </h3>
              
              <div className="w-full h-64 mt-auto">
                {Object.keys(analytics.leads_captured_per_day).length === 0 ? (
                  <div className="flex h-full items-center justify-center">
                    <p className="text-zinc-500 text-sm italic">No leads logged yet.</p>
                  </div>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart
                      data={Object.entries(analytics.leads_captured_per_day)
                        .map(([date, count]) => ({ date, count }))
                        .sort((a, b) => a.date.localeCompare(b.date))}
                      margin={{ top: 10, right: 10, left: -25, bottom: 0 }}
                    >
                      <defs>
                        <linearGradient id="colorLeads" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4}/>
                          <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
                      <XAxis 
                        dataKey="date" 
                        stroke="#71717a" 
                        fontSize={11} 
                        tickLine={false} 
                      />
                      <YAxis 
                        stroke="#71717a" 
                        fontSize={11} 
                        tickLine={false} 
                        allowDecimals={false} 
                      />
                      <Tooltip
                        contentStyle={{ 
                          backgroundColor: '#09090b', 
                          borderColor: '#27272a',
                          borderRadius: '12px',
                          color: '#f4f4f5',
                          fontSize: '11px',
                          fontFamily: 'sans-serif'
                        }}
                      />
                      <Area 
                        type="monotone" 
                        dataKey="count" 
                        stroke="#6366f1" 
                        strokeWidth={2.5}
                        fillOpacity={1} 
                        fill="url(#colorLeads)" 
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                )}
              </div>
            </div>

          </div>
        )}

        {/* LEADS INFORMATION TABLE */}
        <div className="glass-card rounded-2xl overflow-hidden">
          
          {/* Table Toolbar controls */}
          <div className="p-5 border-b border-zinc-900 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h3 className="text-lg font-bold text-white">Lead intelligence Records</h3>
              <p className="text-zinc-500 text-xs mt-0.5">Contact details and lead scores extracted from conversations by LLM.</p>
            </div>
            
            {/* Search Input filter */}
            <div className="relative w-full md:w-80">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-zinc-500" size={16} />
              <input
                type="text"
                placeholder="Search leads..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full glass-input pl-10 py-2.5 text-xs rounded-xl"
                id="input-lead-search"
              />
            </div>
          </div>

          {/* Table display */}
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-zinc-900 text-zinc-400 text-xs font-semibold tracking-wider uppercase bg-zinc-900/10">
                  <th 
                    onClick={() => handleSort('name')} 
                    className="p-4 cursor-pointer hover:text-white transition-colors"
                  >
                    <div className="flex items-center gap-1.5 select-none">
                      <span>Name</span>
                      <ArrowUpDown size={12} />
                    </div>
                  </th>
                  <th 
                    onClick={() => handleSort('email')} 
                    className="p-4 cursor-pointer hover:text-white transition-colors"
                  >
                    <div className="flex items-center gap-1.5 select-none">
                      <span>Email</span>
                      <ArrowUpDown size={12} />
                    </div>
                  </th>
                  <th 
                    onClick={() => handleSort('company')} 
                    className="p-4 cursor-pointer hover:text-white transition-colors"
                  >
                    <div className="flex items-center gap-1.5 select-none">
                      <span>Company</span>
                      <ArrowUpDown size={12} />
                    </div>
                  </th>
                  <th 
                    onClick={() => handleSort('intent')} 
                    className="p-4 cursor-pointer hover:text-white transition-colors"
                  >
                    <div className="flex items-center gap-1.5 select-none">
                      <span>Intent</span>
                      <ArrowUpDown size={12} />
                    </div>
                  </th>
                  <th 
                    onClick={() => handleSort('score')} 
                    className="p-4 cursor-pointer hover:text-white transition-colors"
                  >
                    <div className="flex items-center gap-1.5 select-none">
                      <span>Lead Score</span>
                      <ArrowUpDown size={12} />
                    </div>
                  </th>
                  <th 
                    onClick={() => handleSort('updated_at')} 
                    className="p-4 cursor-pointer hover:text-white transition-colors"
                  >
                    <div className="flex items-center gap-1.5 select-none">
                      <span>Captured Date</span>
                      <ArrowUpDown size={12} />
                    </div>
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-900/40 text-sm font-medium">
                {filteredLeads.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="p-8 text-center text-zinc-500 italic">
                      No matching lead records found.
                    </td>
                  </tr>
                ) : (
                  filteredLeads.map((lead) => (
                    <tr key={lead.id} className="hover:bg-zinc-900/30 transition-colors" id={`lead-row-${lead.id}`}>
                      {/* Name */}
                      <td className="p-4 text-white">
                        <div className="flex items-center gap-2.5">
                          <div className="h-7 w-7 rounded-lg bg-zinc-800 flex items-center justify-center text-zinc-300 text-xs font-bold uppercase">
                            {(lead.name || lead.email || 'U').substring(0, 2)}
                          </div>
                          <span>{lead.name || 'Anonymous User'}</span>
                        </div>
                      </td>
                      
                      {/* Email */}
                      <td className="p-4 text-zinc-400 font-mono text-xs">
                        {lead.email || (
                          <span className="text-zinc-600 italic">Not shared</span>
                        )}
                      </td>
                      
                      {/* Company */}
                      <td className="p-4 text-zinc-300">
                        {lead.company ? (
                          <div className="flex items-center gap-1.5">
                            <Briefcase size={13} className="text-zinc-500" />
                            <span>{lead.company}</span>
                          </div>
                        ) : (
                          <span className="text-zinc-600 italic">Not extracted</span>
                        )}
                      </td>
                      
                      {/* Intent */}
                      <td className="p-4">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${getIntentBadgeClass(lead.intent)}`}>
                          {lead.intent}
                        </span>
                      </td>
                      
                      {/* Score */}
                      <td className="p-4">
                        <div className="flex items-center gap-2">
                          <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold ${getScoreBadgeClass(lead.score)}`}>
                            {lead.score} / 100
                          </span>
                          <span className="text-[10px] text-zinc-500 font-semibold">{getScoreLabel(lead.score)}</span>
                        </div>
                      </td>
                      
                      {/* Captured Date */}
                      <td className="p-4 text-zinc-500 text-xs">
                        {lead.updated_at ? new Date(lead.updated_at).toLocaleString() : 'N/A'}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

        </div>

      </div>
    </div>
  );
};
