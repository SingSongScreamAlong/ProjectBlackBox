import React, { useState, useEffect, useRef, useCallback } from 'react';
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
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const animationRef = useRef<number | null>(null);
    const lastFrameTime = useRef<number>(0);

    // Get time bounds from snapshots
    const timeRange = incident?.snapshots ? {
        min: Math.min(...incident.snapshots.map(s => s.timestamp)),
        max: Math.max(...incident.snapshots.map(s => s.timestamp))
    } : { min: -5000, max: 5000 };

    // Interpolate positions between snapshots
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

        // Interpolate player position
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

    // Draw the track and cars
    const draw = useCallback(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        const width = canvas.width;
        const height = canvas.height;
        const centerX = width / 2;
        const centerY = height / 2;
        const radius = Math.min(width, height) * 0.35;

        // Clear
        ctx.fillStyle = '#0d1117';
        ctx.fillRect(0, 0, width, height);

        // Draw simple oval track
        ctx.strokeStyle = '#30363d';
        ctx.lineWidth = 20;
        ctx.beginPath();
        ctx.ellipse(centerX, centerY, radius * 1.2, radius * 0.8, 0, 0, Math.PI * 2);
        ctx.stroke();

        // Draw track surface
        ctx.strokeStyle = '#1a1f26';
        ctx.lineWidth = 18;
        ctx.stroke();

        // Mark incident location
        if (incident) {
            const incidentAngle = incident.trackPosition * Math.PI * 2 - Math.PI / 2;
            const incidentX = centerX + Math.cos(incidentAngle) * radius * 1.2;
            const incidentY = centerY + Math.sin(incidentAngle) * radius * 0.8;

            // Pulsing incident marker
            const pulseSize = 8 + Math.sin(Date.now() / 200) * 3;
            ctx.fillStyle = '#ff3b3b';
            ctx.beginPath();
            ctx.arc(incidentX, incidentY, pulseSize, 0, Math.PI * 2);
            ctx.fill();

            // Incident icon
            ctx.fillStyle = '#fff';
            ctx.font = 'bold 10px sans-serif';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText('⚠', incidentX, incidentY);
        }

        // Get interpolated positions and draw cars
        const positions = getInterpolatedPositions(currentTime);
        if (positions) {
            // Draw competitors first
            positions.competitorPositions.forEach(comp => {
                const angle = comp.position.trackPosition * Math.PI * 2 - Math.PI / 2;
                const x = centerX + Math.cos(angle) * radius * 1.2;
                const y = centerY + Math.sin(angle) * radius * 0.8;

                ctx.fillStyle = '#666';
                ctx.beginPath();
                ctx.arc(x, y, 6, 0, Math.PI * 2);
                ctx.fill();
            });

            // Draw player on top
            const playerAngle = positions.playerPos.trackPosition * Math.PI * 2 - Math.PI / 2;
            const playerX = centerX + Math.cos(playerAngle) * radius * 1.2;
            const playerY = centerY + Math.sin(playerAngle) * radius * 0.8;

            ctx.fillStyle = '#00d4ff';
            ctx.beginPath();
            ctx.arc(playerX, playerY, 8, 0, Math.PI * 2);
            ctx.fill();

            // Player glow
            ctx.shadowColor = '#00d4ff';
            ctx.shadowBlur = 10;
            ctx.fill();
            ctx.shadowBlur = 0;
        }

        // Draw time indicator
        ctx.fillStyle = '#fff';
        ctx.font = 'bold 14px monospace';
        ctx.textAlign = 'center';
        const timeStr = currentTime >= 0 ? `+${(currentTime / 1000).toFixed(1)}s` : `${(currentTime / 1000).toFixed(1)}s`;
        ctx.fillText(timeStr, centerX, height - 10);

    }, [currentTime, incident, getInterpolatedPositions]);

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

    // Redraw when time changes
    useEffect(() => {
        draw();
    }, [draw, currentTime]);

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

            {/* Track Visualization */}
            <div className="replay-canvas-container">
                <canvas
                    ref={canvasRef}
                    width={300}
                    height={200}
                    className="replay-canvas"
                />
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
