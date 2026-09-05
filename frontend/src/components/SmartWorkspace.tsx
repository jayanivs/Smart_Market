import { useEffect, useState } from 'react';
import { ChevronDown, ChevronUp, Play, RefreshCw, CheckCheck } from 'lucide-react';
import { useApp } from '../context/AppContext';
import AttentionCard from './AttentionCard';
import { fetchWhatYouMissed, ackMissed, triggerRandomSimulator } from '../services/api';
import type { MeaningfulChange } from '../services/api';

function useElapsedSeconds(from: Date | null): number {
  const [secs, setSecs] = useState(0);
  useEffect(() => {
    const id = setInterval(() => {
      setSecs(from ? Math.floor((Date.now() - from.getTime()) / 1000) : 0);
    }, 1000);
    return () => clearInterval(id);
  }, [from]);
  return secs;
}

function WhatYouMissedStrip({ onAck }: { onAck: () => void }) {
  const [changes, setChanges] = useState<MeaningfulChange[]>([]);
  const [expanded, setExpanded] = useState(false);
  const [acking, setAcking] = useState(false);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try { setChanges(await fetchWhatYouMissed()); }
    catch { /* ignore */ }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const handleAck = async () => {
    setAcking(true);
    try {
      await ackMissed();
      setChanges([]);
      onAck();
    } catch { /* ignore */ }
    finally { setAcking(false); }
  };

  const SEVE_COLOR: Record<string, string> = {
    CRITICAL: 'text-danger', IMPORTANT: 'text-warning',
    MODERATE: 'text-primary', NORMAL: 'text-textMuted',
  };

  const severityFromScore = (s: number) =>
    s > 80 ? 'CRITICAL' : s > 60 ? 'IMPORTANT' : s > 30 ? 'MODERATE' : 'NORMAL';

  if (!loading && changes.length === 0) {
    return null;
  }

  return (
    <div className="border-t border-border">
      <div
        className="flex items-center justify-between px-5 py-2.5 cursor-pointer hover:bg-black/5 dark:bg-white/5 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <span className="text-xs text-textMuted">
          While you were away
          {loading ? '' : changes.length > 0 ? (
            <span className="ml-1.5 text-foreground font-semibold">· {changes.length} change{changes.length !== 1 ? 's' : ''}</span>
          ) : ' · all caught up'}
        </span>
        <div className="flex items-center gap-2">
          {changes.length > 0 && (
            <button
              onClick={(e) => { e.stopPropagation(); handleAck(); }}
              disabled={acking}
              className="text-[10px] px-2 py-1 rounded bg-black/5 dark:bg-white/5 border border-border text-textMuted hover:text-foreground transition-colors flex items-center gap-1"
            >
              <CheckCheck className="w-3 h-3" />
              {acking ? 'Clearing...' : 'Mark seen'}
            </button>
          )}
          {changes.length > 0 && (
            expanded ? <ChevronUp className="w-3 h-3 text-textMuted" /> : <ChevronDown className="w-3 h-3 text-textMuted" />
          )}
        </div>
      </div>

      {expanded && changes.length > 0 && (
        <div className="border-t border-border max-h-52 overflow-y-auto">
          {changes.map(c => {
            const sev = severityFromScore(c.current_score);
            const increased = c.current_score > c.previous_score;
            return (
              <div key={c.id} className="flex items-center gap-3 px-5 py-2 border-b border-border hover:bg-black/5 dark:bg-white/5">
                <span className={`text-xs font-semibold ${SEVE_COLOR[sev]}`}>
                  {c.stock?.symbol ?? `#${c.stock_id}`}
                </span>
                <span className="num text-xs text-textMuted">
                  {c.previous_score} → {c.current_score}
                </span>
                <span className="text-[10px] text-textMuted">
                  {increased ? 'attention increased' : 'attention decreased'}
                </span>
                <span className="ml-auto text-[10px] text-textMuted">
                  {new Date(c.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default function SmartWorkspace() {
  const { pulseList, watchlist, lastUpdated, refreshPulse } = useApp();
  const [showAll, setShowAll] = useState(false);
  const [simulating, setSimulating] = useState(false);
  const [simResult, setSimResult] = useState<string | null>(null);
  const elapsed = useElapsedSeconds(lastUpdated);
  const [missedKeyVal, setMissedKeyVal] = useState(0);

  const watchedIds = new Set(watchlist?.stocks.map(s => s.id) ?? []);
  const watchedPulse = pulseList.filter(p => watchedIds.has(p.stock_id));

  const critical = watchedPulse.filter(p => p.severity === 'CRITICAL');
  const important = watchedPulse.filter(p => p.severity === 'IMPORTANT');
  const moderate = watchedPulse.filter(p => p.severity === 'MODERATE');
  const normal = watchedPulse.filter(p => p.severity === 'NORMAL');

  const attentionItems = [...critical, ...important];
  const quietItems = [...moderate, ...normal];

  const handleSimulate = async () => {
    setSimulating(true);
    setSimResult(null);
    try {
      await triggerRandomSimulator();
      await new Promise(r => setTimeout(r, 600));
      await refreshPulse();
      setSimResult('Simulated — scores updated.');
    } catch {
      setSimResult('Simulation failed.');
    } finally {
      setSimulating(false);
      setTimeout(() => setSimResult(null), 3000);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Summary bar */}
      <div className="px-5 py-3 border-b border-border flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-4 text-xs">
          {critical.length > 0 && (
            <span className="text-danger font-semibold">{critical.length} Critical</span>
          )}
          {important.length > 0 && (
            <span className="text-warning font-semibold">{important.length} Important</span>
          )}
          {moderate.length > 0 && (
            <span className="text-primary">{moderate.length} Moderate</span>
          )}
          {normal.length > 0 && (
            <span className="text-textMuted">{normal.length} Normal</span>
          )}
          {watchedPulse.length === 0 && (
            <span className="text-textMuted">No data yet</span>
          )}
          <span className="text-textMuted">·</span>
          <span className="text-textMuted">
            Monitoring {watchedPulse.length} stock{watchedPulse.length !== 1 ? 's' : ''}
            {elapsed > 0 && ` · updated ${elapsed}s ago`}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {simResult && <span className="text-xs text-textMuted">{simResult}</span>}
          <button
            onClick={handleSimulate}
            disabled={simulating}
            className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded bg-surfaceHighlight border border-border text-textMuted hover:text-foreground transition-colors disabled:opacity-50"
          >
            {simulating ? <RefreshCw className="w-3 h-3 animate-spin" /> : <Play className="w-3 h-3" />}
            Simulate
          </button>
        </div>
      </div>

      {/* Attention section */}
      <div className="flex-1 overflow-y-auto">
        <div className="px-5 pt-4">
          <div className="text-[10px] font-semibold text-textMuted uppercase tracking-widest mb-3">
            What deserves your attention now
          </div>

          {watchedPulse.length === 0 ? (
            <div className="py-12 text-center text-textMuted text-sm">
              Run the simulator to generate market events.
            </div>
          ) : attentionItems.length === 0 ? (
            <div className="py-6 text-center text-textMuted text-sm">
              Everything is quiet — no stocks need attention right now.
            </div>
          ) : (
            <div className="space-y-3 mb-4">
              {attentionItems.map(p => (
                <AttentionCard key={p.stock_id} pulse={p} />
              ))}
            </div>
          )}

          {/* Quiet stocks collapse */}
          {quietItems.length > 0 && (
            <div className="mb-4">
              {showAll ? (
                <>
                  <div className="text-[10px] text-textMuted mb-2 uppercase tracking-widest">Quiet</div>
                  <div className="border border-border rounded-sm overflow-hidden">
                    {quietItems.map(p => (
                      <AttentionCard key={p.stock_id} pulse={p} compact />
                    ))}
                  </div>
                  <button
                    onClick={() => setShowAll(false)}
                    className="mt-2 text-xs text-textMuted hover:text-textMuted flex items-center gap-1"
                  >
                    <ChevronUp className="w-3 h-3" /> Show less
                  </button>
                </>
              ) : (
                <button
                  onClick={() => setShowAll(true)}
                  className="text-xs text-textMuted hover:text-textMuted flex items-center gap-1"
                >
                  <ChevronDown className="w-3 h-3" />
                  + {quietItems.length} stock{quietItems.length !== 1 ? 's' : ''} quiet
                  <span className="ml-1 text-textMuted">— show all</span>
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* What You Missed strip */}
      <WhatYouMissedStrip key={missedKeyVal} onAck={() => setMissedKeyVal(k => k + 1)} />
    </div>
  );
}
