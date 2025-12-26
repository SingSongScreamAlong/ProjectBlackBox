/**
 * Leaderboard - Live race standings with gaps and timing
 * 
 * F1 TV-style timing tower showing positions, gaps, and status.
 */

import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Leaderboard.css';

interface DriverStanding {
    position: number;
    driverId: string;
    driverName: string;
    carNumber: string;
    teamName: string;
    gapToLeader: number | null;
    gapToAhead: number | null;
    lastLapTime: number;
    bestLapTime: number;
    currentLap: number;
    inPit: boolean;
    hasFastestLap: boolean;
    status: 'racing' | 'pit' | 'out' | 'finished';
}

interface LeaderboardProps {
    sessionId: string;
    onDriverClick?: (driverId: string) => void;
    compact?: boolean;
    maxDrivers?: number;
}

const Leaderboard: React.FC<LeaderboardProps> = ({
    sessionId,
    onDriverClick,
    compact = false,
    maxDrivers = 20,
}) => {
    const navigate = useNavigate();
    const [standings, setStandings] = useState<DriverStanding[]>([]);
    const [loading, setLoading] = useState(true);
    const [fastestLap, setFastestLap] = useState<{ time: number; driverId: string } | null>(null);

    useEffect(() => {
        const fetchStandings = async () => {
            // Try real API first
            if (sessionId && sessionId !== 'current') {
                try {
                    const response = await fetch(`/api/broadcast/standings/${sessionId}`);
                    if (response.ok) {
                        const data = await response.json();
                        if (data.standings?.length > 0) {
                            setStandings(data.standings);
                            setLoading(false);
                            return;
                        }
                    }
                } catch (err) {
                    console.log('[Leaderboard] API unavailable, using mock data');
                }
            }

            // Fallback to mock data
            const { MOCK_DRIVERS, generateMockTelemetry } = await import('../../services/MockDataEngine');
            const mockStandings: DriverStanding[] = MOCK_DRIVERS.map((driver, index) => {
                const telemetry = generateMockTelemetry(driver, index + 1);
                const lapTime = 80.5 + Math.random() * 2;
                return {
                    position: index + 1,
                    driverId: driver.driverId,
                    driverName: driver.driverName,
                    carNumber: driver.carNumber,
                    teamName: driver.teamName,
                    gapToLeader: index === 0 ? null : (index * 1.5 + Math.random()),
                    gapToAhead: index === 0 ? null : (1.2 + Math.random() * 0.8),
                    lastLapTime: lapTime,
                    bestLapTime: 80.123 + index * 0.1,
                    currentLap: 18 - Math.floor(index / 3),
                    inPit: index === 5, // Sainz in pit
                    hasFastestLap: index === 0,
                    status: index === 5 ? 'pit' : 'racing',
                };
            });

            // Find fastest lap
            const fastest = mockStandings.reduce((prev, curr) =>
                curr.bestLapTime < prev.bestLapTime ? curr : prev
            );
            setFastestLap({ time: fastest.bestLapTime, driverId: fastest.driverId });

            setStandings(mockStandings);
            setLoading(false);
        };

        fetchStandings();
        const interval = setInterval(fetchStandings, 2000);
        return () => clearInterval(interval);
    }, [sessionId]);

    const formatTime = (seconds: number): string => {
        if (!seconds || seconds <= 0) return '--:--.---';
        const mins = Math.floor(seconds / 60);
        const secs = (seconds % 60).toFixed(3);
        return `${mins}:${secs.padStart(6, '0')}`;
    };

    const formatGap = (gap: number | null): string => {
        if (gap === null) return '';
        if (gap < 60) return `+${gap.toFixed(1)}s`;
        const mins = Math.floor(gap / 60);
        const secs = (gap % 60).toFixed(1);
        return `+${mins}:${secs}`;
    };

    const handleDriverClick = (driverId: string) => {
        if (onDriverClick) {
            onDriverClick(driverId);
        } else {
            navigate(`/broadcast/driver/${driverId}`);
        }
    };

    if (loading) {
        return <div className="leaderboard leaderboard--loading">Loading standings...</div>;
    }

    return (
        <div className={`leaderboard ${compact ? 'leaderboard--compact' : ''}`}>
            <header className="leaderboard__header">
                <h2>🏆 Race Standings</h2>
                <span className="leaderboard__lap">LAP {standings[0]?.currentLap || 0}</span>
            </header>

            <div className="leaderboard__table">
                <div className="leaderboard__row leaderboard__row--header">
                    <span className="col-pos">POS</span>
                    <span className="col-driver">DRIVER</span>
                    {!compact && <span className="col-gap">GAP</span>}
                    <span className="col-interval">INT</span>
                    {!compact && <span className="col-last">LAST</span>}
                    {!compact && <span className="col-best">BEST</span>}
                </div>

                {standings.slice(0, maxDrivers).map((driver, index) => (
                    <div
                        key={driver.driverId}
                        className={`leaderboard__row ${driver.inPit ? 'leaderboard__row--pit' : ''} ${driver.hasFastestLap ? 'leaderboard__row--fastest' : ''
                            }`}
                        style={{ animationDelay: `${index * 0.05}s` }}
                        onClick={() => handleDriverClick(driver.driverId)}
                    >
                        <span className="col-pos">
                            <span className={`position-badge p${driver.position}`}>
                                {driver.position}
                            </span>
                        </span>
                        <span className="col-driver">
                            <span className="car-number">#{driver.carNumber}</span>
                            <span className="driver-name">{driver.driverName.split(' ').pop()}</span>
                            {driver.inPit && <span className="pit-badge">PIT</span>}
                        </span>
                        {!compact && (
                            <span className="col-gap">{formatGap(driver.gapToLeader)}</span>
                        )}
                        <span className="col-interval">
                            {driver.position === 1 ? 'LEADER' : formatGap(driver.gapToAhead)}
                        </span>
                        {!compact && (
                            <span className={`col-last ${driver.lastLapTime === driver.bestLapTime ? 'personal-best' : ''}`}>
                                {formatTime(driver.lastLapTime)}
                            </span>
                        )}
                        {!compact && (
                            <span className={`col-best ${driver.hasFastestLap ? 'fastest-lap' : ''}`}>
                                {formatTime(driver.bestLapTime)}
                                {driver.hasFastestLap && <span className="fl-badge">FL</span>}
                            </span>
                        )}
                    </div>
                ))}
            </div>

            {fastestLap && (
                <footer className="leaderboard__footer">
                    <span className="fastest-lap-info">
                        ⚡ Fastest Lap: {formatTime(fastestLap.time)}
                    </span>
                </footer>
            )}
        </div>
    );
};

export default Leaderboard;
