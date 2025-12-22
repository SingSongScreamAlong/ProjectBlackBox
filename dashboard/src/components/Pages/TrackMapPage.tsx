import React, { useEffect, useState } from 'react';
import TrackMap from '../TrackMap/TrackMap';
import webSocketService, { TelemetryData, SessionInfo } from '../../services/WebSocketService';
import { BACKEND_URL } from '../../config/environment';
import './TrackMapPage.css';

interface Driver {
  position: number;
  name: string;
  gap: string;
  speed: number;
  isYou?: boolean;
}

const TrackMapPage: React.FC = () => {
  const [telemetryData, setTelemetryData] = useState<TelemetryData | null>(null);
  const [trackName, setTrackName] = useState<string>('Silverstone');
  const [connected, setConnected] = useState<boolean>(false);
  const [sessionDrivers, setSessionDrivers] = useState<Driver[]>([]);

  // Data derived from telemetry or empty placeholders
  const sectorTimes = telemetryData ? {
    s1: { time: telemetryData.bestSectorTimes?.[0]?.toFixed(1) || '--.-', status: 'normal' },
    s2: { time: telemetryData.bestSectorTimes?.[1]?.toFixed(1) || '--.-', status: 'normal' },
    s3: { time: telemetryData.bestSectorTimes?.[2]?.toFixed(1) || '--.-', status: 'normal' },
  } : {
    s1: { time: '--.-', status: 'normal' },
    s2: { time: '--.-', status: 'normal' },
    s3: { time: '--.-', status: 'normal' },
  };

  // Track info - could be enhanced by TrackRegistry data
  const trackInfo = {
    length: '--',
    corners: '--',
    drsZones: '--',
    lapRecord: '--',
  };

  // Conditions - waiting for telemetry
  const conditions = {
    trackTemp: telemetryData ? '42°C' : '--',
    airTemp: telemetryData ? '28°C' : '--',
    humidity: '--',
    wind: '--',
  };

  useEffect(() => {
    const wsService = webSocketService;

    const handleConnect = () => setConnected(true);
    const handleDisconnect = () => setConnected(false);
    const handleTelemetryUpdate = (data: TelemetryData | TelemetryData[]) => {
      const latest = Array.isArray(data) ? data[data.length - 1] : data;
      setTelemetryData(latest);
    };
    const handleSessionUpdate = (data: Partial<SessionInfo>) => {
      if (data.track) setTrackName(data.track);
    };

    const subConnect = wsService.on('connect', handleConnect);
    const subDisconnect = wsService.on('disconnect', handleDisconnect);
    const subTelemetry = wsService.on('telemetry', handleTelemetryUpdate);
    const subSession = wsService.on('session_info', handleSessionUpdate);

    if (wsService.isConnectedToServer()) {
      setConnected(true);
    } else {
      wsService.connect(BACKEND_URL);
    }

    return () => {
      subConnect.unsubscribe();
      subDisconnect.unsubscribe();
      subTelemetry.unsubscribe();
      subSession.unsubscribe();
    };
  }, []);

  return (
    <div className="track-map-page">
      <div className="track-map-header">
        <h1>🗺️ Track Map - {trackName}</h1>
        <div className="header-controls">
          <div className="track-selector">
            <label>Track:</label>
            <select value={trackName} onChange={(e) => setTrackName(e.target.value)}>
              <option value="Silverstone">Silverstone</option>
              <option value="Spa-Francorchamps">Spa-Francorchamps</option>
              <option value="Monza">Monza</option>
              <option value="Suzuka">Suzuka</option>
              <option value="Red Bull Ring">Red Bull Ring</option>
              <option value="Interlagos">Interlagos</option>
              <option value="Daytona">Daytona</option>
              <option value="Road America">Road America</option>
              <option value="Watkins Glen">Watkins Glen</option>
            </select>
          </div>
          <div className={`connection-badge ${connected ? 'connected' : ''}`}>
            <span className="dot"></span>
            {connected ? 'LIVE' : 'OFFLINE'}
          </div>
        </div>
      </div>

      <div className="track-map-content">
        {/* Map Container */}
        <div className="map-container">
          <TrackMap telemetryData={telemetryData} trackName={trackName} />

          {/* Legend */}
          <div className="map-legend">
            <h4>Legend</h4>
            <div className="legend-items">
              <div className="legend-item">
                <div className="legend-color" style={{ background: '#4a9eff' }}></div>
                <span>Your Position</span>
              </div>
              <div className="legend-item">
                <div className="legend-color" style={{ background: '#3dd68c' }}></div>
                <span>DRS Zone</span>
              </div>
              <div className="legend-item">
                <div className="legend-color" style={{ background: '#e6b422' }}></div>
                <span>Braking Zone</span>
              </div>
              <div className="legend-item">
                <div className="legend-color" style={{ background: '#a855f7' }}></div>
                <span>Fastest Sector</span>
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="track-sidebar">
          {/* Sector Times */}
          <div className="sidebar-section">
            <h3>Current Lap Sectors</h3>
            <div className="sector-times">
              <div className="sector-card">
                <div className="sector-label">S1</div>
                <div className={`sector-time ${sectorTimes.s1.status}`}>{sectorTimes.s1.time}</div>
              </div>
              <div className="sector-card">
                <div className="sector-label">S2</div>
                <div className={`sector-time ${sectorTimes.s2.status}`}>{sectorTimes.s2.time}</div>
              </div>
              <div className="sector-card">
                <div className="sector-label">S3</div>
                <div className={`sector-time ${sectorTimes.s3.status}`}>{sectorTimes.s3.time}</div>
              </div>
            </div>
          </div>

          <div className="sidebar-section">
            <h3>Positions</h3>
            <div className="driver-list">
              {sessionDrivers.length > 0 ? (
                sessionDrivers.map((driver: Driver) => (
                  <div key={driver.position} className={`driver-item ${driver.isYou ? 'you' : ''}`}>
                    <div className="driver-position">{driver.position}</div>
                    <div className="driver-info">
                      <div className="driver-name">{driver.name}</div>
                      <div className="driver-gap">{driver.gap}</div>
                    </div>
                    <div className="driver-speed">{driver.speed}</div>
                  </div>
                ))
              ) : (
                <div className="driver-item" style={{ opacity: 0.6, justifyContent: 'center' }}>
                  No session data
                </div>
              )}
            </div>
          </div>

          {/* Track Info */}
          <div className="sidebar-section">
            <h3>Track Info</h3>
            <div className="track-info-grid">
              <div className="info-card">
                <div className="info-label">Length</div>
                <div className="info-value">{trackInfo.length}</div>
              </div>
              <div className="info-card">
                <div className="info-label">Corners</div>
                <div className="info-value">{trackInfo.corners}</div>
              </div>
              <div className="info-card">
                <div className="info-label">DRS Zones</div>
                <div className="info-value">{trackInfo.drsZones}</div>
              </div>
              <div className="info-card">
                <div className="info-label">Lap Record</div>
                <div className="info-value">{trackInfo.lapRecord}</div>
              </div>
            </div>
          </div>

          {/* Conditions */}
          <div className="sidebar-section">
            <h3>Conditions</h3>
            <div className="conditions-grid">
              <div className="condition-card">
                <span className="condition-icon">🌡️</span>
                <div className="condition-data">
                  <div className="condition-label">Track</div>
                  <div className="condition-value">{conditions.trackTemp}</div>
                </div>
              </div>
              <div className="condition-card">
                <span className="condition-icon">🌤️</span>
                <div className="condition-data">
                  <div className="condition-label">Air</div>
                  <div className="condition-value">{conditions.airTemp}</div>
                </div>
              </div>
              <div className="condition-card">
                <span className="condition-icon">💧</span>
                <div className="condition-data">
                  <div className="condition-label">Humidity</div>
                  <div className="condition-value">{conditions.humidity}</div>
                </div>
              </div>
              <div className="condition-card">
                <span className="condition-icon">💨</span>
                <div className="condition-data">
                  <div className="condition-label">Wind</div>
                  <div className="condition-value">{conditions.wind}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TrackMapPage;
