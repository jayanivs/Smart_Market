import { useState } from 'react';
import { X, Plus, ChevronRight, ToggleLeft, ToggleRight, Trash2 } from 'lucide-react';
import { useApp } from '../context/AppContext';
import { createQuickGroup, updateQuickGroup, deleteQuickGroup } from '../services/api';

const SENSITIVITY_LABELS: Record<string, { label: string; price: string; volume: string }> = {
  LOW:    { label: 'Low',    price: '7% move', volume: '3x volume' },
  MEDIUM: { label: 'Medium', price: '5% move', volume: '2x volume' },
  HIGH:   { label: 'High',   price: '3% move', volume: '1.5x volume' },
};

export default function QuickGroupModal({ onClose }: { onClose: () => void }) {
  const { allStocks, pulseList, quickGroups, refreshQuickGroups } = useApp();
  const [step, setStep] = useState<'list' | 'create'>('list');
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [name, setName] = useState('');
  const [sensitivity, setSensitivity] = useState<'LOW' | 'MEDIUM' | 'HIGH'>('MEDIUM');
  const [autoWatch, setAutoWatch] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCreate = async () => {
    if (selectedIds.length === 0) { setError('Select at least one stock'); return; }
    setSaving(true);
    try {
      await createQuickGroup(name, selectedIds, sensitivity, autoWatch);
      await refreshQuickGroups();
      onClose();
    } catch (e) {
      setError('Failed to create group');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    await deleteQuickGroup(id);
    await refreshQuickGroups();
  };

  const handleToggle = async (id: number, currentAuto: boolean) => {
    await updateQuickGroup(id, { auto_watch: !currentAuto });
    await refreshQuickGroups();
  };

  const toggleStock = (id: number) => {
    setSelectedIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  };

  // Display stocks — prefer those in watchlist for easy selection
  const watchedIds = new Set(pulseList.map(p => p.stock_id));
  const displayStocks = allStocks.slice(0, 30);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center" onClick={onClose}>
      <div className="absolute inset-0 bg-black/60" />
      <div
        className="relative z-10 w-[480px] max-h-[80vh] bg-surface border border-border rounded-lg shadow-2xl flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-border flex-shrink-0">
          <div className="flex items-center gap-2">
            {step === 'create' && (
              <button onClick={() => setStep('list')} className="text-textMuted hover:text-foreground mr-1">
                <ChevronRight className="w-4 h-4 rotate-180" />
              </button>
            )}
            <span className="text-sm font-semibold text-foreground">
              {step === 'list' ? 'Quick Groups' : 'Create Group'}
            </span>
          </div>
          <div className="flex items-center gap-2">
            {step === 'list' && (
              <button
                onClick={() => { setStep('create'); setSelectedIds([]); setName(''); setSensitivity('MEDIUM'); setAutoWatch(false); }}
                className="flex items-center gap-1 text-xs px-2.5 py-1 rounded bg-primary text-black font-semibold"
              >
                <Plus className="w-3 h-3" /> New Group
              </button>
            )}
            <button onClick={onClose} className="text-textMuted hover:text-foreground transition-colors">
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto">
          {step === 'list' && (
            <div>
              {quickGroups.length === 0 ? (
                <div className="py-12 text-center text-textMuted text-sm">
                  No groups yet.{' '}
                  <button onClick={() => setStep('create')} className="text-primary underline">Create one</button>
                </div>
              ) : quickGroups.map(g => (
                <div key={g.id} className="border-b border-border px-5 py-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="text-sm font-semibold text-foreground">{g.name}</span>
                      <span className="ml-2 text-[10px] text-textMuted">{g.sensitivity}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <button onClick={() => handleToggle(g.id, g.auto_watch)} title="Toggle auto-watch">
                        {g.auto_watch
                          ? <ToggleRight className="w-5 h-5 text-success" />
                          : <ToggleLeft className="w-5 h-5 text-textMuted" />
                        }
                      </button>
                      <button onClick={() => handleDelete(g.id)} className="text-textMuted hover:text-danger transition-colors">
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {g.stocks.map(s => (
                      <span key={s.id} className="text-[10px] px-1.5 py-0.5 rounded bg-black/5 dark:bg-white/5 text-textMuted">{s.symbol}</span>
                    ))}
                    {g.stocks.length === 0 && <span className="text-[10px] text-textMuted">No stocks</span>}
                  </div>
                  <div className="mt-1 text-[10px] text-textMuted">
                    Auto-watch: <span className={g.auto_watch ? 'text-success' : 'text-textMuted'}>{g.auto_watch ? 'ON' : 'OFF'}</span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {step === 'create' && (
            <div className="p-5 space-y-5">
              {/* Name */}
              <div>
                <label className="text-xs text-textMuted block mb-1">Group name (optional)</label>
                <input
                  value={name}
                  onChange={e => setName(e.target.value)}
                  placeholder="Auto-detected from sector"
                  className="w-full bg-black/5 dark:bg-white/5 border border-border rounded px-3 py-2 text-sm text-foreground placeholder-gray-600 focus:outline-none focus:border-primary"
                />
              </div>

              {/* Stocks */}
              <div>
                <label className="text-xs text-textMuted block mb-2">Select stocks ({selectedIds.length} selected)</label>
                <div className="grid grid-cols-3 gap-1.5 max-h-40 overflow-y-auto">
                  {displayStocks.map(s => {
                    const selected = selectedIds.includes(s.id);
                    const inWatchlist = watchedIds.has(s.id);
                    return (
                      <button
                        key={s.id}
                        onClick={() => toggleStock(s.id)}
                        className={
                          "text-left px-2.5 py-1.5 rounded text-xs transition-colors " +
                          (selected
                            ? "bg-primary text-black font-semibold"
                            : inWatchlist
                              ? "bg-black/5 dark:bg-white/10 text-foreground border border-border"
                              : "bg-black/5 dark:bg-white/5 text-textMuted border border-border")
                        }
                      >
                        {s.symbol}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Sensitivity */}
              <div>
                <label className="text-xs text-textMuted block mb-2">Sensitivity</label>
                <div className="flex gap-2">
                  {(['LOW', 'MEDIUM', 'HIGH'] as const).map(s => (
                    <button
                      key={s}
                      onClick={() => setSensitivity(s)}
                      className={
                        "flex-1 py-2 rounded text-xs font-semibold transition-colors " +
                        (sensitivity === s ? "bg-primary text-black" : "bg-black/5 dark:bg-white/5 text-textMuted hover:text-foreground")
                      }
                    >
                      {SENSITIVITY_LABELS[s].label}
                    </button>
                  ))}
                </div>
                <div className="text-[10px] text-textMuted mt-1">
                  Triggers on: {SENSITIVITY_LABELS[sensitivity].price} or {SENSITIVITY_LABELS[sensitivity].volume}
                </div>
              </div>

              {/* Auto-watch */}
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-textMuted">Auto-watch</div>
                  <div className="text-[10px] text-textMuted">Generate notifications for this group</div>
                </div>
                <button onClick={() => setAutoWatch(!autoWatch)}>
                  {autoWatch
                    ? <ToggleRight className="w-7 h-7 text-success" />
                    : <ToggleLeft className="w-7 h-7 text-textMuted" />
                  }
                </button>
              </div>

              {error && <div className="text-danger text-xs">{error}</div>}
            </div>
          )}
        </div>

        {/* Footer */}
        {step === 'create' && (
          <div className="px-5 py-3 border-t border-border flex justify-end gap-2 flex-shrink-0">
            <button onClick={() => setStep('list')} className="text-xs px-3 py-1.5 rounded bg-black/5 dark:bg-white/5 border border-border text-textMuted hover:text-foreground transition-colors">
              Cancel
            </button>
            <button
              onClick={handleCreate}
              disabled={saving}
              className="text-xs px-4 py-1.5 rounded bg-primary text-black font-semibold hover:bg-primary/80 transition-colors disabled:opacity-50"
            >
              {saving ? 'Creating...' : 'Create Group'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
