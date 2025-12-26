/**
 * LiveTelemetryStrip - Compact live telemetry bar
 * 
 * A horizontal strip showing real-time telemetry for multiple drivers,
 * useful as an overlay or ticker at the bottom of the screen.
 */

import React, { useEffect, useState } from 'react';
import './LiveTelemetryStrip.css';

interface DriverTelemetry {
    driverId: string;
    carNumber: string;
    driverName: string;
    position: number;
    speed: number;
    gear: number;
    lastLapTime: number;
    delta: number;
    inPit: boolean;
}

interface LiveTelemetryStripProps {
    sessionId: string;
    driverIds?: string[]; // Filter to specific drivers, or show all
    maxDrivers?: number;
}

const LiveTelemetryStrip: React.FC<LiveTelemetryStripProps> = ({
    sessionId,
    driverIds,
    maxDrivers = 10,
}) => {
    const [drivers, setDrivers] = useState<DriverTelemetry[]>([]);

    useEffect(() => {
        // In production, this would connect to WebSocket
        // For now, polling the API
        const fetchTelemetry = async () => {
            try {
                const response = await fetch(`/api/broadcast/telemetry/${sessionId}/live`);
                if (response.ok) {
                    const data = await response.json();
                    let telemetryData = data.drivers || [];

                    // Filter if specific drivers requested
                    if (driverIds) {
                        telemetryData = telemetryData.filter((d: DriverTelemetry) =>
                            driverIds.includes(d.driverId)
                        );
                    }

                    // Sort by position and limit
                    telemetryData.sort((a: DriverTelemetry, b: DriverTelemetry) => a.position - b.position);
                    setDrivers(telemetryData.slice(0, maxDrivers));
                }
            } catch (err) {
                console.error('Failed to fetch live telemetry:', err);
            }
        };

        fetchTelemetry();
        const interval = setInterval(fetchTelemetry, 500); // High frequency updates
        return () => clearInterval(interval);
    }, [sessionId, driverIds, maxDrivers]);

    const formatLapTime = (seconds: number): string => {
        if (!seconds || seconds <= 0) return '--:--.---';
        const mins = Math.floor(seconds / 60);
        const secs = (seconds % 60).toFixed(3);
        return `${mins}:${secs.padStart(6, '0')}`;
    };

    const formatDelta = (delta: number): { text: string; class: string } => {
        if (!delta) return { text: '-.---', class: '' };
        const prefix = delta > 0 ? '+' : '';
        return {
            text: `${prefix}${delta.toFixed(3)}`,
            class: delta < 0 ? 'faster' : delta > 0 ? 'slower' : ''
        };
    };

    if (drivers.length === 0) {
        return null; // Hide if no data
    }

    return (
        <div className="telemetry-strip">
            <div className="telemetry-strip__scroll">
                {drivers.map((driver, index) => {
                    const delta = formatDelta(driver.delta);

                    return (
                        <div
                            key={driver.driverId}
                            className={`telemetry-strip__driver ${driver.inPit ? 'in-pit' : ''}`}
                        >
                            <span className="position">P{driver.position}</span>
                            <span className="number">#{driver.carNumber}</span>
                            <span className="name">{driver.driverName.split(' ').pop()}</span>
                            <span className={`delta ${delta.class}`}>{delta.text}</span>
                            <span className="lap-time">{formatLapTime(driver.lastLapTime)}</span>
                            <span className="speed">{Math.round(driver.speed)} km/h</span>
                            <span className="gear">G{driver.gear}</span>
                            {driver.inPit && <span className="pit-badge">PIT</span>}
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default LiveTelemetryStrip;
