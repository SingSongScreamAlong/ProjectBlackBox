import React, { useState, useEffect, useCallback } from 'react';
import { FiGrid, FiMap, FiBarChart2, FiActivity } from 'react-icons/fi';
import Track3DVisualization from '../Track3D/Track3DVisualization';
import TimingTower from '../TimingTower/TimingTower';
import TelemetryGraphs from '../Telemetry/TelemetryGraphs';
import TireStrategyVisualization from '../Strategy/TireStrategyVisualization';
import TrackMapGenerator from '../TrackMap/TrackMapGenerator';
import webSocketService, { TelemetryData, SessionInfo } from '../../services/WebSocketService';
import {
  TrackDataBuilder,
  TelemetryHistoryBuilder,
  StrategyDataBuilder,
  MultiDriverAggregator,
  determineTireCompound,
} from '../../adapters/visualizationDataAdapters';

type ViewMode = '3d-track' | 'timing' | 'telemetry' | 'strategy';

export const ProfessionalDashboard: React.FC = () => {
  const [viewMode, setViewMode] = useState<ViewMode>('3d-track');
  const [selectedDriverId, setSelectedDriverId] = useState<string | null>(null);
  const [connected, setConnected] = useState<boolean>(false);
  const [sessionInfo, setSessionInfo] = useState<SessionInfo | null>(null);

  // Data builders
  const [trackBuilder] = useState(() => new TrackDataBuilder());
  const [telemetryBuilder] = useState(() => new TelemetryHistoryBuilder());
  const [strategyBuilder] = useState(() => new StrategyDataBuilder());
  const [driverAggregator] = useState(() => new MultiDriverAggregator());

  // Visualization data states
  const [trackData, setTrackData] = useState<any[]>([]);
  const [drivers, setDrivers] = useState<any[]>([]);
  const [telemetryData, setTelemetryData] = useState<any[]>([]);
  const [timingData, setTimingData] = useState<any[]>([]);
  const [strategyData, setStrategyData] = useState<any[]>([]);
  const [currentLap, setCurrentLap] = useState(1);

  // Handle telemetry updates
  const handleTelemetryUpdate = useCallback((data: TelemetryData) => {
    // Update builders
    trackBuilder.addTelemetryPoint(data);
    telemetryBuilder.addTelemetryPoint(data);
    driverAggregator.updateDriver(data);
    strategyBuilder.updateCurrentLap(data.lap);

    // Update current lap
    setCurrentLap(data.lap);

    // Update visualization data
    setTrackData(trackBuilder.getTrackData());
    setDrivers(driverAggregator.getAllDriverPositions());
    setTelemetryData(telemetryBuilder.getTelemetryData());
    setTimingData(driverAggregator.getAllDriverTimings());

    // Update strategy data (simplified - would need pit stop detection)
    const driverStrategy = strategyBuilder.getDriverStrategy(
      data.driverId || 'player',
      data.driverName || 'Player',
      '#3b82f6'
    );
    setStrategyData([driverStrategy]);
  }, [trackBuilder, telemetryBuilder, driverAggregator, strategyBuilder]);

  // Handle session info updates
  const handleSessionUpdate = useCallback((data: Partial<SessionInfo>) => {
    setSessionInfo(prevState => ({
      ...(prevState || {
        track: '',
        session: '',
        driver: '',
        car: '',
        weather: {
          temperature: 0,
          trackTemperature: 0,
          windSpeed: 0,
          windDirection: '',
          humidity: 0,
          trackGrip: 0,
        },
        totalLaps: 0,
        sessionTime: 0,
        remainingTime: 0,
      }),
      ...data,
    }));
  }, []);

  // Initialize WebSocket connection
  useEffect(() => {
    const wsService = webSocketService;

    const handleConnect = () => {
      console.log('[ProfessionalDashboard] Connected to WebSocket');
      setConnected(true);
    };

    const handleDisconnect = () => {
      console.log('[ProfessionalDashboard] Disconnected from WebSocket');
      setConnected(false);
    };

    // Subscribe to events
    wsService.on('connect', handleConnect);
    wsService.on('disconnect', handleDisconnect);
    wsService.on('telemetry', handleTelemetryUpdate);
    wsService.on('session_info', handleSessionUpdate);

    // Connect to WebSocket (service handles duplicate connections)
    wsService.connect();

    return () => {
      // Cleanup subscriptions
      wsService.off('connect', handleConnect);
      wsService.off('disconnect', handleDisconnect);
      wsService.off('telemetry', handleTelemetryUpdate);
      wsService.off('session_info', handleSessionUpdate);
    };
  }, [handleTelemetryUpdate, handleSessionUpdate]);

  // Render main content based on view mode
  const renderMainContent = () => {
    if (trackData.length === 0 && drivers.length === 0) {
      return (
        <div
          className="glass-card"
          style={{
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexDirection: 'column',
            gap: '16px',
          }}
        >
          <div className={`status-dot ${connected ? 'online' : 'error'}`}></div>
          <h2 style={{ margin: 0 }}>
            {connected ? 'Waiting for telemetry data...' : 'Connecting to server...'}
          </h2>
          <p style={{ color: 'rgba(255, 255, 255, 0.5)', textAlign: 'center', maxWidth: '500px' }}>
            {connected
              ? 'Start a session in iRacing to see live visualization'
              : 'Establishing WebSocket connection...'}
          </p>
        </div>
      );
    }

    switch (viewMode) {
      case '3d-track':
        return (
          <div
            style={{
              height: '100%',
              display: 'grid',
              gridTemplateColumns: '3fr 1fr',
              gap: '16px',
            }}
          >
            <div style={{ height: '100%' }}>
              <Track3DVisualization
                trackData={trackData}
                drivers={drivers}
                isLive={connected}
              />
            </div>
            <div style={{ height: '100%', overflow: 'auto' }}>
              <TrackMapGenerator
                trackData={trackData}
                drivers={drivers.map((d) => ({
                  ...d,
                  distance: 0, // Would need track position
                }))}
                width={400}
                height={300}
                highlightedDriverId={selectedDriverId || undefined}
              />
            </div>
          </div>
        );

      case 'timing':
        return (
          <TimingTower
            drivers={timingData}
            showSectorTimes={true}
            showTireInfo={true}
            highlightedDriverId={selectedDriverId || undefined}
          />
        );

      case 'telemetry':
        return (
          <TelemetryGraphs
            data={telemetryData}
            driverName={drivers[0]?.driverName || 'Driver 1'}
            showSpeed={true}
            showThrottle={true}
            showBrake={true}
            showSteering={true}
            showGear={true}
            showRPM={true}
            height={200}
          />
        );

      case 'strategy':
        return (
          <TireStrategyVisualization
            strategies={strategyData}
            totalLaps={sessionInfo?.totalLaps || 50}
            currentLap={currentLap}
            highlightedDriverId={selectedDriverId || undefined}
          />
        );

      default:
        return null;
    }
  };

  return (
    <div
      className="racing-dashboard"
      style={{
        width: '100%',
        height: '100vh',
        background: 'linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%)',
        padding: '16px',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
      }}
    >
      {/* Header */}
      <div
        className="glass-card"
        style={{
          padding: '16px 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <h1 style={{ margin: 0, fontSize: '24px', fontWeight: 700 }}>
            ProjectBlackBox
          </h1>
          {connected && (
            <div className="live-indicator">LIVE</div>
          )}
        </div>

        {/* View Mode Selector */}
        <div
          style={{
            display: 'flex',
            gap: '8px',
            background: 'rgba(255, 255, 255, 0.05)',
            padding: '4px',
            borderRadius: '8px',
          }}
        >
          {[
            { mode: '3d-track' as ViewMode, label: '3D Track', icon: FiGrid },
            { mode: 'timing' as ViewMode, label: 'Timing', icon: FiActivity },
            {
              mode: 'telemetry' as ViewMode,
              label: 'Telemetry',
              icon: FiBarChart2,
            },
            { mode: 'strategy' as ViewMode, label: 'Strategy', icon: FiMap },
          ].map(({ mode, label, icon: Icon }) => (
            <button
              key={mode}
              onClick={() => setViewMode(mode)}
              className="btn-secondary"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 16px',
                background:
                  viewMode === mode
                    ? 'rgba(255, 255, 255, 0.15)'
                    : 'transparent',
                border:
                  viewMode === mode
                    ? '1px solid rgba(255, 255, 255, 0.3)'
                    : '1px solid transparent',
              }}
            >
              <Icon size={16} />
              <span>{label}</span>
            </button>
          ))}
        </div>

        {/* Session Info */}
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '12px', color: 'rgba(255, 255, 255, 0.5)' }}>
            {sessionInfo?.track || 'No Session'}
          </div>
          <div
            style={{
              fontSize: '14px',
              fontWeight: 600,
              fontFamily: 'monospace',
            }}
          >
            Lap {currentLap} / {sessionInfo?.totalLaps || '--'}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div
        style={{
          flex: 1,
          overflow: 'hidden',
        }}
      >
        {renderMainContent()}
      </div>

      {/* Footer Stats */}
      <div
        className="glass-card"
        style={{
          padding: '12px 24px',
          display: 'flex',
          gap: '32px',
          fontSize: '12px',
        }}
      >
        <div>
          <span style={{ color: 'rgba(255, 255, 255, 0.5)' }}>Drivers:</span>{' '}
          <span style={{ fontWeight: 700 }}>{drivers.length || 0}</span>
        </div>
        <div>
          <span style={{ color: 'rgba(255, 255, 255, 0.5)' }}>
            Track Points:
          </span>{' '}
          <span style={{ fontWeight: 700 }}>{trackData.length}</span>
        </div>
        <div>
          <span style={{ color: 'rgba(255, 255, 255, 0.5)' }}>
            Telemetry Samples:
          </span>{' '}
          <span style={{ fontWeight: 700 }}>{telemetryData.length}</span>
        </div>
        <div
          style={{
            marginLeft: 'auto',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <span className={`status-dot ${connected ? 'online' : 'error'}`}></span>
          <span style={{ color: 'rgba(255, 255, 255, 0.7)' }}>
            {connected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>
    </div>
  );
};

export default ProfessionalDashboard;
