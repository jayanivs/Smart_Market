import { useState, useCallback, useRef } from 'react';
import { Plus, Search, X, Trash2, LayoutList, Layers, Check, GripVertical } from 'lucide-react';
import { useApp } from '../context/AppContext';
import { addStockToWatchlist, removeStockFromWatchlist, createWatchlist } from '../services/api';
import WatchlistDropdown from './WatchlistDropdown';

const SEVERITY_DOT: Record<string, string> = {
  CRITICAL: 'bg-danger animate-pulse',
  IMPORTANT: 'bg-warning',
  MODERATE: 'bg-primary',
  NORMAL: 'bg-gray-600',
};

function fmt(n: number): string {
  return n.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export default function WatchlistSidebar() {
  const {
    watchlist, watchlists, setActiveWatchlist, allStocks, pulseMap,
    refreshWatchlist, openDrawer, reorderActiveWatchlist,
  } = useApp();

  const [search, setSearch] = useState('');
  const [hoveredId, setHoveredId] = useState<number | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [newName, setNewName] = useState('');
  const [groupMode, setGroupMode] = useState<'sector' | 'priority'>(() => {
    return (localStorage.getItem('mp_groupMode') as 'sector' | 'priority') ?? 'sector';
  });

  // Drag-and-drop state
  const dragStock = useRef<number | null>(null);  // stock.id being dragged
  const dragOverStock = useRef<number | null>(null);
  const [draggingId, setDraggingId] = useState<number | null>(null);
  const [dragOverId, setDragOverId] = useState<number | null>(null);

  const setAndPersistGroupMode = (mode: 'sector' | 'priority') => {
    setGroupMode(mode);
    localStorage.setItem('mp_groupMode', mode);
  };

  const watchedIds = new Set(watchlist?.stocks.map(s => s.id) ?? []);

  const filteredSearch = search.trim()
    ? allStocks.filter(s =>
        !watchedIds.has(s.id) &&
        (s.symbol.toLowerCase().includes(search.toLowerCase()) ||
         s.company_name.toLowerCase().includes(search.toLowerCase()))
      )
    : [];

  const handleAdd = useCallback(async (stockId: number) => {
    if (!watchlist) return;
    await addStockToWatchlist(watchlist.id, stockId);
    setSearch('');
    await refreshWatchlist();
  }, [watchlist, refreshWatchlist]);

  const handleRemove = useCallback(async (e: React.MouseEvent, stockId: number) => {
    e.stopPropagation();
    if (!watchlist) return;
    await removeStockFromWatchlist(watchlist.id, stockId);
    await refreshWatchlist();
  }, [watchlist, refreshWatchlist]);

  const handleCreateWatchlist = async () => {
    const nameToUse = newName.trim() || 'My Watchlist';
    const newWl = await createWatchlist(nameToUse);
    setNewName('');
    setIsCreating(false);
    await refreshWatchlist();
    if (newWl && newWl.id) {
      setActiveWatchlist(newWl.id);
    }
  };

  // ── Drag-and-Drop handlers ────────────────────────────────────────────────
  const handleDragStart = (stockId: number) => {
    dragStock.current = stockId;
    setDraggingId(stockId);
  };

  const handleDragEnter = (stockId: number) => {
    if (dragStock.current === stockId) return;
    dragOverStock.current = stockId;
    setDragOverId(stockId);
  };

  const handleDragEnd = async () => {
    const fromId = dragStock.current;
    const toId = dragOverStock.current;
    if (fromId !== null && toId !== null && fromId !== toId) {
      const stocks = watchlist?.stocks ?? [];
      const fromIdx = stocks.findIndex(s => s.id === fromId);
      const toIdx = stocks.findIndex(s => s.id === toId);
      if (fromIdx !== -1 && toIdx !== -1) {
        const reordered = [...stocks];
        const [moved] = reordered.splice(fromIdx, 1);
        reordered.splice(toIdx, 0, moved);
        await reorderActiveWatchlist(reordered.map(s => s.id));
      }
    }
    dragStock.current = null;
    dragOverStock.current = null;
    setDraggingId(null);
    setDragOverId(null);
  };

  const stocks = watchlist?.stocks ?? [];

  const groupedStocks = stocks.reduce((acc, stock) => {
    const s = stock.sector || 'Other';
    if (!acc[s]) acc[s] = [];
    acc[s].push(stock);
    return acc;
  }, {} as Record<string, typeof stocks>);

  const renderStockRow = (stock: (typeof stocks)[0], draggable = false) => {
    const pulse = pulseMap[stock.id];
    const snap = pulse?.snapshot;
    const price = snap?.price ?? 0;
    const prev = snap?.previous_price ?? price;
    const chg = prev > 0 ? ((price - prev) / prev) * 100 : 0;
    const isUp = chg >= 0;
    const severity = pulse?.severity ?? 'NORMAL';
    const isHovered = hoveredId === stock.id;
    const isDragging = draggingId === stock.id;
    const isDragOver = dragOverId === stock.id;

    return (
      <div
        key={stock.id}
        className={`sidebar-row group relative transition-all duration-150 ${
          isDragging ? 'opacity-40 scale-95' : ''
        } ${isDragOver ? 'border-t-2 border-primary' : ''}`}
        draggable={draggable}
        onDragStart={draggable ? () => handleDragStart(stock.id) : undefined}
        onDragEnter={draggable ? () => handleDragEnter(stock.id) : undefined}
        onDragEnd={draggable ? handleDragEnd : undefined}
        onDragOver={draggable ? e => e.preventDefault() : undefined}
        onMouseEnter={() => setHoveredId(stock.id)}
        onMouseLeave={() => setHoveredId(null)}
        onClick={() => openDrawer('stock', stock.id, stock.symbol)}
      >
        {/* Drag handle (priority mode only) */}
        {draggable && (
          <span
            className="mr-1 text-textMuted cursor-grab active:cursor-grabbing opacity-0 group-hover:opacity-100 transition-opacity"
            onMouseDown={e => e.stopPropagation()}
          >
            <GripVertical className="w-3 h-3" />
          </span>
        )}

        <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 mr-2 ${SEVERITY_DOT[severity]}`} />
        <div className="flex-1 min-w-0">
          <div className="text-xs font-semibold text-foreground">{stock.symbol}</div>
          {!isHovered && (
            <div className="text-[10px] text-textMuted truncate">{stock.company_name}</div>
          )}
        </div>
        {isHovered ? (
          <button onClick={(e) => handleRemove(e, stock.id)} className="p-1 rounded text-textMuted hover:text-danger transition-colors">
            <Trash2 className="w-3 h-3" />
          </button>
        ) : (
          <div className="text-right flex-shrink-0">
            {price > 0 ? (
              <>
                <div className={`num text-xs font-medium ${isUp ? 'text-success' : 'text-danger'}`}>
                  ₹{fmt(price)}
                </div>
                <div className={`num text-[10px] ${isUp ? 'text-success/70' : 'text-danger/70'}`}>
                  {isUp ? '+' : ''}{chg.toFixed(2)}%
                </div>
              </>
            ) : (
              <span className="text-textMuted text-xs">—</span>
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <aside className="w-64 flex-shrink-0 bg-surface border-r border-border flex flex-col">
      {/* Header */}
      <div className="px-3 py-2 border-b border-border flex flex-col gap-2">
        <div className="flex items-center justify-between">
          {/* Watchlist dropdown */}
          {watchlists.length > 0 ? (
            <WatchlistDropdown />
          ) : (
            <span className="text-[10px] font-semibold text-textMuted uppercase tracking-widest">
              Watchlist
            </span>
          )}
          {watchlist && <span className="ml-2 text-[10px] text-textMuted">{stocks.length}</span>}

          {/* Toolbar buttons */}
          <div className="flex items-center gap-1 ml-auto">
            {watchlist && (
              <>
                <button
                  id="watchlist-create-btn"
                  onClick={() => setIsCreating(!isCreating)}
                  title="Create new watchlist"
                  className={`p-1 rounded transition-colors ${isCreating ? 'text-primary bg-primary/10' : 'text-textMuted hover:text-textMuted'}`}
                >
                  <Plus className="w-3 h-3" />
                </button>
                <button
                  onClick={() => setAndPersistGroupMode('sector')}
                  title="Group by sector"
                  className={`p-1 rounded transition-colors ${groupMode === 'sector' ? 'text-primary bg-primary/10' : 'text-textMuted hover:text-textMuted'}`}
                >
                  <Layers className="w-3 h-3" />
                </button>
                <button
                  onClick={() => setAndPersistGroupMode('priority')}
                  title="Priority list (drag to reorder)"
                  className={`p-1 rounded transition-colors ${groupMode === 'priority' ? 'text-primary bg-primary/10' : 'text-textMuted hover:text-textMuted'}`}
                >
                  <LayoutList className="w-3 h-3" />
                </button>
              </>
            )}
            {!watchlist && (
              <button
                onClick={() => setIsCreating(!isCreating)}
                className="text-[10px] text-primary hover:text-primary/80 transition-colors flex items-center gap-1"
              >
                <Plus className="w-3 h-3" /> Create
              </button>
            )}
          </div>
        </div>

        {isCreating && (
          <div className="flex items-center gap-1 mt-1">
            <input
              type="text"
              placeholder="Watchlist name..."
              value={newName}
              onChange={e => setNewName(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter') handleCreateWatchlist();
                if (e.key === 'Escape') { setIsCreating(false); setNewName(''); }
              }}
              autoFocus
              className="flex-1 bg-black/10 dark:bg-white/5 border border-border rounded px-2 py-1 text-xs text-foreground placeholder-gray-600 focus:outline-none focus:border-primary"
            />
            <button
              onClick={handleCreateWatchlist}
              className="p-1 bg-primary text-black rounded hover:bg-primary/90 transition-colors"
            >
              <Check className="w-3 h-3" />
            </button>
            <button
              onClick={() => { setIsCreating(false); setNewName(''); }}
              className="p-1 text-textMuted hover:text-foreground transition-colors"
            >
              <X className="w-3 h-3" />
            </button>
          </div>
        )}
      </div>

      {/* Search */}
      <div className="px-2 py-2 border-b border-border relative">
        <div className="relative">
          <Search className="absolute left-2 top-2 w-3 h-3 text-textMuted" />
          <input
            type="text"
            placeholder={watchlist ? 'Add symbol...' : 'Create watchlist first'}
            value={search}
            onChange={e => setSearch(e.target.value)}
            onKeyDown={e => e.key === 'Escape' && setSearch('')}
            disabled={!watchlist}
            className="w-full bg-background border border-border rounded-sm py-1.5 pl-6 pr-6 text-xs text-foreground placeholder-gray-600 focus:outline-none focus:border-white/20 disabled:opacity-50 disabled:cursor-not-allowed"
          />
          {search && (
            <button onClick={() => setSearch('')} className="absolute right-2 top-2 text-textMuted hover:text-foreground">
              <X className="w-3 h-3" />
            </button>
          )}
        </div>

        {/* Search results dropdown */}
        {search.trim() && (
          <div className="absolute top-full left-2 right-2 bg-surfaceHighlight border border-border shadow-lg max-h-48 overflow-y-auto z-50 rounded-sm">
            {filteredSearch.length === 0 ? (
              <div className="p-3 text-xs text-textMuted text-center">No matches</div>
            ) : filteredSearch.map(stock => (
              <div
                key={stock.id}
                onClick={() => handleAdd(stock.id)}
                className="flex items-center justify-between px-3 py-2 hover:bg-black/5 dark:hover:bg-white/5 cursor-pointer border-b border-border"
              >
                <div>
                  <div className="text-xs font-semibold text-foreground">{stock.symbol}</div>
                  <div className="text-[10px] text-textMuted">{stock.sector}</div>
                </div>
                <Plus className="w-3 h-3 text-primary" />
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Stock list */}
      <div className="flex-1 overflow-y-auto">
        {!watchlist ? (
          <div className="p-6 text-center flex flex-col items-center justify-center h-full text-xs text-textMuted">
            <p className="mb-3">You don't have a watchlist yet.</p>
            <button
              onClick={handleCreateWatchlist}
              className="px-4 py-2 bg-primary text-black font-semibold rounded hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20"
            >
              Create Watchlist
            </button>
          </div>
        ) : stocks.length === 0 ? (
          <div className="p-6 text-center text-xs text-textMuted">
            Search above to add stocks
          </div>
        ) : groupMode === 'sector' ? (
          Object.entries(groupedStocks)
            .sort(([a], [b]) => a.localeCompare(b))
            .map(([sector, sectorStocks]) => (
              <div key={sector}>
                <div className="px-3 py-1 bg-surfaceHighlight/60 border-b border-border text-[9px] font-semibold text-textMuted uppercase tracking-widest sticky top-0 z-10">
                  {sector}
                  <span className="ml-1.5 text-textMuted normal-case font-normal">{sectorStocks.length}</span>
                </div>
                {sectorStocks.map(s => renderStockRow(s, false))}
              </div>
            ))
        ) : (
          /* Priority mode — flat list with drag-and-drop */
          <div className="py-1">
            <div className="px-3 py-1 bg-surfaceHighlight/60 border-b border-border text-[9px] font-semibold text-textMuted uppercase tracking-widest sticky top-0 z-10">
              Priority Order
              <span className="ml-1.5 normal-case font-normal text-textMuted/70">drag to reorder</span>
            </div>
            {stocks.map(s => renderStockRow(s, true))}
          </div>
        )}
      </div>
    </aside>
  );
}
