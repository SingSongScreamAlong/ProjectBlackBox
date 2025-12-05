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

// Define available Dashboard Modes
export type DashboardMode = 'OVERVIEW' | 'FOCUS' | 'ENGINEER' | 'STRATEGY';

interface HeaderProps {
  connected: boolean;
  sessionInfo: HeaderSessionInfo;
  onMultiDriverClick?: () => void;
  currentMode: DashboardMode;
  onModeChange: (mode: DashboardMode) => void;
}

const Header: React.FC<HeaderProps> = ({
  connected,
  sessionInfo,
  onMultiDriverClick,
  currentMode,
  onModeChange
}) => {
  return (
    <div className="dashboard-header">
      <div className="header-left">
        <div className="header-logo">
          BLACK<span>BOX</span> RACING
        </div>

        <div className="connection-status">
          <div className={`status-indicator ${connected ? 'connected' : ''}`}></div>
          {connected ? 'LIVE' : 'OFFLINE'}
        </div>
      </div>

      <div className="header-center">
        {/* Mode Switcher */}
        <div className="mode-switcher">
          {(['OVERVIEW', 'FOCUS', 'ENGINEER', 'STRATEGY'] as DashboardMode[]).map((mode) => (
            <button
              key={mode}
              className={`mode-button ${currentMode === mode ? 'active' : ''}`}
              onClick={() => onModeChange(mode)}
            >
              {mode}
            </button>
          ))}
        </div>
      </div>

      <div className="header-right">
        <div className="header-session-info compact">
          <div className="header-stat">
            <div className="header-stat-label">Lap</div>
            <div className="header-stat-value">
              {sessionInfo.lapCount} <span className="stat-sub">/ {sessionInfo.totalLaps}</span>
            </div>
          </div>
        </div>

        {onMultiDriverClick && (
          <button className="multi-driver-button" onClick={onMultiDriverClick}>
            <span className="icon">👥</span>
          </button>
        )}
      </div>
    </div>
  );
};

export default Header;
