import { TrendingUp, TrendingDown } from 'lucide-react';
import { useApp } from '../context/AppContext';
import type { PulseScore } from '../services/api';

const SEVERITY_STYLES: Record<string, { border: string; badge: string; score: string }> = {
  CRITICAL:  { border: 'border-danger/40',  badge: 'badge-critical',  score: 'text-danger' },
  IMPORTANT: { border: 'border-warning/40', badge: 'badge-important', score: 'text-warning' },
  MODERATE:  { border: 'border-primary/30', badge: 'badge-moderate',  score: 'text-primary' },
  NORMAL:    { border: 'border-border',    badge: 'badge-normal',    score: 'text-textMuted' },
};

function fmt(n: number): string {
  return n.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

interface AttentionCardProps {
  pulse: PulseScore;
  compact?: boolean;
}

export default function AttentionCard({ pulse, compact = false }: AttentionCardProps) {
  const { openDrawer } = useApp();
  const style = SEVERITY_STYLES[pulse.severity] ?? SEVERITY_STYLES.NORMAL;

  const snap = pulse.snapshot;
  const price = snap?.price ?? 0;
  const prev = snap?.previous_price ?? price;
  const chg = prev > 0 ? ((price - prev) / prev) * 100 : 0;
  const isUp = chg >= 0;
  const vol = snap?.volume ?? 0;
  const avgVol = snap?.average_volume ?? 1;
  const volRatio = avgVol > 0 ? vol / avgVol : 1;
  const symbol = pulse.stock?.symbol ?? `#${pulse.stock_id}`;

  const momentumLabel =
    (pulse.momentum ?? 0) > 20 ? '↑ Rising' :
    (pulse.momentum ?? 0) < -20 ? '↓ Falling' : null;

  if (compact) {
    return (
      <div
        className={`flex items-center justify-between px-4 py-2.5 border-b border-border hover:bg-black/5 dark:bg-white/5 cursor-pointer transition-colors`}
        onClick={() => openDrawer('stock', pulse.stock_id, symbol)}
      >
        <div className="flex items-center gap-3">
          <span className={`num text-sm font-semibold text-foreground`}>{symbol}</span>
          {price > 0 && (
            <span className={`num text-xs ${isUp ? 'text-success' : 'text-danger'}`}>
              {isUp ? '+' : ''}{chg.toFixed(2)}%
            </span>
          )}
        </div>
        <span className={`num text-sm font-semibold ${style.score}`}>{pulse.score}</span>
      </div>
    );
  }

  return (
    <div className={`bg-surface border ${style.border} rounded-sm p-4 animate-fade-in`}>
      {/* Top row */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-base font-bold text-foreground">{symbol}</span>
            {momentumLabel && (
              <span className={`text-xs text-textMuted`}>{momentumLabel}</span>
            )}
          </div>
          <div className="text-[11px] text-textMuted mt-0.5">{pulse.stock?.company_name}</div>
        </div>
        <div className="flex items-center gap-2">
          <span className={`num text-xl font-bold ${style.score}`}>{pulse.score}</span>
          <span className={`text-[10px] px-1.5 py-0.5 rounded ${style.badge} uppercase tracking-wide`}>
            {pulse.severity}
          </span>
        </div>
      </div>

      {/* Metrics row */}
      <div className="flex items-center gap-4 mb-3 text-sm">
        {price > 0 && (
          <span className={`num font-medium ${isUp ? 'text-success' : 'text-danger'} flex items-center gap-1`}>
            {isUp ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
            {isUp ? '+' : ''}{chg.toFixed(2)}%
            <span className="text-textMuted text-xs">₹{fmt(price)}</span>
          </span>
        )}
        {volRatio > 0 && (
          <span className={`num text-sm ${volRatio >= 2 ? 'text-warning' : 'text-textMuted'}`}>
            Vol {volRatio.toFixed(1)}×
          </span>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => openDrawer('why', pulse.stock_id, symbol)}
          className="text-xs px-3 py-1 rounded bg-black/5 dark:bg-white/5 border border-border text-textMuted hover:text-foreground hover:border-border transition-colors"
        >
          Why?
        </button>
        <button
          onClick={() => openDrawer('trail', pulse.stock_id, symbol)}
          className="text-xs px-3 py-1 rounded bg-black/5 dark:bg-white/5 border border-border text-textMuted hover:text-foreground hover:border-border transition-colors"
        >
          Trail
        </button>
      </div>
    </div>
  );
}
