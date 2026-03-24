import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Activity, 
  Zap, 
  Database, 
  Users,
  TrendingUp,
  Clock,
  CheckCircle,
  AlertCircle,
  Wifi,
  WifiOff
} from 'lucide-react';
import { useWebSocket } from '../hooks/useWebSocket';
import axios from 'axios';

const RealtimeDashboard = () => {
  const [analytics, setAnalytics] = useState(null);
  const [cacheStats, setCacheStats] = useState(null);
  const [realtimeEvents, setRealtimeEvents] = useState([]);
  
  // WebSocket connection
  const { isConnected, lastMessage, sendMessage, connectionStatus } = useWebSocket(
    'ws://localhost:8000/ws/dashboard-client',
    {
      onMessage: (data) => {
        console.log('Dashboard received:', data.type);
        
        // Add to events feed
        setRealtimeEvents(prev => [
          {
            id: Date.now(),
            ...data,
            timestamp: new Date().toISOString()
          },
          ...prev.slice(0, 19) // Keep last 20 events
        ]);

        // Handle specific event types
        if (data.type === 'analytics_update') {
          setAnalytics(data.data);
        }
      },
      onConnect: () => {
        console.log('✅ Dashboard WebSocket connected');
        // Subscribe to analytics updates
        sendMessage('subscribe', { topic: 'analytics' });
      }
    }
  );

  // Fetch initial data
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [analyticsRes, cacheRes] = await Promise.all([
          axios.get('http://localhost:8000/api/analytics'),
          axios.get('http://localhost:8000/api/cache/stats')
        ]);

        setAnalytics(analyticsRes.data.system);
        setCacheStats(cacheRes.data);
      } catch (error) {
        console.error('Error fetching data:', error);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 5000); // Refresh every 5s

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="container mx-auto px-6 py-8">
      
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-4xl font-bold gradient-text">Real-time Dashboard</h1>
          <p className="text-slate-400 mt-2">System analytics and live monitoring</p>
        </div>

        {/* Connection Status */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="flex items-center gap-3 px-6 py-3 rounded-xl glass"
        >
          {isConnected ? (
            <>
              <Wifi className="w-5 h-5 text-emerald-400" />
              <span className="text-emerald-400 font-semibold">Connected</span>
              <motion.div
                className="w-2 h-2 rounded-full bg-emerald-400"
                animate={{ scale: [1, 1.3, 1], opacity: [0.5, 1, 0.5] }}
                transition={{ duration: 2, repeat: Infinity }}
              />
            </>
          ) : (
            <>
              <WifiOff className="w-5 h-5 text-red-400" />
              <span className="text-red-400 font-semibold">Disconnected</span>
            </>
          )}
        </motion.div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        
        {/* Total Requests */}
        <MetricCard
          icon={Activity}
          label="Total Requests"
          value={analytics?.total_requests || 0}
          color="text-blue-400"
          trend="+12%"
        />

        {/* Active Requests */}
        <MetricCard
          icon={Zap}
          label="Active Now"
          value={analytics?.active_requests || 0}
          color="text-yellow-400"
          pulse={analytics?.active_requests > 0}
        />

        {/* Cache Hit Rate */}
        <MetricCard
          icon={Database}
          label="Cache Hit Rate"
          value={`${cacheStats?.hit_rate_percent?.toFixed(1) || 0}%`}
          color="text-emerald-400"
          subtitle={`${cacheStats?.hits || 0} hits`}
        />

        {/* Avg Response Time */}
        <MetricCard
          icon={Clock}
          label="Avg Response"
          value={`${analytics?.avg_processing_time_ms?.toFixed(0) || 0}ms`}
          color="text-purple-400"
        />

      </div>

      {/* Charts Row */}
      <div className="grid lg:grid-cols-2 gap-6 mb-8">
        
        {/* System Stats */}
        <div className="glass rounded-2xl p-6">
          <h3 className="text-xl font-bold text-slate-200 mb-6 flex items-center gap-2">
            <Activity className="w-5 h-5 text-blue-400" />
            System Performance
          </h3>

          <div className="space-y-4">
            <StatBar
              label="Uptime"
              value={formatUptime(analytics?.uptime_seconds || 0)}
              percentage={100}
              color="bg-emerald-500"
            />
            
            <StatBar
              label="Success Rate"
              value={`${(100 - (analytics?.error_rate || 0)).toFixed(1)}%`}
              percentage={100 - (analytics?.error_rate || 0)}
              color="bg-blue-500"
            />
            
            <StatBar
              label="Requests/sec"
              value={analytics?.requests_per_second?.toFixed(2) || 0}
              percentage={Math.min((analytics?.requests_per_second || 0) * 10, 100)}
              color="bg-purple-500"
            />

            <StatBar
              label="Cache Efficiency"
              value={`${cacheStats?.hit_rate_percent?.toFixed(1) || 0}%`}
              percentage={cacheStats?.hit_rate_percent || 0}
              color="bg-cyan-500"
            />
          </div>
        </div>

        {/* Live Events Feed */}
        <div className="glass rounded-2xl p-6">
          <h3 className="text-xl font-bold text-slate-200 mb-6 flex items-center gap-2">
            <Zap className="w-5 h-5 text-yellow-400" />
            Live Events
          </h3>

          <div className="space-y-2 max-h-[300px] overflow-y-auto custom-scrollbar">
            <AnimatePresence>
              {realtimeEvents.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  <Activity className="w-12 h-12 mx-auto mb-3 opacity-30" />
                  <p>Waiting for events...</p>
                </div>
              ) : (
                realtimeEvents.map((event, index) => (
                  <motion.div
                    key={event.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 20 }}
                    transition={{ delay: index * 0.05 }}
                    className="flex items-center gap-3 p-3 rounded-lg bg-slate-800/50 border border-blue-500/10 hover:border-blue-500/30 transition-all"
                  >
                    {getEventIcon(event.type)}
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-semibold text-slate-200 truncate">
                        {formatEventType(event.type)}
                      </div>
                      <div className="text-xs text-slate-500">
                        {new Date(event.timestamp).toLocaleTimeString()}
                      </div>
                    </div>
                  </motion.div>
                ))
              )}
            </AnimatePresence>
          </div>
        </div>

      </div>

      {/* Endpoint Stats */}
      {analytics?.endpoints && (
        <div className="glass rounded-2xl p-6">
          <h3 className="text-xl font-bold text-slate-200 mb-6 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-blue-400" />
            Endpoint Statistics
          </h3>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(analytics.endpoints).map(([endpoint, count]) => (
              <div
                key={endpoint}
                className="p-4 rounded-xl bg-slate-800/50 border border-blue-500/10 hover:border-blue-500/30 transition-all"
              >
                <div className="text-sm text-slate-400 truncate mb-1">{endpoint}</div>
                <div className="text-2xl font-bold text-slate-200">{count}</div>
                <div className="text-xs text-slate-500 mt-1">
                  {((count / analytics.total_requests) * 100).toFixed(1)}% of traffic
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  );
};

// Helper Components

const MetricCard = ({ icon: Icon, label, value, color, trend, subtitle, pulse }) => (
  <motion.div
    whileHover={{ scale: 1.02, y: -2 }}
    className="glass rounded-2xl p-6 relative overflow-hidden"
  >
    {pulse && (
      <motion.div
        className="absolute inset-0 bg-gradient-to-r from-yellow-500/10 to-transparent"
        animate={{ opacity: [0.3, 0.6, 0.3] }}
        transition={{ duration: 2, repeat: Infinity }}
      />
    )}
    
    <div className="relative z-10">
      <div className="flex items-center justify-between mb-4">
        <Icon className={`w-8 h-8 ${color}`} />
        {trend && (
          <span className="text-xs font-semibold text-emerald-400">{trend}</span>
        )}
      </div>
      
      <div className={`text-3xl font-bold mb-1 ${color}`}>{value}</div>
      <div className="text-sm text-slate-400">{label}</div>
      {subtitle && (
        <div className="text-xs text-slate-500 mt-1">{subtitle}</div>
      )}
    </div>
  </motion.div>
);

const StatBar = ({ label, value, percentage, color }) => (
  <div>
    <div className="flex items-center justify-between mb-2">
      <span className="text-sm text-slate-300">{label}</span>
      <span className="text-sm font-semibold text-slate-200">{value}</span>
    </div>
    <div className="h-2 bg-slate-700/50 rounded-full overflow-hidden">
      <motion.div
        className={`h-full ${color} rounded-full`}
        initial={{ width: 0 }}
        animate={{ width: `${percentage}%` }}
        transition={{ duration: 1, ease: "easeOut" }}
      />
    </div>
  </div>
);

// Helper Functions

const formatUptime = (seconds) => {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  
  if (days > 0) return `${days}d ${hours}h`;
  if (hours > 0) return `${hours}h ${mins}m`;
  return `${mins}m`;
};

const formatEventType = (type) => {
  return type.split('_').map(word => 
    word.charAt(0).toUpperCase() + word.slice(1)
  ).join(' ');
};

const getEventIcon = (type) => {
  const icons = {
    'query_received': <Zap className="w-4 h-4 text-blue-400" />,
    'planning_started': <Activity className="w-4 h-4 text-purple-400" />,
    'execution_started': <Activity className="w-4 h-4 text-cyan-400" />,
    'result_ready': <CheckCircle className="w-4 h-4 text-emerald-400" />,
    'error': <AlertCircle className="w-4 h-4 text-red-400" />,
  };

  return icons[type] || <Activity className="w-4 h-4 text-slate-400" />;
};

export default RealtimeDashboard;