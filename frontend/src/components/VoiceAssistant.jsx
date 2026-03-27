import React, { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Mic, 
  MicOff, 
  Volume2, 
  VolumeX,
  Loader2, 
  Play,
  Clock,
  XCircle,
  Sparkles,
  MessageSquare,
  Wifi,
  Trash2,
  Square
} from 'lucide-react';
import axios from 'axios';

const VoiceAssistant = () => {
  // ============ STATE ============
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [interimTranscript, setInterimTranscript] = useState('');
  const [response, setResponse] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [recordingTime, setRecordingTime] = useState(0);
  const [error, setError] = useState(null);
  const [isMuted, setIsMuted] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [speechSupported, setSpeechSupported] = useState(true);

  // ============ REFS ============
  const recognitionRef = useRef(null);
  const synthesisRef = useRef(null);
  const timerRef = useRef(null);
  const analyserRef = useRef(null);
  const audioContextRef = useRef(null);
  const streamRef = useRef(null);
  const animationFrameRef = useRef(null);
  const isRecordingRef = useRef(false);
  const transcriptRef = useRef('');

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  // ============ CLEANUP AUDIO ============
  const cleanupAudio = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }

    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      try {
        audioContextRef.current.close();
      } catch (e) {}
      audioContextRef.current = null;
    }

    analyserRef.current = null;
    setAudioLevel(0);
  }, []);

  // ============ INITIALIZE SPEECH RECOGNITION ============
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
      console.warn('⚠️ Browser Speech Recognition not supported');
      setSpeechSupported(false);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      console.log('🎤 Speech recognition started');
      isRecordingRef.current = true;
      setIsRecording(true);
      setError(null);
      transcriptRef.current = '';
    };

    recognition.onresult = (event) => {
      let finalTranscript = '';
      let interimText = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          finalTranscript += result[0].transcript;
          console.log('✅ Final:', finalTranscript);
        } else {
          interimText += result[0].transcript;
        }
      }

      if (interimText) {
        setInterimTranscript(interimText);
      }

      if (finalTranscript) {
        const newTranscript = (transcriptRef.current + ' ' + finalTranscript).trim();
        transcriptRef.current = newTranscript;
        setTranscript(newTranscript);
        setInterimTranscript('');
      }
    };

    recognition.onerror = (event) => {
      console.log('⚠️ Speech event:', event.error);
      
      if (event.error === 'no-speech') {
        // Don't show error, just continue
        return;
      } else if (event.error === 'audio-capture') {
        setError('No microphone found. Please connect a microphone.');
      } else if (event.error === 'not-allowed') {
        setError('Microphone access denied. Please allow in browser settings.');
      } else if (event.error === 'network') {
        setError('Network error. Check your internet connection.');
      } else if (event.error !== 'aborted') {
        setError(`Speech error: ${event.error}`);
      }
    };

    recognition.onend = () => {
      console.log('🛑 Speech recognition ended');
      isRecordingRef.current = false;
      setIsRecording(false);
    };

    recognitionRef.current = recognition;

    // Initialize Speech Synthesis
    if ('speechSynthesis' in window) {
      synthesisRef.current = window.speechSynthesis;
      const loadVoices = () => {
        synthesisRef.current.getVoices();
      };
      synthesisRef.current.onvoiceschanged = loadVoices;
      loadVoices();
    }

    return () => {
      if (recognitionRef.current) {
        try { recognitionRef.current.stop(); } catch (e) {}
      }
      if (synthesisRef.current) {
        synthesisRef.current.cancel();
      }
      cleanupAudio();
    };
  }, [cleanupAudio]);

  // ============ RECORDING TIMER ============
  useEffect(() => {
    if (isRecording) {
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
      setRecordingTime(0);
    }
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [isRecording]);

  // ============ AUDIO VISUALIZATION ============
  const updateAudioLevel = useCallback(() => {
    if (!analyserRef.current || !isRecordingRef.current) return;

    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
    analyserRef.current.getByteFrequencyData(dataArray);
    
    const average = dataArray.reduce((a, b) => a + b, 0) / dataArray.length;
    setAudioLevel(Math.min(100, (average / 255) * 100));

    if (isRecordingRef.current) {
      animationFrameRef.current = requestAnimationFrame(updateAudioLevel);
    }
  }, []);

  const startAudioVisualization = useCallback(async () => {
    try {
      cleanupAudio();

      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        } 
      });
      
      streamRef.current = stream;
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      audioContextRef.current = audioContext;
      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 256;
      analyser.smoothingTimeConstant = 0.8;
      source.connect(analyser);
      analyserRef.current = analyser;
      updateAudioLevel();
    } catch (err) {
      console.error('Audio visualization error:', err);
    }
  }, [cleanupAudio, updateAudioLevel]);

  // ============ FORMAT TIME ============
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // ============ START RECORDING ============
  const startRecording = async () => {
    if (!speechSupported || !recognitionRef.current) {
      setError('Speech recognition not available. Use Chrome or Edge.');
      return;
    }

    try {
      setError(null);
      setTranscript('');
      setInterimTranscript('');
      setResponse('');
      transcriptRef.current = '';

      await startAudioVisualization();
      recognitionRef.current.start();
      
      console.log('🎙️ Recording started');
    } catch (err) {
      console.error('Start recording error:', err);
      if (err.message?.includes('already started')) {
        recognitionRef.current.stop();
        setTimeout(() => startRecording(), 200);
      } else {
        setError('Failed to start recording: ' + err.message);
      }
    }
  };

  // ============ STOP RECORDING & AUTO PROCESS ============
  const stopRecording = () => {
    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch (e) {}
    }
    
    cleanupAudio();
    setIsRecording(false);
    isRecordingRef.current = false;
    
    // Use ref to get latest transcript value
    const finalText = transcriptRef.current.trim();
    console.log('📝 Final transcript to process:', finalText);

    // AUTO PROCESS if we have text
    if (finalText) {
      processWithAI(finalText);
    } else {
      setError('No speech detected. Please try again and speak clearly.');
    }
  };

  // ============ PROCESS WITH AI ============
  const processWithAI = async (text) => {
    if (!text || !text.trim()) {
      setError('Please speak something first.');
      return;
    }

    setIsProcessing(true);
    setError(null);

    try {
      console.log('🤖 Processing:', text);

      const res = await axios.post(`${API_URL}/api/voice/process`, {
        text: text.trim(),
        enable_tts: false
      });

      const aiResponse = res.data.response_text;
      console.log('✅ AI Response:', aiResponse);

      setResponse(aiResponse);

      if (!isMuted && synthesisRef.current) {
        speakText(aiResponse);
      }

      addToHistory(text, aiResponse);

    } catch (err) {
      console.error('❌ Processing error:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to process.');
    } finally {
      setIsProcessing(false);
    }
  };

  // ============ BROWSER TTS ============
  const speakText = (text) => {
    if (!synthesisRef.current) return;
    synthesisRef.current.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-US';
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;

    const voices = synthesisRef.current.getVoices();
    const preferredVoice = voices.find(v => 
      v.name.includes('Google') || v.name.includes('Samantha') || v.lang.startsWith('en')
    );
    if (preferredVoice) utterance.voice = preferredVoice;

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    synthesisRef.current.speak(utterance);
  };

  // ============ HELPERS ============
  const addToHistory = (userMessage, aiResponse) => {
    setChatHistory(prev => [{
      id: Date.now(),
      timestamp: new Date().toLocaleTimeString(),
      userMessage,
      aiResponse
    }, ...prev]);
  };

  const clearAll = () => {
    setChatHistory([]);
    setTranscript('');
    setInterimTranscript('');
    setResponse('');
    setError(null);
    transcriptRef.current = '';
  };

  const toggleMute = () => {
    setIsMuted(!isMuted);
    if (synthesisRef.current) {
      synthesisRef.current.cancel();
      setIsSpeaking(false);
    }
  };

  const replayResponse = () => {
    if (response && !isMuted) speakText(response);
  };

  // ============ RENDER ============
  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '24px' }}>
      
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '32px' }}>
        
        {/* ============ LEFT: VOICE RECORDER ============ */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          style={{
            background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.9) 100%)',
            border: '1px solid rgba(59, 130, 246, 0.3)',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
            borderRadius: '24px',
            padding: '32px',
            position: 'relative',
            overflow: 'hidden'
          }}
        >
          {/* Background Glow */}
          <div style={{
            position: 'absolute',
            top: '-150px',
            left: '-150px',
            width: '500px',
            height: '500px',
            borderRadius: '50%',
            background: isRecording 
              ? 'radial-gradient(circle, rgba(239, 68, 68, 0.15) 0%, transparent 70%)'
              : 'radial-gradient(circle, rgba(59, 130, 246, 0.1) 0%, transparent 70%)',
            pointerEvents: 'none',
            transition: 'background 0.5s ease'
          }} />

          <div style={{ position: 'relative', zIndex: 10 }}>
            
            {/* Header */}
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'space-between', 
              marginBottom: '32px' 
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <motion.div
                  animate={{ scale: isRecording ? [1, 1.3, 1] : 1 }}
                  transition={{ duration: 1, repeat: isRecording ? Infinity : 0 }}
                  style={{
                    width: '14px',
                    height: '14px',
                    borderRadius: '50%',
                    backgroundColor: isRecording ? '#ef4444' : isProcessing ? '#f59e0b' : isSpeaking ? '#a855f7' : '#10b981',
                    boxShadow: isRecording ? '0 0 20px rgba(239, 68, 68, 0.8)' : 'none'
                  }}
                />
                <span style={{ fontSize: '16px', fontWeight: 600, color: '#e2e8f0' }}>
                  {isRecording ? '🎙️ Listening... Speak now!' : 
                   isProcessing ? '🤖 Processing your request...' : 
                   isSpeaking ? '🔊 Speaking response...' : 
                   '✨ Ready - Click to start'}
                </span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                {/* Mode Badge */}
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '8px 16px',
                  borderRadius: '9999px',
                  backgroundColor: 'rgba(16, 185, 129, 0.1)',
                  border: '1px solid rgba(16, 185, 129, 0.3)'
                }}>
                  <Wifi style={{ width: '16px', height: '16px', color: '#34d399' }} />
                  <span style={{ fontSize: '13px', color: '#34d399', fontWeight: 600 }}>
                    Voice Active
                  </span>
                </div>

                {/* Mute Toggle */}
                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  onClick={toggleMute}
                  style={{
                    width: '44px',
                    height: '44px',
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    backgroundColor: 'rgba(30, 41, 59, 0.8)',
                    border: '1px solid rgba(71, 85, 105, 0.5)',
                    cursor: 'pointer'
                  }}
                >
                  {isMuted ? 
                    <VolumeX style={{ width: '22px', height: '22px', color: '#94a3b8' }} /> : 
                    <Volume2 style={{ width: '22px', height: '22px', color: '#a855f7' }} />
                  }
                </motion.button>
              </div>
            </div>

            {/* Audio Level Visualizer */}
            <AnimatePresence>
              {isRecording && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  style={{ marginBottom: '24px' }}
                >
                  <div style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '16px',
                    padding: '16px',
                    backgroundColor: 'rgba(30, 41, 59, 0.5)',
                    borderRadius: '16px',
                    border: '1px solid rgba(59, 130, 246, 0.2)'
                  }}>
                    <div style={{
                      flex: 1,
                      height: '20px',
                      backgroundColor: 'rgba(15, 23, 42, 0.8)',
                      borderRadius: '10px',
                      overflow: 'hidden'
                    }}>
                      <motion.div
                        style={{
                          height: '100%',
                          width: `${audioLevel}%`,
                          borderRadius: '10px',
                          background: audioLevel > 20 
                            ? 'linear-gradient(90deg, #10b981, #34d399)' 
                            : audioLevel > 5 
                            ? 'linear-gradient(90deg, #f59e0b, #fbbf24)' 
                            : 'linear-gradient(90deg, #ef4444, #f87171)',
                          transition: 'width 0.1s ease'
                        }}
                      />
                    </div>
                    <span style={{ 
                      fontSize: '14px', 
                      fontWeight: 600,
                      color: audioLevel > 20 ? '#10b981' : audioLevel > 5 ? '#f59e0b' : '#ef4444',
                      minWidth: '100px',
                      textAlign: 'right'
                    }}>
                      {audioLevel > 20 ? '🎙️ Perfect!' : audioLevel > 5 ? '🔈 Louder!' : '🔇 Speak up!'}
                    </span>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Timer */}
            <AnimatePresence>
              {isRecording && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  style={{ textAlign: 'center', marginBottom: '24px' }}
                >
                  <div style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '12px',
                    padding: '16px 32px',
                    borderRadius: '9999px',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    border: '1px solid rgba(239, 68, 68, 0.3)'
                  }}>
                    <motion.div
                      animate={{ scale: [1, 1.3, 1] }}
                      transition={{ duration: 1, repeat: Infinity }}
                      style={{ width: '14px', height: '14px', borderRadius: '50%', backgroundColor: '#ef4444' }}
                    />
                    <Clock style={{ width: '24px', height: '24px', color: '#f87171' }} />
                    <span style={{ 
                      fontSize: '32px', 
                      fontFamily: 'monospace', 
                      fontWeight: 'bold', 
                      color: '#f87171' 
                    }}>
                      {formatTime(recordingTime)}
                    </span>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Main Button */}
            <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '32px' }}>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={isRecording ? stopRecording : startRecording}
                disabled={isProcessing || !speechSupported}
                style={{
                  position: 'relative',
                  width: '140px',
                  height: '140px',
                  borderRadius: '50%',
                  border: 'none',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: isProcessing ? 'wait' : 'pointer',
                  background: isRecording 
                    ? 'linear-gradient(135deg, #dc2626, #ef4444)' 
                    : 'linear-gradient(135deg, #2563eb, #7c3aed)',
                  boxShadow: isRecording 
                    ? '0 0 80px rgba(239, 68, 68, 0.5), 0 0 40px rgba(239, 68, 68, 0.3)' 
                    : '0 0 60px rgba(59, 130, 246, 0.4), 0 0 30px rgba(124, 58, 237, 0.3)',
                  opacity: isProcessing || !speechSupported ? 0.5 : 1,
                  transition: 'all 0.3s ease'
                }}
              >
                {isProcessing ? (
                  <Loader2 style={{ width: '56px', height: '56px', color: 'white', animation: 'spin 1s linear infinite' }} />
                ) : isRecording ? (
                  <Square style={{ width: '48px', height: '48px', color: 'white', fill: 'white' }} />
                ) : (
                  <Mic style={{ width: '56px', height: '56px', color: 'white' }} />
                )}

                {/* Pulse rings */}
                {isRecording && (
                  <>
                    <motion.div
                      animate={{ scale: [1, 1.4], opacity: [0.6, 0] }}
                      transition={{ duration: 1.5, repeat: Infinity }}
                      style={{
                        position: 'absolute',
                        inset: 0,
                        borderRadius: '50%',
                        border: '3px solid #ef4444'
                      }}
                    />
                    <motion.div
                      animate={{ scale: [1, 1.7], opacity: [0.4, 0] }}
                      transition={{ duration: 1.5, repeat: Infinity, delay: 0.3 }}
                      style={{
                        position: 'absolute',
                        inset: 0,
                        borderRadius: '50%',
                        border: '3px solid #ef4444'
                      }}
                    />
                  </>
                )}
              </motion.button>
            </div>

            {/* Button Label */}
            <p style={{ 
              textAlign: 'center', 
              color: '#94a3b8', 
              fontSize: '14px',
              marginBottom: '24px'
            }}>
              {isRecording ? 'Click to stop and process' : 'Click to start recording'}
            </p>

            {/* Real-time Transcript */}
            <AnimatePresence>
              {(transcript || interimTranscript) && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  style={{ marginBottom: '24px' }}
                >
                  <div style={{
                    backgroundColor: 'rgba(30, 41, 59, 0.6)',
                    border: '1px solid rgba(59, 130, 246, 0.3)',
                    borderRadius: '20px',
                    padding: '24px'
                  }}>
                    <div style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      gap: '10px', 
                      marginBottom: '16px' 
                    }}>
                      <MessageSquare style={{ width: '22px', height: '22px', color: '#60a5fa' }} />
                      <span style={{ fontSize: '15px', fontWeight: 700, color: '#60a5fa' }}>
                        {isRecording ? 'Listening...' : 'You said'}
                      </span>
                    </div>
                    
                    <p style={{ 
                      color: '#f1f5f9', 
                      fontSize: '20px', 
                      lineHeight: 1.6, 
                      margin: 0 
                    }}>
                      {transcript}
                      {interimTranscript && (
                        <span style={{ color: '#94a3b8', fontStyle: 'italic' }}> {interimTranscript}</span>
                      )}
                      {isRecording && (
                        <motion.span
                          animate={{ opacity: [1, 0, 1] }}
                          transition={{ duration: 0.8, repeat: Infinity }}
                          style={{
                            display: 'inline-block',
                            width: '3px',
                            height: '24px',
                            backgroundColor: '#60a5fa',
                            marginLeft: '6px',
                            verticalAlign: 'middle'
                          }}
                        />
                      )}
                    </p>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Processing Indicator */}
            <AnimatePresence>
              {isProcessing && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  style={{ marginBottom: '24px' }}
                >
                  <div style={{
                    background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(124, 58, 237, 0.1))',
                    border: '1px solid rgba(59, 130, 246, 0.3)',
                    borderRadius: '20px',
                    padding: '24px',
                    textAlign: 'center'
                  }}>
                    <Loader2 style={{ 
                      width: '40px', 
                      height: '40px', 
                      color: '#60a5fa', 
                      margin: '0 auto 16px',
                      animation: 'spin 1s linear infinite' 
                    }} />
                    <p style={{ color: '#94a3b8', fontSize: '16px', margin: 0 }}>
                      Processing with AI agents...
                    </p>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* AI Response */}
            <AnimatePresence>
              {response && !isProcessing && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                >
                  <div style={{
                    background: 'linear-gradient(135deg, rgba(88, 28, 135, 0.2), rgba(157, 23, 77, 0.15))',
                    border: '1px solid rgba(168, 85, 247, 0.3)',
                    borderRadius: '20px',
                    padding: '24px'
                  }}>
                    <div style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'space-between', 
                      marginBottom: '16px' 
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <Sparkles style={{ width: '22px', height: '22px', color: '#f472b6' }} />
                        <span style={{ fontSize: '15px', fontWeight: 700, color: '#f472b6' }}>
                          AI Response
                        </span>
                      </div>
                      
                      <motion.button
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                        onClick={replayResponse}
                        disabled={isMuted}
                        style={{
                          width: '44px',
                          height: '44px',
                          borderRadius: '50%',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          backgroundColor: 'rgba(168, 85, 247, 0.2)',
                          border: '1px solid rgba(168, 85, 247, 0.3)',
                          cursor: 'pointer',
                          opacity: isMuted ? 0.5 : 1
                        }}
                      >
                        {isSpeaking ? (
                          <Loader2 style={{ width: '22px', height: '22px', color: '#c084fc', animation: 'spin 1s linear infinite' }} />
                        ) : (
                          <Play style={{ width: '22px', height: '22px', color: '#c084fc' }} />
                        )}
                      </motion.button>
                    </div>
                    <p style={{ 
                      color: '#f1f5f9', 
                      fontSize: '18px', 
                      lineHeight: 1.7, 
                      margin: 0, 
                      whiteSpace: 'pre-wrap' 
                    }}>
                      {response}
                    </p>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Error */}
            <AnimatePresence>
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  style={{ marginTop: '24px' }}
                >
                  <div style={{
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    borderRadius: '16px',
                    padding: '20px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '14px'
                  }}>
                    <XCircle style={{ width: '24px', height: '24px', color: '#f87171', flexShrink: 0 }} />
                    <p style={{ color: '#f87171', fontSize: '15px', margin: 0, flex: 1 }}>{error}</p>
                    <button 
                      onClick={() => setError(null)} 
                      style={{ 
                        background: 'none', 
                        border: 'none', 
                        color: '#f87171', 
                        cursor: 'pointer', 
                        fontSize: '20px',
                        padding: '4px'
                      }}
                    >
                      ✕
                    </button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Empty State Instructions */}
            {!isRecording && !transcript && !response && !isProcessing && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                style={{ textAlign: 'center', marginTop: '16px' }}
              >
                <p style={{ fontSize: '18px', color: '#94a3b8', marginBottom: '12px' }}>
                  🎤 Click the microphone button to start
                </p>
                <p style={{ fontSize: '14px', color: '#64748b', marginBottom: '20px' }}>
                  Speak naturally and the AI will process your request automatically
                </p>
                <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '10px' }}>
                  {['Weather in Tokyo', 'Top 5 Python repos', 'Latest AI news'].map(example => (
                    <span key={example} style={{
                      padding: '10px 18px',
                      borderRadius: '9999px',
                      backgroundColor: 'rgba(30, 41, 59, 0.8)',
                      border: '1px solid rgba(59, 130, 246, 0.2)',
                      color: '#94a3b8',
                      fontSize: '14px'
                    }}>
                      "{example}"
                    </span>
                  ))}
                </div>
              </motion.div>
            )}

          </div>
        </motion.div>

        {/* ============ RIGHT: CHAT HISTORY ============ */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          style={{
            background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.9) 100%)',
            border: '1px solid rgba(59, 130, 246, 0.2)',
            borderRadius: '24px',
            padding: '24px',
            position: 'sticky',
            top: '100px',
            maxHeight: 'calc(100vh - 150px)',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column'
          }}
        >
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'space-between', 
            marginBottom: '24px' 
          }}>
            <h3 style={{ 
              fontSize: '18px', 
              fontWeight: 700, 
              color: '#e2e8f0', 
              display: 'flex', 
              alignItems: 'center', 
              gap: '10px', 
              margin: 0 
            }}>
              <MessageSquare style={{ width: '22px', height: '22px', color: '#60a5fa' }} />
              Chat History
            </h3>
            {chatHistory.length > 0 && (
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={clearAll}
                style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '6px', 
                  fontSize: '14px', 
                  color: '#f87171', 
                  cursor: 'pointer', 
                  background: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.2)',
                  borderRadius: '8px',
                  padding: '8px 12px'
                }}
              >
                <Trash2 style={{ width: '16px', height: '16px' }} />
                Clear
              </motion.button>
            )}
          </div>

          <div style={{ flex: 1, overflowY: 'auto', paddingRight: '8px' }}>
            {chatHistory.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '60px 0' }}>
                <div style={{ 
                  width: '80px', 
                  height: '80px', 
                  margin: '0 auto 20px', 
                  borderRadius: '50%', 
                  backgroundColor: 'rgba(30, 41, 59, 0.8)', 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'center' 
                }}>
                  <Mic style={{ width: '40px', height: '40px', color: '#475569' }} />
                </div>
                <p style={{ color: '#64748b', fontSize: '16px', margin: 0 }}>No conversations yet</p>
                <p style={{ color: '#475569', fontSize: '14px', marginTop: '8px' }}>
                  Start speaking to see history
                </p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {chatHistory.map((entry, index) => (
                  <motion.div 
                    key={entry.id} 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                    style={{ 
                      backgroundColor: 'rgba(30, 41, 59, 0.6)', 
                      borderRadius: '16px', 
                      padding: '18px',
                      border: '1px solid rgba(59, 130, 246, 0.1)'
                    }}
                  >
                    <p style={{ 
                      fontSize: '12px', 
                      color: '#64748b', 
                      margin: '0 0 12px 0', 
                      display: 'flex', 
                      alignItems: 'center', 
                      gap: '6px' 
                    }}>
                      <Clock style={{ width: '14px', height: '14px' }} />
                      {entry.timestamp}
                    </p>
                    <p style={{ color: '#60a5fa', fontSize: '14px', margin: '0 0 10px 0', lineHeight: 1.5 }}>
                      <strong>You:</strong> {entry.userMessage}
                    </p>
                    <p style={{ color: '#f472b6', fontSize: '14px', margin: 0, lineHeight: 1.5 }}>
                      <strong>AI:</strong> {entry.aiResponse.length > 120 ? entry.aiResponse.substring(0, 120) + '...' : entry.aiResponse}
                    </p>
                    <button
                      onClick={() => speakText(entry.aiResponse)}
                      style={{ 
                        marginTop: '12px', 
                        fontSize: '13px', 
                        color: '#a78bfa', 
                        cursor: 'pointer', 
                        background: 'rgba(167, 139, 250, 0.1)',
                        border: '1px solid rgba(167, 139, 250, 0.2)',
                        borderRadius: '8px',
                        padding: '6px 12px',
                        display: 'flex', 
                        alignItems: 'center', 
                        gap: '6px' 
                      }}
                    >
                      <Play style={{ width: '14px', height: '14px' }} />
                      Replay
                    </button>
                  </motion.div>
                ))}
              </div>
            )}
          </div>
        </motion.div>
      </div>

      <style>{`
        @keyframes spin { 
          from { transform: rotate(0deg); } 
          to { transform: rotate(360deg); } 
        }
      `}</style>
    </div>
  );
};

export default VoiceAssistant;