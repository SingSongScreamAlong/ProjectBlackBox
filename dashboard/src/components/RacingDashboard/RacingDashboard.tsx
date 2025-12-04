import React, { useState, useEffect } from 'react';
import Track3DVisualization from '../Track3D/Track3DVisualization';
import TimingTower from '../TimingTower/TimingTower';
import TelemetryGraphs from '../Telemetry/TelemetryGraphs';
import TireStrategyVisualization from '../Strategy/TireStrategyVisualization';
import TrackMapGenerator from '../TrackMap/TrackMapGenerator';
import { FiGrid, FiMap, FiBarChart2, FiActivity } from 'react-icons/fi';
import '../../styles/professional-racing-theme.css';

type ViewMode = '3d-track' | 'timing' | 'telemetry' | 'strategy';

interface RacingDashboardProps {
  sessionId?: string;
  isLive?: boolean;
}

export const RacingDashboard: React.FC<RacingDashboardProps> = ({
  sessionId,
  isLive = true,
}) => {
  const [viewMode, setViewMode] = useState<ViewMode>('3d-track');
  const [selectedDriverId, setSelectedDriverId] = useState<string | null>(null);

  // Mock data - In production, this would come from WebSocket/API
  const [trackData, setTrackData] = useState<any[]>([]);
  const [drivers, setDrivers] = useState<any[]>([]);
  const [telemetryData, setTelemetryData] = useState<any[]>([]);
  const [strategyData, setStrategyData] = useState<any[]>([]);

  useEffect(() => {
    // TODO: Connect to WebSocket service for real-time data
    // Example: WebSocketService.subscribe('telemetry', handleTelemetryUpdate);

    // Mock data generation for demonstration
    generateMockData();

    return () => {
      // TODO: Cleanup WebSocket subscriptions
    };
  }, [sessionId]);

  const generateMockData = () => {
    // Generate mock track (oval for demonstration)
    const mockTrack = generateOvalTrack(500, 200, 1000);
    setTrackData(mockTrack);

    // Generate mock drivers
    const mockDrivers = [
      {
        driverId: '1',
        driverName: 'Max Verstappen',
        driverNumber: '1',
        position: 1,
        teamName: 'Red Bull Racing',
        teamColor: '#0600ef',
        x: mockTrack[0]?.x || 0,
        y: mockTrack[0]?.y || 0,
        z: 0,
        speed: 285,
        lastLapTime: 87234,
        bestLapTime: 85123,
        gap: 'LEADER',
        interval: undefined,
        sectorTimes: {
          sector1: 25123,
          sector2: 28456,
          sector3: 31655,
          sector1Status: 'fastest',
          sector2Status: 'personal-best',
          sector3Status: 'normal',
        },
        currentSector: 1,
        pitStops: 1,
        tireCompound: 'SOFT' as const,
        tireLaps: 12,
        positionChange: 0,
        isInPit: false,
        isRetired: false,
      },
      {
        driverId: '2',
        driverName: 'Lewis Hamilton',
        driverNumber: '44',
        position: 2,
        teamName: 'Mercedes',
        teamColor: '#00d2be',
        x: mockTrack[50]?.x || 0,
        y: mockTrack[50]?.y || 0,
        z: 0,
        speed: 283,
        lastLapTime: 87856,
        bestLapTime: 85678,
        gap: 2.345,
        interval: 2.345,
        sectorTimes: {
          sector1: 25456,
          sector2: 28234,
          sector3: 32166,
          sector1Status: 'personal-best',
          sector2Status: 'fastest',
          sector3Status: 'normal',
        },
        currentSector: 2,
        pitStops: 1,
        tireCompound: 'MEDIUM' as const,
        tireLaps: 18,
        positionChange: 1,
        isInPit: false,
        isRetired: false,
      },
      {
        driverId: '3',
        driverName: 'Charles Leclerc',
        driverNumber: '16',
        position: 3,
        teamName: 'Ferrari',
        teamColor: '#dc0000',
        x: mockTrack[100]?.x || 0,
        y: mockTrack[100]?.y || 0,
        z: 0,
        speed: 281,
        lastLapTime: 88123,
        bestLapTime: 86234,
        gap: 5.678,
        interval: 3.333,
        sectorTimes: {
          sector1: 25789,
          sector2: 28567,
          sector3: 31767,
          sector1Status: 'normal',
          sector2Status: 'personal-best',
          sector3Status: 'fastest',
        },
        currentSector: 3,
        pitStops: 1,
        tireCompound: 'HARD' as const,
        tireLaps: 24,
        positionChange: -1,
        isInPit: false,
        isRetired: false,
      },
    ];

    setDrivers(mockDrivers);

    // Generate mock telemetry
    const mockTelemetry = Array.from({ length: 1000 }, (_, i) => ({
      timestamp: i * 100,
      distance: i,
      speed: 200 + Math.sin(i / 50) * 80 + Math.random() * 20,
      throttle: Math.max(0, Math.min(100, 80 + Math.sin(i / 30) * 30)),
      brake: Math.max(0, Math.sin(i / 40) > 0.5 ? Math.random() * 100 : 0),
      steering: Math.sin(i / 20) * 45,
      gear: Math.floor(2 + Math.sin(i / 50) * 3),
      rpm: 8000 + Math.sin(i / 30) * 4000,
    }));

    setTelemetryData(mockTelemetry);

    // Generate mock strategy
    const mockStrategy = mockDrivers.map((driver) => ({
      driverId: driver.driverId,
      driverName: driver.driverName,
      driverNumber: driver.driverNumber,
      teamColor: driver.teamColor,
      totalPitStops: 1,
      predictedStops: 2,
      stints: [
        {
          compound: 'MEDIUM' as const,
          startLap: 1,
          endLap: 20,
          lapCount: 20,
          degradation: 45,
          isCurrentStint: false,
        },
        {
          compound: driver.tireCompound,
          startLap: 21,
          endLap: 50,
          lapCount: 30,
          degradation: 40,
          isCurrentStint: true,
        },
      ],
      pitStops: [
        {
          lap: 20,
          duration: 2.4,
          reason: 'tire-change' as const,
          oldCompound: 'MEDIUM' as const,
          newCompound: driver.tireCompound,
        },
      ],
    }));

    setStrategyData(mockStrategy);
  };

  const generateOvalTrack = (
    width: number,
    height: number,
    points: number
  ): any[] => {
    const track = [];
    for (let i = 0; i < points; i++) {
      const angle = (i / points) * Math.PI * 2;
      const x = Math.cos(angle) * width;
      const y = Math.sin(angle) * height;
      const sectorIndex = Math.floor((i / points) * 3);

      track.push({
        x,
        y,
        z: 0,
        distance: i,
        sectorIndex,
      });
    }
    return track;
  };

  const renderMainContent = () => {
    switch (viewMode) {
      case '3d-track':
        return (
          <div style={{ height: '100%', display: 'grid', gridTemplateColumns: '3fr 1fr', gap: '16px' }}>
            <div style={{ height: '100%' }}>
              <Track3DVisualization
                trackData={trackData}
                drivers={drivers.map(d => ({
                  driverId: d.driverId,
                  driverName: d.driverName,
                  position: d.position,
                  x: d.x,
                  y: d.y,
                  z: d.z,
                  speed: d.speed,
                  teamColor: d.teamColor,
                }))}
                isLive={isLive}
              />
            </div>
            <div style={{ height: '100%', overflow: 'auto' }}>
              <TrackMapGenerator
                trackData={trackData}
                drivers={drivers.map(d => ({
                  driverId: d.driverId,
                  driverName: d.driverName,
                  driverNumber: d.driverNumber,
                  position: d.position,
                  teamColor: d.teamColor,
                  x: d.x,
                  y: d.y,
                  distance: d.distance || 0,
                  speed: d.speed,
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
            drivers={drivers}
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
            totalLaps={50}
            currentLap={35}
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
          {isLive && <div className="live-indicator">LIVE</div>}
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
            { mode: 'telemetry' as ViewMode, label: 'Telemetry', icon: FiBarChart2 },
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
            Session ID
          </div>
          <div style={{ fontSize: '14px', fontWeight: 600, fontFamily: 'monospace' }}>
            {sessionId || 'N/A'}
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
          <span style={{ fontWeight: 700 }}>{drivers.length}</span>
        </div>
        <div>
          <span style={{ color: 'rgba(255, 255, 255, 0.5)' }}>Track Points:</span>{' '}
          <span style={{ fontWeight: 700 }}>{trackData.length}</span>
        </div>
        <div>
          <span style={{ color: 'rgba(255, 255, 255, 0.5)' }}>
            Telemetry Samples:
          </span>{' '}
          <span style={{ fontWeight: 700 }}>{telemetryData.length}</span>
        </div>
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span className="status-dot online"></span>
          <span style={{ color: 'rgba(255, 255, 255, 0.7)' }}>Connected</span>
        </div>
      </div>
    </div>
  );
};

export default RacingDashboard;
