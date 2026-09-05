import { useState, useEffect } from 'react';
import { X, BarChart3, TrendingUp, AlertTriangle, Info } from 'lucide-react';
import { fetchWeeklyReport } from '../services/api';
import type { WeeklyReport } from '../services/api';

export default function WeeklyReportModal({ onClose }: { onClose: () => void }) {
  const [report, setReport] = useState<WeeklyReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      setReport(await fetchWeeklyReport());
    } catch (e) {
      setError('Failed to load report');
    } finally {
      setLoading(false);
    }
  };

  // Auto-load on mount
  useEffect(() => { load(); }, []);

  const SEV_ITEMS = report ? [
    { label: 'Critical', count: report.critical_changes, cls: 'text-danger' },
    { label: 'Important', count: report.important_changes, cls: 'text-warning' },
    { label: 'Moderate', count: report.moderate_changes, cls: 'text-primary' },
    { label: 'Normal', count: report.normal_changes, cls: 'text-textMuted' },
  ] : [];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center" onClick={onClose}>
      <div className="absolute inset-0 bg-black/60" />
      <div
        className="relative z-10 w-[480px] bg-surface border border-border rounded-lg shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-border">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-primary" />
            <span className="text-sm font-semibold text-foreground">Weekly Report</span>
            <span className="text-xs text-textMuted">trailing 7 days</span>
          </div>
          <button onClick={onClose} className="text-textMuted hover:text-foreground transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="p-5">
          {loading && (
            <div className="flex items-center gap-2 text-textMuted text-sm py-6 justify-center">
              <span className="animate-pulse">Generating report...</span>
            </div>
          )}
          {error && (
            <div className="text-danger text-sm text-center py-6">{error}</div>
          )}
          {report && !loading && (
            <div className="space-y-5">
              {/* Total count */}
              <div className="text-center">
                <div className="num text-4xl font-bold text-foreground">{report.total_changes}</div>
                <div className="text-xs text-textMuted mt-1">meaningful changes this week</div>
              </div>

              {/* Severity breakdown */}
              <div className="grid grid-cols-4 gap-2">
                {SEV_ITEMS.map(({ label, count, cls }) => (
                  <div key={label} className="bg-black/5 dark:bg-white/5 rounded p-2.5 text-center">
                    <div className={"num text-xl font-bold " + cls}>{count}</div>
                    <div className="text-[10px] text-textMuted mt-0.5">{label}</div>
                  </div>
                ))}
              </div>

              {/* Key metrics */}
              <div className="space-y-2.5 border-t border-border pt-4">
                {report.top_attention_stock && (
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2 text-textMuted">
                      <TrendingUp className="w-3.5 h-3.5" />
                      Top attention
                    </div>
                    <span className="num font-semibold text-foreground">{report.top_attention_stock}</span>
                  </div>
                )}
                {report.most_active_group && (
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2 text-textMuted">
                      <BarChart3 className="w-3.5 h-3.5" />
                      Most active group
                    </div>
                    <span className="text-foreground">{report.most_active_group}</span>
                  </div>
                )}
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2 text-textMuted">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    Threshold crossings
                  </div>
                  <span className="num text-foreground">{report.threshold_crossings}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2 text-textMuted">
                    <Info className="w-3.5 h-3.5" />
                    Volume anomalies
                  </div>
                  <span className="num text-foreground">{report.volume_anomalies}</span>
                </div>
              </div>

              {/* Generated at */}
              <div className="text-[10px] text-textMuted text-right border-t border-border pt-3">
                Generated {new Date(report.generated_at).toLocaleString()}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-border flex justify-end gap-2">
          <button
            onClick={load}
            disabled={loading}
            className="text-xs px-3 py-1.5 rounded bg-black/5 dark:bg-white/5 border border-border text-textMuted hover:text-foreground transition-colors"
          >
            Refresh
          </button>
          <button
            onClick={onClose}
            className="text-xs px-3 py-1.5 rounded bg-primary text-black font-semibold hover:bg-primary/80 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
