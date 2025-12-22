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

// Define available Dashboard Modes - 4 distinct modes with unique functionality
export type DashboardMode = 'RACE' | 'TRACK' | 'STRATEGY' | 'ANALYSIS';

interface HeaderProps {
  connected: boolean;
  sessionInfo: HeaderSessionInfo;
  onMultiDriverClick?: () => void;
  onExportClick?: () => void;
  onSettingsClick?: () => void;
  onHistoryClick?: () => void;
  onShortcutsClick?: () => void;
  onChatClick?: () => void;
  currentMode: DashboardMode;
  onModeChange: (mode: DashboardMode) => void;
}

const Header: React.FC<HeaderProps> = ({
  connected,
  sessionInfo,
  onMultiDriverClick,
  onExportClick,
  onSettingsClick,
  onHistoryClick,
  onShortcutsClick,
  onChatClick,
  currentMode,
  onModeChange
}) => {
  return (
    <div className="dashboard-header">
      <div className="header-left">
        <div className="connection-status">
          <div className={`status-indicator ${connected ? 'connected' : 'standby'}`}></div>
          {connected ? 'LIVE' : 'STANDBY'}
        </div>

        {/* Mode Switcher - 4 Distinct Modes */}
        <div className="mode-switcher">
          {([
            { id: 'RACE', label: '🏎️ RACE', desc: 'Live telemetry' },
            { id: 'TRACK', label: '🗺️ TRACK', desc: 'Track & positions' },
            { id: 'STRATEGY', label: '📊 STRATEGY', desc: 'Pit planner' },
            { id: 'ANALYSIS', label: '📈 ANALYSIS', desc: 'Session review' }
          ] as { id: DashboardMode; label: string; desc: string }[]).map((mode) => (
            <button
              key={mode.id}
              className={`mode-button ${currentMode === mode.id ? 'active' : ''}`}
              onClick={() => onModeChange(mode.id)}
              title={mode.desc}
            >
              {mode.label}
            </button>
          ))}
        </div>
      </div>

      <div className="header-center">
        <div className="header-logo">
          <span className="logo-tagline">OK, Box Box</span>
          <span className="logo-main">Project: <span>PitBox</span></span>
        </div>

        {/* Quick Action Buttons */}
        <div className="header-quick-actions">
          {onChatClick && (
            <button className="quick-action-btn" onClick={onChatClick} title="Team Chat (C)">
              💬
            </button>
          )}
          {onHistoryClick && (
            <button className="quick-action-btn" onClick={onHistoryClick} title="Session History">
              📂
            </button>
          )}
          {onSettingsClick && (
            <button className="quick-action-btn" onClick={onSettingsClick} title="Settings (S)">
              ⚙️
            </button>
          )}
          {onShortcutsClick && (
            <button className="quick-action-btn" onClick={onShortcutsClick} title="Keyboard Shortcuts">
              ⌨️
            </button>
          )}
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

        {onExportClick && (
          <button className="export-button" onClick={onExportClick} title="Export Session Data">
            <span className="icon">📥</span>
          </button>
        )}

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
