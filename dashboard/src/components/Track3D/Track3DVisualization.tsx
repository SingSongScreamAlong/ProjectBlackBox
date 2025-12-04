import React, { useEffect, useRef, useState } from 'react';
import {
  Track3DRenderer,
  TrackCoordinate,
  DriverPosition,
  CameraMode,
} from './Track3DRenderer';
import { FiMaximize2, FiMinimize2, FiPlay, FiPause, FiCamera } from 'react-icons/fi';

interface Track3DVisualizationProps {
  trackData: TrackCoordinate[];
  drivers: DriverPosition[];
  isLive?: boolean;
  className?: string;
}

export const Track3DVisualization: React.FC<Track3DVisualizationProps> = ({
  trackData,
  drivers,
  isLive = true,
  className = '',
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const rendererRef = useRef<Track3DRenderer | null>(null);

  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [cameraMode, setCameraMode] = useState<CameraMode>({ type: 'orbit' });
  const [selectedDriver, setSelectedDriver] = useState<string | null>(null);

  // Initialize renderer
  useEffect(() => {
    if (!containerRef.current) return;

    const renderer = new Track3DRenderer(containerRef.current);
    rendererRef.current = renderer;

    renderer.startAnimation();

    return () => {
      renderer.dispose();
    };
  }, []);

  // Update track when data changes
  useEffect(() => {
    if (!rendererRef.current || trackData.length === 0) return;

    rendererRef.current.createTrack(trackData);
  }, [trackData]);

  // Update drivers in real-time
  useEffect(() => {
    if (!rendererRef.current || isPaused) return;

    rendererRef.current.updateDrivers(drivers);
  }, [drivers, isPaused]);

  // Update camera mode
  useEffect(() => {
    if (!rendererRef.current) return;

    rendererRef.current.setCameraMode(cameraMode);
  }, [cameraMode]);

  const handleFullscreen = () => {
    if (!containerRef.current) return;

    if (!isFullscreen) {
      containerRef.current.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  const handlePlayPause = () => {
    setIsPaused(!isPaused);
  };

  const handleCameraMode = (mode: CameraMode['type']) => {
    if (mode === 'follow' && drivers.length > 0) {
      const leadDriver = drivers.sort((a, b) => a.position - b.position)[0];
      setCameraMode({ type: 'follow', targetDriverId: leadDriver.driverId });
      setSelectedDriver(leadDriver.driverId);
    } else {
      setCameraMode({ type: mode });
      setSelectedDriver(null);
    }
  };

  const handleDriverSelect = (driverId: string) => {
    setSelectedDriver(driverId);
    setCameraMode({ type: 'follow', targetDriverId: driverId });
  };

  return (
    <div className={`track-3d-container ${className}`}>
      {/* 3D Canvas Container */}
      <div
        ref={containerRef}
        className="track-3d-canvas"
        style={{
          width: '100%',
          height: '100%',
          position: 'relative',
          background: 'linear-gradient(to bottom, #87CEEB 0%, #6B8E23 100%)',
          borderRadius: isFullscreen ? '0' : '12px',
          overflow: 'hidden',
        }}
      />

      {/* Control Panel */}
      <div
        className="track-3d-controls"
        style={{
          position: 'absolute',
          top: '16px',
          right: '16px',
          display: 'flex',
          gap: '8px',
          zIndex: 10,
        }}
      >
        {/* Camera Mode Selector */}
        <div
          className="control-group"
          style={{
            background: 'rgba(0, 0, 0, 0.7)',
            backdropFilter: 'blur(10px)',
            borderRadius: '8px',
            padding: '8px',
            display: 'flex',
            gap: '4px',
          }}
        >
          <button
            onClick={() => handleCameraMode('orbit')}
            className={`control-btn ${cameraMode.type === 'orbit' ? 'active' : ''}`}
            style={{
              padding: '8px 12px',
              background: cameraMode.type === 'orbit' ? 'rgba(255, 255, 255, 0.2)' : 'transparent',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '12px',
              fontWeight: 600,
            }}
          >
            <FiCamera size={16} style={{ marginRight: '4px', verticalAlign: 'middle' }} />
            Orbit
          </button>
          <button
            onClick={() => handleCameraMode('follow')}
            className={`control-btn ${cameraMode.type === 'follow' ? 'active' : ''}`}
            style={{
              padding: '8px 12px',
              background: cameraMode.type === 'follow' ? 'rgba(255, 255, 255, 0.2)' : 'transparent',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '12px',
              fontWeight: 600,
            }}
          >
            Follow
          </button>
          <button
            onClick={() => handleCameraMode('broadcast')}
            className={`control-btn ${cameraMode.type === 'broadcast' ? 'active' : ''}`}
            style={{
              padding: '8px 12px',
              background: cameraMode.type === 'broadcast' ? 'rgba(255, 255, 255, 0.2)' : 'transparent',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '12px',
              fontWeight: 600,
            }}
          >
            Broadcast
          </button>
        </div>

        {/* Playback Controls */}
        <button
          onClick={handlePlayPause}
          className="control-btn"
          style={{
            padding: '10px',
            background: 'rgba(0, 0, 0, 0.7)',
            backdropFilter: 'blur(10px)',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
          }}
        >
          {isPaused ? <FiPlay size={20} /> : <FiPause size={20} />}
        </button>

        {/* Fullscreen Toggle */}
        <button
          onClick={handleFullscreen}
          className="control-btn"
          style={{
            padding: '10px',
            background: 'rgba(0, 0, 0, 0.7)',
            backdropFilter: 'blur(10px)',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
          }}
        >
          {isFullscreen ? <FiMinimize2 size={20} /> : <FiMaximize2 size={20} />}
        </button>
      </div>

      {/* Driver Selection Panel */}
      {drivers.length > 0 && (
        <div
          className="driver-selection-panel"
          style={{
            position: 'absolute',
            top: '16px',
            left: '16px',
            background: 'rgba(0, 0, 0, 0.7)',
            backdropFilter: 'blur(10px)',
            borderRadius: '8px',
            padding: '12px',
            maxHeight: '300px',
            overflowY: 'auto',
            minWidth: '200px',
            zIndex: 10,
          }}
        >
          <h3
            style={{
              color: 'white',
              fontSize: '14px',
              fontWeight: 600,
              marginBottom: '8px',
            }}
          >
            Drivers
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {drivers
              .sort((a, b) => a.position - b.position)
              .map((driver) => (
                <button
                  key={driver.driverId}
                  onClick={() => handleDriverSelect(driver.driverId)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '6px 8px',
                    background:
                      selectedDriver === driver.driverId
                        ? 'rgba(255, 255, 255, 0.2)'
                        : 'transparent',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    color: 'white',
                    fontSize: '12px',
                    textAlign: 'left',
                    transition: 'background 0.2s',
                  }}
                  onMouseEnter={(e) => {
                    if (selectedDriver !== driver.driverId) {
                      e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (selectedDriver !== driver.driverId) {
                      e.currentTarget.style.background = 'transparent';
                    }
                  }}
                >
                  <div
                    style={{
                      width: '12px',
                      height: '12px',
                      borderRadius: '2px',
                      background: driver.teamColor,
                    }}
                  />
                  <span style={{ fontWeight: 600, minWidth: '20px' }}>
                    P{driver.position}
                  </span>
                  <span>{driver.driverName}</span>
                  <span
                    style={{
                      marginLeft: 'auto',
                      opacity: 0.7,
                      fontSize: '11px',
                    }}
                  >
                    {Math.round(driver.speed)} km/h
                  </span>
                </button>
              ))}
          </div>
        </div>
      )}

      {/* Live Indicator */}
      {isLive && !isPaused && (
        <div
          style={{
            position: 'absolute',
            bottom: '16px',
            right: '16px',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '6px 12px',
            background: 'rgba(255, 0, 0, 0.9)',
            backdropFilter: 'blur(10px)',
            borderRadius: '20px',
            zIndex: 10,
          }}
        >
          <div
            style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: 'white',
              animation: 'pulse 2s infinite',
            }}
          />
          <span
            style={{
              color: 'white',
              fontSize: '12px',
              fontWeight: 700,
              letterSpacing: '0.5px',
            }}
          >
            LIVE
          </span>
        </div>
      )}

      <style>{`
        .track-3d-container {
          position: relative;
          width: 100%;
          height: 100%;
        }

        .driver-selection-panel::-webkit-scrollbar {
          width: 6px;
        }

        .driver-selection-panel::-webkit-scrollbar-track {
          background: rgba(255, 255, 255, 0.1);
          border-radius: 3px;
        }

        .driver-selection-panel::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.3);
          border-radius: 3px;
        }

        .driver-selection-panel::-webkit-scrollbar-thumb:hover {
          background: rgba(255, 255, 255, 0.5);
        }

        @keyframes pulse {
          0%, 100% {
            opacity: 1;
          }
          50% {
            opacity: 0.3;
          }
        }

        .control-btn {
          transition: all 0.2s ease;
        }

        .control-btn:hover {
          background: rgba(255, 255, 255, 0.15) !important;
          transform: scale(1.05);
        }

        .control-btn:active {
          transform: scale(0.95);
        }
      `}</style>
    </div>
  );
};

export default Track3DVisualization;
