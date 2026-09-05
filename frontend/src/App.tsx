import { AppProvider } from './context/AppContext';
import { WebSocketProvider } from './context/WebSocketContext';
import { ThemeProvider } from './context/ThemeContext';
import { GoogleOAuthProvider } from '@react-oauth/google';
import AppShell from './components/AppShell';

export default function App() {
  return (
    <GoogleOAuthProvider clientId="754487682307-vrnpne8d5egs9r3i35rlh1e9p7lfurdg.apps.googleusercontent.com">
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
