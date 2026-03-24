import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Mic, 
  MicOff, 
  Volume2, 
  VolumeX,
  Loader2, 
  Radio,
  Play,
  Pause,
  Clock,
  XCircle,
  Sparkles,
  MessageSquare,
  Wifi,
  WifiOff
} from 'lucide-react';
import axios from 'axios';
import AudioVisualizer from './AudioVisualizer';
import VoiceChatHistory from './VoiceChatHistory';

const VoiceAssistant = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [response, setResponse] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [recordingTime, setRecordingTime] = useState(0);
  const [error, setError] = useState(null);
  const [isMuted, setIsMuted] = useState(false);
  const [useBrowserVoice, setUseBrowserVoice] = useState(true);

  const recognitionRef = useRef(null);
  const synthesisRef = useRef(null);
  const timerRef = useRef(null);

  // Initialize Browser Speech Recognition
  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = 'en-US';

      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        handleTranscript(transcript);
      };

      recognitionRef.current.onerror = (event) => {
        setError(`Speech recognition error: ${event.error}`);
        setIsRecording(false);
      };

      recognitionRef.current.onend = () => {
        setIsRecording(false);
      };
    } else {
      setError('Browser speech recognition not supported. Use Chrome/Edge.');
      setUseBrowserVoice(false);
    }

    // Initialize Browser Speech Synthesis
    if ('speechSynthesis' in window) {
      synthesisRef.current = window.speechSynthesis;
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      if (synthesisRef.current) {
        synthesisRef.current.cancel();
      }
    };
  }, []);

  // Recording Timer
  useEffect(() => {
    if (isRecording) {
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
      setRecordingTime(0);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isRecording]);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Start Recording (Browser)
  const startRecording = () => {
    if (!recognitionRef.current) {
      setError('Speech recognition not available');
      return;
    }

    try {
      setError(null);
      recognitionRef.current.start();
      setIsRecording(true);
    } catch (err) {
      setError('Failed to start recording');
      console.error(err);
    }
  };

  // Stop Recording
  const stopRecording = () => {
    if (recognitionRef.current && isRecording) {
      recognitionRef.current.stop();
      setIsRecording(false);
    }
  };

  // Handle Transcript
  const handleTranscript = async (text) => {
    setTranscript(text);
    setIsProcessing(true);
    setError(null);

    try {
      // ✅ FIXED: Correct API endpoint
      const res = await axios.post('http://localhost:8000/api/voice/process', {
        text: text,
        enable_tts: false // We'll use browser TTS instead
      });

      const aiResponse = res.data.response_text;
      setResponse(aiResponse);

      // Speak using browser TTS (FREE!)
      if (!isMuted && synthesisRef.current) {
        speakText(aiResponse);
      }

      // Add to chat history
      addToHistory(text, aiResponse);

    } catch (err) {
      console.error('Processing error:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to process. Check backend connection.');
    } finally {
      setIsProcessing(false);
    }
  };

  // Browser Text-to-Speech (FREE!)
  const speakText = (text) => {
    if (!synthesisRef.current) return;

    synthesisRef.current.cancel(); // Stop any ongoing speech

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-US';
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    // Get available voices
    const voices = synthesisRef.current.getVoices();
    const femaleVoice = voices.find(v => v.name.includes('Female') || v.name.includes('Samantha'));
    if (femaleVoice) {
      utterance.voice = femaleVoice;
    }

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    synthesisRef.current.speak(utterance);
  };

  // Add to Chat History
  const addToHistory = (userMessage, aiResponse) => {
    const newEntry = {
      id: Date.now(),
      timestamp: new Date().toLocaleTimeString(),
      userMessage,
      aiResponse
    };
    setChatHistory(prev => [newEntry, ...prev]);
  };

  const clearHistory = () => {
    setChatHistory([]);
  };

  const toggleMute = () => {
    setIsMuted(!isMuted);
    if (synthesisRef.current) {
      synthesisRef.current.cancel();
    }
  };

  const replayResponse = () => {
    if (response && !isMuted) {
      speakText(response);
    }
  };

  return (
    <div className="max-w-7xl mx-auto">
      
      <div className="grid lg:grid-cols-3 gap-8">
        
        {/* Left: Voice Recorder */}
        <div className="lg:col-span-2">
          <div className="glass rounded-3xl p-8 relative overflow-hidden">
            
            {/* Background Animation */}
            <div className="absolute inset-0 pointer-events-none">
              <motion.div
                className="absolute top-0 left-0 w-full h-full"
                animate={{
                  background: isRecording 
                    ? [
                        'radial-gradient(circle at 20% 50%, rgba(168, 85, 247, 0.1) 0%, transparent 50%)',
                        'radial-gradient(circle at 80% 50%, rgba(236, 72, 153, 0.1) 0%, transparent 50%)',
                      ]
                    : 'radial-gradient(circle, transparent 0%, transparent 100%)'
                }}
                transition={{ duration: 3, repeat: Infinity }}
              />
            </div>

            <div className="relative z-10">
              
              {/* Status Badge */}
              <div className="flex items-center justify-between mb-8">
                <div className="flex items-center gap-3">
                  <motion.div
                    animate={{
                      scale: isRecording ? [1, 1.2, 1] : 1,
                      opacity: isRecording ? [0.5, 1, 0.5] : 1
                    }}
                    transition={{ duration: 1.5, repeat: isRecording ? Infinity : 0 }}
                    className={`w-3 h-3 rounded-full ${
                      isRecording ? 'bg-red-500' : isProcessing ? 'bg-yellow-500 animate-pulse' : isSpeaking ? 'bg-purple-500 animate-pulse' : 'bg-emerald-500'
                    }`}
                  />
                  <span className="text-sm font-medium text-slate-300">
                    {isRecording ? 'Listening...' : isProcessing ? 'Processing...' : isSpeaking ? 'Speaking...' : 'Ready'}
                  </span>
                </div>

                <div className="flex items-center gap-3">
                  {/* Voice Mode Indicator */}
                  <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30">
                    {useBrowserVoice ? <Wifi className="w-4 h-4 text-emerald-400" /> : <WifiOff className="w-4 h-4 text-slate-400" />}
                    <span className="text-xs text-emerald-400">Browser Voice (Free)</span>
                  </div>

                  {/* Mute Toggle */}
                  <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={toggleMute}
                    className="w-10 h-10 rounded-full flex items-center justify-center bg-slate-800/50 border border-slate-700/50 hover:border-purple-500/50 transition-all"
                  >
                    {isMuted ? <VolumeX className="w-5 h-5 text-slate-400" /> : <Volume2 className="w-5 h-5 text-purple-400" />}
                  </motion.button>
                </div>
              </div>

              {/* Audio Visualizer */}
              <div className="mb-8">
                <AudioVisualizer isActive={isRecording || isProcessing} />
              </div>

              {/* Recording Timer */}
              <AnimatePresence>
                {isRecording && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.9 }}
                    className="text-center mb-8"
                  >
                    <div className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-red-500/10 border border-red-500/30">
                      <Clock className="w-5 h-5 text-red-400" />
                      <span className="text-2xl font-mono font-bold text-red-400">
                        {formatTime(recordingTime)}
                      </span>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Main Control Button */}
              <div className="flex justify-center mb-8">
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={isRecording ? stopRecording : startRecording}
                  disabled={isProcessing}
                  className={`relative w-24 h-24 rounded-full flex items-center justify-center transition-all disabled:opacity-50 disabled:cursor-not-allowed ${
                    isRecording 
                      ? 'bg-gradient-to-br from-red-600 to-red-500 shadow-lg shadow-red-500/50' 
                      : 'bg-gradient-to-br from-purple-600 to-pink-600 shadow-lg shadow-purple-500/50'
                  }`}
                >
                  <AnimatePresence mode="wait">
                    {isProcessing ? (
                      <Loader2 key="loader" className="w-10 h-10 text-white animate-spin" />
                    ) : isRecording ? (
                      <MicOff key="micoff" className="w-10 h-10 text-white" />
                    ) : (
                      <Mic key="mic" className="w-10 h-10 text-white" />
                    )}
                  </AnimatePresence>

                  {isRecording && (
                    <motion.div
                      className="absolute inset-0 rounded-full border-4 border-red-400"
                      animate={{ scale: [1, 1.5, 1], opacity: [0.5, 0, 0.5] }}
                      transition={{ duration: 2, repeat: Infinity }}
                    />
                  )}
                </motion.button>
              </div>

              {/* Transcript */}
              <AnimatePresence>
                {transcript && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    className="mb-6"
                  >
                    <div className="bg-slate-800/50 border border-purple-500/20 rounded-2xl p-6">
                      <div className="flex items-center gap-2 mb-3">
                        <MessageSquare className="w-5 h-5 text-purple-400" />
                        <span className="text-sm font-semibold text-purple-400">You said</span>
                      </div>
                      <p className="text-slate-200 text-lg leading-relaxed">{transcript}</p>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* AI Response */}
              <AnimatePresence>
                {response && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                  >
                    <div className="bg-gradient-to-br from-purple-900/30 to-pink-900/20 border border-purple-500/30 rounded-2xl p-6">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <Sparkles className="w-5 h-5 text-pink-400" />
                          <span className="text-sm font-semibold text-pink-400">AI Response</span>
                        </div>
                        
                        <motion.button
                          whileHover={{ scale: 1.1 }}
                          whileTap={{ scale: 0.9 }}
                          onClick={replayResponse}
                          className="w-8 h-8 rounded-full flex items-center justify-center bg-purple-500/20 border border-purple-500/30 hover:bg-purple-500/30 transition-all"
                        >
                          <Play className="w-4 h-4 text-purple-400" />
                        </motion.button>
                      </div>
                      <p className="text-slate-200 text-lg leading-relaxed">{response}</p>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Error Message */}
              <AnimatePresence>
                {error && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    className="mt-6"
                  >
                    <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 flex items-center gap-3">
                      <XCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
                      <p className="text-red-400 text-sm">{error}</p>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

            </div>
          </div>
        </div>

        {/* Right: Chat History */}
        <div>
          <VoiceChatHistory 
            history={chatHistory} 
            onClear={clearHistory}
            onPlayAudio={(text) => speakText(text)}
          />
        </div>

      </div>
    </div>
  );
};

export default VoiceAssistant;