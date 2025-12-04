import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FiTrendingUp, FiTrendingDown, FiMinus } from 'react-icons/fi';

export interface SectorTime {
  sector1?: number;
  sector2?: number;
  sector3?: number;
  sector1Status?: 'fastest' | 'personal-best' | 'normal' | 'slow';
  sector2Status?: 'fastest' | 'personal-best' | 'normal' | 'slow';
  sector3Status?: 'fastest' | 'personal-best' | 'normal' | 'slow';
}

export interface DriverTiming {
  position: number;
  driverId: string;
  driverName: string;
  driverNumber: string;
  teamName: string;
  teamColor: string;
  lastLapTime?: number;
  bestLapTime?: number;
  gap?: number | 'LEADER' | 'LAP';
  interval?: number;
  sectorTimes: SectorTime;
  currentSector: number;
  pitStops: number;
  tireCompound?: 'SOFT' | 'MEDIUM' | 'HARD' | 'INTERMEDIATE' | 'WET';
  tireLaps: number;
  positionChange: number; // +/- position change from start
  isInPit: boolean;
  isRetired: boolean;
}

interface TimingTowerProps {
  drivers: DriverTiming[];
  showSectorTimes?: boolean;
  showTireInfo?: boolean;
  highlightedDriverId?: string;
  className?: string;
}

export const TimingTower: React.FC<TimingTowerProps> = ({
  drivers,
  showSectorTimes = true,
  showTireInfo = true,
  highlightedDriverId,
  className = '',
}) => {
  const formatTime = (milliseconds: number): string => {
    if (!milliseconds || isNaN(milliseconds)) return '--:--.---';

    const totalSeconds = milliseconds / 1000;
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;

    return `${minutes}:${seconds.toFixed(3).padStart(6, '0')}`;
  };

  const formatGap = (gap: number | 'LEADER' | 'LAP'): string => {
    if (gap === 'LEADER') return 'LEADER';
    if (gap === 'LAP') return '+1 LAP';
    if (typeof gap === 'number') {
      return `+${gap.toFixed(3)}`;
    }
    return '--';
  };

  const getSectorColor = (status?: string): string => {
    switch (status) {
      case 'fastest':
        return '#9333ea'; // Purple - Overall fastest
      case 'personal-best':
        return '#22c55e'; // Green - Personal best
      case 'slow':
        return '#eab308'; // Yellow - Slow
      default:
        return '#ffffff'; // White - Normal
    }
  };

  const getTireColor = (compound?: string): string => {
    switch (compound) {
      case 'SOFT':
        return '#ef4444'; // Red
      case 'MEDIUM':
        return '#eab308'; // Yellow
      case 'HARD':
        return '#f0f0f0'; // White
      case 'INTERMEDIATE':
        return '#22c55e'; // Green
      case 'WET':
        return '#3b82f6'; // Blue
      default:
        return '#6b7280'; // Gray
    }
  };

  const getPositionIcon = (change: number) => {
    if (change > 0) return <FiTrendingUp color="#22c55e" size={14} />;
    if (change < 0) return <FiTrendingDown color="#ef4444" size={14} />;
    return <FiMinus color="#6b7280" size={14} />;
  };

  return (
    <div
      className={`timing-tower ${className}`}
      style={{
        width: '100%',
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
          LIVE TIMING
        </h2>
        <div
          style={{
            marginLeft: 'auto',
            display: 'flex',
            gap: '4px',
            alignItems: 'center',
          }}
        >
          <div
            style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: '#ef4444',
              animation: 'pulse 2s infinite',
            }}
          />
          <span
            style={{
              color: '#ef4444',
              fontSize: '12px',
              fontWeight: 700,
              letterSpacing: '0.5px',
            }}
          >
            LIVE
          </span>
        </div>
      </div>

      {/* Column Headers */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: showTireInfo
            ? '60px 50px 1fr 90px 80px 80px 120px 80px'
            : '60px 50px 1fr 90px 80px 80px 120px',
          gap: '8px',
          padding: '8px 12px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
          fontSize: '11px',
          fontWeight: 600,
          color: 'rgba(255, 255, 255, 0.5)',
          letterSpacing: '0.5px',
        }}
      >
        <div>POS</div>
        <div>NO</div>
        <div>DRIVER</div>
        <div>GAP</div>
        <div>INTERVAL</div>
        <div>LAST</div>
        <div style={{ textAlign: 'center' }}>SECTORS</div>
        {showTireInfo && <div>TIRE</div>}
      </div>

      {/* Driver Rows */}
      <AnimatePresence>
        {drivers
          .sort((a, b) => {
            if (a.isRetired && !b.isRetired) return 1;
            if (!a.isRetired && b.isRetired) return -1;
            return a.position - b.position;
          })
          .map((driver, index) => (
            <motion.div
              key={driver.driverId}
              layout
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
              transition={{ duration: 0.3, delay: index * 0.02 }}
              style={{
                display: 'grid',
                gridTemplateColumns: showTireInfo
                  ? '60px 50px 1fr 90px 80px 80px 120px 80px'
                  : '60px 50px 1fr 90px 80px 80px 120px',
                gap: '8px',
                padding: '10px 12px',
                background:
                  highlightedDriverId === driver.driverId
                    ? 'rgba(255, 255, 255, 0.1)'
                    : index % 2 === 0
                    ? 'rgba(255, 255, 255, 0.02)'
                    : 'transparent',
                borderLeft: `4px solid ${driver.teamColor}`,
                borderRadius: '6px',
                marginBottom: '4px',
                alignItems: 'center',
                fontSize: '13px',
                color: 'white',
                opacity: driver.isRetired ? 0.5 : 1,
                transition: 'all 0.2s ease',
              }}
            >
              {/* Position */}
              <div
                style={{
                  fontWeight: 700,
                  fontSize: '16px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                <span>{driver.position}</span>
                {getPositionIcon(driver.positionChange)}
              </div>

              {/* Driver Number */}
              <div
                style={{
                  fontWeight: 700,
                  color: driver.teamColor,
                  fontSize: '14px',
                }}
              >
                {driver.driverNumber}
              </div>

              {/* Driver Name */}
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '2px',
                }}
              >
                <div
                  style={{
                    fontWeight: 700,
                    fontSize: '14px',
                  }}
                >
                  {driver.driverName}
                  {driver.isInPit && (
                    <span
                      style={{
                        marginLeft: '8px',
                        padding: '2px 6px',
                        background: '#eab308',
                        color: 'black',
                        borderRadius: '3px',
                        fontSize: '10px',
                        fontWeight: 700,
                      }}
                    >
                      PIT
                    </span>
                  )}
                  {driver.isRetired && (
                    <span
                      style={{
                        marginLeft: '8px',
                        padding: '2px 6px',
                        background: '#ef4444',
                        color: 'white',
                        borderRadius: '3px',
                        fontSize: '10px',
                        fontWeight: 700,
                      }}
                    >
                      OUT
                    </span>
                  )}
                </div>
                <div
                  style={{
                    fontSize: '11px',
                    color: 'rgba(255, 255, 255, 0.5)',
                  }}
                >
                  {driver.teamName}
                </div>
              </div>

              {/* Gap */}
              <div
                style={{
                  fontWeight: 600,
                  fontFamily: '"Roboto Mono", monospace',
                }}
              >
                {formatGap(driver.gap || 'LEADER')}
              </div>

              {/* Interval */}
              <div
                style={{
                  fontWeight: 600,
                  fontFamily: '"Roboto Mono", monospace',
                  color: 'rgba(255, 255, 255, 0.7)',
                }}
              >
                {driver.interval ? `+${driver.interval.toFixed(3)}` : '--'}
              </div>

              {/* Last Lap Time */}
              <div
                style={{
                  fontWeight: 600,
                  fontFamily: '"Roboto Mono", monospace',
                  color:
                    driver.lastLapTime === driver.bestLapTime
                      ? '#9333ea'
                      : 'rgba(255, 255, 255, 0.9)',
                }}
              >
                {driver.lastLapTime ? formatTime(driver.lastLapTime) : '--:--.---'}
              </div>

              {/* Sector Times */}
              {showSectorTimes && (
                <div
                  style={{
                    display: 'flex',
                    gap: '4px',
                    justifyContent: 'center',
                  }}
                >
                  {[1, 2, 3].map((sector) => {
                    const sectorKey = `sector${sector}` as keyof SectorTime;
                    const statusKey = `sector${sector}Status` as keyof SectorTime;
                    const time = driver.sectorTimes[sectorKey] as number | undefined;
                    const status = driver.sectorTimes[statusKey] as string | undefined;

                    return (
                      <div
                        key={sector}
                        style={{
                          width: '36px',
                          height: '24px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          background:
                            driver.currentSector === sector
                              ? 'rgba(234, 179, 8, 0.3)'
                              : 'rgba(255, 255, 255, 0.05)',
                          border:
                            driver.currentSector === sector
                              ? '1px solid #eab308'
                              : '1px solid rgba(255, 255, 255, 0.1)',
                          borderRadius: '4px',
                          fontSize: '11px',
                          fontWeight: 700,
                          fontFamily: '"Roboto Mono", monospace',
                          color: getSectorColor(status),
                        }}
                      >
                        {time ? (time / 1000).toFixed(3) : '--'}
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Tire Info */}
              {showTireInfo && (
                <div
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
                      background: getTireColor(driver.tireCompound),
                      border: '2px solid rgba(255, 255, 255, 0.3)',
                    }}
                  />
                  <div
                    style={{
                      fontSize: '11px',
                      fontWeight: 600,
                      color: 'rgba(255, 255, 255, 0.7)',
                    }}
                  >
                    {driver.tireLaps} laps
                  </div>
                </div>
              )}
            </motion.div>
          ))}
      </AnimatePresence>

      <style>{`
        @keyframes pulse {
          0%, 100% {
            opacity: 1;
          }
          50% {
            opacity: 0.3;
          }
        }

        .timing-tower::-webkit-scrollbar {
          width: 8px;
        }

        .timing-tower::-webkit-scrollbar-track {
          background: rgba(255, 255, 255, 0.05);
          border-radius: 4px;
        }

        .timing-tower::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.2);
          border-radius: 4px;
        }

        .timing-tower::-webkit-scrollbar-thumb:hover {
          background: rgba(255, 255, 255, 0.3);
        }
      `}</style>
    </div>
  );
};

export default TimingTower;
