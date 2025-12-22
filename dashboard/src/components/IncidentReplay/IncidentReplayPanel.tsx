import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { tracks, TrackDefinition } from '../../data/tracks/TrackRegistry';
import './IncidentReplayPanel.css';

// Types for incident replay data
export interface IncidentPosition {
    x: number;
    y: number;
    trackPosition: number; // 0-1 position around track
}

export interface IncidentSnapshot {
    timestamp: number; // Relative time in ms (0 = incident moment, negative = before, positive = after)
    playerPosition: IncidentPosition;
    competitorPositions: Array<{
        driver: string;
        carNumber?: string;
        position: IncidentPosition;
    }>;
}

export interface ReplayIncident {
    id: string;
    lap: number;
    sector: number;
    type: 'off-track' | 'contact' | 'spin' | 'lockup' | 'oversteer' | 'understeer';
    severity: 'minor' | 'moderate' | 'major';
    timeLost: number;
    corner?: string;
    trackPosition: number; // Where on track it occurred (0-1)
    snapshots: IncidentSnapshot[]; // -5s to +5s around incident
}

interface IncidentReplayPanelProps {
    incident?: ReplayIncident | null;
    trackName?: string;
    onClose?: () => void;
}

const IncidentReplayPanel: React.FC<IncidentReplayPanelProps> = ({
    incident,
    trackName = 'Unknown Track',
    onClose
}) => {
    const [isPlaying, setIsPlaying] = useState(false);
    const [playbackSpeed, setPlaybackSpeed] = useState(1);
    const [currentTime, setCurrentTime] = useState(0); // Current playback time in ms
    const animationRef = useRef<number | null>(null);
    const lastFrameTime = useRef<number>(0);

    // Get track definition for SVG rendering
    const trackDef: TrackDefinition | undefined = useMemo(() => {
        if (!trackName) return undefined;
        // Try exact match first, then fuzzy match
        if (tracks[trackName]) return tracks[trackName];
        const key = Object.keys(tracks).find(k =>
            k.toLowerCase().includes(trackName.toLowerCase()) ||
            trackName.toLowerCase().includes(k.toLowerCase())
        );
        return key ? tracks[key] : undefined;
    }, [trackName]);

    // Parse viewBox for coordinate mapping
    const viewBox = useMemo(() => {
        if (!trackDef?.viewBox) return { minX: 0, minY: 0, width: 800, height: 800 };
        const parts = trackDef.viewBox.split(' ').map(Number);
        return { minX: parts[0], minY: parts[1], width: parts[2], height: parts[3] };
    }, [trackDef]);

    // Get time bounds from snapshots
    const timeRange = incident?.snapshots ? {
        min: Math.min(...incident.snapshots.map(s => s.timestamp)),
        max: Math.max(...incident.snapshots.map(s => s.timestamp))
    } : { min: -5000, max: 5000 };

    // Interpolate positions between snapshots and convert to SVG coords
    const getInterpolatedPositions = useCallback((time: number) => {
        if (!incident?.snapshots || incident.snapshots.length < 2) return null;

        const snapshots = incident.snapshots.sort((a, b) => a.timestamp - b.timestamp);

        // Find the two snapshots to interpolate between
        let before = snapshots[0];
        let after = snapshots[snapshots.length - 1];

        for (let i = 0; i < snapshots.length - 1; i++) {
            if (snapshots[i].timestamp <= time && snapshots[i + 1].timestamp >= time) {
                before = snapshots[i];
                after = snapshots[i + 1];
                break;
            }
        }

        // Calculate interpolation factor
        const range = after.timestamp - before.timestamp;
        const t = range === 0 ? 0 : (time - before.timestamp) / range;

        // Interpolate player position (x, y are in viewBox coordinates)
        const playerPos = {
            x: before.playerPosition.x + (after.playerPosition.x - before.playerPosition.x) * t,
            y: before.playerPosition.y + (after.playerPosition.y - before.playerPosition.y) * t,
            trackPosition: before.playerPosition.trackPosition + (after.playerPosition.trackPosition - before.playerPosition.trackPosition) * t
        };

        // Interpolate competitor positions
        const competitorPositions = before.competitorPositions.map((comp, i) => {
            const afterComp = after.competitorPositions[i];
            if (!afterComp) return comp;
            return {
                driver: comp.driver,
                carNumber: comp.carNumber,
                position: {
                    x: comp.position.x + (afterComp.position.x - comp.position.x) * t,
                    y: comp.position.y + (afterComp.position.y - comp.position.y) * t,
                    trackPosition: comp.position.trackPosition + (afterComp.position.trackPosition - comp.position.trackPosition) * t
                }
            };
        });

        return { playerPos, competitorPositions };
    }, [incident]);

    // Get current interpolated positions
    const positions = useMemo(() => getInterpolatedPositions(currentTime), [currentTime, getInterpolatedPositions]);

    // Animation loop
    useEffect(() => {
        if (!isPlaying || !incident) return;

        const animate = (timestamp: number) => {
            if (lastFrameTime.current === 0) {
                lastFrameTime.current = timestamp;
            }

            const delta = (timestamp - lastFrameTime.current) * playbackSpeed;
            lastFrameTime.current = timestamp;

            setCurrentTime(prev => {
                const next = prev + delta;
                if (next >= timeRange.max) {
                    setIsPlaying(false);
                    return timeRange.max;
                }
                return next;
            });

            animationRef.current = requestAnimationFrame(animate);
        };

        animationRef.current = requestAnimationFrame(animate);

        return () => {
            if (animationRef.current) {
                cancelAnimationFrame(animationRef.current);
            }
            lastFrameTime.current = 0;
        };
    }, [isPlaying, playbackSpeed, incident, timeRange.max]);

    // Reset when incident changes
    useEffect(() => {
        setCurrentTime(timeRange.min);
        setIsPlaying(false);
    }, [incident, timeRange.min]);

    const handlePlayPause = () => {
        if (currentTime >= timeRange.max) {
            setCurrentTime(timeRange.min);
        }
        setIsPlaying(!isPlaying);
    };

    const handleTimelineChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setCurrentTime(parseInt(e.target.value));
        setIsPlaying(false);
    };

    const getTypeIcon = (type: string) => {
        switch (type) {
            case 'off-track': return '🚧';
            case 'contact': return '💥';
            case 'spin': return '🔄';
            case 'lockup': return '🔒';
            case 'oversteer': return '↩️';
            case 'understeer': return '↪️';
            default: return '⚠️';
        }
    };

    const getSeverityColor = (severity: string) => {
        switch (severity) {
            case 'minor': return '#ffeb3b';
            case 'moderate': return '#ff9800';
            case 'major': return '#f44336';
            default: return '#fff';
        }
    };

    // No incident selected state
    if (!incident) {
        return (
            <div className="incident-replay-panel">
                <div className="panel-header">INCIDENT REPLAY</div>
                <div className="no-incident">
                    <div className="no-incident-icon">🔍</div>
                    <div className="no-incident-text">No incident selected</div>
                    <div className="no-incident-hint">Select an incident from the Analysis tab to view replay</div>
                </div>
            </div>
        );
    }

    return (
        <div className="incident-replay-panel">
            <div className="panel-header">
                <span>INCIDENT REPLAY</span>
                {onClose && (
                    <button className="close-btn" onClick={onClose}>×</button>
                )}
            </div>

            {/* Incident Info */}
            <div className="incident-info">
                <span className="incident-type-badge" style={{ borderColor: getSeverityColor(incident.severity) }}>
                    {getTypeIcon(incident.type)} {incident.type.toUpperCase()}
                </span>
                <span className="incident-location">
                    Lap {incident.lap} • {incident.corner || `Sector ${incident.sector}`}
                </span>
                <span className="time-lost" style={{ color: '#ff3b3b' }}>
                    -{incident.timeLost.toFixed(2)}s
                </span>
            </div>

            {/* Track Visualization - SVG Based */}
            <div className="replay-svg-container">
                <svg
                    viewBox={trackDef?.viewBox || "0 0 800 800"}
                    className="replay-track-svg"
                    preserveAspectRatio="xMidYMid meet"
                >
                    {/* Track outline */}
                    {trackDef?.path ? (
                        <path
                            d={trackDef.path}
                            fill="none"
                            stroke={trackDef.style?.strokeColor || '#4facfe'}
                            strokeWidth="16"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            opacity="0.6"
                        />
                    ) : (
                        // Fallback oval if no track data
                        <ellipse
                            cx={viewBox.width / 2}
                            cy={viewBox.height / 2}
                            rx={viewBox.width * 0.4}
                            ry={viewBox.height * 0.3}
                            fill="none"
                            stroke="#30363d"
                            strokeWidth="16"
                        />
                    )}

                    {/* Track surface (thinner line on top) */}
                    {trackDef?.path && (
                        <path
                            d={trackDef.path}
                            fill="none"
                            stroke="#1a1f26"
                            strokeWidth="14"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                        />
                    )}

                    {/* Corner markers */}
                    {trackDef?.corners?.map(corner => (
                        <g key={corner.id}>
                            <circle
                                cx={corner.x}
                                cy={corner.y}
                                r="12"
                                fill="rgba(255,255,255,0.1)"
                            />
                            <text
                                x={corner.x}
                                y={corner.y + 4}
                                textAnchor="middle"
                                fontSize="10"
                                fill="#666"
                            >
                                {corner.id}
                            </text>
                        </g>
                    ))}

                    {/* Incident location marker */}
                    {incident && trackDef?.corners && trackDef.corners.length > 0 && (
                        <g>
                            {/* Pulsing incident marker at a corner near the incident */}
                            <circle
                                cx={trackDef.corners[0].x}
                                cy={trackDef.corners[0].y}
                                r="20"
                                fill="rgba(255, 59, 59, 0.3)"
                                className="pulse-marker"
                            />
                            <circle
                                cx={trackDef.corners[0].x}
                                cy={trackDef.corners[0].y}
                                r="8"
                                fill="#ff3b3b"
                            />
                            <text
                                x={trackDef.corners[0].x}
                                y={trackDef.corners[0].y + 3}
                                textAnchor="middle"
                                fontSize="8"
                                fill="#fff"
                                fontWeight="bold"
                            >
                                ⚠
                            </text>
                        </g>
                    )}

                    {/* Competitor cars */}
                    {positions?.competitorPositions.map((comp, i) => (
                        <g key={`comp-${i}`}>
                            <circle
                                cx={comp.position.x}
                                cy={comp.position.y}
                                r="10"
                                fill="#555"
                                stroke="#888"
                                strokeWidth="2"
                            />
                            <text
                                x={comp.position.x}
                                y={comp.position.y + 3}
                                textAnchor="middle"
                                fontSize="8"
                                fill="#fff"
                            >
                                {i + 2}
                            </text>
                        </g>
                    ))}

                    {/* Player car - on top */}
                    {positions && (
                        <g className="player-car">
                            <circle
                                cx={positions.playerPos.x}
                                cy={positions.playerPos.y}
                                r="14"
                                fill="#00d4ff"
                                stroke="#fff"
                                strokeWidth="2"
                                filter="drop-shadow(0 0 6px rgba(0, 212, 255, 0.8))"
                            />
                            <text
                                x={positions.playerPos.x}
                                y={positions.playerPos.y + 4}
                                textAnchor="middle"
                                fontSize="10"
                                fill="#fff"
                                fontWeight="bold"
                            >
                                P
                            </text>
                        </g>
                    )}

                    {/* Time indicator */}
                    <text
                        x={viewBox.width / 2}
                        y={viewBox.height - 20}
                        textAnchor="middle"
                        fontSize="24"
                        fill="#fff"
                        fontFamily="monospace"
                        fontWeight="bold"
                    >
                        {currentTime >= 0 ? `+${(currentTime / 1000).toFixed(1)}s` : `${(currentTime / 1000).toFixed(1)}s`}
                    </text>
                </svg>
            </div>

            {/* Timeline Scrubber */}
            <div className="timeline-container">
                <span className="time-label">{(timeRange.min / 1000).toFixed(1)}s</span>
                <input
                    type="range"
                    min={timeRange.min}
                    max={timeRange.max}
                    value={currentTime}
                    onChange={handleTimelineChange}
                    className="timeline-slider"
                />
                <span className="time-label">+{(timeRange.max / 1000).toFixed(1)}s</span>
            </div>

            {/* Playback Controls */}
            <div className="playback-controls">
                <button
                    className="control-btn"
                    onClick={() => setCurrentTime(timeRange.min)}
                    title="Reset"
                >
                    ⏮
                </button>
                <button
                    className="control-btn play-btn"
                    onClick={handlePlayPause}
                    title={isPlaying ? 'Pause' : 'Play'}
                >
                    {isPlaying ? '⏸' : '▶'}
                </button>
                <div className="speed-controls">
                    {[0.5, 1, 2].map(speed => (
                        <button
                            key={speed}
                            className={`speed-btn ${playbackSpeed === speed ? 'active' : ''}`}
                            onClick={() => setPlaybackSpeed(speed)}
                        >
                            {speed}x
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default IncidentReplayPanel;
