/**
 * IncidentScrubber - Interactive incident timeline with video sync
 * 
 * Allows viewers to scrub through incidents and sync with video playback.
 */

import React, { useState, useRef, useEffect } from 'react';
import './IncidentScrubber.css';

interface Incident {
    id: string;
    timestamp: number;
    lap: number;
    corner: string | null;
    drivers: { driverId: string; driverName: string }[];
    type: string;
    severity: 'minor' | 'moderate' | 'major';
    description: string;
}

interface IncidentScrubberProps {
    sessionId: string;
    incidents: Incident[];
    raceStartTime: number;
    raceDuration: number; // in seconds
    onSeek?: (timestamp: number) => void;
    currentTime?: number;
}

const IncidentScrubber: React.FC<IncidentScrubberProps> = ({
    sessionId,
    incidents,
    raceStartTime,
    raceDuration,
    onSeek,
    currentTime = 0,
}) => {
    const scrubberRef = useRef<HTMLDivElement>(null);
    const [hoveredIncident, setHoveredIncident] = useState<Incident | null>(null);
    const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
    const [isDragging, setIsDragging] = useState(false);

    // Calculate position percentage for an incident
    const getPositionPercent = (timestamp: number): number => {
        const elapsed = (timestamp - raceStartTime) / 1000;
        return Math.max(0, Math.min(100, (elapsed / raceDuration) * 100));
    };

    // Current playhead position
    const playheadPercent = (currentTime / raceDuration) * 100;

    // Handle click on timeline
    const handleTimelineClick = (e: React.MouseEvent) => {
        if (!scrubberRef.current || !onSeek) return;

        const rect = scrubberRef.current.getBoundingClientRect();
        const percent = (e.clientX - rect.left) / rect.width;
        const newTime = percent * raceDuration;
        onSeek(raceStartTime + newTime * 1000);
    };

    // Handle incident click
    const handleIncidentClick = (incident: Incident) => {
        setSelectedIncident(incident);
        if (onSeek) {
            onSeek(incident.timestamp);
        }
    };

    // Get severity color
    const getSeverityColor = (severity: string): string => {
        switch (severity) {
            case 'major': return '#ff3333';
            case 'moderate': return '#ff9900';
            default: return '#ffff00';
        }
    };

    // Get type icon
    const getTypeIcon = (type: string): string => {
        switch (type) {
            case 'contact': return '💥';
            case 'unsafe_rejoin': return '⚠️';
            case 'offtrack': return '🛤️';
            case 'block': return '🚫';
            case 'push': return '👋';
            default: return '❗';
        }
    };

    // Format time for display
    const formatTime = (seconds: number): string => {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    return (
        <div className="incident-scrubber">
            <header className="incident-scrubber__header">
                <h3>⚡ Incident Timeline</h3>
                <span className="incident-scrubber__count">
                    {incidents.length} incident{incidents.length !== 1 ? 's' : ''}
                </span>
            </header>

            <div
                className="incident-scrubber__timeline"
                ref={scrubberRef}
                onClick={handleTimelineClick}
            >
                {/* Track background */}
                <div className="incident-scrubber__track" />

                {/* Playhead */}
                <div
                    className="incident-scrubber__playhead"
                    style={{ left: `${playheadPercent}%` }}
                />

                {/* Incident markers */}
                {incidents.map(incident => {
                    const position = getPositionPercent(incident.timestamp);
                    return (
                        <div
                            key={incident.id}
                            className={`incident-scrubber__marker severity--${incident.severity} ${selectedIncident?.id === incident.id ? 'selected' : ''
                                }`}
                            style={{
                                left: `${position}%`,
                                backgroundColor: getSeverityColor(incident.severity),
                            }}
                            onMouseEnter={() => setHoveredIncident(incident)}
                            onMouseLeave={() => setHoveredIncident(null)}
                            onClick={(e) => {
                                e.stopPropagation();
                                handleIncidentClick(incident);
                            }}
                        >
                            <span className="marker-icon">{getTypeIcon(incident.type)}</span>
                        </div>
                    );
                })}

                {/* Time labels */}
                <div className="incident-scrubber__labels">
                    <span>0:00</span>
                    <span>{formatTime(raceDuration / 2)}</span>
                    <span>{formatTime(raceDuration)}</span>
                </div>
            </div>

            {/* Tooltip */}
            {hoveredIncident && (
                <div
                    className="incident-scrubber__tooltip"
                    style={{ left: `${getPositionPercent(hoveredIncident.timestamp)}%` }}
                >
                    <div className="tooltip-header">
                        <span className="icon">{getTypeIcon(hoveredIncident.type)}</span>
                        <span className="type">{hoveredIncident.type.replace('_', ' ')}</span>
                        <span className={`severity ${hoveredIncident.severity}`}>
                            {hoveredIncident.severity.toUpperCase()}
                        </span>
                    </div>
                    <div className="tooltip-body">
                        <p>{hoveredIncident.description}</p>
                        <span className="lap">Lap {hoveredIncident.lap}</span>
                        {hoveredIncident.corner && (
                            <span className="corner">• {hoveredIncident.corner}</span>
                        )}
                    </div>
                </div>
            )}

            {/* Selected incident detail */}
            {selectedIncident && (
                <div className="incident-scrubber__detail">
                    <div className="detail-header">
                        <span className="icon">{getTypeIcon(selectedIncident.type)}</span>
                        <h4>{selectedIncident.type.replace('_', ' ')}</h4>
                        <span className={`severity-badge ${selectedIncident.severity}`}>
                            {selectedIncident.severity}
                        </span>
                        <button
                            className="close-btn"
                            onClick={() => setSelectedIncident(null)}
                        >
                            ✕
                        </button>
                    </div>
                    <p className="description">{selectedIncident.description}</p>
                    <div className="drivers">
                        {selectedIncident.drivers.map((d, i) => (
                            <span key={d.driverId} className="driver-tag">
                                {d.driverName}
                            </span>
                        ))}
                    </div>
                    <div className="meta">
                        <span>Lap {selectedIncident.lap}</span>
                        {selectedIncident.corner && <span>{selectedIncident.corner}</span>}
                    </div>
                </div>
            )}
        </div>
    );
};

export default IncidentScrubber;
