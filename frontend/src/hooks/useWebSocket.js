/**
 * 🔌 WEBSOCKET HOOK - FIXED VERSION
 * Prevents infinite reconnection loop
 */

import { useState, useEffect, useRef, useCallback } from 'react';

export const useWebSocket = (url, options = {}) => {
  const {
    onMessage = () => {},
    onConnect = () => {},
    onDisconnect = () => {},
    onError = () => {},
    reconnectAttempts = 3,  // ✅ REDUCED from 5
    reconnectInterval = 5000,  // ✅ INCREASED from 3000
    autoConnect = true,
    enabled = true  // ✅ NEW: Allow disabling
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectCountRef = useRef(0);
  const manualDisconnectRef = useRef(false);
  const isConnectingRef = useRef(false);  // ✅ NEW: Prevent duplicate connections
  const isMountedRef = useRef(true);  // ✅ NEW: Prevent state updates after unmount

  // ✅ IMPROVED: Better connection logic
  const connect = useCallback(() => {
    // Don't connect if disabled
    if (!enabled) {
      console.log('🔌 WebSocket disabled');
      return;
    }

    // Don't connect if already connecting or connected
    if (isConnectingRef.current || wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('🔌 Already connecting/connected');
      return;
    }

    // Max reconnect attempts reached
    if (reconnectCountRef.current >= reconnectAttempts) {
      console.log('🔌 Max reconnect attempts reached');
      setConnectionStatus('failed');
      return;
    }

    try {
      isConnectingRef.current = true;
      setConnectionStatus('connecting');
      console.log('🔌 Connecting to:', url, `(attempt ${reconnectCountRef.current + 1}/${reconnectAttempts})`);

      wsRef.current = new WebSocket(url);

      wsRef.current.onopen = (event) => {
        if (!isMountedRef.current) return;
        
        console.log('✅ WebSocket connected');
        isConnectingRef.current = false;
        setIsConnected(true);
        setConnectionStatus('connected');
        reconnectCountRef.current = 0;
        manualDisconnectRef.current = false;
        onConnect(event);

        // Start heartbeat
        startHeartbeat();
      };

      wsRef.current.onmessage = (event) => {
        if (!isMountedRef.current) return;
        
        try {
          const data = JSON.parse(event.data);
          setLastMessage(data);
          onMessage(data);

          if (data.type === 'pong') {
            console.log('💓 Heartbeat OK');
          }
        } catch (error) {
          console.error('❌ Message parse error:', error);
        }
      };

      wsRef.current.onerror = (error) => {
        if (!isMountedRef.current) return;
        
        console.error('❌ WebSocket error');
        isConnectingRef.current = false;
        setConnectionStatus('error');
        onError(error);
      };

      wsRef.current.onclose = (event) => {
        if (!isMountedRef.current) return;
        
        console.log('🔌 WebSocket closed:', event.code);
        isConnectingRef.current = false;
        setIsConnected(false);
        setConnectionStatus('disconnected');
        onDisconnect(event);

        stopHeartbeat();

        // ✅ IMPROVED: Only reconnect if not manual and component mounted
        if (!manualDisconnectRef.current && 
            isMountedRef.current && 
            enabled &&
            reconnectCountRef.current < reconnectAttempts) {
          
          console.log(`🔄 Reconnecting in ${reconnectInterval/1000}s...`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            if (isMountedRef.current && !manualDisconnectRef.current) {
              reconnectCountRef.current += 1;
              connect();
            }
          }, reconnectInterval);
        } else if (reconnectCountRef.current >= reconnectAttempts) {
          console.log('❌ Max reconnect attempts reached. Giving up.');
          setConnectionStatus('failed');
        }
      };

    } catch (error) {
      console.error('❌ Connection error:', error);
      isConnectingRef.current = false;
      setConnectionStatus('error');
    }
  }, [url, onConnect, onMessage, onDisconnect, onError, reconnectAttempts, reconnectInterval, enabled]);

  // Disconnect
  const disconnect = useCallback(() => {
    console.log('🔌 Disconnecting WebSocket...');
    manualDisconnectRef.current = true;
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual disconnect');
      wsRef.current = null;
    }

    isConnectingRef.current = false;
    setIsConnected(false);
    setConnectionStatus('disconnected');
  }, []);

  // Send message
  const sendMessage = useCallback((type, data = {}) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const message = {
        type,
        data,
        timestamp: new Date().toISOString()
      };

      wsRef.current.send(JSON.stringify(message));
      console.log('📤 Message sent:', type);
      return true;
    } else {
      console.warn('⚠️ WebSocket not connected. State:', wsRef.current?.readyState);
      return false;
    }
  }, []);

  // Heartbeat
  const heartbeatIntervalRef = useRef(null);

  const startHeartbeat = useCallback(() => {
    stopHeartbeat();

    heartbeatIntervalRef.current = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        sendMessage('ping');
      }
    }, 30000); // Every 30 seconds
  }, [sendMessage]);

  const stopHeartbeat = () => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }
  };

  // Auto-connect on mount
  useEffect(() => {
    isMountedRef.current = true;

    if (autoConnect && enabled) {
      // ✅ DELAY initial connection to prevent race conditions
      const initialConnectTimeout = setTimeout(() => {
        if (isMountedRef.current) {
          connect();
        }
      }, 100);

      return () => {
        clearTimeout(initialConnectTimeout);
      };
    }
  }, [autoConnect, enabled]); // ✅ REMOVED connect from dependencies

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      console.log('🔌 useWebSocket unmounting...');
      isMountedRef.current = false;
      manualDisconnectRef.current = true;
      
      stopHeartbeat();
      
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      
      if (wsRef.current) {
        wsRef.current.close(1000, 'Component unmount');
      }
    };
  }, []);

  return {
    isConnected,
    connectionStatus,
    lastMessage,
    sendMessage,
    connect,
    disconnect
  };
};

export default useWebSocket;