import { useEffect, useState, useRef } from 'react';
import { X, CheckCheck } from 'lucide-react';
import { useApp } from '../context/AppContext';
import { fetchNotifications, markAllNotificationsRead } from '../services/api';
import type { Notification } from '../services/api';

const FILTERS = ['ALL', 'CRITICAL', 'IMPORTANT', 'INFO'] as const;
type Filter = (typeof FILTERS)[number];

const SEV_COLOR: Record<string, string> = {
  CRITICAL: 'text-danger', IMPORTANT: 'text-warning',
  MODERATE: 'text-primary', NORMAL: 'text-textMuted',
};

const SEV_DOT: Record<string, string> = {
  CRITICAL: 'bg-danger', IMPORTANT: 'bg-warning',
  MODERATE: 'bg-primary', NORMAL: 'bg-gray-600',
};

function timeAgo(iso: string): string {
  const secs = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (secs < 60) return `${secs}s ago`;
  if (secs < 3600) return `${Math.floor(secs / 60)}m ago`;
  return `${Math.floor(secs / 3600)}h ago`;
}

export default function NotificationPopover() {
  const { notifOpen, setNotifOpen } = useApp();
  const [filter, setFilter] = useState<Filter>('ALL');
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(false);
  const [marking, setMarking] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const load = async (f: Filter) => {
    setLoading(true);
    try { setNotifications(await fetchNotifications(f)); }
    catch { /* ignore */ }
    finally { setLoading(false); }
  };

  useEffect(() => {
    if (notifOpen) load(filter);
  }, [notifOpen, filter]);

  // Close on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setNotifOpen(false);
      }
    };
    if (notifOpen) document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [notifOpen, setNotifOpen]);

  const handleMarkAll = async () => {
    setMarking(true);
    try {
      await markAllNotificationsRead();
      await load(filter);
    } catch { /* ignore */ }
    finally { setMarking(false); }
  };

  if (!notifOpen) return null;

  const unread = notifications.filter(n => !n.is_read).length;

  return (
    <div ref={ref} className="fixed top-11 right-0 w-80 z-50 animate-fade-in">
      <div className="bg-surface border border-border shadow-2xl flex flex-col max-h-[70vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-border">
          <div className="text-sm font-semibold text-foreground">
            Notifications
            {unread > 0 && (
              <span className="ml-2 text-xs text-textMuted">{unread} unread</span>
            )}
          </div>
          <div className="flex items-center gap-2">
            {unread > 0 && (
              <button
                onClick={handleMarkAll}
                disabled={marking}
                className="text-[10px] text-textMuted hover:text-foreground flex items-center gap-1 transition-colors"
              >
                <CheckCheck className="w-3 h-3" />
                Mark all read
              </button>
            )}
            <button onClick={() => setNotifOpen(false)} className="p-1 text-textMuted hover:text-foreground">
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Filter tabs */}
        <div className="flex border-b border-border">
          {FILTERS.map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`flex-1 py-2 text-[10px] font-semibold uppercase tracking-wide transition-colors ${
                filter === f
                  ? 'text-primary border-b-2 border-primary'
                  : 'text-textMuted hover:text-textMuted'
              }`}
            >
              {f}
            </button>
          ))}
        </div>

        {/* List */}
        <div className="flex-1 overflow-y-auto divide-y divide-white/5">
          {loading ? (
            <div className="py-8 text-center text-xs text-textMuted">Loading...</div>
          ) : notifications.length === 0 ? (
            <div className="py-12 flex flex-col items-center justify-center text-center">
              <CheckCheck className="w-8 h-8 text-foreground/10 mb-3" />
              <div className="text-xs font-semibold text-textMuted">All caught up</div>
              <div className="text-[10px] text-textMuted mt-1">No {filter.toLowerCase()} notifications found.</div>
            </div>
          ) : notifications.map(n => (
            <div
              key={n.id}
              className={`flex items-start gap-3 px-4 py-3 hover:bg-black/5 dark:bg-white/5 transition-colors ${
                !n.is_read ? 'bg-black/5 dark:bg-white/5' : ''
              }`}
            >
              <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 mt-1.5 ${SEV_DOT[n.severity] ?? 'bg-gray-600'}`} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className={`text-xs font-semibold ${SEV_COLOR[n.severity] ?? 'text-textMuted'}`}>
                    {n.stock_symbol}
                  </span>
                  {!n.is_read && (
                    <span className="w-1.5 h-1.5 rounded-full bg-primary flex-shrink-0" />
                  )}
                </div>
                <div className="text-[11px] text-textMuted mt-0.5 leading-relaxed">{n.message}</div>
                <div className="text-[10px] text-textMuted mt-1">{timeAgo(n.created_at)}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
