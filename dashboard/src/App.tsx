import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import './App.css';
import './styles/dashboard.css';
import Dashboard from './components/Dashboard/Dashboard';
import ComponentValidator from './components/validation/ComponentValidator';
import RelayAgentPage from './components/RelayAgentPage';
import { multiDriverService } from './services/MultiDriverService';
import { Provider } from 'react-redux';
import { store } from './redux/store';
import { initializeMockDriverData } from './utils/mockDriverData';

function App() {
  // Initialize MultiDriverService and mock data when the app starts
  useEffect(() => {
    multiDriverService.initialize();
    
    // Initialize mock driver data for development/debugging
    if (process.env.NODE_ENV === 'development') {
      initializeMockDriverData();
    }
    
    return () => {
      // Any cleanup if needed
    };
  }, []);
  return (
    <Provider store={store}>
      <Router>
      <div className="App">
        <nav className="app-nav">
          <ul>
            <li>
              <Link to="/">Dashboard</Link>
            </li>
            <li>
              <Link to="/validator">Component Validator</Link>
            </li>
            <li>
              <Link to="/relay-agent">Relay Agent</Link>
            </li>
          </ul>
        </nav>
        
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/validator" element={<ComponentValidator />} />
          <Route path="/relay-agent" element={<RelayAgentPage />} />
        </Routes>
      </div>
    </Router>
    </Provider>
  );
}

export default App;
