import { useEffect, useState } from 'react';
import { X } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { fetchPulseHistory } from '../services/api';
import type { PulseScore } from '../services/api';

interface Props {
  stockId: number;
  symbol: string;
  onClose: () => void;
}

function scoreToColor(score: number): string {
  if (score > 80) return '#e8102a';
  if (score > 60) return '#d97706';
  if (score > 30) return '#f25100';
  return '#6b7280';
}

const CustomTooltip = ({ active, payload }: any) => {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload as { score: number; severity: string; time: string };
  return (
    <div className="bg-surfaceHighlight border border-border rounded px-3 py-2 text-xs shadow-lg">
      <div className={`num font-bold`} style={{ color: scoreToColor(d.score) }}>{d.score}</div>
      <div className="text-textMuted">{d.severity}</div>
      <div className="text-textMuted">{d.time}</div>
    </div>
  );
};

export default function PulseTrailDrawer({ stockId, symbol, onClose }: Props) {
  const [history, setHistory] = useState<PulseScore[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetchPulseHistory(stockId)
      .then(setHistory)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [stockId]);

  const chartData = history.map(h => ({
    score: h.score,
    severity: h.severity,
    time: new Date(h.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    timestamp: h.timestamp,
  }));

  const latest = history[history.length - 1];

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative w-full max-w-lg bg-surface border-l border-border flex flex-col animate-slide-in shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <div>
            <span className="text-base font-bold text-foreground">{symbol}</span>
            <span className="ml-2 text-xs text-textMuted">— Pulse Trail</span>
          </div>
          <button onClick={onClose} className="p-1.5 rounded hover:bg-black/5 dark:bg-white/10 text-textMuted hover:text-foreground transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-5">
          {loading ? (
            <div className="py-12 text-center text-textMuted text-sm">Loading trail...</div>
          ) : history.length === 0 ? (
            <div className="py-12 text-center text-textMuted text-sm">No history yet. Run the simulator to generate data.</div>
          ) : (
            <>
              {/* Current score */}
              {latest && (
                <div className="mb-6 pb-4 border-b border-border flex items-baseline gap-3">
                  <span className="num text-3xl font-bold" style={{ color: scoreToColor(latest.score) }}>
                    {latest.score}
                  </span>
                  <span className="text-sm text-textMuted">{latest.severity}</span>
                  <span className="ml-auto text-xs text-textMuted">
                    {history.length} data point{history.length !== 1 ? 's' : ''}
                  </span>
                </div>
              )}

              {/* Chart */}
              <div className="h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis
                      dataKey="time"
                      tick={{ fill: '#6b7280', fontSize: 10 }}
                      tickLine={false}
                      axisLine={false}
                    />
                    <YAxis
                      domain={[0, 100]}
                      tick={{ fill: '#6b7280', fontSize: 10 }}
                      tickLine={false}
                      axisLine={false}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    {/* Severity bands */}
                    <ReferenceLine y={30} stroke="rgba(255,255,255,0.05)" strokeDasharray="4 4" />
                    <ReferenceLine y={60} stroke="rgba(215,119,6,0.15)" strokeDasharray="4 4" />
                    <ReferenceLine y={80} stroke="rgba(232,16,42,0.15)" strokeDasharray="4 4" />
                    <Line
                      type="monotone"
                      dataKey="score"
                      stroke="#f25100"
                      strokeWidth={2}
                      dot={(props) => {
                        const { cx, cy, payload } = props;
                        return (
                          <circle
                            key={`dot-${payload.timestamp}`}
                            cx={cx} cy={cy} r={3}
                            fill={scoreToColor(payload.score)}
                            stroke="none"
                          />
                        );
                      }}
                      isAnimationActive={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* Legend */}
              <div className="flex items-center gap-4 mt-4 text-[10px] text-textMuted">
                <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-danger/50 inline-block" /> Critical (&gt;80)</span>
                <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-warning/50 inline-block" /> Important (61-80)</span>
                <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-gray-600 inline-block" /> Normal (0-30)</span>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
