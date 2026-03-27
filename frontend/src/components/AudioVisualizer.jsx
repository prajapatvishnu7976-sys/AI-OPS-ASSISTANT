import React, { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';

const AudioVisualizer = ({ isActive, stream }) => {
  const [levels, setLevels] = useState(Array(40).fill(20));
  const analyserRef = useRef(null);
  const audioContextRef = useRef(null);
  const animationFrameRef = useRef(null);

  useEffect(() => {
    if (isActive && stream) {
      // Setup audio analyzer
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      analyserRef.current = audioContextRef.current.createAnalyser();
      analyserRef.current.fftSize = 128;
      source.connect(analyserRef.current);

      // Update levels
      const updateLevels = () => {
        if (!analyserRef.current) return;

        const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
        analyserRef.current.getByteFrequencyData(dataArray);
        
        const newLevels = Array.from({ length: 40 }, (_, i) => {
          const index = Math.floor(i * dataArray.length / 40);
          return Math.min(100, (dataArray[index] / 255) * 100) || 20;
        });
        
        setLevels(newLevels);
        animationFrameRef.current = requestAnimationFrame(updateLevels);
      };

      updateLevels();
    } else {
      setLevels(Array(40).fill(20));
    }

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, [isActive, stream]);

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '2px',
      height: '128px',
      background: 'rgba(15, 23, 42, 0.3)',
      borderRadius: '16px',
      border: '1px solid rgba(168, 85, 247, 0.1)',
      padding: '16px'
    }}>
      {levels.map((level, index) => (
        <motion.div
          key={index}
          style={{
            width: '4px',
            background: 'linear-gradient(to top, #9333ea, #ec4899)',
            borderRadius: '2px'
          }}
          animate={{
            height: isActive ? `${level}%` : '20%',
            opacity: isActive ? [0.5, 1, 0.5] : 0.3
          }}
          transition={{
            duration: 0.2,
            ease: "easeOut"
          }}
        />
      ))}
    </div>
  );
};

export default AudioVisualizer;