import React, { createContext, useCallback, useContext, useEffect, useRef } from 'react';
import { useApp } from './AppContext';
import { getUserId } from '../services/api';

interface WSContextType {
  connected: boolean;
}
const WSContext = createContext<WSContextType>({ connected: false });

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
  const { refreshPulse, applyPulseUpdate } = useApp();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef = useRef(true);
  const connectedRef = useRef(false);

  const connect = useCallback(() => {
    if (!mountedRef.current) return;
    try {
      const uid = getUserId();
      const ws = new WebSocket(`ws://localhost:8000/ws/market?user_id=${uid}`);
      wsRef.current = ws;

      ws.onopen = () => {
        connectedRef.current = true;
        refreshPulse();
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.event === 'PULSE_UPDATE') {
            applyPulseUpdate(
              data.stock_id,
              data.current_score,
              data.severity,
              data.momentum ?? 0,
            );
            setTimeout(refreshPulse, 600);
          } else if (data.event === 'NOTIFICATION') {
            refreshPulse();
          }
        } catch { /* ignore */ }
      };

      ws.onclose = () => {
        connectedRef.current = false;
        if (mountedRef.current) {
          reconnectRef.current = setTimeout(connect, 3000);
        }
      };

      ws.onerror = () => ws.close();
    } catch { /* ignore */ }
  }, [refreshPulse, applyPulseUpdate]);

  useEffect(() => {
    mountedRef.current = true;
    connect();
    return () => {
      mountedRef.current = false;
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return <WSContext.Provider value={{ connected: connectedRef.current }}>{children}</WSContext.Provider>;
}

export function useGlobalWebSocket() {
  return useContext(WSContext);
}
