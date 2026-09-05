import { useState, useRef, useEffect } from 'react';
import { ChevronDown, Plus, Pencil, Trash2, Check, X } from 'lucide-react';
import { useApp } from '../context/AppContext';
import { renameWatchlist } from '../services/api';

export default function WatchlistDropdown() {
  const { watchlist, watchlists, setActiveWatchlist, deleteWatchlistById, refreshWatchlist } = useApp();
  const [open, setOpen] = useState(false);
  const [renaming, setRenaming] = useState<number | null>(null);
  const [renameValue, setRenameValue] = useState('');
  const [confirmDelete, setConfirmDelete] = useState<number | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
        setRenaming(null);
        setConfirmDelete(null);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const startRename = (id: number, currentName: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setRenaming(id);
    setRenameValue(currentName);
    setConfirmDelete(null);
  };

  const commitRename = async (id: number) => {
    if (!renameValue.trim()) return;
    await renameWatchlist(id, renameValue.trim());
    await refreshWatchlist();
    setRenaming(null);
  };

  const handleDelete = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirmDelete === id) {
      await deleteWatchlistById(id);
      setConfirmDelete(null);
      setOpen(false);
    } else {
      setConfirmDelete(id);
    }
  };

  const handleSelect = (id: number) => {
    setActiveWatchlist(id);
    setOpen(false);
    setRenaming(null);
    setConfirmDelete(null);
  };

  return (
    <div ref={containerRef} className="relative">
      {/* Trigger */}
      <button
        id="watchlist-dropdown-trigger"
        onClick={() => setOpen(o => !o)}
        className="flex items-center gap-1.5 group"
      >
        <span className="text-[10px] font-semibold text-textMuted uppercase tracking-widest group-hover:text-foreground transition-colors truncate max-w-[100px]">
          {watchlist?.name ?? 'Watchlist'}
        </span>
        <ChevronDown
          className={`w-3 h-3 text-textMuted transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
        />
      </button>

      {/* Dropdown panel */}
      {open && (
        <div className="absolute top-full left-0 mt-1 w-52 bg-surfaceHighlight border border-border rounded-lg shadow-xl z-50 overflow-hidden">
          {watchlists.length === 0 && (
            <div className="px-3 py-3 text-xs text-textMuted text-center">No watchlists yet</div>
          )}

          {watchlists.map(wl => (
            <div
              key={wl.id}
              className={`group flex items-center gap-2 px-3 py-2.5 cursor-pointer transition-colors hover:bg-black/5 dark:hover:bg-white/5 border-b border-border last:border-b-0 ${
                wl.id === watchlist?.id ? 'bg-primary/10' : ''
              }`}
              onClick={() => renaming === wl.id ? undefined : handleSelect(wl.id)}
            >
              {/* Active indicator */}
              <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${wl.id === watchlist?.id ? 'bg-primary' : 'bg-transparent'}`} />

              {/* Name or rename input */}
              {renaming === wl.id ? (
                <input
                  autoFocus
                  value={renameValue}
                  onChange={e => setRenameValue(e.target.value)}
                  onKeyDown={e => {
                    if (e.key === 'Enter') { e.stopPropagation(); commitRename(wl.id); }
                    if (e.key === 'Escape') { e.stopPropagation(); setRenaming(null); }
                  }}
                  onClick={e => e.stopPropagation()}
                  className="flex-1 min-w-0 bg-black/10 dark:bg-white/10 border border-primary/50 rounded px-1.5 py-0.5 text-xs text-foreground focus:outline-none"
                />
              ) : (
                <span className="flex-1 min-w-0 text-xs font-medium text-foreground truncate">
                  {wl.name}
                  <span className="ml-1 text-textMuted font-normal">({wl.stocks.length})</span>
                </span>
              )}

              {/* Action buttons */}
              <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                {renaming === wl.id ? (
                  <>
                    <button
                      onClick={e => { e.stopPropagation(); commitRename(wl.id); }}
                      className="p-0.5 rounded text-success hover:bg-success/10 transition-colors"
                    >
                      <Check className="w-3 h-3" />
                    </button>
                    <button
                      onClick={e => { e.stopPropagation(); setRenaming(null); }}
                      className="p-0.5 rounded text-textMuted hover:text-foreground transition-colors"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </>
                ) : (
                  <>
                    <button
                      onClick={e => startRename(wl.id, wl.name, e)}
                      title="Rename"
                      className="p-0.5 rounded text-textMuted hover:text-foreground transition-colors"
                    >
                      <Pencil className="w-3 h-3" />
                    </button>
                    <button
                      onClick={e => handleDelete(wl.id, e)}
                      title={confirmDelete === wl.id ? 'Click again to confirm' : 'Delete watchlist'}
                      className={`p-0.5 rounded transition-colors ${
                        confirmDelete === wl.id
                          ? 'text-danger bg-danger/10'
                          : 'text-textMuted hover:text-danger'
                      }`}
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </>
                )}
              </div>
            </div>
          ))}

          {/* Create new divider row */}
          <div className="border-t border-border">
            <div
              id="watchlist-create-new"
              className="flex items-center gap-2 px-3 py-2.5 text-xs font-medium text-primary hover:bg-primary/5 cursor-pointer transition-colors"
              onClick={() => { setOpen(false); /* parent handles isCreating */ document.getElementById('watchlist-create-btn')?.click(); }}
            >
              <Plus className="w-3.5 h-3.5" />
              New Watchlist
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
