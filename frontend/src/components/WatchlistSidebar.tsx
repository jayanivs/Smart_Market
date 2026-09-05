import { useState, useCallback } from 'react';
import { Plus, Search, X, Trash2, LayoutList, Layers, Check, ChevronDown } from 'lucide-react';
import { useApp } from '../context/AppContext';
import {
  addStockToWatchlist, removeStockFromWatchlist, createWatchlist
} from '../services/api';

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
  const { watchlist, watchlists, setActiveWatchlist, allStocks, pulseMap, refreshWatchlist, openDrawer } = useApp();
  const [search, setSearch] = useState('');
  const [hoveredId, setHoveredId] = useState<number | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [newName, setNewName] = useState('');
  const [groupMode, setGroupMode] = useState<'sector' | 'list'>(() => {
    return (localStorage.getItem('mp_groupMode') as 'sector' | 'list') ?? 'sector';
  });

  const setAndPersistGroupMode = (mode: 'sector' | 'list') => {
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
    const nameToUse = newName.trim() || "My Watchlist";
    const newWl = await createWatchlist(nameToUse);
    setNewName('');
    setIsCreating(false);
    await refreshWatchlist();
    if (newWl && newWl.id) {
      setActiveWatchlist(newWl.id);
    }
  };

  const stocks = watchlist?.stocks ?? [];

  const groupedStocks = stocks.reduce((acc, stock) => {
    const s = stock.sector || 'Other';
    if (!acc[s]) acc[s] = [];
    acc[s].push(stock);
    return acc;
  }, {} as Record<string, typeof stocks>);

  const renderStockRows = (list: typeof stocks) => list.map(stock => {
    const pulse = pulseMap[stock.id];
    const snap = pulse?.snapshot;
    const price = snap?.price ?? 0;
    const prev = snap?.previous_price ?? price;
    const chg = prev > 0 ? ((price - prev) / prev) * 100 : 0;
    const isUp = chg >= 0;
    const severity = pulse?.severity ?? 'NORMAL';
    const isHovered = hoveredId === stock.id;
    return (
      <div
        key={stock.id}
        className="sidebar-row group relative"
        onMouseEnter={() => setHoveredId(stock.id)}
        onMouseLeave={() => setHoveredId(null)}
        onClick={() => openDrawer('stock', stock.id, stock.symbol)}
      >
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
  });

  return (
    <aside className="w-64 flex-shrink-0 bg-surface border-r border-border flex flex-col">
      {/* Header */}
      <div className="px-3 py-2 border-b border-border flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <div className="text-[10px] font-semibold text-textMuted uppercase tracking-widest flex items-center">
            {watchlists.length > 0 ? (
              <div className="relative flex items-center">
                <select 
                  value={watchlist?.id || ''}
                  onChange={(e) => setActiveWatchlist(Number(e.target.value))}
                  className="bg-transparent text-foreground uppercase tracking-widest font-semibold focus:outline-none cursor-pointer hover:text-primary transition-colors appearance-none pr-4"
                  style={{ WebkitAppearance: 'none', MozAppearance: 'none' }}
                >
                  {watchlists.map(wl => (
                    <option key={wl.id} value={wl.id} className="bg-surface text-foreground normal-case tracking-normal">
                      {wl.name}
                    </option>
                  ))}
                </select>
                <ChevronDown className="w-3 h-3 absolute right-0 pointer-events-none text-textMuted" />
              </div>
            ) : (
              "Watchlist"
            )}
            {watchlist && <span className="ml-2 text-textMuted">{stocks.length}</span>}
          </div>
          <div className="flex items-center gap-1">
            {watchlist && (
              <>
                <button
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
                  onClick={() => setAndPersistGroupMode('list')}
                  title="Flat list"
                  className={`p-1 rounded transition-colors ${groupMode === 'list' ? 'text-primary bg-primary/10' : 'text-textMuted hover:text-textMuted'}`}
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
            placeholder={watchlist ? "Add symbol..." : "Create watchlist first"}
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
                className="flex items-center justify-between px-3 py-2 hover:bg-black/5 dark:bg-white/5 cursor-pointer border-b border-border"
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
                {renderStockRows(sectorStocks)}
              </div>
            ))
        ) : (
          renderStockRows([...stocks].sort((a, b) => a.symbol.localeCompare(b.symbol)))
        )}
      </div>
    </aside>
  );
}

