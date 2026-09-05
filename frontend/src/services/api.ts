/// <reference types="vite/client" />
// Use VITE_API_BASE env var in production (set in .env or Vercel dashboard).
// Falls back to localhost:8000 for local development.
export const API_BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? 'http://localhost:8000';

// ── Types ────────────────────────────────────────────────────────────────────

export interface Stock {
  id: number;
  symbol: string;
  company_name: string;
  sector: string;
}

export interface SnapshotInfo {
  price: number;
  previous_price: number;
  volume: number;
  average_volume: number;
  is_stale: boolean;
  data_timestamp: string;
}

export interface PulseExplanation {
  id: number;
  reason_type: string;
  message: string;
  impact: number;
}

export interface PulseScore {
  id: number;
  stock_id: number;
  score: number;
  price_signal: number;
  volume_signal: number;
  sector_signal: number;
  threshold_signal: number;
  momentum: number;
  severity: 'NORMAL' | 'MODERATE' | 'IMPORTANT' | 'CRITICAL';
  timestamp: string;
  explanations: PulseExplanation[];
  stock: Stock | null;
  snapshot: SnapshotInfo | null;
}

export interface WhyResponse {
  score: number;
  severity: 'NORMAL' | 'MODERATE' | 'IMPORTANT' | 'CRITICAL';
  momentum: number;
  reasons: { type: string; message: string; impact: number }[];
}

export interface MeaningfulChange {
  id: number;
  stock_id: number;
  previous_score: number;
  current_score: number;
  created_at: string;
  seen_at: string | null;
  stock: Stock | null;
  severity?: string;
  momentum?: number;
}

export interface Watchlist {
  id: number;
  name: string;
  stocks: Stock[];
}

export interface SmartWatchPreference {
  id: number;
  user_id: number;
  enabled: boolean;
  price_threshold: number;
  volume_threshold: number;
  sensitivity: string;
  updated_at?: string;
}

export interface Notification {
  id: number;
  stock_id: number;
  stock_symbol: string;
  stock_name: string;
  previous_score: number;
  current_score: number;
  severity: string;
  message: string;
  created_at: string;
  seen_at: string | null;
  is_read: boolean;
}

export interface SimulatorSpikeResult {
  status: string;
  symbol: string;
  stock_id: number;
  price_before: number;
  price_after: number;
  change_pct: number;
  volume: number;
  pulse_score: number | null;
  severity: string | null;
}

export interface User {
  id: number;
  name: string;
  email: string;
  picture: string | null;
  /** Signed JWT returned by /api/auth/google and /api/auth/login */
  token?: string;
}


// ── Helper ───────────────────────────────────────────────────────────────────

export function getUserId(): string {
  return localStorage.getItem('market_pulse_user_id') || '1';
}

export function getToken(): string | null {
  return localStorage.getItem('market_pulse_token');
}

export function getUserDetails() {
  return {
    name: localStorage.getItem('market_pulse_user_name') || '',
    picture: localStorage.getItem('market_pulse_user_picture') || ''
  };
}

export function setUserId(id: string, name?: string, picture?: string | null, token?: string | null) {
  localStorage.setItem('market_pulse_user_id', id);
  if (name) localStorage.setItem('market_pulse_user_name', name);
  else localStorage.removeItem('market_pulse_user_name');
  
  if (picture) localStorage.setItem('market_pulse_user_picture', picture);
  else localStorage.removeItem('market_pulse_user_picture');
  
  if (token) localStorage.setItem('market_pulse_token', token);
  else localStorage.removeItem('market_pulse_token');
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const authHeader: Record<string, string> = token
    ? { Authorization: `Bearer ${token}` }
    : { 'X-User-Id': getUserId() };  // dev fallback when no token stored yet

  const headers = {
    'Content-Type': 'application/json',
    ...authHeader,
    ...(options.headers || {}),
  };
  const resp = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
    cache: 'no-store',
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`API error ${resp.status}: ${text}`);
  }
  return (await resp.json()) as T;
}

// ── Auth ─────────────────────────────────────────────────────────────────────
export const googleLogin = (name: string, email: string, picture: string | null) =>
  request<User>('/api/auth/google', {
    method: 'POST',
    body: JSON.stringify({ name, email, picture }),
  });

// ── Watchlists ───────────────────────────────────────────────────────────────
export const fetchStocks = () => request<Stock[]>('/api/stocks');
export const fetchWatchlists = () => request<Watchlist[]>('/api/watchlists');
export const createWatchlist = (name: string) =>
  request<Watchlist>('/api/watchlists', { method: 'POST', body: JSON.stringify({ name }) });
export const addStockToWatchlist = (watchlistId: number, stockId: number) =>
  request<Watchlist>(`/api/watchlists/${watchlistId}/stocks`, {
    method: 'POST',
    body: JSON.stringify({ stock_id: stockId }),
  });
export const removeStockFromWatchlist = (watchlistId: number, stockId: number) =>
  request<void>(`/api/watchlists/${watchlistId}/stocks/${stockId}`, { method: 'DELETE' });
export const deleteWatchlist = (watchlistId: number) =>
  request<{ status: string }>(`/api/watchlists/${watchlistId}`, { method: 'DELETE' });
export const renameWatchlist = (watchlistId: number, name: string) =>
  request<Watchlist>(`/api/watchlists/${watchlistId}`, {
    method: 'PATCH',
    body: JSON.stringify({ name }),
  });
export const reorderWatchlist = (watchlistId: number, stock_ids: number[]) =>
  request<Watchlist>(`/api/watchlists/${watchlistId}/stocks/reorder`, {
    method: 'PATCH',
    body: JSON.stringify({ stock_ids }),
  });

// ── Pulse ────────────────────────────────────────────────────────────────────
export const fetchPulse = () => request<PulseScore[]>('/api/pulse');
export const fetchPulseWhy = (stockId: number) =>
  request<WhyResponse>(`/api/pulse/${stockId}/why`);
export const fetchPulseHistory = (stockId: number) =>
  request<PulseScore[]>(`/api/pulse/${stockId}/history`);

// ── Simulator ────────────────────────────────────────────────────────────────
export const triggerSpike = (symbol: string) =>
  request<{ status: string; stock_id: number }>(`/api/simulator/spike/${symbol}`, { method: 'POST' });
export const triggerRandomSimulator = () =>
  request<{ status: string; message: string }>(`/api/simulator/trigger-random`, { method: 'POST' });
export const triggerLive = () =>
  request<{ status: string; message: string }>(`/api/simulator/trigger-live`, { method: 'POST' });

// ── What You Missed ──────────────────────────────────────────────────────────
export const fetchWhatYouMissed = () => request<MeaningfulChange[]>('/api/what-you-missed');
export const ackMissed = () =>
  request<{ status: string }>('/api/what-you-missed/ack', { method: 'POST' });

// ── Smart Watch Preferences ──────────────────────────────────────────────────
export const getSmartWatch = () => request<SmartWatchPreference>('/api/smart-watch');
export const updateSmartWatch = (data: Partial<SmartWatchPreference>) =>
  request<SmartWatchPreference>('/api/smart-watch', {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
export const toggleSmartWatch = () =>
  request<SmartWatchPreference>('/api/smart-watch/toggle', { method: 'POST' });

// ── Notifications ────────────────────────────────────────────────────────────
export const fetchNotifications = (filter = 'ALL', limit = 50) =>
  request<Notification[]>(`/api/notifications?filter=${filter}&limit=${limit}`);
export const markNotificationRead = (id: number) =>
  request<{ status: string }>(`/api/notifications/${id}/read`, { method: 'PATCH' });
export const markAllNotificationsRead = () =>
  request<{ status: string }>('/api/notifications/read-all', { method: 'POST' });

// ── Quick Groups ─────────────────────────────────────────────────────────────
export interface QuickGroup {
  id: number;
  name: string;
  sensitivity: string;
  auto_watch: boolean;
  stocks: Stock[];
}

export const fetchQuickGroups = () => request<QuickGroup[]>('/api/quick-groups');
export const createQuickGroup = (name: string, stockIds: number[], sensitivity: string, autoWatch: boolean) =>
  request<QuickGroup>('/api/quick-groups', {
    method: 'POST',
    body: JSON.stringify({ name, stock_ids: stockIds, sensitivity, auto_watch: autoWatch }),
  });
export const updateQuickGroup = (id: number, data: { sensitivity?: string; auto_watch?: boolean }) =>
  request<QuickGroup>(`/api/quick-groups/${id}`, { method: 'PATCH', body: JSON.stringify(data) });
export const deleteQuickGroup = (id: number) =>
  request<{ status: string }>(`/api/quick-groups/${id}`, { method: 'DELETE' });

// ── Weekly Report ─────────────────────────────────────────────────────────────
export interface WeeklyReport {
  period_days: number;
  total_changes: number;
  critical_changes: number;
  important_changes: number;
  moderate_changes: number;
  normal_changes: number;
  top_attention_stock: string | null;
  most_active_group: string | null;
  threshold_crossings: number;
  volume_anomalies: number;
  generated_at: string;
}

export const fetchWeeklyReport = () => request<WeeklyReport>('/api/reports/weekly');

