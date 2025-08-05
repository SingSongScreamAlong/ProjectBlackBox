import React from 'react';
import { TelemetryData } from '../../services/WebSocketService';

interface TrackMapProps {
  telemetryData: TelemetryData | null;
  trackName?: string;
}

interface Corner {
  id: string;
  name: string;
  x: number;
  y: number;
  coordinates: string;
}

interface SpeedZone {
  type: 'high' | 'medium' | 'low';
  top: string;
  left: string;
  width: string;
  height: string;
}

const TrackMap: React.FC<TrackMapProps> = ({ telemetryData, trackName = 'Unknown Track' }) => {
  // Sample corners for Silverstone (would be loaded dynamically based on track)
  const corners: Corner[] = [
    { id: 'T1', name: 'Abbey', x: 25, y: 15, coordinates: '(150,42)' },
    { id: 'T3', name: 'Village', x: 15, y: 25, coordinates: '(90,70)' },
    { id: 'T4', name: 'Loop', x: 10, y: 45, coordinates: '(60,126)' },
    { id: 'T5', name: 'Luffield', x: 15, y: 65, coordinates: '(90,182)' },
    { id: 'T6', name: 'Club', x: 35, y: 80, coordinates: '(210,224)' },
    { id: 'T7', name: 'Vale', x: 75, y: 75, coordinates: '(450,210)' },
    { id: 'T8', name: 'Stowe', x: 85, y: 55, coordinates: '(510,154)' },
    { id: 'T9', name: 'Becketts', x: 75, y: 35, coordinates: '(450,98)' },
    { id: 'T10', name: 'Maggotts', x: 65, y: 25, coordinates: '(390,70)' },
    { id: 'T11', name: 'Copse', x: 55, y: 15, coordinates: '(330,42)' },
  ];

  // Sample speed zones
  const speedZones: SpeedZone[] = [
    { type: 'high', top: '10%', left: '20%', width: '60%', height: '15%' },
    { type: 'medium', top: '30%', left: '70%', width: '25%', height: '40%' },
    { type: 'low', top: '40%', left: '5%', width: '20%', height: '25%' },
    { type: 'high', top: '70%', left: '25%', width: '50%', height: '15%' },
  ];

  // Calculate car position (in a real implementation, this would be based on telemetry)
  const carPosition = telemetryData ? {
    x: 75, // This would be calculated from telemetryData.position
    y: 35  // This would be calculated from telemetryData.position
  } : { x: 0, y: 0 };

  // Format sector time
  const formatSectorTime = (time: number | undefined): string => {
    if (!time || time <= 0) return '---.---';
    return `${time.toFixed(3)}s`;
  };

  // Calculate delta class
  const getDeltaClass = (delta: number): string => {
    if (delta < 0) return 'status-good';
    if (delta > 0.5) return 'status-critical';
    return 'status-warning';
  };

  return (
    <div className="panel track-map-panel">
      <div className="panel-header">{trackName.toUpperCase()} - SECTOR 2 (BECKETTS COMPLEX)</div>
      <div className="track-container">
        <div className="track-map">
          {/* Grid overlay */}
          <div className="grid-overlay"></div>
          
          {/* Grid coordinates */}
          <div className="grid-coords" style={{ top: '5px', left: '5px' }}>X:0 Y:0</div>
          <div className="grid-coords" style={{ top: '5px', right: '5px' }}>X:600 Y:0</div>
          <div className="grid-coords" style={{ bottom: '50px', left: '5px' }}>X:0 Y:280</div>
          <div className="grid-coords" style={{ bottom: '50px', right: '5px' }}>X:600 Y:280</div>
          
          {/* Speed zones */}
          {speedZones.map((zone, index) => (
            <div 
              key={`zone-${index}`}
              className={`speed-zone ${zone.type}`} 
              style={{ 
                top: zone.top, 
                left: zone.left, 
                width: zone.width, 
                height: zone.height 
              }}
            ></div>
          ))}
          
          {/* Track outline (would be a SVG in a real implementation) */}
          <div className="track-outline"></div>
          
          {/* Corner markers */}
          {corners.map(corner => (
            <React.Fragment key={corner.id}>
              <div 
                className="corner-marker" 
                style={{ top: `${corner.y}%`, left: `${corner.x}%` }}
              ></div>
              <div 
                className="corner-label" 
                style={{ 
                  top: `${corner.y - 7}%`, 
                  left: `${corner.x - 7}%` 
                }}
              >
                {corner.id} {corner.name} {corner.coordinates}
              </div>
            </React.Fragment>
          ))}
          
          {/* Car position */}
          {telemetryData && (
            <div 
              className="car-position" 
              style={{ top: `${carPosition.y}%`, left: `${carPosition.x}%` }} 
              title={`Car Position: X:${carPosition.x * 6} Y:${carPosition.y * 2.8}`}
            ></div>
          )}
          
          {/* Track info */}
          <div className="track-info">
            <div className="track-info-item">
              <div className="track-info-label">Position</div>
              <div className="track-info-value">
                {telemetryData 
                  ? `X:${carPosition.x * 6} Y:${carPosition.y * 2.8}` 
                  : 'No Data'
                }
              </div>
            </div>
            <div className="track-info-item">
              <div className="track-info-label">Sector 2</div>
              <div className="track-info-value">
                {telemetryData 
                  ? formatSectorTime(telemetryData.sectorTime)
                  : '---'
                }
              </div>
            </div>
            <div className="track-info-item">
              <div className="track-info-label">Best S2</div>
              <div className="track-info-value">
                {telemetryData && telemetryData.bestSectorTimes && telemetryData.bestSectorTimes[1] 
                  ? formatSectorTime(telemetryData.bestSectorTimes[1])
                  : '---'
                }
              </div>
            </div>
            <div className="track-info-item">
              <div className="track-info-label">Delta</div>
              <div className={`track-info-value ${
                telemetryData && telemetryData.bestSectorTimes && telemetryData.bestSectorTimes[1] && telemetryData.sectorTime
                  ? getDeltaClass(telemetryData.sectorTime - telemetryData.bestSectorTimes[1])
                  : ''
              }`}>
                {telemetryData && telemetryData.bestSectorTimes && telemetryData.bestSectorTimes[1] && telemetryData.sectorTime
                  ? `${telemetryData.sectorTime > telemetryData.bestSectorTimes[1] ? '+' : ''}${
                      (telemetryData.sectorTime - telemetryData.bestSectorTimes[1]).toFixed(3)
                    }s`
                  : '---'
                }
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TrackMap;
