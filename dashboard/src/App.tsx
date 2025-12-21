import React, { useEffect } from 'react';
import './App.css';
import './styles/dashboard.css';
import Dashboard from './components/Dashboard/Dashboard';
import { multiDriverService } from './services/MultiDriverService';
import { Provider } from 'react-redux';
import { store } from './redux/store';
import { AuthProvider } from './context/AuthContext';

// Simplified App - renders Dashboard directly without routing
// This bypasses all routing and auth issues for production testing

function AppContent() {
  useEffect(() => {
    multiDriverService.initialize();
    console.log('🔧 Dashboard App initialized (simplified mode) - Build: Dec 21 2024 06:15');
  }, []);

  return (
    <div className="App">
      <div style={{ background: '#1a1a2e', padding: '10px', color: '#0f0', fontSize: '12px', fontFamily: 'monospace' }}>
        ✅ SIMPLIFIED BUILD - Dec 21 2024 06:15 - No Routing
      </div>
      <Dashboard />
    </div>
  );
}

function App() {
  return (
    <Provider store={store}>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </Provider>
  );
}

export default App;
