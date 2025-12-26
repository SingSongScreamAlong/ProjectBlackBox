/**
 * IncidentTimeline - Event log with scrubber
 */

import React, { useEffect, useState } from 'react';
import './IncidentTimeline.css';

interface Incident {
    id: string;
    timestamp: number;
    lap: number;
    corner: string | null;
    drivers: Array<{
        driverId: string;
        driverName: string;
        overlapPercent: number;
        atFault: boolean | null;
    }>;
    type: 'contact' | 'unsafe_rejoin' | 'offtrack' | 'block' | 'push';
    description: string;
    severity: 'minor' | 'moderate' | 'major';
}

interface IncidentTimelineProps {
    sessionId: string;
    filterDriverId?: string;
}

const IncidentTimeline: React.FC<IncidentTimelineProps> = ({
    sessionId,
    filterDriverId
}) => {
    const [incidents, setIncidents] = useState<Incident[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchIncidents = async () => {
            try {
                const response = await fetch(`/api/broadcast/stats/${sessionId}/incidents`);
                if (response.ok) {
                    const data = await response.json();
                    let incidentList = data.incidents || [];

                    // Filter by driver if specified
                    if (filterDriverId) {
                        incidentList = incidentList.filter((inc: Incident) =>
                            inc.drivers.some(d => d.driverId === filterDriverId)
                        );
                    }

                    setIncidents(incidentList);
                }
            } catch (err) {
                console.error('Failed to fetch incidents:', err);
            } finally {
                setLoading(false);
            }
        };

        fetchIncidents();
        const interval = setInterval(fetchIncidents, 5000);
        return () => clearInterval(interval);
    }, [sessionId, filterDriverId]);

    const getTypeIcon = (type: string) => {
        const icons: Record<string, string> = {
            contact: '💥',
            unsafe_rejoin: '⚠️',
            offtrack: '🚗',
            block: '🚧',
            push: '👊',
        };
        return icons[type] || '❓';
    };

    const getSeverityClass = (severity: string) => {
        return `incident--${severity}`;
    };

    const formatTime = (timestamp: number): string => {
        const date = new Date(timestamp);
        return date.toLocaleTimeString('en-US', {
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    };

    if (loading) {
        return <div className="incident-timeline incident-timeline--loading">Loading...</div>;
    }

    if (incidents.length === 0) {
        return (
            <div className="incident-timeline incident-timeline--empty">
                <p>No incidents recorded</p>
                {filterDriverId && <small>Filtered for selected driver</small>}
            </div>
        );
    }

    return (
        <div className="incident-timeline">
            <h3>📋 Incident Timeline</h3>
            <div className="incident-timeline__list">
                {incidents.slice().reverse().map(incident => (
                    <div
                        key={incident.id}
                        className={`incident-timeline__item ${getSeverityClass(incident.severity)}`}
                    >
                        <div className="incident-timeline__time">
                            {formatTime(incident.timestamp)}
                        </div>

                        <div className="incident-timeline__icon">
                            {getTypeIcon(incident.type)}
                        </div>

                        <div className="incident-timeline__content">
                            <div className="incident-timeline__header">
                                <span className="incident-timeline__type">
                                    {incident.type.replace('_', ' ').toUpperCase()}
                                </span>
                                <span className="incident-timeline__lap">
                                    Lap {incident.lap}
                                </span>
                                {incident.corner && (
                                    <span className="incident-timeline__corner">
                                        {incident.corner}
                                    </span>
                                )}
                            </div>

                            <p className="incident-timeline__description">
                                {incident.description}
                            </p>

                            <div className="incident-timeline__drivers">
                                {incident.drivers.map(driver => (
                                    <span
                                        key={driver.driverId}
                                        className={`incident-timeline__driver ${driver.atFault === true ? 'incident-timeline__driver--fault' : ''
                                            }`}
                                    >
                                        {driver.driverName}
                                        {driver.atFault === true && ' (at fault)'}
                                        {driver.overlapPercent > 0 && (
                                            <small> ({Math.round(driver.overlapPercent * 100)}% overlap)</small>
                                        )}
                                    </span>
                                ))}
                            </div>
                        </div>

                        <div className={`incident-timeline__severity severity--${incident.severity}`}>
                            {incident.severity.toUpperCase()}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default IncidentTimeline;
