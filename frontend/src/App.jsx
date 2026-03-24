import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { 
  Brain, 
  Moon, 
  Sun, 
  Zap, 
  Sparkles, 
  Activity, 
  Shield, 
  Cpu, 
  CheckCircle,
  BarChart3,
  Home
} from 'lucide-react';
import Dashboard from './components/Dashboard';
import RealtimeDashboard from './components/RealtimeDashboard';
import { motion, AnimatePresence } from 'framer-motion';

const AppContent = () => {
  const [darkMode, setDarkMode] = useState(true);
  const [particles, setParticles] = useState([]);
  const location = useLocation();

  // Generate stable particles on mount
  useEffect(() => {
    const newParticles = Array.from({ length: 30 }, (_, i) => ({
      id: i,
      left: Math.random() * 100,
      top: Math.random() * 100,
      duration: 3 + Math.random() * 4,
      delay: Math.random() * 3,
      size: Math.random() > 0.7 ? 2 : 1,
    }));
    setParticles(newParticles);
  }, []);

  // Agent data array
  const agents = [
    { icon: Brain, name: 'Planner', color: '#3b82f6', status: 'Ready' },
    { icon: Cpu, name: 'Executor', color: '#06b6d4', status: 'Ready' },
    { icon: Shield, name: 'Critic', color: '#f59e0b', status: 'Ready' },
    { icon: CheckCircle, name: 'Verifier', color: '#22c55e', status: 'Ready' },
  ];

  return (
    <div className="min-h-screen relative bg-[#030712] overflow-x-hidden">
      
      {/* ============ ANIMATED BACKGROUND ============ */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        {/* Gradient Orbs */}
        <motion.div
          className="absolute w-[600px] h-[600px] rounded-full"
          style={{
            background: 'radial-gradient(circle, rgba(30, 64, 175, 0.15) 0%, transparent 70%)',
            left: '-200px',
            top: '-200px',
          }}
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.3, 0.5, 0.3],
          }}
          transition={{
            duration: 8,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
        
        <motion.div
          className="absolute w-[500px] h-[500px] rounded-full"
          style={{
            background: 'radial-gradient(circle, rgba(59, 130, 246, 0.1) 0%, transparent 70%)',
            right: '-150px',
            bottom: '-150px',
          }}
          animate={{
            scale: [1.2, 1, 1.2],
            opacity: [0.2, 0.4, 0.2],
          }}
          transition={{
            duration: 10,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />

        {/* Grid Pattern */}
        <div 
          className="absolute inset-0 opacity-[0.02]"
          style={{
            backgroundImage: `
              linear-gradient(rgba(59, 130, 246, 0.5) 1px, transparent 1px),
              linear-gradient(90deg, rgba(59, 130, 246, 0.5) 1px, transparent 1px)
            `,
            backgroundSize: '50px 50px',
          }}
        />

        {/* Floating Particles */}
        {particles.map((particle) => (
          <motion.div
            key={particle.id}
            className="absolute rounded-full"
            style={{
              left: `${particle.left}%`,
              top: `${particle.top}%`,
              width: particle.size,
              height: particle.size,
              background: 'linear-gradient(135deg, #3b82f6, #60a5fa)',
              boxShadow: '0 0 10px rgba(59, 130, 246, 0.5)',
            }}
            animate={{
              y: [0, -40, 0],
              x: [0, 10, 0],
              opacity: [0.2, 0.8, 0.2],
              scale: [1, 1.5, 1],
            }}
            transition={{
              duration: particle.duration,
              repeat: Infinity,
              delay: particle.delay,
              ease: "easeInOut",
            }}
          />
        ))}
      </div>

      {/* ============ MAIN CONTENT ============ */}
      <div className="relative z-10">
        
        {/* ============ PREMIUM HEADER ============ */}
        <motion.header
          initial={{ y: -100, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ type: "spring", stiffness: 100, damping: 20 }}
          className="sticky top-0 z-50 backdrop-blur-xl"
          style={{
            background: 'linear-gradient(180deg, rgba(3, 7, 18, 0.95) 0%, rgba(3, 7, 18, 0.8) 100%)',
            borderBottom: '1px solid rgba(59, 130, 246, 0.2)',
          }}
        >
          <div className="container mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              
              {/* Logo Section */}
              <Link to="/" className="flex items-center gap-4 hover:opacity-80 transition-opacity">
                <div className="relative">
                  {/* Glow Effect */}
                  <motion.div
                    className="absolute inset-0 rounded-xl blur-xl"
                    style={{
                      background: 'linear-gradient(135deg, #1e40af, #3b82f6)',
                    }}
                    animate={{
                      opacity: [0.5, 0.8, 0.5],
                      scale: [1, 1.1, 1],
                    }}
                    transition={{
                      duration: 3,
                      repeat: Infinity,
                      ease: "easeInOut",
                    }}
                  />
                  
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                    className="relative w-12 h-12 rounded-xl flex items-center justify-center"
                    style={{
                      background: 'linear-gradient(135deg, #1e40af 0%, #3b82f6 50%, #60a5fa 100%)',
                      boxShadow: '0 0 30px rgba(59, 130, 246, 0.5)',
                    }}
                  >
                    <Brain className="w-7 h-7 text-white" />
                  </motion.div>
                </div>
                
                <div>
                  <h1 
                    className="text-2xl font-bold"
                    style={{
                      background: 'linear-gradient(135deg, #60a5fa 0%, #3b82f6 50%, #1e40af 100%)',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                      textShadow: '0 0 40px rgba(59, 130, 246, 0.3)',
                    }}
                  >
                    AI Operations Assistant
                  </h1>
                  <p className="text-xs text-slate-500">
                    Enterprise v6.0 • Powered by <span className="text-blue-400">Gemini</span>
                  </p>
                </div>
              </Link>

              {/* Navigation */}
              <nav className="hidden md:flex items-center gap-2">
                <NavLink to="/" icon={Home} active={location.pathname === '/'}>
                  Research
                </NavLink>
                <NavLink to="/dashboard" icon={BarChart3} active={location.pathname === '/dashboard'}>
                  Analytics
                </NavLink>
              </nav>

              {/* Right Section */}
              <div className="flex items-center gap-4">
                
                {/* Status Badge */}
                <motion.div
                  className="hidden md:flex items-center gap-2 px-4 py-2 rounded-full"
                  style={{
                    background: 'rgba(30, 64, 175, 0.2)',
                    border: '1px solid rgba(59, 130, 246, 0.3)',
                  }}
                  whileHover={{ scale: 1.05 }}
                >
                  <motion.div
                    className="w-2 h-2 rounded-full bg-emerald-400"
                    animate={{
                      scale: [1, 1.3, 1],
                      opacity: [0.5, 1, 0.5],
                    }}
                    transition={{
                      duration: 2,
                      repeat: Infinity,
                    }}
                    style={{
                      boxShadow: '0 0 10px rgba(52, 211, 153, 0.8)',
                    }}
                  />
                  <span className="text-sm font-medium text-slate-300">4 Agents Online</span>
                </motion.div>

                {/* Theme Toggle */}
                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  onClick={() => setDarkMode(!darkMode)}
                  className="w-10 h-10 rounded-full flex items-center justify-center"
                  style={{
                    background: 'rgba(30, 64, 175, 0.2)',
                    border: '1px solid rgba(59, 130, 246, 0.3)',
                  }}
                >
                  <AnimatePresence mode="wait">
                    {darkMode ? (
                      <motion.div
                        key="sun"
                        initial={{ rotate: -180, opacity: 0, scale: 0 }}
                        animate={{ rotate: 0, opacity: 1, scale: 1 }}
                        exit={{ rotate: 180, opacity: 0, scale: 0 }}
                        transition={{ duration: 0.3 }}
                      >
                        <Sun className="w-5 h-5 text-amber-400" />
                      </motion.div>
                    ) : (
                      <motion.div
                        key="moon"
                        initial={{ rotate: 180, opacity: 0, scale: 0 }}
                        animate={{ rotate: 0, opacity: 1, scale: 1 }}
                        exit={{ rotate: -180, opacity: 0, scale: 0 }}
                        transition={{ duration: 0.3 }}
                      >
                        <Moon className="w-5 h-5 text-blue-400" />
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.button>
              </div>
            </div>
          </div>
        </motion.header>

        {/* ============ AGENTS STATUS BAR (Only on home) ============ */}
        {location.pathname === '/' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="container mx-auto px-6 py-4"
          >
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {agents.map((agent, index) => {
                const IconComponent = agent.icon;
                return (
                  <motion.div
                    key={agent.name}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4 + index * 0.1 }}
                    whileHover={{ 
                      scale: 1.02,
                      y: -2,
                    }}
                    className="flex items-center gap-3 p-3 rounded-xl cursor-pointer"
                    style={{
                      background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.8) 0%, rgba(30, 41, 59, 0.6) 100%)',
                      border: '1px solid rgba(59, 130, 246, 0.2)',
                    }}
                  >
                    <div 
                      className="w-10 h-10 rounded-lg flex items-center justify-center"
                      style={{
                        background: `${agent.color}20`,
                        border: `1px solid ${agent.color}40`,
                      }}
                    >
                      <IconComponent className="w-5 h-5" style={{ color: agent.color }} />
                    </div>
                    <div>
                      <div className="text-sm font-semibold text-slate-200">{agent.name}</div>
                      <div className="text-xs text-emerald-400 flex items-center gap-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                        {agent.status}
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </motion.div>
        )}

        {/* ============ ROUTES ============ */}
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/dashboard" element={<RealtimeDashboard />} />
        </Routes>

        {/* ============ PREMIUM FOOTER ============ */}
        <motion.footer
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1 }}
          className="mt-20"
          style={{
            background: 'linear-gradient(180deg, transparent 0%, rgba(3, 7, 18, 0.95) 100%)',
            borderTop: '1px solid rgba(59, 130, 246, 0.2)',
          }}
        >
          <div className="container mx-auto px-6 py-8">
            <div className="flex flex-col md:flex-row items-center justify-between gap-4">
              
              {/* Left */}
              <motion.div 
                className="flex items-center gap-3"
                whileHover={{ scale: 1.02 }}
              >
                <div 
                  className="w-10 h-10 rounded-xl flex items-center justify-center"
                  style={{
                    background: 'linear-gradient(135deg, #1e40af 0%, #3b82f6 100%)',
                    boxShadow: '0 0 20px rgba(59, 130, 246, 0.4)',
                  }}
                >
                  <Sparkles className="w-5 h-5 text-white" />
                </div>
                <div>
                  <div className="font-semibold text-slate-200">AI Operations Assistant v6.0</div>
                  <div className="text-xs text-slate-500">
                    Built with <span className="text-blue-400">LangGraph</span> • <span className="text-blue-400">Gemini</span> • <span className="text-blue-400">React</span>
                  </div>
                </div>
              </motion.div>

              {/* Center */}
              <div className="flex items-center gap-6 text-sm text-slate-500">
                <motion.div 
                  className="flex items-center gap-2"
                  whileHover={{ color: '#60a5fa' }}
                >
                  <Activity className="w-4 h-4" />
                  <span>Parallel Execution</span>
                </motion.div>
                <motion.div 
                  className="flex items-center gap-2"
                  whileHover={{ color: '#60a5fa' }}
                >
                  <Zap className="w-4 h-4 text-amber-400" />
                  <span>Redis Cache</span>
                </motion.div>
                <motion.div 
                  className="flex items-center gap-2"
                  whileHover={{ color: '#60a5fa' }}
                >
                  <Shield className="w-4 h-4 text-emerald-400" />
                  <span>WebSocket Real-time</span>
                </motion.div>
              </div>

              {/* Right */}
              <div className="text-xs text-slate-600">
                © 2024 Enterprise Edition
              </div>
            </div>
          </div>
        </motion.footer>
      </div>
    </div>
  );
};

// Navigation Link Component
const NavLink = ({ to, icon: Icon, children, active }) => (
  <Link to={to}>
    <motion.div
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      className={`flex items-center gap-2 px-4 py-2 rounded-xl transition-all ${
        active
          ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
          : 'text-slate-400 hover:text-slate-200 border border-transparent hover:border-blue-500/20'
      }`}
    >
      <Icon className="w-4 h-4" />
      <span className="text-sm font-semibold">{children}</span>
    </motion.div>
  </Link>
);

// Main App with Router
const App = () => {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
};

export default App;