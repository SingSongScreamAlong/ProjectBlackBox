import React from 'react';
import { TelemetryData } from '../../services/WebSocketService';

import './TelemetryCockpit.css';

interface TelemetryProps {
  telemetryData: TelemetryData | null;
}

const Telemetry: React.FC<TelemetryProps> = ({ telemetryData }) => {
  // Show zero-state UI when no telemetry data
  const data = telemetryData || {
    throttle: 0,
    brake: 0,
    clutch: 0,
    speed: 0,
    rpm: 0,
    gear: 0,
    lapTime: 0,
    bestLapTime: 0,
    deltaToBestLap: 0,
    gapAhead: 0,
    gapBehind: 0,
    racePosition: 0,
    flags: 0,
    tires: {
      frontLeft: { temp: 0, wear: 0, pressure: 0 },
      frontRight: { temp: 0, wear: 0, pressure: 0 },
      rearLeft: { temp: 0, wear: 0, pressure: 0 },
      rearRight: { temp: 0, wear: 0, pressure: 0 },
    },
    fuel: { level: 0, usagePerHour: 0, remaining: 0 },
    carSettings: { brakeBias: 0, fuelMixture: 0, tractionControl: 0, abs: 0 },
    energy: { batteryPct: 0 },
    gForce: { lateral: 0, longitudinal: 0 },
    weather: { windSpeed: 0 }
  };

  // Helpers
  const isGreenFlag = (data.flags || 0) === 0;
  const delta = data.deltaToBestLap || 0;
  const deltaColor = delta < 0 ? 'delta-neg' : 'delta-pos'; // Green if negative (faster)
  const rpmPct = Math.min(100, Math.max(0, (data.rpm / 14000) * 100)); // Assuming 14k max for now
  const isRedline = rpmPct > 95;
  const rpmColor = isRedline ? '#ff3b3b' : (rpmPct > 80 ? '#ffd700' : '#00d4ff');

  return (
    <div className="cockpit-container">
      {/* --- LEFT COLUMN: VEHICLE STATUS --- */}
      <div className="cockpit-column">
        {/* Tires */}
        <div className="cockpit-card">
          <div className="cockpit-card-title">Tires (Temp/Wear)</div>
          <div className="tire-box">
            <TireDisplay position="FL" {...data.tires.frontLeft} />
            <TireDisplay position="FR" {...data.tires.frontRight} />
            <TireDisplay position="RL" {...data.tires.rearLeft} />
            <TireDisplay position="RR" {...data.tires.rearRight} />
          </div>
        </div>

        {/* Car Settings Grid */}
        <div className="cockpit-card">
          <div className="cockpit-card-title">Settings</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', textAlign: 'center' }}>
            <div>
              <div style={{ fontSize: '9px', color: '#888' }}>BRAKE BIAS</div>
              <div style={{ fontSize: '16px', fontWeight: 'bold' }}>{data.carSettings?.brakeBias?.toFixed(1) ?? '-'}%</div>
            </div>
            <div>
              <div style={{ fontSize: '9px', color: '#888' }}>FUEL MAP</div>
              <div style={{ fontSize: '16px', fontWeight: 'bold' }}>{data.carSettings?.fuelMixture ?? '-'}</div>
            </div>
            <div>
              <div style={{ fontSize: '9px', color: '#888' }}>TC</div>
              <div style={{ fontSize: '16px', fontWeight: 'bold' }}>{data.carSettings?.tractionControl ?? '-'}</div>
            </div>
            <div>
              <div style={{ fontSize: '9px', color: '#888' }}>ABS</div>
              <div style={{ fontSize: '16px', fontWeight: 'bold' }}>{data.carSettings?.abs ?? '-'}</div>
            </div>
          </div>
        </div>

        {/* Fuel */}
        <div className="cockpit-card">
          <div className="cockpit-card-title">Fuel</div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
            <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{data.fuel?.level?.toFixed(1) ?? '0.0'} <span style={{ fontSize: '12px', color: '#666' }}>L</span></div>
            <div style={{ fontSize: '12px', color: '#888' }}>Est. Laps: {data.fuel?.usagePerHour ? (data.fuel.level / (data.fuel.usagePerHour / 3600 * data.lapTime)).toFixed(1) : '-'}</div>
          </div>
        </div>
      </div>

      {/* --- CENTER COLUMN: DRIVING --- */}
      <div className="cockpit-column">
        {/* Flag Status */}
        <div className={`flag-banner ${isGreenFlag ? 'flag-green' : 'flag-yellow'}`}>
          {isGreenFlag ? 'GREEN FLAG' : 'CAUTION / YELLOW'}
        </div>

        {/* Main Dash */}
        <div className="cockpit-card center-dash">
          <div className={`gear-display ${isRedline ? 'redline' : ''}`}>
            {data.gear === 0 ? 'N' : (data.gear === -1 ? 'R' : data.gear)}
          </div>
          <div className="speed-display">
            {Math.round(data.speed)}<span className="speed-unit">KM/H</span>
          </div>

          {/* RPM Bar */}
          <div className="rpm-bar-container">
            <div
              className="rpm-bar-fill"
              style={{
                width: `${rpmPct}%`,
                backgroundColor: rpmColor
              }}
            />
          </div>
          <div style={{ marginTop: '4px', fontSize: '12px', color: '#666', width: '100%', display: 'flex', justifyContent: 'space-between' }}>
            <span>0</span>
            <span>{Math.round(data.rpm)}</span>
            <span>14000</span>
          </div>
        </div>

        {/* ERS / Boost */}
        <div className="cockpit-card">
          <div className="cockpit-card-title">Hybrid Energy</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ flex: 1, background: '#333', height: '8px', borderRadius: '4px' }}>
              <div style={{ width: `${(data.energy?.batteryPct || 0) * 100}%`, background: '#4caf50', height: '100%', borderRadius: '4px' }} />
            </div>
            <div style={{ fontWeight: 'bold' }}>{Math.round((data.energy?.batteryPct || 0) * 100)}%</div>
          </div>
        </div>

        {/* Inputs (Thin bar) */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '4px' }}>
          <InputBar label="THR" value={data.throttle} color="#00ff9d" />
          <InputBar label="BRK" value={data.brake} color="#ff3b3b" />
          <InputBar label="CLT" value={data.clutch} color="#e2e2e2" />
        </div>
      </div>

      {/* --- RIGHT COLUMN: TIMING --- */}
      <div className="cockpit-column">
        {/* Delta */}
        <div className="cockpit-card">
          <div className="cockpit-card-title">Delta to Best</div>
          <div className={`delta-display ${deltaColor}`}>
            {delta > 0 ? '+' : ''}{delta.toFixed(2)}
          </div>
        </div>

        {/* Timing List */}
        <div className="cockpit-card">
          <div className="cockpit-card-title">Timing</div>

          <div className="timing-row">
            <span className="timing-label">CURRENT LAP</span>
            <span className="timing-value highlight">{formatTime(data.lapTime)}</span>
          </div>
          <div className="timing-row">
            <span className="timing-label">BEST LAP</span>
            <span className="timing-value">{formatTime(data.bestLapTime)}</span>
          </div>
          <div className="timing-row">
            <span className="timing-label">GAP AHEAD</span>
            <span className="timing-value">{data.gapAhead > 0 ? `+${data.gapAhead.toFixed(1)}` : '-'}</span>
          </div>
          <div className="timing-row">
            <span className="timing-label">GAP BEHIND</span>
            <span className="timing-value">{data.gapBehind > 0 ? `+${data.gapBehind.toFixed(1)}` : '-'}</span>
          </div>
          <div className="timing-row">
            <span className="timing-label">POSITION</span>
            <span className="timing-value" style={{ color: 'var(--accent-color)' }}>P{data.racePosition}</span>
          </div>
        </div>

        {/* Weather / G-Force */}
        <div className="cockpit-card">
          <div className="cockpit-card-title">Environment</div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '18px', fontWeight: 'bold' }}>{(data.weather?.windSpeed ?? 0).toFixed(1)}</div>
              <div style={{ fontSize: '9px', color: '#666' }}>Wind (m/s)</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '18px', fontWeight: 'bold' }}>{data.gForce?.lateral?.toFixed(1) ?? '0.0'}</div>
              <div style={{ fontSize: '9px', color: '#666' }}>Lat G</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '18px', fontWeight: 'bold' }}>{data.gForce?.longitudinal?.toFixed(1) ?? '0.0'}</div>
              <div style={{ fontSize: '9px', color: '#666' }}>Long G</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Sub-components for cleaner code
const InputBar: React.FC<{ label: string; value: number; color: string }> = ({ label, value, color }) => (
  <div style={{ background: 'rgba(0,0,0,0.3)', borderRadius: '4px', height: '40px', position: 'relative', overflow: 'hidden' }}>
    <div style={{ position: 'absolute', bottom: 0, left: 0, width: '100%', height: `${value * 100}%`, background: color, transition: 'height 0.05s' }} />
    <div style={{ position: 'absolute', bottom: 2, left: 0, width: '100%', textAlign: 'center', fontSize: '10px', fontWeight: 'bold', textShadow: '0 1px 2px black', color: '#fff' }}>{label}</div>
  </div>
);

interface TireDisplayProps {
  position: string;
  temp: number;
  wear: number;
  pressure: number;
}

const TireDisplay: React.FC<TireDisplayProps> = ({ position, temp, wear, pressure }) => {
  const getTempClass = (t: number) => {
    if (t < 80 || t > 110) return 'color: #ff3b3b'; // Critical
    return 'color: #fff';
  };

  return (
    <div style={{ background: '#161b22', borderRadius: '4px', padding: '6px', textAlign: 'center', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
      <div style={{ fontSize: '10px', fontWeight: 'bold', color: '#666', marginBottom: '2px' }}>{position}</div>
      <div style={{ fontSize: '14px', fontWeight: 'bold', color: temp > 105 ? '#ff3b3b' : '#fff' }}>{Math.round(temp)}°</div>
      <div style={{ fontSize: '10px', color: parseInt(String(wear)) < 50 ? '#ffd700' : '#888' }}>{Math.round(wear)}%</div>
    </div>
  );
};

// Helper function to format time in mm:ss.SSS format
const formatTime = (timeInSeconds: number): string => {
  if (timeInSeconds <= 0) return '--:--.---';
  const minutes = Math.floor(timeInSeconds / 60);
  const seconds = Math.floor(timeInSeconds % 60);
  const milliseconds = Math.floor((timeInSeconds % 1) * 1000);
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}.${String(milliseconds).padStart(1, '0')}`;
};

export default Telemetry;
