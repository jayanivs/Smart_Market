import { AppProvider } from './context/AppContext';
import { WebSocketProvider } from './context/WebSocketContext';
import { ThemeProvider } from './context/ThemeContext';
import { GoogleOAuthProvider } from '@react-oauth/google';
import AppShell from './components/AppShell';

export default function App() {
  return (
    <GoogleOAuthProvider clientId={import.meta.env.VITE_GOOGLE_CLIENT_ID || ''}>
      <ThemeProvider>
        <AppProvider>
          <WebSocketProvider>
            <AppShell />
          </WebSocketProvider>
        </AppProvider>
      </ThemeProvider>
    </GoogleOAuthProvider>
  );
}
