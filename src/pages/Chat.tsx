import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../App';
import { 
  Bot, User, LogOut, LayoutDashboard, Plus, Trash2, Send, Paperclip, 
  ChevronDown, ChevronUp, ThumbsUp, ThumbsDown, FileText, Check, AlertTriangle, 
  HelpCircle, MessageSquarePlus, Sparkles
} from 'lucide-react';

interface Source {
  source: string;
  content: string;
  score?: number;
}

interface Message {
  id?: string;
  sender: 'user' | 'bot';
  text: string;
  timestamp: string;
  sources?: Source[];
  feedback?: 'up' | 'down' | null;
  intent?: string;
}

interface Session {
  id: string;
  title: string;
  lastActive: string;
}

// Simple Markdown/HTML formatting helper for RAG responses
const formatMessageText = (text: string) => {
  if (!text) return '';
  
  // Replace bold syntax
  let formatted = text.replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold text-white">$1</strong>');
  
  // Replace italic syntax
  formatted = formatted.replace(/\*(.*?)\*/g, '<em class="italic text-zinc-300">$1</em>');
  
  // Parse headers
  formatted = formatted.replace(/^### (.*?)$/gm, '<h4 class="text-md font-semibold text-indigo-300 mt-2 mb-1">$1</h4>');
  formatted = formatted.replace(/^## (.*?)$/gm, '<h3 class="text-lg font-bold text-indigo-400 mt-3 mb-1.5">$1</h3>');
  formatted = formatted.replace(/^# (.*?)$/gm, '<h2 class="text-xl font-extrabold text-indigo-500 mt-4 mb-2">$1</h2>');

  // Parse lists
  formatted = formatted.replace(/^\s*[-*]\s+(.*?)$/gm, '<li class="ml-4 list-disc text-zinc-300">$1</li>');

  // Convert code blocks
  formatted = formatted.replace(/`(.*?)`/g, '<code class="bg-zinc-800 text-indigo-300 px-1.5 py-0.5 rounded font-mono text-xs">$1</code>');

  // Replace double linebreaks with paragraphs
  const paragraphs = formatted.split(/\n\n+/);
  return paragraphs.map((para) => {
    if (para.trim().startsWith('<li') || para.trim().startsWith('<h')) {
      return para;
    }
    // Replace single line breaks inside paragraph with <br/>
    return `<p class="mb-2.5 leading-relaxed text-zinc-200">${para.replace(/\n/g, '<br/>')}</p>`;
  }).join('');
};

export const Chat: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  // Sessions state
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string>('');
  
  // Active chat state
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isBotTyping, setIsBotTyping] = useState(false);
  const [expandedSources, setExpandedSources] = useState<{ [messageIndex: number]: boolean }>({});

  // Document upload state
  const [uploadState, setUploadState] = useState<{
    status: 'idle' | 'loading' | 'success' | 'error';
    message: string;
    chunksAdded?: number;
  }>({ status: 'idle', message: '' });

  // UI state
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Initialize and load sessions from LocalStorage
  useEffect(() => {
    const cachedSessions = localStorage.getItem('chat_sessions');
    if (cachedSessions) {
      const parsed = JSON.parse(cachedSessions) as Session[];
      setSessions(parsed);
      if (parsed.length > 0) {
        // Select the most recent session
        setActiveSessionId(parsed[0].id);
      } else {
        createNewSession();
      }
    } else {
      createNewSession();
    }
  }, []);

  // Fetch history from DB whenever the active session ID changes
  useEffect(() => {
    if (!activeSessionId) return;

    const fetchSessionHistory = async () => {
      setMessages([]);
      setIsBotTyping(false);
      try {
        const response = await axios.get(`/api/chat/history/${activeSessionId}`, { withCredentials: true });
        const turns = response.data;
        const formattedMessages: Message[] = [];
        
        turns.forEach((turn: any) => {
          // User message
          formattedMessages.push({
            sender: 'user',
            text: turn.message,
            timestamp: turn.timestamp,
            intent: turn.intent
          });
          // Bot answer
          formattedMessages.push({
            id: turn.id, // MongoDB turn ID for feedback
            sender: 'bot',
            text: turn.answer,
            timestamp: turn.timestamp,
            sources: turn.sources || [],
            feedback: turn.feedback
          });
        });
        setMessages(formattedMessages);
      } catch (err: any) {
        console.error('Error fetching session history:', err);
        showToast('Failed to load chat history.', 'error');
      }
    };

    fetchSessionHistory();
  }, [activeSessionId]);

  // Scroll to bottom whenever messages are added
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isBotTyping]);

  // Toast auto-dismissal
  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [toast]);

  const showToast = (message: string, type: 'success' | 'error') => {
    setToast({ message, type });
  };

  const createNewSession = (customTitle?: string) => {
    const newId = `session_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
    const newSession: Session = {
      id: newId,
      title: customTitle || `New Chat Session`,
      lastActive: new Date().toISOString()
    };

    const updatedSessions = [newSession, ...sessions];
    setSessions(updatedSessions);
    localStorage.setItem('chat_sessions', JSON.stringify(updatedSessions));
    setActiveSessionId(newId);
    setMessages([]);
  };

  const deleteSession = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const updated = sessions.filter(s => s.id !== id);
    setSessions(updated);
    localStorage.setItem('chat_sessions', JSON.stringify(updated));

    if (activeSessionId === id) {
      if (updated.length > 0) {
        setActiveSessionId(updated[0].id);
      } else {
        createNewSession();
      }
    }
  };

  const updateSessionTitle = (id: string, message: string) => {
    // Generate a title based on the first user message (up to 30 chars)
    const title = message.length > 30 ? `${message.substring(0, 27)}...` : message;
    const updated = sessions.map(s => {
      if (s.id === id) {
        return { ...s, title, lastActive: new Date().toISOString() };
      }
      return s;
    });
    setSessions(updated);
    localStorage.setItem('chat_sessions', JSON.stringify(updated));
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || isBotTyping) return;

    const userQuery = inputText.trim();
    setInputText('');

    // Append User Message in UI
    const userMessage: Message = {
      sender: 'user',
      text: userQuery,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMessage]);

    // If it is the first message of the session, rename the session title
    const sessionMessages = messages.filter(m => m.sender === 'user');
    if (sessionMessages.length === 0) {
      updateSessionTitle(activeSessionId, userQuery);
    }

    setIsBotTyping(true);

    try {
      const response = await axios.post('/api/chat', {
        session_id: activeSessionId,
        message: userQuery
      }, { withCredentials: true });

      const { answer, sources, conversation_id } = response.data;

      // Append Bot response
      setMessages(prev => [...prev, {
        id: conversation_id, // stored MongoDB turn ID
        sender: 'bot',
        text: answer,
        timestamp: new Date().toISOString(),
        sources: sources || [],
        feedback: null
      }]);
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Error getting RAG answer.', 'error');
      setMessages(prev => [...prev, {
        sender: 'bot',
        text: '❌ I encountered an error while trying to process your request. Please check that the backend is running and you have uploaded files for RAG context.',
        timestamp: new Date().toISOString()
      }]);
    } finally {
      setIsBotTyping(false);
    }
  };

  const submitFeedback = async (messageIndex: number, turnId: string, rating: 'up' | 'down') => {
    try {
      await axios.post('/api/feedback', {
        conversation_id: turnId,
        rating
      }, { withCredentials: true });

      // Update local state
      setMessages(prev => prev.map((msg, idx) => {
        if (idx === messageIndex) {
          return { ...msg, feedback: rating };
        }
        return msg;
      }));

      showToast(`Feedback recorded as thumbs ${rating}!`, 'success');
    } catch (err: any) {
      showToast('Failed to submit feedback.', 'error');
    }
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
        message: `Indexed "${file.name}"`,
        chunksAdded: res.data.chunks_added
      });
      showToast('Document ingested successfully!', 'success');
      
      // Auto clear upload success state after 5 seconds
      setTimeout(() => {
        setUploadState({ status: 'idle', message: '' });
      }, 5000);
    } catch (err: any) {
      setUploadState({
        status: 'error',
        message: err.response?.data?.detail || 'Failed to upload document.'
      });
      showToast('Ingestion failed.', 'error');
    } finally {
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleLogout = async () => {
    try {
      await axios.post('/api/auth/logout');
      logout();
      navigate('/login');
    } catch (err) {
      showToast('Failed to log out.', 'error');
    }
  };

  const toggleSources = (index: number) => {
    setExpandedSources(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  return (
    <div className="h-screen w-screen flex bg-zinc-950 text-zinc-100 font-sans select-none overflow-hidden relative">
      
      {/* Toast Alert */}
      {toast && (
        <div className={`absolute top-6 right-6 z-50 flex items-center gap-2.5 px-4 py-3 rounded-xl shadow-2xl border transition-all duration-300 animate-slide-in ${
          toast.type === 'success' 
            ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' 
            : 'bg-rose-500/10 border-rose-500/20 text-rose-400'
        }`}>
          {toast.type === 'success' ? <Check size={18} /> : <AlertTriangle size={18} />}
          <span className="text-sm font-medium">{toast.message}</span>
        </div>
      )}

      {/* LEFT SIDEBAR */}
      <div className="w-[310px] shrink-0 border-r border-zinc-900 bg-zinc-950 flex flex-col justify-between">
        
        {/* Upper Sidebar */}
        <div className="flex flex-col flex-1 min-h-0">
          
          {/* Sidebar Header & Brand Logo */}
          <div className="p-5 border-b border-zinc-900/60 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                <Bot size={22} />
              </div>
              <div>
                <h2 className="text-md font-bold text-zinc-100 tracking-tight leading-none">Nexus RAG</h2>
                <span className="text-[10px] text-zinc-500 font-medium">FastAPI & FAISS</span>
              </div>
            </div>
            
            <button
              onClick={() => createNewSession()}
              className="p-2 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-white hover:bg-zinc-800 transition-colors"
              title="New Conversation"
              id="btn-new-chat"
            >
              <Plus size={16} />
            </button>
          </div>

          {/* Conversations Session List */}
          <div className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
            <span className="text-[10px] font-bold text-zinc-500 px-3 uppercase tracking-wider block mb-2">
              Recent Conversations
            </span>
            {sessions.length === 0 ? (
              <div className="text-zinc-600 text-xs text-center py-4 italic">No conversations</div>
            ) : (
              sessions.map((session) => (
                <div
                  key={session.id}
                  onClick={() => setActiveSessionId(session.id)}
                  className={`group flex items-center justify-between px-3 py-2.5 rounded-xl cursor-pointer text-sm font-medium transition-all duration-200 ${
                    activeSessionId === session.id
                      ? 'bg-indigo-600/10 text-indigo-400 border border-indigo-500/20'
                      : 'text-zinc-400 border border-transparent hover:bg-zinc-900/60 hover:text-zinc-200'
                  }`}
                  id={`session-item-${session.id}`}
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <HelpCircle size={15} className={activeSessionId === session.id ? 'text-indigo-400' : 'text-zinc-500'} />
                    <span className="truncate pr-2">{session.title}</span>
                  </div>
                  <button
                    onClick={(e) => deleteSession(session.id, e)}
                    className="p-1 text-zinc-600 hover:text-rose-400 rounded hover:bg-zinc-800 opacity-0 group-hover:opacity-100 transition-all"
                    title="Delete Session"
                    id={`btn-delete-session-${session.id}`}
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              ))
            )}
          </div>

          {/* Context Ingestion Panel (Admin Only) */}
          {user?.role === 'admin' && (
            <div className="p-4 border-t border-zinc-900 bg-zinc-950">
              <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider block mb-2.5">
                Knowledge Ingestion
              </span>
              
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileUpload}
                className="hidden"
                accept=".pdf,.docx,.txt"
                id="input-file-upload"
              />
              
              <div 
                onClick={() => fileInputRef.current?.click()}
                className={`border border-dashed rounded-xl p-3.5 text-center cursor-pointer group transition-all duration-300 ${
                  uploadState.status === 'loading'
                    ? 'border-indigo-500/50 bg-indigo-500/5 pointer-events-none'
                    : 'border-zinc-800 bg-zinc-900/20 hover:border-indigo-500/30 hover:bg-zinc-900/60'
                }`}
                id="dropzone-file-upload"
              >
                {uploadState.status === 'loading' ? (
                  <div className="flex flex-col items-center gap-2">
                    <div className="h-6 w-6 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent"></div>
                    <span className="text-xs font-medium text-zinc-400">Embedding document...</span>
                  </div>
                ) : uploadState.status === 'success' ? (
                  <div className="flex flex-col items-center gap-1">
                    <Check className="text-emerald-400" size={20} />
                    <span className="text-xs font-semibold text-emerald-400">{uploadState.message}</span>
                    <span className="text-[9px] text-zinc-500">{uploadState.chunksAdded} text chunks indexed</span>
                  </div>
                ) : uploadState.status === 'error' ? (
                  <div className="flex flex-col items-center gap-1">
                    <AlertTriangle className="text-rose-400" size={20} />
                    <span className="text-xs font-semibold text-rose-400 truncate w-full px-2">{uploadState.message}</span>
                    <span className="text-[9px] text-zinc-500 hover:text-indigo-400 transition-colors">Click to retry</span>
                  </div>
                ) : (
                  <div className="flex flex-col items-center gap-1">
                    <Paperclip className="text-zinc-500 group-hover:text-indigo-400 transition-colors" size={18} />
                    <span className="text-xs font-medium text-zinc-300">Upload context document</span>
                    <span className="text-[9px] text-zinc-500">Supports PDF, DOCX, TXT</span>
                  </div>
                )}
              </div>
            </div>
          )}

        </div>

        {/* Lower Sidebar (User Profile & Actions) */}
        <div className="p-4 border-t border-zinc-900 bg-zinc-950 flex flex-col gap-2.5">
          <div className="flex items-center gap-3 px-1.5 py-1">
            <div className="h-9 w-9 rounded-xl bg-zinc-800 border border-zinc-700 flex items-center justify-center text-zinc-300">
              <User size={18} />
            </div>
            <div className="min-w-0 flex-1">
              <h4 className="text-sm font-semibold text-zinc-200 truncate leading-none mb-0.5">{user?.name}</h4>
              <span className={`text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded-full ${
                user?.role === 'admin' 
                  ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' 
                  : 'bg-zinc-800 text-zinc-400 border border-zinc-700/50'
              }`}>{user?.role}</span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2 mt-1">
            {user?.role === 'admin' && (
              <button
                onClick={() => navigate('/admin')}
                className="flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-300 hover:text-indigo-400 hover:border-indigo-500/30 hover:bg-zinc-900 transition-all text-xs font-semibold"
                id="btn-admin-dashboard"
              >
                <LayoutDashboard size={14} />
                <span>Admin</span>
              </button>
            )}
            <button
              onClick={handleLogout}
              className={`flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-rose-400 hover:border-rose-500/20 hover:bg-zinc-900 transition-all text-xs font-semibold ${
                user?.role !== 'admin' ? 'col-span-2' : ''
              }`}
              id="btn-logout"
            >
              <LogOut size={14} />
              <span>Log Out</span>
            </button>
          </div>
        </div>

      </div>

      {/* RIGHT CHAT AREA */}
      <div className="flex-1 flex flex-col bg-zinc-950">
        
        {/* Chat header */}
        <div className="h-[65px] border-b border-zinc-900 flex items-center justify-between px-6">
          <div className="flex items-center gap-3">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <h1 className="text-md font-bold text-zinc-200">
              {sessions.find(s => s.id === activeSessionId)?.title || 'Chat Agent'}
            </h1>
          </div>
          
          <div className="flex items-center gap-2">
            <button
              onClick={() => createNewSession(`New Chat Session`)}
              className="flex items-center gap-1.5 py-1.5 px-3 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-white hover:bg-zinc-800 transition-all text-xs font-medium"
              id="btn-clear-chat"
            >
              <MessageSquarePlus size={14} />
              <span>New Thread</span>
            </button>
          </div>
        </div>

        {/* Message Log */}
        <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
          
          {messages.length === 0 && !isBotTyping ? (
            <div className="h-full flex flex-col items-center justify-center text-center max-w-xl mx-auto space-y-6 select-none">
              <div className="p-4 rounded-3xl bg-indigo-500/5 border border-indigo-500/10 text-indigo-400">
                <Sparkles size={40} className="animate-pulse" />
              </div>
              <div className="space-y-2">
                <h3 className="text-2xl font-bold tracking-tight text-zinc-100">AI Knowledge Assistant</h3>
                <p className="text-zinc-400 text-sm font-light leading-relaxed">
                  {user?.role === 'admin'
                    ? 'Welcome to Nexus RAG! Upload a company policy, contract, or notes in the sidebar to index them, and test questions grounded directly in the text.'
                    : 'Welcome to Nexus RAG! Ask me questions about company policies, products, or guidelines, and I will answer them grounded in our corporate database.'}
                </p>
              </div>
              <div className="grid grid-cols-2 gap-3 w-full">
                <div 
                  onClick={() => setInputText("What is the main topic of the uploaded document?")}
                  className="p-3.5 rounded-xl bg-zinc-900/40 border border-zinc-900 hover:border-zinc-800/80 hover:bg-zinc-900 cursor-pointer text-left transition-all group"
                >
                  <h4 className="text-xs font-bold text-zinc-300 mb-1 group-hover:text-indigo-400">Document Overview</h4>
                  <p className="text-[11px] text-zinc-500">"What is the main topic of the uploaded document?"</p>
                </div>
                <div 
                  onClick={() => setInputText("Summarize the key requirements or details.")}
                  className="p-3.5 rounded-xl bg-zinc-900/40 border border-zinc-900 hover:border-zinc-800/80 hover:bg-zinc-900 cursor-pointer text-left transition-all group"
                >
                  <h4 className="text-xs font-bold text-zinc-300 mb-1 group-hover:text-indigo-400">Context Summary</h4>
                  <p className="text-[11px] text-zinc-500">"Summarize the key requirements or details."</p>
                </div>
              </div>
            </div>
          ) : (
            messages.map((msg, index) => (
              <div
                key={index}
                className={`flex gap-4 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                id={`chat-message-${index}`}
              >
                {/* Bot Avatar */}
                {msg.sender === 'bot' && (
                  <div className="h-9 w-9 rounded-xl bg-indigo-600/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center shrink-0">
                    <Bot size={18} />
                  </div>
                )}

                {/* Message bubble wrapper */}
                <div className={`max-w-[70%] flex flex-col gap-1.5 ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}>
                  
                  {/* Sender Metadata */}
                  <div className="flex items-center gap-2 px-1 text-[10px] text-zinc-500 font-semibold tracking-wider">
                    <span>{msg.sender === 'user' ? 'YOU' : 'ASSISTANT'}</span>
                    <span>•</span>
                    <span>{new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    {msg.intent && (
                      <>
                        <span>•</span>
                        <span className="bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 px-1.5 py-0.5 rounded-full text-[8px] font-bold">
                          {msg.intent}
                        </span>
                      </>
                    )}
                  </div>

                  {/* Main Bubble */}
                  <div className={`rounded-2xl p-4 shadow-md leading-relaxed ${
                    msg.sender === 'user'
                      ? 'bg-gradient-to-br from-indigo-600 to-indigo-700 text-white rounded-tr-none'
                      : 'bg-zinc-900/60 border border-zinc-800/80 rounded-tl-none text-zinc-100'
                  }`}>
                    {msg.sender === 'user' ? (
                      <p className="text-zinc-100 text-sm whitespace-pre-wrap">{msg.text}</p>
                    ) : (
                      <div 
                        className="text-sm prose prose-invert max-w-none"
                        dangerouslySetInnerHTML={{ __html: formatMessageText(msg.text) }}
                      />
                    )}
                  </div>

                  {/* Bot Sources and Feedback controls */}
                  {msg.sender === 'bot' && (
                    <div className="flex items-center justify-between w-full px-1 text-zinc-500 text-xs">
                      
                      {/* Collapsible Sources Toggle */}
                      {msg.sources && msg.sources.length > 0 ? (
                        <button
                          onClick={() => toggleSources(index)}
                          className="flex items-center gap-1 hover:text-indigo-400 transition-colors font-medium text-[11px]"
                          id={`btn-toggle-sources-${index}`}
                        >
                          {expandedSources[index] ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
                          <span>{expandedSources[index] ? 'Hide' : 'View'} References ({msg.sources.length})</span>
                        </button>
                      ) : (
                        <span className="text-[10px] text-zinc-600">No referenced sources</span>
                      )}

                      {/* Feedback Buttons */}
                      {msg.id && (
                        <div className="flex items-center gap-1.5">
                          <button
                            onClick={() => submitFeedback(index, msg.id!, 'up')}
                            className={`p-1.5 rounded-lg border transition-all duration-200 ${
                              msg.feedback === 'up'
                                ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
                                : 'bg-transparent border-zinc-900 hover:text-zinc-300 hover:bg-zinc-900'
                            }`}
                            title="Upvote response"
                            id={`btn-feedback-up-${index}`}
                          >
                            <ThumbsUp size={12} />
                          </button>
                          <button
                            onClick={() => submitFeedback(index, msg.id!, 'down')}
                            className={`p-1.5 rounded-lg border transition-all duration-200 ${
                              msg.feedback === 'down'
                                ? 'bg-rose-500/10 border-rose-500/20 text-rose-400'
                                : 'bg-transparent border-zinc-900 hover:text-zinc-300 hover:bg-zinc-900'
                            }`}
                            title="Downvote response"
                            id={`btn-feedback-down-${index}`}
                          >
                            <ThumbsDown size={12} />
                          </button>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Expanded References List */}
                  {msg.sender === 'bot' && msg.sources && msg.sources.length > 0 && expandedSources[index] && (
                    <div className="w-full mt-2 space-y-2 border-l border-zinc-800 pl-3.5 py-1 text-left animate-slide-in">
                      {msg.sources.map((source, sIdx) => (
                        <div key={sIdx} className="bg-zinc-900/30 p-2.5 rounded-xl border border-zinc-900">
                          <div className="flex items-center justify-between mb-1.5">
                            <div className="flex items-center gap-1.5 text-zinc-400 text-xs font-semibold">
                              <FileText size={12} className="text-indigo-400" />
                              <span className="truncate max-w-[180px]">{source.source}</span>
                            </div>
                            {source.score !== undefined && (
                              <span className="text-[10px] bg-zinc-800 text-zinc-400 px-1.5 py-0.5 rounded font-mono">
                                Match: {source.score.toFixed(3)}
                              </span>
                            )}
                          </div>
                          <p className="text-[11px] text-zinc-500 italic leading-relaxed">
                            "{source.content}"
                          </p>
                        </div>
                      ))}
                    </div>
                  )}

                </div>

                {/* User Avatar */}
                {msg.sender === 'user' && (
                  <div className="h-9 w-9 rounded-xl bg-zinc-800 border border-zinc-700 text-zinc-300 flex items-center justify-center shrink-0">
                    <User size={18} />
                  </div>
                )}
              </div>
            ))
          )}

          {/* Typing Indicator */}
          {isBotTyping && (
            <div className="flex gap-4 justify-start" id="bot-typing-indicator">
              <div className="h-9 w-9 rounded-xl bg-indigo-600/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center shrink-0">
                <Bot size={18} />
              </div>
              <div className="flex flex-col gap-1.5">
                <div className="flex items-center gap-1 text-[10px] text-zinc-500 font-semibold tracking-wider">
                  <span>ASSISTANT</span>
                  <span>•</span>
                  <span>thinking...</span>
                </div>
                <div className="rounded-2xl p-4 bg-zinc-900/40 border border-zinc-900 rounded-tl-none flex items-center gap-1 px-5 py-3.5">
                  <div className="h-2 w-2 bg-indigo-400 rounded-full typing-dot"></div>
                  <div className="h-2 w-2 bg-indigo-400 rounded-full typing-dot"></div>
                  <div className="h-2 w-2 bg-indigo-400 rounded-full typing-dot"></div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-6 border-t border-zinc-900 bg-zinc-950">
          <form onSubmit={handleSendMessage} className="relative flex items-center max-w-4xl mx-auto">
            <input
              type="text"
              placeholder="Ask a question about your documents..."
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              disabled={isBotTyping}
              className="w-full glass-input pr-16 py-3.5"
              autoFocus
              id="input-chat-query"
            />
            <button
              type="submit"
              disabled={!inputText.trim() || isBotTyping}
              className="absolute right-2 top-1/2 -translate-y-1/2 h-10 w-10 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white flex items-center justify-center transition-all disabled:opacity-30 disabled:cursor-not-allowed"
              id="btn-submit-chat"
            >
              <Send size={16} />
            </button>
          </form>
        </div>

      </div>

    </div>
  );
};
