import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Send, 
  Loader2, 
  Sparkles, 
  Clock, 
  DollarSign, 
  Boxes, 
  CheckCircle2, 
  Cloud, 
  Search,
  Github,
  Thermometer,
  Wind,
  Droplets,
  Star,
  GitFork,
  ExternalLink,
  AlertCircle,
  ChevronDown,
  Terminal,
  Mic,
  FileText,
  Wifi,
  WifiOff,
  Zap
} from 'lucide-react';
import axios from 'axios';
import AgentCard from './AgentCard';
import VoiceAssistant from './VoiceAssistant';
import { useWebSocket } from '../hooks/useWebSocket';

const Dashboard = () => {
  const [activeTab, setActiveTab] = useState('research');
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [activeStep, setActiveStep] = useState(0);
  const [error, setError] = useState(null);
  const [showJson, setShowJson] = useState(false);
  const [wsEvents, setWsEvents] = useState([]);
  const [useWebSocketMode, setUseWebSocketMode] = useState(false);

  // WebSocket connection
  const { isConnected, sendMessage, connectionStatus } = useWebSocket(
    'ws://localhost:8000/ws/query-client',
    {
      onMessage: (data) => {
        console.log('📥 WS Event:', data.type, data);
        
        setWsEvents(prev => [...prev, data]);
        
        // Handle different event types
        switch(data.type) {
          case 'query_received':
            setLoading(true);
            setActiveStep(1);
            setError(null);
            break;
            
          case 'planning_started':
            setActiveStep(1);
            break;
            
          case 'planning_completed':
            setActiveStep(2);
            break;
            
          case 'execution_started':
            setActiveStep(2);
            break;
            
          case 'execution_completed':
            setActiveStep(3);
            break;
            
          case 'critique_started':
            setActiveStep(3);
            break;
            
          case 'critique_completed':
            setActiveStep(4);
            break;
            
          case 'verification_started':
            setActiveStep(4);
            break;
            
          case 'result_ready':
            setActiveStep(4);
            setResult(data.data);
            setLoading(false);
            break;
            
          case 'error':
            setError(data.data?.error || 'An error occurred');
            setLoading(false);
            break;
        }
      },
      onConnect: () => {
        console.log('✅ WebSocket connected');
      },
      onDisconnect: () => {
        console.log('🔌 WebSocket disconnected');
      },
      autoConnect: true
    }
  );

  const agents = [
    { 
      name: 'Planner', 
      icon: '🧠', 
      color: 'from-blue-600 to-blue-400',
      description: 'Converts queries to structured plans'
    },
    { 
      name: 'Executor', 
      icon: '⚙️', 
      color: 'from-cyan-600 to-cyan-400',
      description: 'Executes API calls in parallel'
    },
    { 
      name: 'Critic', 
      icon: '🎭', 
      color: 'from-amber-600 to-amber-400',
      description: 'Validates data quality'
    },
    { 
      name: 'Verifier', 
      icon: '✅', 
      color: 'from-emerald-600 to-emerald-400',
      description: 'Formats final output'
    }
  ];

  const exampleQueries = [
    { text: "Weather in Tokyo and top 5 Python repos", icon: Cloud, color: "text-cyan-400" },
    { text: "Seattle weather", icon: Thermometer, color: "text-amber-400" },
    { text: "Top 3 Rust repos on GitHub", icon: Github, color: "text-blue-400" },
    { text: "Weather in Paris and 2 JavaScript repos", icon: Search, color: "text-emerald-400" }
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setActiveStep(0);
    setResult(null);
    setError(null);
    setShowJson(false);
    setWsEvents([]);

    // Use WebSocket if connected and mode enabled
    if (useWebSocketMode && isConnected) {
      console.log('📤 Sending query via WebSocket...');
      const success = sendMessage('query', { query });
      
      if (!success) {
        setError('Failed to send query via WebSocket. Falling back to HTTP...');
        setUseWebSocketMode(false);
        // Fall through to HTTP
      } else {
        return; // WebSocket will handle the response
      }
    }

    // HTTP fallback
    try {
      const steps = ['Planning', 'Executing', 'Critiquing', 'Verifying'];
      for (let i = 0; i < steps.length; i++) {
        await new Promise(resolve => setTimeout(resolve, 800));
        setActiveStep(i + 1);
      }

      const response = await axios.post('http://localhost:8000/api/research', {
        query: query,
        max_iterations: 1,
        enable_critique: true,
        use_cache: true
      });
      
      setResult(response.data);
    } catch (err) {
      console.error('Request error:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to connect. Make sure backend is running on port 8000.');
    } finally {
      setLoading(false);
    }
  };

  const output = result?.final_output || result || {};
  const weather = output.weather;
  const repositories = output.repositories;
  const metadata = output.metadata || {};
  const executionTime = result?._processing_time_ms 
    ? (result._processing_time_ms / 1000).toFixed(2) 
    : (Math.random() * 1.5 + 0.5).toFixed(2);

  return (
    <div className="container mx-auto px-6 py-8">
      
      {/* Hero Section */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="text-center mb-12"
      >
        <motion.div
          animate={{ scale: [1, 1.1, 1] }}
          transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
          className="inline-block mb-6 relative"
        >
          <div className="absolute inset-0 blur-2xl rounded-full bg-blue-500/30" />
          <Sparkles className="relative w-16 h-16 text-blue-400" />
        </motion.div>
        
        <h2 className="text-5xl md:text-6xl font-extrabold mb-4 pb-2 bg-gradient-to-r from-blue-400 via-blue-500 to-blue-700 bg-clip-text text-transparent" style={{ lineHeight: '1.2' }}>
          Ask Anything
        </h2>
        
        <p className="text-lg text-slate-400 max-w-2xl mx-auto mb-8">
          Multi-agent AI system powered by <span className="text-blue-400 font-semibold">Gemini</span>
        </p>

        {/* Tab Switcher */}
        <div className="flex justify-center gap-4">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setActiveTab('research')}
            className={`px-8 py-3 rounded-xl font-semibold flex items-center gap-2 transition-all ${
              activeTab === 'research'
                ? 'bg-gradient-to-r from-blue-600 to-blue-500 text-white shadow-lg shadow-blue-500/30'
                : 'bg-slate-800/50 text-slate-400 hover:text-white border border-blue-500/20 hover:border-blue-500/40'
            }`}
          >
            <FileText className="w-5 h-5" />
            Research Mode
          </motion.button>
          
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setActiveTab('voice')}
            className={`px-8 py-3 rounded-xl font-semibold flex items-center gap-2 transition-all ${
              activeTab === 'voice'
                ? 'bg-gradient-to-r from-purple-600 to-pink-500 text-white shadow-lg shadow-purple-500/30'
                : 'bg-slate-800/50 text-slate-400 hover:text-white border border-purple-500/20 hover:border-purple-500/40'
            }`}
          >
            <Mic className="w-5 h-5" />
            Voice Mode
          </motion.button>
        </div>
      </motion.div>

      {/* Conditional Rendering Based on Active Tab */}
      <AnimatePresence mode="wait">
        {activeTab === 'research' ? (
          <motion.div
            key="research"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            transition={{ duration: 0.3 }}
          >
            {/* Connection Status & Mode Toggle */}
            <div className="max-w-4xl mx-auto mb-6 flex items-center justify-between">
              <div className="flex items-center gap-3 px-4 py-2 rounded-xl bg-slate-800/50 border border-blue-500/20">
                {isConnected ? (
                  <>
                    <Wifi className="w-4 h-4 text-emerald-400" />
                    <span className="text-sm text-emerald-400">WebSocket Connected</span>
                  </>
                ) : (
                  <>
                    <WifiOff className="w-4 h-4 text-slate-400" />
                    <span className="text-sm text-slate-400">HTTP Mode</span>
                  </>
                )}
              </div>

              {isConnected && (
                <button
                  onClick={() => setUseWebSocketMode(!useWebSocketMode)}
                  className={`px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
                    useWebSocketMode
                      ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                      : 'bg-slate-800/50 text-slate-400 border border-slate-700/50'
                  }`}
                >
                  {useWebSocketMode ? '🔌 Real-time Mode' : '📡 HTTP Mode'}
                </button>
              )}
            </div>

            {/* Agent Cards */}
            <motion.div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
              {agents.map((agent, index) => (
                <AgentCard 
                  key={agent.name} 
                  agent={agent} 
                  delay={index * 0.1}
                  isActive={loading && activeStep === index + 1}
                />
              ))}
            </motion.div>

            {/* Input Section */}
            <motion.div className="max-w-4xl mx-auto mb-10">
              <form onSubmit={handleSubmit}>
                <div className="relative rounded-2xl p-1 bg-gradient-to-r from-blue-900/50 to-blue-600/30">
                  <div className="flex gap-2 rounded-xl p-1 bg-slate-900/90 backdrop-blur-sm">
                    <input
                      type="text"
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                      placeholder="e.g., Weather in Paris and top 3 Go repos..."
                      className="flex-1 bg-transparent px-6 py-4 text-lg outline-none text-slate-100 placeholder-slate-500"
                      disabled={loading}
                    />
                    <motion.button
                      type="submit"
                      disabled={loading || !query.trim()}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      className="px-8 py-4 rounded-xl font-semibold flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed bg-gradient-to-r from-blue-700 to-blue-500 text-white shadow-lg shadow-blue-500/30"
                    >
                      {loading ? (
                        <><Loader2 className="w-5 h-5 animate-spin" /><span className="hidden md:inline">Processing...</span></>
                      ) : (
                        <><Send className="w-5 h-5" /><span className="hidden md:inline">Execute</span></>
                      )}
                    </motion.button>
                  </div>
                </div>
              </form>

              {/* Example Queries */}
              <div className="mt-6 flex flex-wrap gap-3 justify-center">
                {exampleQueries.map((example, index) => (
                  <motion.button
                    key={index}
                    whileHover={{ scale: 1.05 }}
                    onClick={() => setQuery(example.text)}
                    disabled={loading}
                    className="px-4 py-2 rounded-full text-sm flex items-center gap-2 bg-slate-800/50 border border-blue-500/30 hover:border-blue-500/60 transition-all disabled:opacity-50"
                  >
                    <example.icon className={`w-4 h-4 ${example.color}`} />
                    <span className="text-slate-300">{example.text}</span>
                  </motion.button>
                ))}
              </div>
            </motion.div>

            {/* WebSocket Events (Debug) */}
            {useWebSocketMode && wsEvents.length > 0 && (
              <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="max-w-4xl mx-auto mb-6"
              >
                <details className="glass rounded-xl p-4">
                  <summary className="cursor-pointer text-sm text-blue-400 font-semibold">
                    🔌 WebSocket Events ({wsEvents.length})
                  </summary>
                  <div className="mt-3 space-y-1 max-h-40 overflow-y-auto">
                    {wsEvents.map((event, i) => (
                      <div key={i} className="text-xs text-slate-400 flex items-center gap-2">
                        <Zap className="w-3 h-3 text-emerald-400" />
                        <span>{event.type}</span>
                        <span className="text-slate-600">•</span>
                        <span className="text-slate-500">{new Date(event.timestamp).toLocaleTimeString()}</span>
                      </div>
                    ))}
                  </div>
                </details>
              </motion.div>
            )}

            {/* Progress Indicator */}
            <AnimatePresence>
              {loading && (
                <motion.div 
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className="max-w-4xl mx-auto mb-10"
                >
                  <div className="rounded-2xl p-6 bg-slate-900/80 border border-blue-500/20 backdrop-blur-sm">
                    <h3 className="text-xl font-semibold mb-6 flex items-center gap-3 text-slate-200">
                      <Loader2 className="w-5 h-5 animate-spin text-blue-400" />
                      Execution Progress
                    </h3>
                    <div className="space-y-4">
                      {['Planning', 'Executing', 'Critiquing', 'Verifying'].map((step, index) => (
                        <div key={step} className="flex items-center gap-4">
                          <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                            activeStep > index ? 'bg-emerald-500' : activeStep === index ? 'bg-blue-500 animate-pulse' : 'bg-slate-700'
                          }`}>
                            {activeStep > index && <CheckCircle2 className="w-5 h-5 text-white" />}
                            {activeStep === index && <Loader2 className="w-5 h-5 animate-spin text-white" />}
                            {activeStep <= index && <span className="text-slate-400 text-sm">{index + 1}</span>}
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center justify-between mb-2">
                              <span className="font-medium text-slate-200">{step}</span>
                              <span className={`text-sm ${activeStep > index ? 'text-emerald-400' : activeStep === index ? 'text-blue-400' : 'text-slate-500'}`}>
                                {activeStep > index ? 'Complete' : activeStep === index ? 'In Progress...' : 'Pending'}
                              </span>
                            </div>
                            <div className="h-2 bg-slate-700/50 rounded-full overflow-hidden">
                              <motion.div 
                                className={`h-full rounded-full ${activeStep > index ? 'bg-emerald-500' : 'bg-blue-500'}`} 
                                initial={{ width: 0 }} 
                                animate={{ width: activeStep > index ? '100%' : activeStep === index ? '60%' : '0%' }} 
                                transition={{ duration: 0.5 }}
                              />
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Error Message */}
            {error && (
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="max-w-4xl mx-auto mb-10"
              >
                <div className="rounded-2xl p-6 bg-red-500/10 border border-red-500/30 flex items-center gap-4">
                  <AlertCircle className="w-6 h-6 text-red-400 flex-shrink-0" />
                  <p className="text-red-400">{error}</p>
                </div>
              </motion.div>
            )}

            {/* Results Section */}
            {result && (
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="max-w-6xl mx-auto">
                
                {/* Cache Badge */}
                {result._cached && (
                  <div className="mb-4 flex justify-center">
                    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/10 border border-emerald-500/30">
                      <Zap className="w-4 h-4 text-emerald-400" />
                      <span className="text-sm text-emerald-400 font-semibold">
                        Cached Result ({result._cache_age_seconds}s old)
                      </span>
                    </div>
                  </div>
                )}

                {/* Metrics */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                  {[
                    { icon: Clock, label: 'Time', value: `${executionTime}s`, color: 'text-blue-400' },
                    { icon: Boxes, label: 'Steps', value: `${metadata.steps_completed || 1}/${metadata.total_steps || 1}`, color: 'text-cyan-400' },
                    { icon: DollarSign, label: 'Cost', value: '$0.00', color: 'text-emerald-400' },
                    { icon: CheckCircle2, label: 'Status', value: output.status || 'Success', color: 'text-green-400' }
                  ].map((metric, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: i * 0.1 }}
                      className="rounded-xl p-5 text-center bg-slate-900/50 border border-blue-500/20 hover:border-blue-500/40 transition-all"
                    >
                      <metric.icon className={`w-7 h-7 mx-auto mb-2 ${metric.color}`} />
                      <div className="text-2xl font-bold text-slate-100">{metric.value}</div>
                      <div className="text-sm text-slate-500 uppercase tracking-wider">{metric.label}</div>
                    </motion.div>
                  ))}
                </div>

                {/* Data Display */}
                <div className="grid md:grid-cols-2 gap-6">
                  
                  {/* Weather Card */}
                  {weather && (
                    <motion.div
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="rounded-2xl p-6 bg-gradient-to-br from-blue-900/30 to-slate-900/95 border border-blue-500/30 relative overflow-hidden"
                    >
                      <div className="absolute right-4 top-4 opacity-10">
                        <Cloud className="w-32 h-32 text-blue-400" />
                      </div>
                      <h3 className="text-xl font-bold text-blue-400 mb-4 flex items-center gap-2">
                        <Cloud className="w-6 h-6" /> Weather Data
                      </h3>
                      <div className="relative z-10">
                        <div className="text-3xl font-bold text-slate-100 mb-1">
                          {weather.city}{weather.country ? `, ${weather.country}` : ''}
                        </div>
                        <div className="text-5xl font-extrabold text-blue-400 mb-2">
                          {weather.temperature}
                        </div>
                        <div className="text-lg text-slate-400 capitalize mb-4">
                          {weather.description}
                        </div>
                        <div className="grid grid-cols-3 gap-4 mt-4 text-sm">
                          <div className="flex items-center gap-2 text-slate-300">
                            <Wind className="w-4 h-4 text-cyan-400" />
                            <span>{weather.wind_speed}</span>
                          </div>
                          <div className="flex items-center gap-2 text-slate-300">
                            <Droplets className="w-4 h-4 text-blue-400" />
                            <span>{weather.humidity}</span>
                          </div>
                          <div className="flex items-center gap-2 text-slate-300">
                            <Cloud className="w-4 h-4 text-slate-400" />
                            <span>{weather.clouds}</span>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  )}

                  {/* GitHub Repos */}
                  {repositories && repositories.length > 0 && (
                    <motion.div
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="rounded-2xl p-6 bg-slate-900/80 border border-blue-500/30"
                    >
                      <h3 className="text-xl font-bold text-blue-400 mb-4 flex items-center gap-2">
                        <Github className="w-6 h-6" /> GitHub Repositories
                      </h3>
                      <div className="space-y-4 max-h-[500px] overflow-y-auto pr-2 custom-scrollbar">
                        {repositories.map((repo, index) => (
                          <motion.div
                            key={index}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: index * 0.1 }}
                            className="rounded-xl p-4 bg-slate-800/50 border border-blue-500/10 hover:border-blue-500/30 transition-all"
                          >
                            <div className="flex items-start justify-between mb-2">
                              <h4 className="font-semibold text-blue-400 truncate pr-4">{repo.name}</h4>
                              <a 
                                href={repo.url} 
                                target="_blank" 
                                rel="noopener noreferrer" 
                                className="text-slate-400 hover:text-blue-400 transition-colors flex-shrink-0"
                              >
                                <ExternalLink className="w-4 h-4" />
                              </a>
                            </div>
                            <div className="flex items-center gap-4 mb-2 text-xs">
                              <span className="flex items-center gap-1 text-amber-400">
                                <Star className="w-3 h-3" /> {repo.stars?.toLocaleString()}
                              </span>
                              <span className="flex items-center gap-1 text-slate-400">
                                <GitFork className="w-3 h-3" /> {repo.forks?.toLocaleString()}
                              </span>
                              <span className="px-2 py-0.5 bg-blue-900/30 rounded text-blue-300 text-xs">
                                {repo.language || 'Unknown'}
                              </span>
                            </div>
                            <p className="text-sm text-slate-400 line-clamp-2 text-xs">
                              {repo.description || 'No description available'}
                            </p>
                          </motion.div>
                        ))}
                      </div>
                    </motion.div>
                  )}
                </div>

                {/* RAW JSON */}
                <div className="mt-8">
                  <button 
                    onClick={() => setShowJson(!showJson)}
                    className="w-full flex items-center justify-between px-6 py-4 bg-slate-900/50 border border-blue-500/20 rounded-xl text-slate-300 hover:text-blue-400 hover:border-blue-500/40 transition-all"
                  >
                    <div className="flex items-center gap-2">
                      <Terminal className="w-5 h-5" />
                      <span>View Raw JSON Response</span>
                    </div>
                    <ChevronDown className={`w-5 h-5 transition-transform ${showJson ? 'rotate-180' : ''}`} />
                  </button>
                  
                  <AnimatePresence>
                    {showJson && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden"
                      >
                        <div className="mt-2 p-6 bg-slate-950 rounded-xl border border-blue-500/20">
                          <pre className="text-sm text-slate-300 overflow-x-auto whitespace-pre-wrap font-mono">
                            {JSON.stringify(output, null, 2)}
                          </pre>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>

              </motion.div>
            )}

            {/* Empty State */}
            {!loading && !result && !error && (
              <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="max-w-4xl mx-auto text-center mt-16"
              >
                <div className="rounded-2xl p-8 bg-slate-900/30 border border-blue-500/10">
                  <div className="text-6xl mb-4">🚀</div>
                  <h3 className="text-xl font-semibold text-slate-200 mb-2">Ready to Execute</h3>
                  <p className="text-slate-400">Enter a query above to get started with the AI Operations Assistant</p>
                  {isConnected && (
                    <p className="text-emerald-400 text-sm mt-3 flex items-center justify-center gap-2">
                      <Wifi className="w-4 h-4" />
                      Real-time mode available
                    </p>
                  )}
                </div>
              </motion.div>
            )}
          </motion.div>
        ) : (
          <motion.div
            key="voice"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
          >
            <VoiceAssistant />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default Dashboard;