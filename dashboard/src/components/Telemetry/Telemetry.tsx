import React from 'react';
import { TelemetryData } from '../../services/WebSocketService';

interface TelemetryProps {
  telemetryData: TelemetryData | null;
}

const Telemetry: React.FC<TelemetryProps> = ({ telemetryData }) => {
  if (!telemetryData) {
    return (
      <div className="panel telemetry-panel">
        <div className="panel-header">TELEMETRY DATA</div>
        <div className="panel-content">
          <div style={{ textAlign: 'center', padding: '2rem' }}>
            <div>No telemetry data available</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="panel telemetry-panel">
      <div className="panel-header">TELEMETRY DATA</div>
      <div className="panel-content">
        <div className="telemetry-grid">
          <div className="telemetry-item">
            <div className="telemetry-label">SPEED</div>
            <div className="telemetry-value">
              {Math.round(telemetryData.speed)}
              <span className="telemetry-unit">km/h</span>
            </div>
          </div>
          
          <div className="telemetry-item">
            <div className="telemetry-label">RPM</div>
            <div className="telemetry-value">
              {Math.round(telemetryData.rpm)}
            </div>
          </div>
          
          <div className="telemetry-item">
            <div className="telemetry-label">GEAR</div>
            <div className="telemetry-value">
              {telemetryData.gear === 0 ? 'N' : telemetryData.gear}
            </div>
          </div>
          
          <div className="telemetry-item">
            <div className="telemetry-label">LAP TIME</div>
            <div className="telemetry-value">
              {formatTime(telemetryData.lapTime)}
            </div>
          </div>
        </div>
        
        <div style={{ marginTop: '1rem' }}>
          <div className="section-title">INPUTS</div>
          <div className="telemetry-grid">
            <div className="telemetry-item">
              <div className="telemetry-label">THROTTLE</div>
              <div className="telemetry-value">
                {Math.round(telemetryData.throttle * 100)}%
              </div>
              <div className="telemetry-gauge">
                <div 
                  className="telemetry-gauge-fill throttle" 
                  style={{ width: `${telemetryData.throttle * 100}%` }}
                ></div>
              </div>
            </div>
            
            <div className="telemetry-item">
              <div className="telemetry-label">BRAKE</div>
              <div className="telemetry-value">
                {Math.round(telemetryData.brake * 100)}%
              </div>
              <div className="telemetry-gauge">
                <div 
                  className="telemetry-gauge-fill brake" 
                  style={{ width: `${telemetryData.brake * 100}%` }}
                ></div>
              </div>
            </div>
            
            <div className="telemetry-item">
              <div className="telemetry-label">STEERING</div>
              <div className="telemetry-value">
                {Math.round(telemetryData.steering * 100)}%
              </div>
              <div className="telemetry-gauge">
                <div 
                  className="telemetry-gauge-fill" 
                  style={{ width: `${Math.abs(telemetryData.steering) * 100}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>
        
        <div style={{ marginTop: '1rem' }}>
          <div className="section-title">TIRE DATA</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.5rem' }}>
              <TireDisplay 
                position="FL" 
                temp={telemetryData.tires.frontLeft.temp} 
                wear={telemetryData.tires.frontLeft.wear} 
                pressure={telemetryData.tires.frontLeft.pressure}
              />
              <TireDisplay 
                position="FR" 
                temp={telemetryData.tires.frontRight.temp} 
                wear={telemetryData.tires.frontRight.wear} 
                pressure={telemetryData.tires.frontRight.pressure}
              />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.5rem' }}>
              <TireDisplay 
                position="RL" 
                temp={telemetryData.tires.rearLeft.temp} 
                wear={telemetryData.tires.rearLeft.wear} 
                pressure={telemetryData.tires.rearLeft.pressure}
              />
              <TireDisplay 
                position="RR" 
                temp={telemetryData.tires.rearRight.temp} 
                wear={telemetryData.tires.rearRight.wear} 
                pressure={telemetryData.tires.rearRight.pressure}
              />
            </div>
          </div>
        </div>
        
        <div style={{ marginTop: '1rem' }}>
          <div className="section-title">VEHICLE DYNAMICS</div>
          <div className="telemetry-grid">
            <div className="telemetry-item">
              <div className="telemetry-label">G-FORCE LAT</div>
              <div className="telemetry-value">
                {telemetryData.gForce.lateral.toFixed(2)}G
              </div>
            </div>
            
            <div className="telemetry-item">
              <div className="telemetry-label">G-FORCE LONG</div>
              <div className="telemetry-value">
                {telemetryData.gForce.longitudinal.toFixed(2)}G
              </div>
            </div>
          </div>
        </div>
        
        <div style={{ marginTop: '1rem' }}>
          <div className="section-title">RACE POSITION</div>
          <div className="telemetry-grid">
            <div className="telemetry-item">
              <div className="telemetry-label">POSITION</div>
              <div className="telemetry-value">P{telemetryData.racePosition}</div>
            </div>
            
            <div className="telemetry-item">
              <div className="telemetry-label">GAP AHEAD</div>
              <div className="telemetry-value">
                {telemetryData.gapAhead > 0 ? `+${telemetryData.gapAhead.toFixed(2)}s` : '-'}
              </div>
            </div>
            
            <div className="telemetry-item">
              <div className="telemetry-label">GAP BEHIND</div>
              <div className="telemetry-value">
                {telemetryData.gapBehind > 0 ? `+${telemetryData.gapBehind.toFixed(2)}s` : '-'}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

interface TireDisplayProps {
  position: string;
  temp: number;
  wear: number;
  pressure: number;
}

const TireDisplay: React.FC<TireDisplayProps> = ({ position, temp, wear, pressure }) => {
  const getWearClass = (wear: number) => {
    if (wear > 80) return 'status-good';
    if (wear > 50) return 'status-warning';
    return 'status-critical';
  };
  
  const getTempClass = (temp: number) => {
    if (temp < 80) return 'status-critical';
    if (temp > 110) return 'status-critical';
    if (temp < 90 || temp > 105) return 'status-warning';
    return 'status-good';
  };

  return (
    <div style={{ 
      backgroundColor: 'rgba(22, 27, 34, 0.8)', 
      borderRadius: '4px',
      padding: '0.5rem',
      textAlign: 'center'
    }}>
      <div style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: '0.25rem' }}>
        {position}
      </div>
      <div style={{ fontSize: '0.8rem', marginBottom: '0.25rem' }}>
        <span className={getTempClass(temp)}>{Math.round(temp)}°C</span>
      </div>
      <div style={{ fontSize: '0.8rem', marginBottom: '0.25rem' }}>
        <span className={getWearClass(wear)}>{Math.round(wear)}%</span>
      </div>
      <div style={{ fontSize: '0.8rem' }}>
        {pressure.toFixed(1)} psi
      </div>
    </div>
  );
};

// Helper function to format time in mm:ss.SSS format
const formatTime = (timeInSeconds: number): string => {
  if (timeInSeconds <= 0) return '--:--.---';
  
  const minutes = Math.floor(timeInSeconds / 60);
  const seconds = Math.floor(timeInSeconds % 60);
  const milliseconds = Math.floor((timeInSeconds % 1) * 1000);
  
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}.${String(milliseconds).padStart(3, '0')}`;
};

export default Telemetry;
