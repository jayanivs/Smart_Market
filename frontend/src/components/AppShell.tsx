import Header from './Header';
import WatchlistSidebar from './WatchlistSidebar';
import ManualWorkspace from './ManualWorkspace';
import SmartWorkspace from './SmartWorkspace';
import SmartWatchBar from './SmartWatchBar';
import WhyDrawer from './WhyDrawer';
import PulseTrailDrawer from './PulseTrailDrawer';
import NotificationPopover from './NotificationPopover';
import { useApp } from '../context/AppContext';

export default function AppShell() {
  const { smartWatchEnabled, drawer, closeDrawer } = useApp();

  return (
    <div className="flex flex-col h-screen bg-background overflow-hidden">
      <Header />
      <div className="flex flex-1 min-h-0">
        <WatchlistSidebar />
        <main className="flex-1 overflow-y-auto">
          {smartWatchEnabled ? <SmartWorkspace /> : <ManualWorkspace />}
        </main>
      </div>
      <SmartWatchBar />

      {/* Drawers — overlaid, not routed */}
      {drawer.type === 'why' && drawer.stockId !== null && (
        <WhyDrawer stockId={drawer.stockId} symbol={drawer.symbol ?? ''} onClose={closeDrawer} />
      )}
      {drawer.type === 'trail' && drawer.stockId !== null && (
        <PulseTrailDrawer stockId={drawer.stockId} symbol={drawer.symbol ?? ''} onClose={closeDrawer} />
      )}

      {/* Notification popover rendered at root level */}
      <NotificationPopover />
    </div>
  );
}
