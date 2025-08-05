import React from 'react';
// Import types but create our own HeaderSessionInfo interface

// Define a custom interface for the Header component
interface HeaderSessionInfo {
  trackName: string;
  sessionType: string;
  lapCount: number;
  totalLaps: number;
  driverName: string;
  carName: string;
  weather: string;
}

interface HeaderProps {
  connected: boolean;
  sessionInfo: HeaderSessionInfo;
  onMultiDriverClick?: () => void;
}

const Header: React.FC<HeaderProps> = ({ connected, sessionInfo, onMultiDriverClick }) => {
  return (
    <div className="dashboard-header">
      <div className="header-left">
        <div className="header-logo">
          BLACK<span>BOX</span> RACING
        </div>
        
        <div className="connection-status">
          <div className={`status-indicator ${connected ? 'connected' : ''}`}></div>
          {connected ? 'Connected' : 'Disconnected'}
        </div>
      </div>
      
      <div className="header-center">
        <div className="header-session-info">
          <div className="header-stat">
            <div className="header-stat-label">Track</div>
            <div className="header-stat-value">{sessionInfo.trackName}</div>
          </div>
          
          <div className="header-stat">
            <div className="header-stat-label">Session</div>
            <div className="header-stat-value">
              {sessionInfo.sessionType}
            </div>
          </div>
          
          <div className="header-stat">
            <div className="header-stat-label">Driver</div>
            <div className="header-stat-value">{sessionInfo.driverName}</div>
          </div>
          
          <div className="header-stat">
            <div className="header-stat-label">Car</div>
            <div className="header-stat-value">{sessionInfo.carName}</div>
          </div>
          
          <div className="header-stat">
            <div className="header-stat-label">Lap</div>
            <div className="header-stat-value">
              {sessionInfo.lapCount}/{sessionInfo.totalLaps}
            </div>
          </div>
          
          <div className="header-stat">
            <div className="header-stat-label">Weather</div>
            <div className="header-stat-value">
              {sessionInfo.weather}
            </div>
          </div>
        </div>
      </div>
      
      <div className="header-right">
        <div className="header-stat">
          <div className="header-stat-label">Time</div>
          <div className="header-stat-value" id="current-time">
            {new Date().toLocaleTimeString()}
          </div>
        </div>
        
        {onMultiDriverClick && (
          <button className="multi-driver-button" onClick={onMultiDriverClick}>
            <span className="icon">👥</span>
            Multi-Driver
          </button>
        )}
      </div>
    </div>
  );
};

export default Header;
