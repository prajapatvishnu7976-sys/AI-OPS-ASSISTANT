import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  MessageSquare, 
  Sparkles, 
  Trash2, 
  Clock,
  Volume2
} from 'lucide-react';

const VoiceChatHistory = ({ history, onClear, onPlayAudio }) => {
  return (
    <div className="glass rounded-3xl p-6 h-full max-h-[800px] flex flex-col">
      
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <MessageSquare className="w-5 h-5 text-purple-400" />
          <h3 className="text-xl font-bold text-slate-200">Chat History</h3>
        </div>
        
        {history.length > 0 && (
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={onClear}
            className="w-9 h-9 rounded-full flex items-center justify-center bg-red-500/10 border border-red-500/30 hover:bg-red-500/20 transition-all"
          >
            <Trash2 className="w-4 h-4 text-red-400" />
          </motion.button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto pr-2 space-y-4 custom-scrollbar">
        <AnimatePresence>
          {history.length === 0 ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center py-12"
            >
              <div className="text-6xl mb-4">💬</div>
              <p className="text-slate-500">No conversations yet</p>
              <p className="text-sm text-slate-600 mt-2">Start recording to see history</p>
            </motion.div>
          ) : (
            history.map((entry, index) => (
              <motion.div
                key={entry.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ delay: index * 0.05 }}
                className="bg-slate-800/30 border border-purple-500/10 rounded-xl p-4 hover:border-purple-500/30 transition-all"
              >
                <div className="flex items-center gap-2 mb-3 text-xs text-slate-500">
                  <Clock className="w-3 h-3" />
                  {entry.timestamp}
                </div>

                <div className="mb-3">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-6 h-6 rounded-full bg-purple-500/20 flex items-center justify-center">
                      <MessageSquare className="w-3 h-3 text-purple-400" />
                    </div>
                    <span className="text-xs font-semibold text-purple-400">You</span>
                  </div>
                  <p className="text-sm text-slate-300 pl-8">{entry.userMessage}</p>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <div className="w-6 h-6 rounded-full bg-pink-500/20 flex items-center justify-center">
                        <Sparkles className="w-3 h-3 text-pink-400" />
                      </div>
                      <span className="text-xs font-semibold text-pink-400">AI</span>
                    </div>
                    
                    {/* Replay button - works with text for browser TTS */}
                    <motion.button
                      whileHover={{ scale: 1.1 }}
                      whileTap={{ scale: 0.9 }}
                      onClick={() => onPlayAudio(entry.aiResponse)}
                      className="w-7 h-7 rounded-full flex items-center justify-center bg-purple-500/10 border border-purple-500/20 hover:bg-purple-500/20 transition-all"
                      title="Replay response"
                    >
                      <Volume2 className="w-3 h-3 text-purple-400" />
                    </motion.button>
                  </div>
                  <p className="text-sm text-slate-400 pl-8">{entry.aiResponse}</p>
                </div>
              </motion.div>
            ))
          )}
        </AnimatePresence>
      </div>

    </div>
  );
};

export default VoiceChatHistory;