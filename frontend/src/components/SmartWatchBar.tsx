import { useState, useEffect } from 'react';
import { Settings } from 'lucide-react';
import { useApp } from '../context/AppContext';
import { getSmartWatch, updateSmartWatch } from '../services/api';
import type { SmartWatchPreference } from '../services/api';

const SENSITIVITY_OPTIONS = [
  { value: 'LOW', label: 'Low', price: 8.0, volume: 3.0 },
  { value: 'MEDIUM', label: 'Medium', price: 5.0, volume: 2.0 },
  { value: 'HIGH', label: 'High', price: 2.0, volume: 1.5 },
] as const;

export default function SmartWatchBar() {
  const { smartWatchEnabled, watchlist } = useApp();
  const [prefs, setPrefs] = useState<SmartWatchPreference | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getSmartWatch().then(setPrefs).catch(() => {});
  }, []);

  const handleSensitivityChange = async (value: 'LOW' | 'MEDIUM' | 'HIGH') => {
    const opt = SENSITIVITY_OPTIONS.find(o => o.value === value)!;
    setSaving(true);
    try {
      const updated = await updateSmartWatch({
        sensitivity: opt.value,
        price_threshold: opt.price,
        volume_threshold: opt.volume,
      });
      setPrefs(updated);
    } catch { /* ignore */ }
    finally { setSaving(false); }
  };

  const stockCount = watchlist?.stocks.length ?? 0;

  return (
    <div className="h-9 flex-shrink-0 border-t border-border bg-surface flex items-center px-4 z-20">
      {smartWatchEnabled ? (
        /* ON state */
        <div className="flex items-center gap-4 w-full text-xs">
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
            <span className="font-semibold text-primary">Smart Watch ON</span>
          </div>
          <span className="text-textMuted">
            {stockCount} stock{stockCount !== 1 ? 's' : ''}
          </span>
          {prefs && (
            <>
              <span className="text-textMuted">·</span>
              <span className="text-textMuted">{prefs.sensitivity}</span>
              <span className="text-textMuted">·</span>
              <span className="num text-textMuted">{prefs.price_threshold}%</span>
            </>
          )}
          <button
            onClick={() => setSettingsOpen(!settingsOpen)}
            className="p-1 rounded hover:bg-black/5 dark:bg-white/10 text-textMuted hover:text-foreground transition-colors"
          >
            <Settings className="w-3.5 h-3.5" />
          </button>

        </div>
      ) : (
        /* OFF state */
        <div className="flex items-center gap-3 w-full text-xs">
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-gray-600" />
            <span className="text-textMuted">Smart Watch OFF</span>
          </div>
          <span className="text-textMuted">·</span>
          <span className="text-textMuted">Manual mode — you decide when to look</span>
        </div>
      )}

      {/* Settings popover */}
      {settingsOpen && prefs && (
        <div className="absolute bottom-9 right-4 w-56 bg-surface border border-border rounded shadow-xl z-50 p-3 animate-fade-in">
          <div className="text-[10px] font-semibold text-textMuted uppercase tracking-widest mb-2">Sensitivity</div>
          <div className="space-y-1">
            {SENSITIVITY_OPTIONS.map(opt => (
              <button
                key={opt.value}
                onClick={() => handleSensitivityChange(opt.value)}
                disabled={saving}
                className={`w-full text-left px-3 py-2 rounded text-xs transition-colors ${
                  prefs.sensitivity === opt.value
                    ? 'bg-primary/10 text-primary border border-primary/20'
                    : 'hover:bg-black/5 dark:bg-white/5 text-textMuted border border-transparent'
                }`}
              >
                <div className="font-medium">{opt.label}</div>
                <div className="text-[10px] text-textMuted">Price {opt.price}% · Vol {opt.volume}×</div>
              </button>
            ))}
          </div>
          <button
            onClick={() => setSettingsOpen(false)}
            className="mt-2 w-full text-[10px] text-textMuted hover:text-textMuted transition-colors"
          >
            Close
          </button>
        </div>
      )}
    </div>
  );
}
