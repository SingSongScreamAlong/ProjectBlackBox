/**
 * DriverHub - Individual driver view with stream + telemetry
 * 
 * Shows the driver's onboard camera with live telemetry overlay,
 * lap/sector deltas, and incident timeline.
 */

import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import StreamPlayer from './StreamPlayer';
import TelemetryOverlay from './TelemetryOverlay';
import IncidentTimeline from './IncidentTimeline';
import './DriverHub.css';

interface DriverStats {
    paceModel: {
        cleanLapAvg: number;
        cleanLapStdDev: number;
        lastCleanLap: number | null;
        cleanLapCount: number;
        confidence: number;
    };
    currentDelta: {
        vsPersonalBest: number;
        vsLeader: number;
        vsBehind: number;
        sector: number;
    };
    predictedGap: {
        ahead: number;
        behind: number;
        inLaps: number;
        confidence: number;
    };
    tireModel: {
        estimatedWear: number;
        estimatedLapsRemaining: number;
        degradationRate: number;
        confidence: number;
    };
    fuelModel: {
        currentFuel: number;
        fuelPerLap: number;
        lapsRemaining: number;
        canFinish: boolean;
        confidence: number;
    };
}

interface DriverHubProps {
    sessionId?: string;
}

const DriverHub: React.FC<DriverHubProps> = ({ sessionId }) => {
    const { driverId } = useParams<{ driverId: string }>();
    const navigate = useNavigate();

    const [streamId, setStreamId] = useState<string | null>(null);
    const [driverName, setDriverName] = useState<string>('');
    const [stats, setStats] = useState<DriverStats | null>(null);
    const [showOverlay, setShowOverlay] = useState(true);
    const [showTimeline, setShowTimeline] = useState(false);
    const [quality, setQuality] = useState<'auto' | 'low' | 'med' | 'high'>('auto');

    const [mockMode, setMockMode] = useState(false);

    // Fetch stream info for this driver
    useEffect(() => {
        if (!driverId) return;

        const fetchStreamInfo = async () => {
            // First try real API
            if (sessionId && sessionId !== 'current') {
                try {
                    const response = await fetch(`/api/broadcast/streams?sessionId=${sessionId}`);
                    const contentType = response.headers.get('content-type');
                    if (contentType?.includes('application/json')) {
                        const data = await response.json();
                        const driverStream = data.streams?.find(
                            (s: any) => s.driverId === driverId
                        );
                        if (driverStream) {
                            setStreamId(driverStream.streamId);
                            setDriverName(driverStream.driverName);
                            return;
                        }
                    }
                } catch (err) {
                    console.log('[DriverHub] API unavailable, using mock data');
                }
            }

            // Fallback to mock data
            const { MOCK_DRIVERS } = await import('../../services/MockDataEngine');
            const mockDriver = MOCK_DRIVERS.find(d => d.driverId === driverId);
            if (mockDriver) {
                setStreamId(`stream-${mockDriver.driverId}`);
                setDriverName(mockDriver.driverName);
                setMockMode(true);
            }
        };

        fetchStreamInfo();
    }, [sessionId, driverId]);

    // Fetch driver stats
    useEffect(() => {
        if (!driverId) return;

        const fetchStats = async () => {
            // First try real API
            if (sessionId && sessionId !== 'current') {
                try {
                    const response = await fetch(
                        `/api/broadcast/stats/${sessionId}/driver/${driverId}`
                    );
                    if (response.ok) {
                        const data = await response.json();
                        setStats(data.data);
                        return;
                    }
                } catch (err) {
                    console.log('[DriverHub] Stats API unavailable, using mock data');
                }
            }

            // Fallback to mock data
            const { generateMockDriverStats } = await import('../../services/MockDataEngine');
            const mockStats = generateMockDriverStats(driverId);
            // Convert to expected format
            setStats({
                paceModel: {
                    cleanLapAvg: mockStats.paceModel.rollingAvgPace,
                    cleanLapStdDev: 0.15,
                    lastCleanLap: mockStats.paceModel.currentPace,
                    cleanLapCount: 12,
                    confidence: mockStats.paceModel.consistency,
                },
                currentDelta: {
                    vsPersonalBest: mockStats.paceModel.currentPace - mockStats.paceModel.bestPace,
                    vsLeader: mockStats.gaps.toLeader,
                    vsBehind: mockStats.gaps.toBehind,
                    sector: 2,
                },
                predictedGap: {
                    ahead: mockStats.gaps.toAhead,
                    behind: mockStats.gaps.toBehind,
                    inLaps: mockStats.gaps.predictedOvertake?.inLaps || 0,
                    confidence: mockStats.gaps.predictedOvertake?.confidence || 0.5,
                },
                tireModel: {
                    estimatedWear: mockStats.tireModel.lapsOnTires * 3,
                    estimatedLapsRemaining: 30 - mockStats.tireModel.lapsOnTires,
                    degradationRate: mockStats.tireModel.degradationRate,
                    confidence: 0.7,
                },
                fuelModel: {
                    currentFuel: mockStats.fuelModel.currentFuel,
                    fuelPerLap: mockStats.fuelModel.consumptionPerLap,
                    lapsRemaining: mockStats.fuelModel.estimatedLapsRemaining,
                    canFinish: mockStats.fuelModel.estimatedLapsRemaining > 5,
                    confidence: 0.8,
                },
            });
        };

        fetchStats();
        const interval = setInterval(fetchStats, 2000);
        return () => clearInterval(interval);
    }, [sessionId, driverId]);

    const formatDelta = (delta: number): string => {
        const sign = delta >= 0 ? '+' : '';
        return `${sign}${delta.toFixed(3)}s`;
    };

    const getDeltaClass = (delta: number): string => {
        if (delta < 0) return 'delta--faster';
        if (delta > 0.5) return 'delta--slower';
        return 'delta--neutral';
    };

    if (!sessionId || !driverId) {
        return (
            <div className="driver-hub driver-hub--empty">
                <p>No driver selected</p>
                <button onClick={() => navigate('/broadcast')}>Back to Race Hub</button>
            </div>
        );
    }

    return (
        <div className="driver-hub">
            <header className="driver-hub__header">
                <button
                    className="driver-hub__back"
                    onClick={() => navigate('/broadcast')}
                >
                    ← Back
                </button>
                <h1>{driverName || 'Loading...'}</h1>
                <div className="driver-hub__controls">
                    <button
                        className={showOverlay ? 'active' : ''}
                        onClick={() => setShowOverlay(!showOverlay)}
                    >
                        📊 Telemetry
                    </button>
                    <button
                        className={showTimeline ? 'active' : ''}
                        onClick={() => setShowTimeline(!showTimeline)}
                    >
                        📋 Timeline
                    </button>
                    <select
                        value={quality}
                        onChange={(e) => setQuality(e.target.value as any)}
                    >
                        <option value="auto">Auto Quality</option>
                        <option value="low">Low (480p)</option>
                        <option value="med">Medium (720p)</option>
                        <option value="high">High (1080p)</option>
                    </select>
                </div>
            </header>

            <main className="driver-hub__content">
                <div className="driver-hub__video">
                    {streamId ? (
                        <StreamPlayer
                            streamId={streamId}
                            quality={quality}
                        />
                    ) : (
                        <div className="driver-hub__no-stream">
                            <p>Stream not available</p>
                        </div>
                    )}

                    {showOverlay && stats && (
                        <TelemetryOverlay
                            driverId={driverId}
                            sessionId={sessionId}
                        />
                    )}

                    {/* Floating glass stat cards */}
                    {stats && (
                        <aside className="driver-hub__stats">
                            <div className="stat-card">
                                <h3>Delta to PB</h3>
                                <span className={getDeltaClass(stats.currentDelta.vsPersonalBest)}>
                                    {formatDelta(stats.currentDelta.vsPersonalBest)}
                                </span>
                            </div>
                            <div className="stat-card">
                                <h3>Gap Ahead</h3>
                                <span>{stats.predictedGap.ahead.toFixed(1)}s</span>
                                {stats.predictedGap.confidence < 0.7 && (
                                    <small className="confidence-warning">
                                        ⚠️ Low confidence
                                    </small>
                                )}
                            </div>
                            <div className="stat-card">
                                <h3>Gap Behind</h3>
                                <span>{stats.predictedGap.behind.toFixed(1)}s</span>
                            </div>
                            <div className="stat-card">
                                <h3>Pace (Clean)</h3>
                                <span>{stats.paceModel.cleanLapAvg.toFixed(3)}s</span>
                                <small>σ {stats.paceModel.cleanLapStdDev.toFixed(3)}s</small>
                            </div>
                            <div className="stat-card">
                                <h3>Fuel</h3>
                                <span>{stats.fuelModel.lapsRemaining} laps</span>
                                {!stats.fuelModel.canFinish && (
                                    <small className="fuel-warning">⚠️ Pit needed</small>
                                )}
                            </div>
                            <div className="stat-card">
                                <h3>Tire Wear</h3>
                                <span>{stats.tireModel.estimatedWear.toFixed(0)}%</span>
                                <small>{stats.tireModel.estimatedLapsRemaining} laps left</small>
                            </div>
                        </aside>
                    )}
                </div>
            </main>

            {showTimeline && (
                <section className="driver-hub__timeline">
                    <IncidentTimeline
                        sessionId={sessionId}
                        filterDriverId={driverId}
                    />
                </section>
            )}
        </div>
    );
};

export default DriverHub;

