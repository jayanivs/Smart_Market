import React, { useEffect, useState } from 'react';
import { X, TrendingUp, BarChart2, Globe, Target } from 'lucide-react';
import { fetchPulseWhy } from '../services/api';
import type { WhyResponse } from '../services/api';

const REASON_ICON: Record<string, React.ReactNode> = {
  PRICE: <TrendingUp className="w-4 h-4" />,
  VOLUME: <BarChart2 className="w-4 h-4" />,
  SECTOR: <Globe className="w-4 h-4" />,
  THRESHOLD: <Target className="w-4 h-4" />,
};

const REASON_COLOR: Record<string, string> = {
  PRICE: 'text-success bg-success/10',
  VOLUME: 'text-warning bg-warning/10',
  SECTOR: 'text-primary bg-primary/10',
  THRESHOLD: 'text-danger bg-danger/10',
};

const SEVERITY_COLOR: Record<string, string> = {
  CRITICAL: 'text-danger', IMPORTANT: 'text-warning', MODERATE: 'text-primary', NORMAL: 'text-textMuted',
};

interface Props {
  stockId: number;
  symbol: string;
  onClose: () => void;
}

export default function WhyDrawer({ stockId, symbol, onClose }: Props) {
  const [data, setData] = useState<WhyResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetchPulseWhy(stockId)
      .then(setData)
      .catch(() => setError('Could not load analysis.'))
      .finally(() => setLoading(false));
  }, [stockId]);

  const momentumLabel =
    data && (data.momentum > 20 ? '↑ Rising' : data.momentum < -20 ? '↓ Cooling' : null);

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />

      {/* Drawer */}
      <div className="relative w-full max-w-md bg-surface border-l border-border flex flex-col animate-slide-in shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-base font-bold text-foreground">{symbol}</span>
              <span className="text-xs text-textMuted">— Why does this deserve attention?</span>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded hover:bg-black/5 dark:bg-white/10 text-textMuted hover:text-foreground transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-5">
          {loading ? (
            <div className="py-12 text-center text-textMuted text-sm">Loading analysis...</div>
          ) : error ? (
            <div className="py-12 text-center text-textMuted text-sm">{error}</div>
          ) : data ? (
            <>
              {/* Score summary */}
              <div className="mb-6 pb-5 border-b border-border">
                <div className="flex items-baseline gap-3 mb-1">
                  <span className={`num text-3xl font-bold ${SEVERITY_COLOR[data.severity]}`}>{data.score}</span>
                  <span className={`text-sm font-semibold ${SEVERITY_COLOR[data.severity]}`}>{data.severity}</span>
                  {momentumLabel && (
                    <span className="text-sm text-textMuted ml-2">{momentumLabel}</span>
                  )}
                </div>
                <div className="text-xs text-textMuted">Pulse score out of 100</div>
              </div>

              {/* Reasons */}
              <div className="space-y-4">
                <div className="text-[10px] font-semibold text-textMuted uppercase tracking-widest mb-3">Signals</div>
                {data.reasons.length === 0 ? (
                  <div className="text-sm text-textMuted">No significant signals detected.</div>
                ) : data.reasons
                  .sort((a, b) => b.impact - a.impact)
                  .map((reason, i) => (
                    <div key={i} className="space-y-2">
                      <div className="flex items-center gap-2">
                        <span className={`p-1.5 rounded ${REASON_COLOR[reason.type] ?? 'text-textMuted bg-black/5 dark:bg-white/5'}`}>
                          {REASON_ICON[reason.type] ?? <TrendingUp className="w-4 h-4" />}
                        </span>
                        <div className="flex-1">
                          <div className="text-xs font-semibold text-foreground">{reason.type}</div>
                          <div className="text-xs text-textMuted mt-0.5">{reason.message}</div>
                        </div>
                        <span className="num text-xs text-textMuted">{reason.impact}pt</span>
                      </div>
                      {/* Impact bar */}
                      <div className="h-1 bg-black/5 dark:bg-white/5 rounded-full overflow-hidden ml-8">
                        <div
                          className="h-full bg-black/20 dark:bg-black/5 dark:bg-white/50 rounded-full transition-all"
                          style={{ width: `${Math.min(100, (reason.impact / 30) * 100)}%` }}
                        />
                      </div>
                    </div>
                  ))}
              </div>

              {/* Disclaimer */}
              <div className="mt-6 pt-4 border-t border-border">
                <p className="text-[10px] text-textMuted leading-relaxed">
                  Pulse Score is attention prioritization based on observable change — not a price prediction. Market Pulse never says buy, sell, or hold.
                </p>
              </div>
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
}
