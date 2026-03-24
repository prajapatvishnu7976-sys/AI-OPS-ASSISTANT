import React from 'react';
import { motion } from 'framer-motion';

const AudioVisualizer = ({ isActive }) => {
  const bars = Array.from({ length: 40 });

  return (
    <div className="flex items-center justify-center gap-1 h-32 bg-slate-900/30 rounded-2xl border border-purple-500/10 p-4">
      {bars.map((_, index) => (
        <motion.div
          key={index}
          className="w-1 bg-gradient-to-t from-purple-600 to-pink-500 rounded-full"
          animate={{
            height: isActive 
              ? [
                  `${Math.random() * 60 + 20}%`,
                  `${Math.random() * 80 + 10}%`,
                  `${Math.random() * 60 + 20}%`,
                ]
              : '20%',
            opacity: isActive ? [0.5, 1, 0.5] : 0.3
          }}
          transition={{
            duration: 0.5 + Math.random() * 0.5,
            repeat: isActive ? Infinity : 0,
            ease: "easeInOut",
            delay: index * 0.02
          }}
        />
      ))}
    </div>
  );
};

export default AudioVisualizer;