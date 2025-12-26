/**
 * StatsPanel - Driver stats display panel
 * 
 * Shows pace model, gap predictions, tire/fuel models with confidence indicators.
 */

import React, { useEffect, useState } from 'react';
import './StatsPanel.css';

interface PaceModel {
    currentPace: number;
    rollingAvgPace: number;
    bestPace: number;
    consistency: number;
    trend: 'improving' | 'stable' | 'degrading';
}

interface GapPrediction {
    inLaps: number;
    withPaceAdvantage: number;
    confidence: number;
}

interface TireModel {
    compound: string;
    lapsOnTires: number;
    estimatedGripLoss: number;
    degradationRate: number;
}

interface FuelModel {
    currentFuel: number;
    consumptionPerLap: number;
    estimatedLapsRemaining: number;
    pitWindowLap: number | null;
}

interface DriverStats {
    paceModel: PaceModel;
    gaps: {
        toLeader: number;
        toBehind: number;
        toAhead: number;
        predictedOvertake: GapPrediction | null;
    };
    tireModel: TireModel;
    fuelModel: FuelModel;
}

interface StatsPanelProps {
    driverId: string;
    sessionId: string;
    compact?: boolean;
}

const StatsPanel: React.FC<StatsPanelProps> = ({ driverId, sessionId, compact = false }) => {
    const [stats, setStats] = useState<DriverStats | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const response = await fetch(`/api/broadcast/stats/${sessionId}/driver/${driverId}`);
                if (response.ok) {
                    const data = await response.json();
                    setStats(data);
                }
            } catch (err) {
                console.error('Failed to fetch stats:', err);
            } finally {
                setLoading(false);
            }
        };

        fetchStats();
        const interval = setInterval(fetchStats, 2000);
        return () => clearInterval(interval);
    }, [driverId, sessionId]);

    const formatTime = (seconds: number): string => {
        if (!seconds || seconds <= 0) return '--:--.---';
        const mins = Math.floor(seconds / 60);
        const secs = (seconds % 60).toFixed(3);
        return `${mins}:${secs.padStart(6, '0')}`;
    };

    const formatDelta = (seconds: number): { text: string; class: string } => {
        if (!seconds) return { text: '--', class: 'neutral' };
        const prefix = seconds > 0 ? '+' : '-';
        const abs = Math.abs(seconds);
        return {
            text: `${prefix}${abs.toFixed(3)}`,
            class: seconds < 0 ? 'faster' : seconds > 0 ? 'slower' : 'neutral'
        };
    };

    const getConfidenceColor = (confidence: number): string => {
        if (confidence >= 0.8) return '#00ff00';
        if (confidence >= 0.5) return '#ffff00';
        return '#ff6600';
    };

    const getTrendIcon = (trend: string): string => {
        switch (trend) {
            case 'improving': return '📈';
            case 'degrading': return '📉';
            default: return '➡️';
        }
    };

    if (loading) {
        return <div className="stats-panel stats-panel--loading">Loading stats...</div>;
    }

    if (!stats) {
        return (
            <div className="stats-panel stats-panel--empty">
                <p>No stats available</p>
                <small>Stats appear when telemetry is received</small>
            </div>
        );
    }

    if (compact) {
        return (
            <div className="stats-panel stats-panel--compact">
                <div className="stat-row">
                    <span className="label">Pace</span>
                    <span className="value">{formatTime(stats.paceModel.currentPace)}</span>
                </div>
                <div className="stat-row">
                    <span className="label">Gap</span>
                    <span className={`value ${formatDelta(stats.gaps.toAhead).class}`}>
                        {formatDelta(stats.gaps.toAhead).text}
                    </span>
                </div>
                <div className="stat-row">
                    <span className="label">Tires</span>
                    <span className="value">{stats.tireModel.lapsOnTires}L</span>
                </div>
                <div className="stat-row">
                    <span className="label">Fuel</span>
                    <span className="value">{stats.fuelModel.estimatedLapsRemaining.toFixed(1)}L</span>
                </div>
            </div>
        );
    }

    return (
        <div className="stats-panel">
            {/* Pace Section */}
            <section className="stats-panel__section">
                <h3>
                    Pace {getTrendIcon(stats.paceModel.trend)}
                </h3>
                <div className="stats-grid">
                    <div className="stat-card">
                        <span className="label">Current</span>
                        <span className="value">{formatTime(stats.paceModel.currentPace)}</span>
                    </div>
                    <div className="stat-card">
                        <span className="label">Best</span>
                        <span className="value best">{formatTime(stats.paceModel.bestPace)}</span>
                    </div>
                    <div className="stat-card">
                        <span className="label">Avg</span>
                        <span className="value">{formatTime(stats.paceModel.rollingAvgPace)}</span>
                    </div>
                    <div className="stat-card">
                        <span className="label">Consistency</span>
                        <span className="value">{(stats.paceModel.consistency * 100).toFixed(0)}%</span>
                    </div>
                </div>
            </section>

            {/* Gap Section */}
            <section className="stats-panel__section">
                <h3>Gaps</h3>
                <div className="stats-grid">
                    <div className="stat-card">
                        <span className="label">To Leader</span>
                        <span className={`value ${formatDelta(stats.gaps.toLeader).class}`}>
                            {formatDelta(stats.gaps.toLeader).text}
                        </span>
                    </div>
                    <div className="stat-card">
                        <span className="label">Car Ahead</span>
                        <span className={`value ${formatDelta(stats.gaps.toAhead).class}`}>
                            {formatDelta(stats.gaps.toAhead).text}
                        </span>
                    </div>
                    <div className="stat-card">
                        <span className="label">Car Behind</span>
                        <span className={`value ${formatDelta(-stats.gaps.toBehind).class}`}>
                            {formatDelta(-stats.gaps.toBehind).text}
                        </span>
                    </div>
                    {stats.gaps.predictedOvertake && (
                        <div className="stat-card prediction">
                            <span className="label">Overtake In</span>
                            <span className="value">{stats.gaps.predictedOvertake.inLaps} laps</span>
                            <span
                                className="confidence"
                                style={{ color: getConfidenceColor(stats.gaps.predictedOvertake.confidence) }}
                            >
                                {(stats.gaps.predictedOvertake.confidence * 100).toFixed(0)}% conf
                            </span>
                        </div>
                    )}
                </div>
            </section>

            {/* Tire Section */}
            <section className="stats-panel__section">
                <h3>Tires</h3>
                <div className="stats-grid">
                    <div className="stat-card">
                        <span className="label">Compound</span>
                        <span className="value compound">{stats.tireModel.compound}</span>
                    </div>
                    <div className="stat-card">
                        <span className="label">Laps</span>
                        <span className="value">{stats.tireModel.lapsOnTires}</span>
                    </div>
                    <div className="stat-card">
                        <span className="label">Grip Loss</span>
                        <span className="value warn">
                            -{(stats.tireModel.estimatedGripLoss * 100).toFixed(1)}%
                        </span>
                    </div>
                    <div className="stat-card">
                        <span className="label">Deg Rate</span>
                        <span className="value">
                            {(stats.tireModel.degradationRate * 100).toFixed(2)}%/lap
                        </span>
                    </div>
                </div>
            </section>

            {/* Fuel Section */}
            <section className="stats-panel__section">
                <h3>
                    Fuel
                    {stats.fuelModel.estimatedLapsRemaining < 3 && (
                        <span className="warning-badge">⚠️ LOW</span>
                    )}
                </h3>
                <div className="stats-grid">
                    <div className="stat-card">
                        <span className="label">Current</span>
                        <span className="value">{stats.fuelModel.currentFuel.toFixed(1)}L</span>
                    </div>
                    <div className="stat-card">
                        <span className="label">Per Lap</span>
                        <span className="value">{stats.fuelModel.consumptionPerLap.toFixed(2)}L</span>
                    </div>
                    <div className="stat-card">
                        <span className="label">Laps Left</span>
                        <span className={`value ${stats.fuelModel.estimatedLapsRemaining < 3 ? 'critical' : ''}`}>
                            {stats.fuelModel.estimatedLapsRemaining.toFixed(1)}
                        </span>
                    </div>
                    {stats.fuelModel.pitWindowLap && (
                        <div className="stat-card">
                            <span className="label">Pit Window</span>
                            <span className="value">Lap {stats.fuelModel.pitWindowLap}</span>
                        </div>
                    )}
                </div>
            </section>
        </div>
    );
};

export default StatsPanel;
