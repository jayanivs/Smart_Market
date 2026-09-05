import React, { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';
import type { PulseScore, Stock, Watchlist, QuickGroup } from '../services/api';
import { fetchPulse, fetchWatchlists, fetchStocks, fetchQuickGroups, markAllNotificationsRead, deleteWatchlist, reorderWatchlist } from '../services/api';

interface DrawerState {
  type: 'why' | 'trail' | 'stock' | null;
  stockId: number | null;
  symbol: string | null;
}

interface AppContextType {
  // Mode
  smartWatchEnabled: boolean;
  setSmartWatchEnabled: (v: boolean) => void;

  // Data
  pulseMap: Record<number, PulseScore>;  // keyed by stock_id
  pulseList: PulseScore[];               // sorted by rank
  watchlist: Watchlist | null;
  watchlists: Watchlist[];
  setActiveWatchlist: (id: number) => void;
  allStocks: Stock[];
  quickGroups: QuickGroup[];
  unreadCount: number;
  lastUpdated: Date | null;
  isStale: boolean;

  // Actions
  refreshPulse: () => Promise<void>;
  refreshWatchlist: () => Promise<void>;
  refreshQuickGroups: () => Promise<void>;
  applyPulseUpdate: (stockId: number, score: number, severity: string, momentum: number) => void;
  clearUnread: () => void;
  deleteWatchlistById: (id: number) => Promise<void>;
  reorderActiveWatchlist: (stock_ids: number[]) => Promise<void>;

  // Drawer
  drawer: DrawerState;
  openDrawer: (type: DrawerState['type'], stockId: number, symbol: string) => void;
  closeDrawer: () => void;

  // Notification popover
  notifOpen: boolean;
  setNotifOpen: (v: boolean) => void;

  // Weekly Report modal
  reportOpen: boolean;
  setReportOpen: (v: boolean) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

const SEVERITY_ORDER: Record<string, number> = {
  CRITICAL: 4, IMPORTANT: 3, MODERATE: 2, NORMAL: 1,
};

function sortByRank(scores: PulseScore[]): PulseScore[] {
  return [...scores].sort((a, b) => {
    const sevDiff = (SEVERITY_ORDER[b.severity] ?? 0) - (SEVERITY_ORDER[a.severity] ?? 0);
    if (sevDiff !== 0) return sevDiff;
    const momDiff = (b.momentum ?? 0) - (a.momentum ?? 0);
    if (momDiff !== 0) return momDiff;
    return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
  });
}

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [smartWatchEnabled, setSmartWatchEnabled] = useState(false);
  const [pulseMap, setPulseMap] = useState<Record<number, PulseScore>>({});
  const [watchlist, setWatchlist] = useState<Watchlist | null>(null);
  const [watchlists, setWatchlists] = useState<Watchlist[]>([]);
  const [allStocks, setAllStocks] = useState<Stock[]>([]);
  const [quickGroups, setQuickGroups] = useState<QuickGroup[]>([]);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [unreadCount, setUnreadCount] = useState(0);
  const prevCriticalRef = useRef<Set<number>>(new Set());
  const [drawer, setDrawer] = useState<DrawerState>({ type: null, stockId: null, symbol: null });
  const [notifOpen, setNotifOpen] = useState(false);
  const [reportOpen, setReportOpen] = useState(false);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const clearUnread = useCallback(() => {
    setUnreadCount(0);
  }, []);

  // Opening the notification panel auto-marks all as read on backend + clears badge
  const handleSetNotifOpen = useCallback((v: boolean) => {
    setNotifOpen(v);
    if (v) {
      markAllNotificationsRead().catch(() => {});
      setUnreadCount(0);
    }
  }, []);

  const refreshPulse = useCallback(async () => {
    try {
      const scores = await fetchPulse();
      const map: Record<number, PulseScore> = {};
      scores.forEach(s => { map[s.stock_id] = s; });
      setPulseMap(map);
      setLastUpdated(new Date());

      // Only badge for stocks that are NEWLY critical — not ones already known
      const nowCritical = new Set(
        scores
          .filter(s => s.severity === 'CRITICAL' || s.severity === 'IMPORTANT')
          .map(s => s.stock_id)
      );
      const genuinelyNew = [...nowCritical].filter(id => !prevCriticalRef.current.has(id));
      if (genuinelyNew.length > 0) {
        setUnreadCount(prev => prev + genuinelyNew.length);
      }
      prevCriticalRef.current = nowCritical;
    } catch (e) {
      console.error('Failed to refresh pulse:', e);
    }
  }, []);

  const refreshWatchlist = useCallback(async () => {
    try {
      const [wls, stocks] = await Promise.all([fetchWatchlists(), fetchStocks()]);
      setWatchlists(wls);
      setWatchlist(prev => {
        if (!prev) return wls[0] ?? null;
        return wls.find(w => w.id === prev.id) ?? wls[0] ?? null;
      });
      setAllStocks(stocks);
    } catch (e) {
      console.error('Failed to refresh watchlist:', e);
    }
  }, []);

  const setActiveWatchlist = useCallback((id: number) => {
    setWatchlist(watchlists.find(w => w.id === id) ?? null);
  }, [watchlists]);

  const refreshQuickGroups = useCallback(async () => {
    try {
      const groups = await fetchQuickGroups();
      setQuickGroups(groups);
    } catch (e) {
      console.error('Failed to refresh quick groups:', e);
    }
  }, []);

  const applyPulseUpdate = useCallback((stockId: number, score: number, severity: string, momentum: number) => {
    setPulseMap(prev => {
      const existing = prev[stockId];
      if (!existing) return prev;
      return {
        ...prev,
        [stockId]: { ...existing, score, severity: severity as PulseScore['severity'], momentum },
      };
    });
    setLastUpdated(new Date());
  }, []);

  const openDrawer = useCallback((type: DrawerState['type'], stockId: number, symbol: string) => {
    setDrawer({ type, stockId, symbol });
  }, []);

  const closeDrawer = useCallback(() => {
    setDrawer({ type: null, stockId: null, symbol: null });
  }, []);

  const deleteWatchlistById = useCallback(async (id: number) => {
    try {
      await deleteWatchlist(id);
      await refreshWatchlist();
    } catch (e) {
      console.error('Failed to delete watchlist:', e);
      alert('Failed to delete watchlist. It might not exist or you lack permission.');
    }
  }, [refreshWatchlist]);

  const reorderActiveWatchlist = useCallback(async (stock_ids: number[]) => {
    if (!watchlist) return;
    try {
      await reorderWatchlist(watchlist.id, stock_ids);
      await refreshWatchlist();
    } catch (e) {
      console.error('Failed to reorder watchlist:', e);
    }
  }, [watchlist, refreshWatchlist]);

  // Initial load
  useEffect(() => {
    refreshWatchlist();
    refreshPulse();
    refreshQuickGroups();
    pollingRef.current = setInterval(refreshPulse, 30_000);
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, []);

  const pulseList = sortByRank(Object.values(pulseMap));

  const isStale = lastUpdated
    ? (Date.now() - lastUpdated.getTime()) > 120_000
    : false;

  return (
    <AppContext.Provider value={{
      smartWatchEnabled, setSmartWatchEnabled,
      pulseMap, pulseList, watchlist, watchlists, setActiveWatchlist, allStocks, quickGroups,
      unreadCount, lastUpdated, isStale,
      refreshPulse, refreshWatchlist, refreshQuickGroups, applyPulseUpdate, clearUnread,
      deleteWatchlistById, reorderActiveWatchlist,
      drawer, openDrawer, closeDrawer,
      notifOpen, setNotifOpen: handleSetNotifOpen,
      reportOpen, setReportOpen,
    }}>
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useApp must be used within AppProvider');
  return ctx;
}

