import { useState } from 'react';
import { ChevronUp, ChevronDown, Play, RefreshCw } from 'lucide-react';
import { useApp } from '../context/AppContext';
import { triggerRandomSimulator } from '../services/api';

const SEVERITY_DOT: Record<string, string> = {
  CRITICAL: 'bg-danger animate-pulse',
  IMPORTANT: 'bg-warning',
  MODERATE: 'bg-primary',
  NORMAL: 'bg-gray-700',
};

const SEVERITY_BADGE: Record<string, string> = {
  CRITICAL: 'text-danger',
  IMPORTANT: 'text-warning',
  MODERATE: 'text-primary',
  NORMAL: 'text-textMuted',
};

function fmt(n: number, decimals = 2): string {
  return n.toLocaleString('en-IN', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
}

export default function ManualWorkspace() {
  const { pulseList, watchlist, openDrawer, refreshPulse } = useApp();
  const [simulating, setSimulating] = useState(false);
  const [simResult, setSimResult] = useState<string | null>(null);
  const [sortKey, setSortKey] = useState<string>('symbol');
  const [sortAsc, setSortAsc] = useState(true);

  const watchedIds = new Set(watchlist?.stocks.map(s => s.id) ?? []);
  const rows = pulseList.filter(p => watchedIds.has(p.stock_id));

  const handleSort = (key: string) => {
    if (sortKey === key) setSortAsc(!sortAsc);
    else { setSortKey(key); setSortAsc(true); }
  };

  const sorted = [...rows].sort((a, b) => {
    let av: number | string = 0, bv: number | string = 0;
    const aSnap = a.snapshot;
    const bSnap = b.snapshot;
    if (sortKey === 'symbol') { av = a.stock?.symbol ?? ''; bv = b.stock?.symbol ?? ''; }
    else if (sortKey === 'price') { av = aSnap?.price ?? 0; bv = bSnap?.price ?? 0; }
    else if (sortKey === 'change') {
      const ap = aSnap?.previous_price ?? 0; const ac = aSnap?.price ?? 0;
      const bp = bSnap?.previous_price ?? 0; const bc = bSnap?.price ?? 0;
      av = ap > 0 ? ((ac - ap) / ap) * 100 : 0;
      bv = bp > 0 ? ((bc - bp) / bp) * 100 : 0;
    }
    else if (sortKey === 'volume') {
      const avol = aSnap?.volume ?? 0; const aavg = aSnap?.average_volume ?? 1;
      const bvol = bSnap?.volume ?? 0; const bavg = bSnap?.average_volume ?? 1;
      av = avol / aavg; bv = bvol / bavg;
    }
    else if (sortKey === 'pulse') { av = a.score; bv = b.score; }
    if (typeof av === 'string') return sortAsc ? av.localeCompare(bv as string) : (bv as string).localeCompare(av);
    return sortAsc ? av - (bv as number) : (bv as number) - av;
  });

  const handleSimulate = async () => {
    setSimulating(true);
    setSimResult(null);
    try {
      await triggerRandomSimulator();
      await new Promise(r => setTimeout(r, 500));
      await refreshPulse();
      setSimResult('Done — check the pulse scores.');
    } catch {
      setSimResult('Simulation failed.');
    } finally {
      setSimulating(false);
      setTimeout(() => setSimResult(null), 4000);
    }
  };

  const SortIcon = ({ col }: { col: string }) => (
    sortKey === col
      ? (sortAsc ? <ChevronUp className="w-3 h-3 inline ml-0.5" /> : <ChevronDown className="w-3 h-3 inline ml-0.5" />)
      : null
  );

  return (
    <div className="p-6">
      {/* Header row */}
      <div className="flex items-center justify-between mb-4">
        <div className="text-sm text-textMuted">
          {rows.length} stocks in watchlist
        </div>
        <div className="flex items-center gap-2">
          {simResult && (
            <span className="text-xs text-textMuted">{simResult}</span>
          )}
          <button
            onClick={handleSimulate}
            disabled={simulating}
            className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded bg-surfaceHighlight border border-border text-textMuted hover:text-foreground hover:border-border transition-colors disabled:opacity-50"
          >
            {simulating ? <RefreshCw className="w-3 h-3 animate-spin" /> : <Play className="w-3 h-3" />}
            Simulate
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="rounded border border-border overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-surfaceHighlight">
              {[
                { key: 'symbol', label: 'Symbol' },
                { key: 'price', label: 'Price' },
                { key: 'change', label: 'Change' },
                { key: 'volume', label: 'Volume' },
                { key: 'pulse', label: 'Pulse' },
              ].map(col => (
                <th
                  key={col.key}
                  onClick={() => handleSort(col.key)}
                  className="px-4 py-2.5 text-left text-[10px] font-semibold text-textMuted uppercase tracking-widest cursor-pointer hover:text-textMuted select-none"
                >
                  {col.label}<SortIcon col={col.key} />
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-12 text-center text-textMuted text-sm">
                  No stocks in watchlist. Use the sidebar to add some.
                </td>
              </tr>
            ) : sorted.map(row => {
              const snap = row.snapshot;
              const price = snap?.price ?? 0;
              const prev = snap?.previous_price ?? price;
              const chg = prev > 0 ? ((price - prev) / prev) * 100 : 0;
              const isUp = chg >= 0;
              const vol = snap?.volume ?? 0;
              const avgVol = snap?.average_volume ?? 1;
              const volRatio = avgVol > 0 ? vol / avgVol : 1;
              const isStale = snap?.is_stale ?? false;

              return (
                <tr
                  key={row.stock_id}
                  onClick={() => openDrawer('stock', row.stock_id, row.stock?.symbol ?? '')}
                  className="border-b border-border hover:bg-black/5 dark:bg-white/5 cursor-pointer transition-colors"
                >
                  {/* Symbol */}
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${SEVERITY_DOT[row.severity]}`} />
                      <div>
                        <div className="font-semibold text-foreground text-sm">{row.stock?.symbol}</div>
                        <div className="text-[10px] text-textMuted truncate max-w-[120px]">{row.stock?.company_name}</div>
                      </div>
                    </div>
                  </td>
                  {/* Price */}
                  <td className="px-4 py-3">
                    {price > 0 ? (
                      <span className="num text-sm text-foreground">₹{fmt(price)}</span>
                    ) : <span className="text-textMuted">—</span>}
                    {isStale && <span className="ml-1 text-[9px] text-warning">Delayed</span>}
                  </td>
                  {/* Change */}
                  <td className="px-4 py-3">
                    {prev > 0 ? (
                      <span className={`num text-sm font-medium ${isUp ? 'text-success' : 'text-danger'}`}>
                        {isUp ? '+' : ''}{chg.toFixed(2)}%
                      </span>
                    ) : <span className="text-textMuted">—</span>}
                  </td>
                  {/* Volume */}
                  <td className="px-4 py-3">
                    {vol > 0 ? (
                      <span className={`num text-sm ${volRatio >= 2 ? 'text-warning' : 'text-textMuted'}`}>
                        {volRatio.toFixed(1)}×
                      </span>
                    ) : <span className="text-textMuted">—</span>}
                  </td>
                  {/* Pulse */}
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <span className={`num text-sm font-medium ${SEVERITY_BADGE[row.severity]}`}>
                        {row.score}
                      </span>
                      <span className={`w-1.5 h-1.5 rounded-full ${SEVERITY_DOT[row.severity]}`} />
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
