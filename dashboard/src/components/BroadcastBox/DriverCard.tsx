/**
 * DriverCard - Compact driver status card
 */

import React from 'react';
import './DriverCard.css';

interface DriverStream {
    driverId: string;
    driverName: string;
    carNumber: string;
    teamName: string;
    streamId: string;
    status: 'live' | 'starting' | 'offline' | 'degraded';
    resolution: string;
    fps: number;
    accessLevel: string;
    viewerCount: number;
    position: number;
    classId: number;
    className: string;
}

interface DriverCardProps {
    driver: DriverStream;
    onClick: () => void;
}

const DriverCard: React.FC<DriverCardProps> = ({ driver, onClick }) => {
    const statusColors: Record<string, string> = {
        live: '#00ff00',
        starting: '#ffff00',
        degraded: '#ff9900',
        offline: '#666666',
    };

    return (
        <div
            className={`driver-card driver-card--${driver.status}`}
            onClick={onClick}
        >
            <div className="driver-card__position">
                P{driver.position || '?'}
            </div>

            <div className="driver-card__info">
                <div className="driver-card__name">
                    <span className="driver-card__number">#{driver.carNumber || '00'}</span>
                    {driver.driverName}
                </div>
                <div className="driver-card__team">{driver.teamName || 'Independent'}</div>
                {driver.className && (
                    <div className="driver-card__class">{driver.className}</div>
                )}
            </div>

            <div className="driver-card__stream">
                <span
                    className="driver-card__status-dot"
                    style={{ backgroundColor: statusColors[driver.status] }}
                />
                <span className="driver-card__status-text">
                    {driver.status === 'live' ? 'LIVE' : driver.status.toUpperCase()}
                </span>
                {driver.viewerCount > 0 && (
                    <span className="driver-card__viewers">
                        👁 {driver.viewerCount}
                    </span>
                )}
            </div>
        </div>
    );
};

export default DriverCard;
