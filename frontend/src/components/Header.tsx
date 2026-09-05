import { useEffect, useState, useRef } from 'react';
import { Bell, FileText, Sun, Moon, User } from 'lucide-react';
import { useApp } from '../context/AppContext';
import { useTheme } from '../context/ThemeContext';
import { getUserId, setUserId, googleLogin, getUserDetails } from '../services/api';
import WeeklyReportModal from './WeeklyReportModal';
import { useGoogleLogin, googleLogout } from '@react-oauth/google';

function LiveStatus({ lastUpdated, isStale }: { lastUpdated: Date | null; isStale: boolean }) {
  const [age, setAge] = useState(0);
  useEffect(() => {
    const id = setInterval(() => {
      setAge(lastUpdated ? Math.floor((Date.now() - lastUpdated.getTime()) / 1000) : 0);
    }, 1000);
    return () => clearInterval(id);
  }, [lastUpdated]);

  if (!lastUpdated) return <span className="text-textMuted text-xs">Connecting...</span>;
  if (isStale) return (
    <span className="flex items-center gap-1.5 text-warning text-xs">
      <span className="w-1.5 h-1.5 rounded-full bg-warning" />
      Delayed data
    </span>
  );
  if (age < 10) return (
    <span className="flex items-center gap-1.5 text-success text-xs">
      <span className="w-1.5 h-1.5 rounded-full bg-success animate-pulse" />
      Live
    </span>
  );
  return (
    <span className="flex items-center gap-1.5 text-textMuted text-xs">
      <span className="w-1.5 h-1.5 rounded-full bg-textMuted" />
      Updated {age}s ago
    </span>
  );
}

function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  const cycleTheme = () => {
    setTheme(theme === 'light' ? 'dark' : 'light');
  };

  const Icon = theme === 'light' ? Sun : Moon;

  return (
    <button
      onClick={cycleTheme}
      className="p-1.5 rounded hover:bg-black/5 dark:hover:bg-white/10 text-textMuted hover:text-foreground transition-colors"
      title={`Toggle Theme`}
    >
      <Icon className="w-4 h-4" />
    </button>
  );
}

function UserAuthSelector() {
  const currentUserId = getUserId();
  const userDetails = getUserDetails();
  const [userId, setLocalUserId] = useState(currentUserId);
  const [userName, setUserName] = useState(userDetails.name);
  const [userPicture, setUserPicture] = useState(userDetails.picture);

  const login = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      try {
        const userInfo = await fetch('https://www.googleapis.com/oauth2/v3/userinfo', {
          headers: { Authorization: `Bearer ${tokenResponse.access_token}` },
        }).then(res => res.json());
        
        const res = await googleLogin(userInfo.name, userInfo.email, userInfo.picture || null);
        if (res && res.id) {
          setUserId(res.id.toString(), res.name, res.picture, res.token);
          setLocalUserId(res.id.toString());
          setUserName(res.name);
          setUserPicture(res.picture || '');
          window.location.reload();
        }
      } catch (error) {
        console.error('Login failed', error);
      }
    },
    onError: () => console.error('Login Failed'),
  });

  const handleLogout = () => {
    googleLogout();
    setUserId('1', '', ''); // Fallback to mock user 1
    window.location.reload();
  };

  if (userId && userName) {
    return (
      <button
        onClick={handleLogout}
        className="flex items-center gap-2 px-2.5 py-1 rounded-md text-xs font-semibold border border-border bg-surface hover:bg-black/5 dark:hover:bg-white/10 text-textMuted hover:text-foreground transition-all shadow-sm"
        title="Click to logout"
      >
        {userPicture ? (
          <img src={userPicture} alt={userName} className="w-5 h-5 rounded-full" />
        ) : (
          <User className="w-3.5 h-3.5 text-primary" />
        )}
        <span>{userName}</span>
      </button>
    );
  }

  return (
    <div className="flex items-center">
      <button
        onClick={() => login()}
        className="group relative flex items-center gap-2 px-4 py-1.5 rounded-full bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white shadow-md hover:shadow-lg transition-all duration-300 ease-out transform hover:-translate-y-0.5"
      >
        <div className="absolute inset-0 rounded-full bg-white/20 opacity-0 group-hover:opacity-100 transition-opacity" />
        <svg className="w-4 h-4 bg-white rounded-full p-0.5" viewBox="0 0 24 24">
          <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
          <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
          <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
          <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
        </svg>
        <span className="text-xs font-bold tracking-wide">Sign in with Google</span>
      </button>
    </div>
  );
}

export default function Header() {
  const { smartWatchEnabled, setSmartWatchEnabled, pulseList, lastUpdated, isStale, unreadCount, notifOpen, setNotifOpen, reportOpen, setReportOpen } = useApp();
  const notifRef = useRef<HTMLButtonElement>(null);

  const criticalCount = pulseList.filter(p => p.severity === 'CRITICAL').length;

  return (
    <>
      <header className="h-14 flex-shrink-0 flex items-center justify-between px-6 border-b border-border bg-surface/80 backdrop-blur-md z-30 shadow-sm sticky top-0">
        {/* Left: logo or attention summary */}
        <div className="flex items-center gap-4">
          {smartWatchEnabled && criticalCount > 0 ? (
            <span className="flex items-center gap-2 text-danger text-sm font-semibold bg-danger/10 px-3 py-1 rounded-full">
              <span className="w-2 h-2 rounded-full bg-danger animate-pulse" />
              {criticalCount} Need{criticalCount === 1 ? 's' : ''} Attention
            </span>
          ) : (
            <h1 className="text-sm font-bold tracking-widest text-primary uppercase drop-shadow-sm">
              Market Pulse
            </h1>
          )}
          <LiveStatus lastUpdated={lastUpdated} isStale={isStale} />
        </div>

        {/* Right: toggle + report + bell */}
        <div className="flex items-center gap-3 sm:gap-4">
          {/* Google Auth Selector */}
          <UserAuthSelector />

          {/* Smart Watch toggle */}
          <label className="flex items-center gap-2 cursor-pointer select-none">
            <span className="text-xs font-medium text-textMuted uppercase tracking-wider">
              Smart Watch
            </span>
            <button
              role="switch"
              aria-checked={smartWatchEnabled}
              onClick={() => setSmartWatchEnabled(!smartWatchEnabled)}
              className={`relative w-11 h-6 rounded-full transition-colors duration-300 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary/50 shadow-inner ${
                smartWatchEnabled ? 'bg-primary' : 'bg-gray-300 dark:bg-gray-600'
              }`}
            >
              <span
                className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-surface shadow-md transition-transform duration-300 ease-in-out ${
                  smartWatchEnabled ? 'translate-x-5' : 'translate-x-0'
                }`}
              />
            </button>
            </label>

          <div className="w-px h-6 bg-border mx-1" />

          {/* Theme Toggle */}
          <ThemeToggle />

          {/* Weekly Report */}
          <button
            onClick={() => setReportOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md hover:bg-black/5 dark:hover:bg-white/10 text-textMuted hover:text-foreground transition-colors font-medium text-sm"
          >
            <FileText className="w-4 h-4" />
            <span className="hidden sm:inline">Report</span>
          </button>

          {/* Bell */}
          <button
            ref={notifRef}
            onClick={() => setNotifOpen(!notifOpen)}
            className="relative p-1.5 rounded-md hover:bg-black/5 dark:hover:bg-white/10 text-textMuted hover:text-foreground transition-colors"
          >
            <Bell className="w-5 h-5" />
            {unreadCount > 0 && (
              <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-danger flex items-center justify-center text-foreground text-[10px] font-bold shadow-sm ring-2 ring-surface">
                {unreadCount > 9 ? '9+' : unreadCount}
              </span>
            )}
          </button>
        </div>
      </header>
      {reportOpen && <WeeklyReportModal onClose={() => setReportOpen(false)} />}
    </>
  );
}

