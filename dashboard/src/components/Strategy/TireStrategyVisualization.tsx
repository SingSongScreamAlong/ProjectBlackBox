import React from 'react';
import { motion } from 'framer-motion';
import { FiAlertCircle } from 'react-icons/fi';

export type TireCompound = 'SOFT' | 'MEDIUM' | 'HARD' | 'INTERMEDIATE' | 'WET';

export interface TireStint {
  compound: TireCompound;
  startLap: number;
  endLap: number;
  lapCount: number;
  degradation?: number; // 0-100%
  isCurrentStint: boolean;
}

export interface PitStop {
  lap: number;
  duration: number; // seconds
  reason: 'tire-change' | 'damage' | 'fuel' | 'penalty';
  oldCompound?: TireCompound;
  newCompound?: TireCompound;
}

export interface DriverStrategy {
  driverId: string;
  driverName: string;
  driverNumber: string;
  teamColor: string;
  stints: TireStint[];
  pitStops: PitStop[];
  totalPitStops: number;
  predictedStops?: number;
}

interface TireStrategyVisualizationProps {
  strategies: DriverStrategy[];
  totalLaps: number;
  currentLap: number;
  highlightedDriverId?: string;
  className?: string;
}

export const TireStrategyVisualization: React.FC<TireStrategyVisualizationProps> = ({
  strategies,
  totalLaps,
  currentLap,
  highlightedDriverId,
  className = '',
}) => {
  const getTireColor = (compound: TireCompound): string => {
    switch (compound) {
      case 'SOFT':
        return '#ef4444';
      case 'MEDIUM':
        return '#eab308';
      case 'HARD':
        return '#f0f0f0';
      case 'INTERMEDIATE':
        return '#22c55e';
      case 'WET':
        return '#3b82f6';
      default:
        return '#6b7280';
    }
  };

  const getTireLabel = (compound: TireCompound): string => {
    return compound.charAt(0);
  };

  const calculateStintWidth = (stint: TireStint): string => {
    const percentage = (stint.lapCount / totalLaps) * 100;
    return `${percentage}%`;
  };

  const calculateStintPosition = (startLap: number): string => {
    const percentage = (startLap / totalLaps) * 100;
    return `${percentage}%`;
  };

  return (
    <div
      className={`tire-strategy ${className}`}
      style={{
        background: 'rgba(0, 0, 0, 0.85)',
        backdropFilter: 'blur(20px)',
        borderRadius: '12px',
        padding: '16px',
        fontFamily: '"Formula1", "Roboto Mono", monospace',
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '12px',
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
          TIRE STRATEGY
        </h2>
        <div
          style={{
            color: 'rgba(255, 255, 255, 0.7)',
            fontSize: '14px',
            fontWeight: 600,
          }}
        >
          Lap {currentLap} / {totalLaps}
        </div>
      </div>

      {/* Tire Compound Legend */}
      <div
        style={{
          display: 'flex',
          gap: '16px',
          marginBottom: '16px',
          padding: '12px',
          background: 'rgba(255, 255, 255, 0.05)',
          borderRadius: '8px',
        }}
      >
        {(['SOFT', 'MEDIUM', 'HARD', 'INTERMEDIATE', 'WET'] as TireCompound[]).map(
          (compound) => (
            <div
              key={compound}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              <div
                style={{
                  width: '20px',
                  height: '20px',
                  borderRadius: '50%',
                  background: getTireColor(compound),
                  border: '2px solid rgba(255, 255, 255, 0.3)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 700,
                  fontSize: '11px',
                  color: compound === 'HARD' ? 'black' : 'white',
                }}
              >
                {getTireLabel(compound)}
              </div>
              <span
                style={{
                  color: 'rgba(255, 255, 255, 0.7)',
                  fontSize: '12px',
                  fontWeight: 500,
                }}
              >
                {compound}
              </span>
            </div>
          )
        )}
      </div>

      {/* Lap Scale */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          marginBottom: '8px',
          paddingLeft: '140px',
          paddingRight: '16px',
        }}
      >
        {[0, Math.floor(totalLaps * 0.25), Math.floor(totalLaps * 0.5), Math.floor(totalLaps * 0.75), totalLaps].map((lap) => (
          <div
            key={lap}
            style={{
              color: 'rgba(255, 255, 255, 0.5)',
              fontSize: '11px',
              fontWeight: 600,
            }}
          >
            {lap}
          </div>
        ))}
      </div>

      {/* Strategy Visualization */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
        }}
      >
        {strategies
          .sort((a, b) => parseInt(a.driverNumber) - parseInt(b.driverNumber))
          .map((strategy, index) => (
            <motion.div
              key={strategy.driverId}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3, delay: index * 0.05 }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '12px',
                background:
                  highlightedDriverId === strategy.driverId
                    ? 'rgba(255, 255, 255, 0.1)'
                    : index % 2 === 0
                    ? 'rgba(255, 255, 255, 0.02)'
                    : 'transparent',
                borderLeft: `4px solid ${strategy.teamColor}`,
                borderRadius: '6px',
              }}
            >
              {/* Driver Info */}
              <div
                style={{
                  minWidth: '120px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '2px',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                  }}
                >
                  <span
                    style={{
                      color: strategy.teamColor,
                      fontSize: '14px',
                      fontWeight: 700,
                    }}
                  >
                    {strategy.driverNumber}
                  </span>
                  <span
                    style={{
                      color: 'white',
                      fontSize: '13px',
                      fontWeight: 600,
                    }}
                  >
                    {strategy.driverName.split(' ').pop()}
                  </span>
                </div>
                <div
                  style={{
                    color: 'rgba(255, 255, 255, 0.5)',
                    fontSize: '11px',
                  }}
                >
                  {strategy.totalPitStops} stop{strategy.totalPitStops !== 1 ? 's' : ''}
                  {strategy.predictedStops !== undefined &&
                    strategy.predictedStops > strategy.totalPitStops && (
                      <span
                        style={{
                          marginLeft: '4px',
                          color: '#eab308',
                        }}
                      >
                        (+{strategy.predictedStops - strategy.totalPitStops})
                      </span>
                    )}
                </div>
              </div>

              {/* Stint Timeline */}
              <div
                style={{
                  flex: 1,
                  position: 'relative',
                  height: '40px',
                  background: 'rgba(255, 255, 255, 0.05)',
                  borderRadius: '6px',
                  overflow: 'hidden',
                }}
              >
                {/* Current Lap Indicator */}
                <div
                  style={{
                    position: 'absolute',
                    left: calculateStintPosition(currentLap),
                    top: 0,
                    bottom: 0,
                    width: '2px',
                    background: '#eab308',
                    zIndex: 10,
                  }}
                >
                  <div
                    style={{
                      position: 'absolute',
                      top: '-6px',
                      left: '50%',
                      transform: 'translateX(-50%)',
                      width: 0,
                      height: 0,
                      borderLeft: '4px solid transparent',
                      borderRight: '4px solid transparent',
                      borderTop: '6px solid #eab308',
                    }}
                  />
                </div>

                {/* Tire Stints */}
                {strategy.stints.map((stint, stintIndex) => (
                  <div
                    key={stintIndex}
                    style={{
                      position: 'absolute',
                      left: calculateStintPosition(stint.startLap),
                      width: calculateStintWidth(stint),
                      height: '100%',
                      background: getTireColor(stint.compound),
                      opacity: stint.isCurrentStint ? 1 : 0.7,
                      border: stint.isCurrentStint
                        ? '2px solid #eab308'
                        : '1px solid rgba(0, 0, 0, 0.3)',
                      borderRadius: '4px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      transition: 'all 0.3s ease',
                    }}
                  >
                    {/* Tire Compound Label */}
                    <div
                      style={{
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        gap: '2px',
                      }}
                    >
                      <span
                        style={{
                          color: stint.compound === 'HARD' ? 'black' : 'white',
                          fontSize: '12px',
                          fontWeight: 700,
                        }}
                      >
                        {getTireLabel(stint.compound)}
                      </span>
                      <span
                        style={{
                          color:
                            stint.compound === 'HARD'
                              ? 'rgba(0, 0, 0, 0.7)'
                              : 'rgba(255, 255, 255, 0.7)',
                          fontSize: '10px',
                          fontWeight: 600,
                        }}
                      >
                        {stint.lapCount}L
                      </span>
                    </div>

                    {/* Degradation Warning */}
                    {stint.degradation !== undefined && stint.degradation > 80 && (
                      <div
                        style={{
                          position: 'absolute',
                          top: '2px',
                          right: '2px',
                        }}
                      >
                        <FiAlertCircle
                          size={12}
                          color={stint.compound === 'HARD' ? 'black' : 'white'}
                        />
                      </div>
                    )}
                  </div>
                ))}

                {/* Pit Stop Markers */}
                {strategy.pitStops.map((pitStop, pitIndex) => (
                  <div
                    key={pitIndex}
                    style={{
                      position: 'absolute',
                      left: calculateStintPosition(pitStop.lap),
                      top: '50%',
                      transform: 'translate(-50%, -50%)',
                      width: '6px',
                      height: '6px',
                      background: '#ffffff',
                      border: '2px solid #000000',
                      borderRadius: '50%',
                      zIndex: 5,
                      cursor: 'pointer',
                    }}
                    title={`Lap ${pitStop.lap}: ${pitStop.duration.toFixed(1)}s`}
                  />
                ))}
              </div>
            </motion.div>
          ))}
      </div>

      {/* Pit Stop Summary */}
      <div
        style={{
          marginTop: '16px',
          padding: '12px',
          background: 'rgba(255, 255, 255, 0.05)',
          borderRadius: '8px',
          display: 'flex',
          gap: '24px',
          fontSize: '12px',
        }}
      >
        <div>
          <span style={{ color: 'rgba(255, 255, 255, 0.5)' }}>
            Total Pit Stops:{' '}
          </span>
          <span style={{ color: 'white', fontWeight: 700 }}>
            {strategies.reduce((sum, s) => sum + s.totalPitStops, 0)}
          </span>
        </div>
        <div>
          <span style={{ color: 'rgba(255, 255, 255, 0.5)' }}>Avg Stop Time: </span>
          <span style={{ color: 'white', fontWeight: 700 }}>
            {(
              strategies
                .flatMap((s) => s.pitStops)
                .reduce((sum, p) => sum + p.duration, 0) /
              Math.max(strategies.flatMap((s) => s.pitStops).length, 1)
            ).toFixed(1)}
            s
          </span>
        </div>
        <div>
          <span style={{ color: 'rgba(255, 255, 255, 0.5)' }}>Most Used: </span>
          <span style={{ color: 'white', fontWeight: 700 }}>
            {(() => {
              const compounds = strategies
                .flatMap((s) => s.stints)
                .map((st) => st.compound);
              const counts = compounds.reduce((acc, c) => {
                acc[c] = (acc[c] || 0) + 1;
                return acc;
              }, {} as Record<string, number>);
              const mostUsed = Object.entries(counts).sort((a, b) => b[1] - a[1])[0];
              return mostUsed ? mostUsed[0] : 'N/A';
            })()}
          </span>
        </div>
      </div>
    </div>
  );
};

export default TireStrategyVisualization;
