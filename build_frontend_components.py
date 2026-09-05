import os

BASE_DIR = r"c:\Users\sithi\OneDrive\Desktop\GROW\market-pulse\frontend\src"

files = {
    "components/Layout.tsx": """import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Activity, List, Settings, Bell } from 'lucide-react';

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  
  const navItems = [
    { name: 'Dashboard', path: '/', icon: Activity },
    { name: 'Watchlist', path: '/watchlist', icon: List },
    { name: 'Smart Watch', path: '/smart-watch', icon: Settings },
  ];

  return (
    <div className="flex h-screen overflow-hidden">
      <aside className="w-64 border-r border-white/10 bg-surface flex flex-col">
        <div className="p-6">
          <h1 className="text-xl font-bold tracking-wider text-primary flex items-center gap-2">
            <Activity className="w-6 h-6" />
            MARKET PULSE
          </h1>
        </div>
        
        <nav className="flex-1 px-4 space-y-2 mt-4">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.name}
                to={item.path}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                  isActive ? 'bg-primary/20 text-primary' : 'text-gray-400 hover:text-white hover:bg-white/5'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span className="font-medium">{item.name}</span>
              </Link>
            )
          })}
        </nav>
      </aside>
      
      <main className="flex-1 overflow-auto bg-background p-8">
        <header className="flex justify-between items-center mb-8">
          <h2 className="text-2xl font-semibold capitalize">
            {location.pathname === '/' ? 'Dashboard' : location.pathname.substring(1).replace('-', ' ')}
          </h2>
          <div className="flex items-center gap-4">
            <button className="p-2 rounded-full hover:bg-white/10 relative">
              <Bell className="w-5 h-5" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-danger rounded-full"></span>
            </button>
          </div>
        </header>
        
        {children}
      </main>
    </div>
  )
}
""",
    "pages/Dashboard.tsx": """import React, { useEffect, useState } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import PulseCard from '../components/PulseCard';

export default function Dashboard() {
  const { wsData } = useWebSocket();
  const [pulseData, setPulseData] = useState<any>({
    INFY: { score: 61, severity: 'IMPORTANT', previous: 40, stock: 'INFY', trail: [40, 48, 61] }
  });

  useEffect(() => {
    if (wsData?.event === 'PULSE_UPDATE') {
      setPulseData((prev: any) => ({
        ...prev,
        [wsData.stock]: {
          ...prev[wsData.stock],
          score: wsData.current_score,
          severity: wsData.severity,
          trail: [...(prev[wsData.stock]?.trail || []), wsData.current_score].slice(-5)
        }
      }));
    }
  }, [wsData]);

  const critical = Object.values(pulseData).filter((d: any) => d.severity === 'CRITICAL');
  const important = Object.values(pulseData).filter((d: any) => d.severity === 'IMPORTANT');

  const handleSimulate = async () => {
    await fetch('http://localhost:8000/api/simulator/market-change', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        stock_id: 1, user_id: 1, current_price: 1540.25, previous_price: 1464.5,
        volume: 2400000, avg_volume: 1000000, sector_change: 0.8
      })
    });
  };

  return (
    <div className="space-y-8">
      <section className="flex gap-4 items-center">
        <div className="glass-panel p-6 flex-1">
          <h3 className="text-gray-400 mb-2">Attention Required</h3>
          <div className="flex gap-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-danger">{critical.length}</div>
              <div className="text-sm">Critical</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-warning">{important.length}</div>
              <div className="text-sm">Important</div>
            </div>
          </div>
        </div>
        
        <button 
          onClick={handleSimulate}
          className="bg-primary hover:bg-primary/80 text-white px-6 py-4 rounded-xl font-bold transition-all shadow-[0_0_20px_rgba(59,130,246,0.3)] hover:shadow-[0_0_30px_rgba(59,130,246,0.5)]"
        >
          Simulate Market Change
        </button>
      </section>

      <section className="space-y-4">
        <h3 className="font-bold text-xl flex items-center gap-2">
          CRITICAL ATTENTION 🔴
        </h3>
        {critical.length === 0 && <p className="text-gray-500">No critical alerts right now.</p>}
        {critical.map((d: any) => (
          <PulseCard key={d.stock} data={d} />
        ))}
      </section>

      <section className="space-y-4">
        <h3 className="font-bold text-xl flex items-center gap-2 text-warning">
          IMPORTANT 🟠
        </h3>
        {important.length === 0 && <p className="text-gray-500">No important alerts right now.</p>}
        {important.map((d: any) => (
          <PulseCard key={d.stock} data={d} />
        ))}
      </section>
    </div>
  );
}
""",
    "pages/Watchlist.tsx": """import React from 'react';

export default function Watchlist() {
  return (
    <div className="glass-panel p-6">
      <h3 className="text-xl font-bold mb-6">Hierarchy</h3>
      <div className="font-mono bg-surface p-4 rounded-lg text-gray-300 whitespace-pre">
{`▼ Financial
  ▼ Private
    ├── INFY
    ├── TCS
    └── HDFCBANK

  ▼ Government / PSU
    ├── SBI
    └── ONGC`}
      </div>
    </div>
  )
}
""",
    "pages/SmartWatch.tsx": """import React from 'react';

export default function SmartWatch() {
  return (
    <div className="glass-panel p-6 max-w-2xl">
      <div className="flex justify-between items-center mb-8 border-b border-white/10 pb-6">
        <div>
          <h3 className="text-2xl font-bold">SMART WATCH</h3>
          <p className="text-gray-400 mt-1">Watching 24 stocks</p>
        </div>
        <div className="bg-success text-white px-6 py-2 rounded-full font-bold">
          [ ON ]
        </div>
      </div>
      
      <div className="space-y-6">
        <div>
          <label className="block text-gray-400 mb-2">Price Threshold</label>
          <input type="text" value="5%" readOnly className="bg-surfaceHighlight px-4 py-2 rounded-lg w-full" />
        </div>
        <div>
          <label className="block text-gray-400 mb-2">Volume Anomaly</label>
          <input type="text" value="2x" readOnly className="bg-surfaceHighlight px-4 py-2 rounded-lg w-full" />
        </div>
      </div>
    </div>
  )
}
""",
    "components/PulseCard.tsx": """import React, { useState } from 'react';
import { TrendingUp, AlertTriangle } from 'lucide-react';

export default function PulseCard({ data }: { data: any }) {
  const [showWhy, setShowWhy] = useState(false);
  
  return (
    <div className={`glass-panel border-l-4 ${data.severity === 'CRITICAL' ? 'border-l-danger' : 'border-l-warning'} p-6 transition-all duration-300`}>
      <div className="flex justify-between items-start">
        <div>
          <div className="flex items-center gap-4 mb-4">
            <h4 className="text-2xl font-bold">{data.stock}</h4>
            <div className={`text-xl font-bold ${data.severity === 'CRITICAL' ? 'text-danger' : 'text-warning'}`}>
              {data.severity === 'CRITICAL' ? '🔴' : '🟠'} {data.score}
            </div>
          </div>
          <div className="space-y-2 text-gray-300">
            <div className="flex gap-2 items-center"><TrendingUp className="w-4 h-4 text-success" /> +5.2%</div>
            <div className="flex gap-2 items-center"><AlertTriangle className="w-4 h-4 text-warning" /> Volume 2.4×</div>
            <div>Sector +0.8%</div>
          </div>
          <div className="mt-4 pt-4 border-t border-white/10 text-sm text-gray-400">
            Pulse Trail: {data.trail?.join(' → ')}
          </div>
        </div>
        <button 
          onClick={() => setShowWhy(!showWhy)}
          className="px-4 py-2 bg-surfaceHighlight hover:bg-white/10 rounded-lg transition-colors"
        >
          [ Why? ]
        </button>
      </div>
      
      {showWhy && (
        <div className="mt-6 p-4 bg-surfaceHighlight rounded-lg border border-white/5 animate-fade-in text-sm space-y-2 text-gray-300">
          <p><span className="text-success">↑</span> Price +5.2%</p>
          <p><span className="text-warning">↑</span> Volume 2.4× normal</p>
          <p><span className="text-success">↑</span> Outperformed sector by 4.4%</p>
          <p className="text-danger flex items-center gap-2"><AlertTriangle className="w-4 h-4" /> Your 5% threshold was crossed</p>
        </div>
      )}
    </div>
  )
}
""",
    "hooks/useWebSocket.ts": """import { useState, useEffect } from 'react';

export const useWebSocket = () => {
  const [wsData, setWsData] = useState<any>(null);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/market');
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('WS WSData:', data);
      setWsData(data);
    };

    return () => ws.close();
  }, []);

  return { wsData };
}
"""
}

for filepath, content in files.items():
    full_path = os.path.join(BASE_DIR, filepath.replace("/", "\\\\"))
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Frontend components created.")
