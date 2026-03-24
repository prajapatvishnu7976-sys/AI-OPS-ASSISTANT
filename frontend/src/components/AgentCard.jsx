import React from 'react';
import { motion } from 'framer-motion';
import { CheckCircle2, Loader2 } from 'lucide-react';

const AgentCard = ({ agent, delay = 0, isActive = false }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, type: "spring", stiffness: 100 }}
      whileHover={{ y: -5, scale: 1.02 }}
      className="agent-card group"
    >
      <div className={`absolute inset-0 bg-gradient-to-br ${agent.color} opacity-0 group-hover:opacity-10 transition-opacity duration-300 rounded-2xl`} />
      
      <div className="relative z-10">
        <div className="flex items-center justify-between mb-4">
          <motion.div 
            className="text-4xl"
            animate={{ rotate: isActive ? [0, 10, -10, 0] : 0 }}
            transition={{ duration: 0.5, repeat: isActive ? Infinity : 0, repeatDelay: 1 }}
          >
            {agent.icon}
          </motion.div>
          
          <motion.div
            animate={{ 
              scale: isActive ? [1, 1.2, 1] : 1,
              opacity: isActive ? [0.5, 1, 0.5] : 1
            }}
            transition={{ duration: 1.5, repeat: isActive ? Infinity : 0 }}
          >
            {isActive ? (
              <Loader2 className="w-5 h-5 text-purple-400 animate-spin" />
            ) : (
              <CheckCircle2 className="w-5 h-5 text-green-400" />
            )}
          </motion.div>
        </div>

        <h3 className="text-xl font-bold mb-2 gradient-text">
          {agent.name}
        </h3>
        
        <p className="text-sm text-gray-400">
          {agent.description}
        </p>

        <div className="mt-4 flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${
            isActive ? 'bg-purple-400 animate-pulse' : 'bg-green-400'
          }`} />
          <span className="text-xs text-gray-500 uppercase tracking-wider">
            {isActive ? 'Processing' : 'Ready'}
          </span>
        </div>
      </div>

      <div className="absolute inset-0 shimmer opacity-0 group-hover:opacity-100 transition-opacity rounded-2xl" />
    </motion.div>
  );
};

export default AgentCard;