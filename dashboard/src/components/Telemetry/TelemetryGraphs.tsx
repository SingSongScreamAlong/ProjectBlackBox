import React, { useMemo } from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';

export interface TelemetryDataPoint {
  timestamp: number;
  distance: number;
  speed: number;
  throttle: number;
  brake: number;
  steering: number;
  gear: number;
  rpm: number;
  lapTime?: number;
  sector?: number;
}

interface TelemetryGraphsProps {
  data: TelemetryDataPoint[];
  comparisonData?: TelemetryDataPoint[];
  driverName?: string;
  comparisonDriverName?: string;
  showSpeed?: boolean;
  showThrottle?: boolean;
  showBrake?: boolean;
  showSteering?: boolean;
  showGear?: boolean;
  showRPM?: boolean;
  height?: number;
  className?: string;
}

export const TelemetryGraphs: React.FC<TelemetryGraphsProps> = ({
  data,
  comparisonData,
  driverName = 'Driver',
  comparisonDriverName = 'Comparison',
  showSpeed = true,
  showThrottle = true,
  showBrake = true,
  showSteering = true,
  showGear = false,
  showRPM = false,
  height = 250,
  className = '',
}) => {
  // Merge data for synchronized display
  const mergedData = useMemo(() => {
    if (!comparisonData) return data;

    const merged = data.map((point, index) => ({
      ...point,
      comparisonSpeed: comparisonData[index]?.speed,
      comparisonThrottle: comparisonData[index]?.throttle,
      comparisonBrake: comparisonData[index]?.brake,
      comparisonSteering: comparisonData[index]?.steering,
    }));

    return merged;
  }, [data, comparisonData]);

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload || payload.length === 0) return null;

    return (
      <div
        style={{
          background: 'rgba(0, 0, 0, 0.9)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          borderRadius: '8px',
          padding: '12px',
          minWidth: '200px',
        }}
      >
        <p
          style={{
            color: 'white',
            fontSize: '12px',
            fontWeight: 600,
            marginBottom: '8px',
          }}
        >
          Distance: {label.toFixed(0)}m
        </p>
        {payload.map((entry: any, index: number) => (
          <p
            key={index}
            style={{
              color: entry.color,
              fontSize: '11px',
              margin: '4px 0',
              display: 'flex',
              justifyContent: 'space-between',
              gap: '12px',
            }}
          >
            <span>{entry.name}:</span>
            <span style={{ fontWeight: 700 }}>
              {typeof entry.value === 'number' ? entry.value.toFixed(2) : '--'}
            </span>
          </p>
        ))}
      </div>
    );
  };

  const chartMargin = { top: 10, right: 30, left: 0, bottom: 0 };

  return (
    <div
      className={`telemetry-graphs ${className}`}
      style={{
        background: 'rgba(0, 0, 0, 0.85)',
        backdropFilter: 'blur(20px)',
        borderRadius: '12px',
        padding: '16px',
      }}
    >
      {/* Header */}
      <div
        style={{
          marginBottom: '16px',
          paddingBottom: '12px',
          borderBottom: '2px solid rgba(255, 255, 255, 0.1)',
        }}
      >
        <h2
          style={{
            color: 'white',
            fontSize: '18px',
            fontWeight: 700,
            letterSpacing: '1px',
            margin: 0,
          }}
        >
          TELEMETRY ANALYSIS
        </h2>
        {comparisonData && (
          <div
            style={{
              display: 'flex',
              gap: '16px',
              marginTop: '8px',
              fontSize: '12px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div
                style={{
                  width: '12px',
                  height: '3px',
                  background: '#3b82f6',
                  borderRadius: '2px',
                }}
              />
              <span style={{ color: 'rgba(255, 255, 255, 0.7)' }}>{driverName}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div
                style={{
                  width: '12px',
                  height: '3px',
                  background: '#ef4444',
                  borderRadius: '2px',
                }}
              />
              <span style={{ color: 'rgba(255, 255, 255, 0.7)' }}>
                {comparisonDriverName}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Speed Graph */}
      {showSpeed && (
        <div
          style={{
            marginBottom: '24px',
          }}
        >
          <h3
            style={{
              color: 'white',
              fontSize: '14px',
              fontWeight: 600,
              marginBottom: '8px',
              letterSpacing: '0.5px',
            }}
          >
            SPEED (km/h)
          </h3>
          <ResponsiveContainer width="100%" height={height}>
            <LineChart data={mergedData} margin={chartMargin}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis
                dataKey="distance"
                stroke="rgba(255,255,255,0.5)"
                style={{ fontSize: '11px' }}
                label={{ value: 'Distance (m)', position: 'insideBottom', offset: -5 }}
              />
              <YAxis
                stroke="rgba(255,255,255,0.5)"
                style={{ fontSize: '11px' }}
                domain={[0, 'auto']}
              />
              <Tooltip content={<CustomTooltip />} />
              <Line
                type="monotone"
                dataKey="speed"
                name={driverName}
                stroke="#3b82f6"
                strokeWidth={2}
                dot={false}
                animationDuration={300}
              />
              {comparisonData && (
                <Line
                  type="monotone"
                  dataKey="comparisonSpeed"
                  name={comparisonDriverName}
                  stroke="#ef4444"
                  strokeWidth={2}
                  dot={false}
                  strokeDasharray="5 5"
                  animationDuration={300}
                />
              )}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Throttle & Brake Graph (Combined) */}
      {(showThrottle || showBrake) && (
        <div
          style={{
            marginBottom: '24px',
          }}
        >
          <h3
            style={{
              color: 'white',
              fontSize: '14px',
              fontWeight: 600,
              marginBottom: '8px',
              letterSpacing: '0.5px',
            }}
          >
            THROTTLE & BRAKE (%)
          </h3>
          <ResponsiveContainer width="100%" height={height}>
            <AreaChart data={mergedData} margin={chartMargin}>
              <defs>
                <linearGradient id="throttleGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#22c55e" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#22c55e" stopOpacity={0.1} />
                </linearGradient>
                <linearGradient id="brakeGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0.1} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis
                dataKey="distance"
                stroke="rgba(255,255,255,0.5)"
                style={{ fontSize: '11px' }}
              />
              <YAxis
                stroke="rgba(255,255,255,0.5)"
                style={{ fontSize: '11px' }}
                domain={[0, 100]}
              />
              <Tooltip content={<CustomTooltip />} />
              <ReferenceLine y={100} stroke="rgba(255,255,255,0.2)" strokeDasharray="3 3" />
              {showThrottle && (
                <Area
                  type="monotone"
                  dataKey="throttle"
                  name="Throttle"
                  stroke="#22c55e"
                  strokeWidth={2}
                  fill="url(#throttleGradient)"
                  animationDuration={300}
                />
              )}
              {showBrake && (
                <Area
                  type="monotone"
                  dataKey="brake"
                  name="Brake"
                  stroke="#ef4444"
                  strokeWidth={2}
                  fill="url(#brakeGradient)"
                  animationDuration={300}
                />
              )}
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Steering Graph */}
      {showSteering && (
        <div
          style={{
            marginBottom: '24px',
          }}
        >
          <h3
            style={{
              color: 'white',
              fontSize: '14px',
              fontWeight: 600,
              marginBottom: '8px',
              letterSpacing: '0.5px',
            }}
          >
            STEERING ANGLE (°)
          </h3>
          <ResponsiveContainer width="100%" height={height}>
            <LineChart data={mergedData} margin={chartMargin}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis
                dataKey="distance"
                stroke="rgba(255,255,255,0.5)"
                style={{ fontSize: '11px' }}
              />
              <YAxis
                stroke="rgba(255,255,255,0.5)"
                style={{ fontSize: '11px' }}
                domain={[-90, 90]}
              />
              <Tooltip content={<CustomTooltip />} />
              <ReferenceLine y={0} stroke="rgba(255,255,255,0.3)" />
              <Line
                type="monotone"
                dataKey="steering"
                name={driverName}
                stroke="#a855f7"
                strokeWidth={2}
                dot={false}
                animationDuration={300}
              />
              {comparisonData && (
                <Line
                  type="monotone"
                  dataKey="comparisonSteering"
                  name={comparisonDriverName}
                  stroke="#f59e0b"
                  strokeWidth={2}
                  dot={false}
                  strokeDasharray="5 5"
                  animationDuration={300}
                />
              )}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Gear & RPM Graph */}
      {(showGear || showRPM) && (
        <div>
          <h3
            style={{
              color: 'white',
              fontSize: '14px',
              fontWeight: 600,
              marginBottom: '8px',
              letterSpacing: '0.5px',
            }}
          >
            {showGear && showRPM ? 'GEAR & RPM' : showGear ? 'GEAR' : 'RPM'}
          </h3>
          <ResponsiveContainer width="100%" height={height}>
            <LineChart data={mergedData} margin={chartMargin}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis
                dataKey="distance"
                stroke="rgba(255,255,255,0.5)"
                style={{ fontSize: '11px' }}
              />
              <YAxis
                yAxisId="left"
                stroke="rgba(255,255,255,0.5)"
                style={{ fontSize: '11px' }}
                domain={showGear ? [0, 8] : [0, 'auto']}
              />
              {showRPM && showGear && (
                <YAxis
                  yAxisId="right"
                  orientation="right"
                  stroke="rgba(255,255,255,0.5)"
                  style={{ fontSize: '11px' }}
                  domain={[0, 'auto']}
                />
              )}
              <Tooltip content={<CustomTooltip />} />
              {showGear && (
                <Line
                  yAxisId="left"
                  type="stepAfter"
                  dataKey="gear"
                  name="Gear"
                  stroke="#06b6d4"
                  strokeWidth={3}
                  dot={false}
                  animationDuration={300}
                />
              )}
              {showRPM && (
                <Line
                  yAxisId={showGear ? 'right' : 'left'}
                  type="monotone"
                  dataKey="rpm"
                  name="RPM"
                  stroke="#f59e0b"
                  strokeWidth={2}
                  dot={false}
                  animationDuration={300}
                />
              )}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      <style>{`
        .recharts-wrapper {
          font-family: 'Roboto Mono', monospace !important;
        }
      `}</style>
    </div>
  );
};

export default TelemetryGraphs;
