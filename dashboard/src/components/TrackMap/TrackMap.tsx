import React, { useMemo, useState, useEffect } from 'react';
import { TelemetryData } from '../../services/WebSocketService';
import { tracks, TrackDefinition } from '../../data/tracks/TrackRegistry';
import { trackAssetService } from '../../services/TrackAssetService';
import { trackLearningService } from '../../services/TrackLearningService';

interface TrackMapProps {
  telemetryData: TelemetryData | null;
  trackName?: string;
}

const TrackMap: React.FC<TrackMapProps> = ({ telemetryData, trackName }) => {
  // State for dynamic SVG url
  const [dynamicMapUrl, setDynamicMapUrl] = useState<string | null>(null);

  // Initialize service and try to fetch dynamic map
  useEffect(() => {
    if (!trackName) {
      setDynamicMapUrl(null);
      return;
    }
    const fetchMap = async () => {
      await trackAssetService.initialize();
      const url = trackAssetService.getTrackMapUrl(trackName);
      if (url) {
        setDynamicMapUrl(url);
      } else {
        setDynamicMapUrl(null);
      }
    };
    fetchMap();
  }, [trackName]);

  const trackDef: TrackDefinition | undefined = useMemo(() => {
    if (!trackName) return undefined;
    const staticData = trackAssetService.getStaticTrackData(trackName);
    return staticData || tracks[trackName];
  }, [trackName]);

  // State for session trace (dynamic map improvement)
  const [sessionTrace, setSessionTrace] = useState<{ x: number, y: number }[]>([]);
  const [isLearning, setIsLearning] = useState(false);
  const [learnedPath, setLearnedPath] = useState<string | null>(null);

  // Initialize track learning when track changes
  useEffect(() => {
    if (trackName && trackDef) {
      // Check if we have a learned path for this track
      const existingPath = trackLearningService.getLearnedPath(trackDef.id);
      if (existingPath) {
        setLearnedPath(existingPath);
        console.log(`TrackMap: Using learned path for ${trackName}`);
      }

      // Start recording for this track
      trackLearningService.startRecording(trackDef.id, trackName);
      setIsLearning(true);
    }

    return () => {
      if (isLearning) {
        trackLearningService.stopRecording();
        setIsLearning(false);
      }
    };
  }, [trackName, trackDef?.id]);

  // Update session trace with new telemetry data AND record to learning service
  useEffect(() => {
    if (telemetryData) {
      let viewBox = [0, 0, 1000, 1000]; // Default
      if (trackDef && trackDef.viewBox) {
        viewBox = trackDef.viewBox.split(' ').map(Number);
      }

      const width = viewBox[2];
      const height = viewBox[3];

      // Map telemetry position to SVG coordinates
      // Using modulo to keep within viewBox bounds
      const mappedX = (telemetryData.position?.x || 0) % width;
      const mappedY = (telemetryData.position?.y || 0) % height;

      // Record to TrackLearningService for map improvement
      if (isLearning && telemetryData.trackPosition !== undefined) {
        trackLearningService.recordPoint(mappedX, mappedY, telemetryData.trackPosition);
      }

      setSessionTrace(prev => {
        const last = prev[prev.length - 1];
        if (last && Math.abs(last.x - mappedX) < 2 && Math.abs(last.y - mappedY) < 2) {
          return prev;
        }
        const newTrace = [...prev, { x: mappedX, y: mappedY }];
        if (newTrace.length > 500) return newTrace.slice(-500);
        return newTrace;
      });

      // Check if learning service generated a new path
      if (trackDef && trackLearningService.hasLearnedPath(trackDef.id)) {
        const newPath = trackLearningService.getLearnedPath(trackDef.id);
        if (newPath && newPath !== learnedPath) {
          setLearnedPath(newPath);
          console.log(`TrackMap: Generated new learned path for ${trackName}`);
        }
      }
    }
  }, [telemetryData, trackDef, isLearning, learnedPath, trackName]);

  // Car Position Calculation using SVG path interpolation
  // Uses trackPosition (0-1) to find actual position along the track path
  const [carPosition, setCarPosition] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const pathRef = React.useRef<SVGPathElement | null>(null);

  // Update car position when trackPosition changes
  useEffect(() => {
    if (trackDef && telemetryData) {
      // Try to use the path element to calculate position
      // We'll set up a hidden path element for calculation
      const trackProgress = telemetryData.trackPosition || 0;

      // Create temporary SVG to calculate path position
      const svgNS = "http://www.w3.org/2000/svg";
      const tempSvg = document.createElementNS(svgNS, "svg");
      const tempPath = document.createElementNS(svgNS, "path") as SVGPathElement;
      tempPath.setAttribute("d", trackDef.path);
      tempSvg.appendChild(tempPath);
      document.body.appendChild(tempSvg);

      try {
        const totalLength = tempPath.getTotalLength();
        const point = tempPath.getPointAtLength(trackProgress * totalLength);
        setCarPosition({ x: point.x, y: point.y });
      } catch (e) {
        // Fallback to circular approximation if path calculation fails
        const viewBoxParts = trackDef.viewBox.split(' ').map(Number);
        const centerX = viewBoxParts[2] / 2;
        const centerY = viewBoxParts[3] / 2;
        const radius = Math.min(centerX, centerY) * 0.6;
        const angle = trackProgress * Math.PI * 2 - Math.PI / 2;
        setCarPosition({
          x: centerX + Math.cos(angle) * radius,
          y: centerY + Math.sin(angle) * radius
        });
      } finally {
        document.body.removeChild(tempSvg);
      }
    } else if (!telemetryData && trackDef) {
      // No telemetry - position at start
      const viewBoxParts = trackDef.viewBox.split(' ').map(Number);
      setCarPosition({ x: viewBoxParts[2] / 2, y: viewBoxParts[3] / 2 });
    }
  }, [telemetryData?.trackPosition, trackDef]);

  const carX = carPosition.x;
  const carY = carPosition.y;

  if (!trackDef && !dynamicMapUrl) {
    return (
      <div className="panel track-map-panel">
        <div className="panel-header">{trackName || 'Track Map'}</div>
        <div className="track-container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          <div style={{ color: '#888' }}>Unknown Track</div>
        </div>
      </div>
    );
  }

  // Safe to access trackDef properties primarily if we have it, or fallback if only dynamicUrl exists (but we usually need viewBox)
  // If we have dynamicUrl but no trackDef, we might lack viewBox. 
  // For now assume trackDef is required for static rendering.
  // If dynamicMapUrl exists, we render IMG.

  return (
    <div className="panel track-map-panel">
      <div className="panel-header" style={{ display: 'flex', justifyContent: 'space-between' }}>
        <span>{trackName}</span>
        <span style={{ fontSize: '0.8em', opacity: 0.7 }}>
          Map Source: {dynamicMapUrl ? 'iRacing Data' : 'Library'}
        </span>
      </div>

      <div className="track-container" style={{ position: 'relative', width: '100%', height: '100%', minHeight: '300px' }}>
        {dynamicMapUrl ? (
          // Dynamic SVG from Asset
          <div style={{ width: '100%', height: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
            <img src={dynamicMapUrl} alt={trackName} style={{ maxWidth: '100%', maxHeight: '100%', filter: 'invert(1)' }} />
          </div>
        ) : (
          trackDef ? (
            // Fallback to Static SVG
            <svg
              width="100%"
              height="100%"
              viewBox={trackDef.viewBox}
              preserveAspectRatio="xMidYMid meet"
              style={{ overflow: 'visible' }}
            >
              {/* Grid background effect */}
              <pattern id="grid" width="100" height="100" patternUnits="userSpaceOnUse">
                <path d="M 100 0 L 0 0 0 100" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="1" />
              </pattern>
              <rect width="100%" height="100%" fill="url(#grid)" />

              {/* Base Static Track Map */}
              <path
                d={trackDef.path}
                fill="none"
                stroke={trackDef.style.strokeColor}
                strokeWidth="15"
                strokeOpacity="0.2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              {/* Active Track Line (Brighter) */}
              <path
                d={trackDef.path}
                fill="none"
                stroke={trackDef.style.strokeColor}
                strokeWidth="3"
                strokeOpacity="0.8"
                strokeLinecap="round"
                strokeLinejoin="round"
                filter="drop-shadow(0 0 4px rgba(255,255,255,0.3))"
              />

              {/* User-Driven Data Trace (The "Learning" Part) */}
              {sessionTrace.length > 1 && (
                <polyline
                  points={sessionTrace.map(p => `${p.x},${p.y}`).join(' ')}
                  fill="none"
                  stroke="#00ff9d" // Green for user path
                  strokeWidth="2"
                  strokeDasharray="4 2"
                  opacity="0.8"
                />
              )}

              {/* Corner Markers */}
              {trackDef.corners.map(corner => (
                <g key={corner.id} transform={`translate(${corner.x}, ${corner.y})`}>
                  <circle r="4" fill="#fff" opacity="0.5" />
                  <text
                    y="-10"
                    fill="#fff"
                    fontSize="24"
                    textAnchor="middle"
                    opacity="0.7"
                    style={{ textShadow: '0 2px 4px rgba(0,0,0,0.8)' }}
                  >
                    {corner.id}
                  </text>
                </g>
              ))}

              {/* Car Marker */}
              {telemetryData && (
                <g transform={`translate(${carX}, ${carY})`}>
                  <circle r="12" fill={trackDef.style.strokeColor} fillOpacity="0.3">
                    <animate attributeName="r" values="12;16;12" dur="1.5s" repeatCount="indefinite" />
                  </circle>
                  <circle r="6" fill="#fff" stroke="#000" strokeWidth="2" />
                </g>
              )}
            </svg>
          ) : null
        )}

        {/* Track Info Overlay */}
        <div className="track-info" style={{ pointerEvents: 'none' }}>
        </div>
      </div>
    </div>
  );
};

export default TrackMap;
