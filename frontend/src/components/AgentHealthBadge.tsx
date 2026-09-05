import React, { useEffect, useState } from 'react';
import { io, Socket } from 'socket.io-client';

// Hook to monitor backend agent health via WebSocket.
function useAgentStatus() {
  const [healthy, setHealthy] = useState<boolean>(false);
  useEffect(() => {
    const backendUrl = (import.meta as any).env?.VITE_BACKEND_URL || '';
    const socket: Socket = io(backendUrl);
    // Backend should emit 'agentStatus' with a boolean.
    socket.on('agentStatus', (status: boolean) => {
      setHealthy(status);
    });
    // Request initial status.
    socket.emit('requestAgentStatus');
    return () => {
      socket.disconnect();
    };
  }, []);

  return healthy;
}

const AgentHealthBadge: React.FC = () => {
  const healthy = useAgentStatus();
  const color = healthy ? 'bg-success' : 'bg-danger';
  return (
    <span
      className={`inline-block w-2 h-2 rounded-full ${color} mr-2`}
      title={healthy ? 'Agents healthy' : 'Agents offline'}
    />
  );
};

export default AgentHealthBadge;
