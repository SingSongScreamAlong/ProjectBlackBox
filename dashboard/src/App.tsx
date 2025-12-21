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
    console.log('🔧 Dashboard App initialized (simplified mode)');
  }, []);

  return (
    <div className="App">
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
