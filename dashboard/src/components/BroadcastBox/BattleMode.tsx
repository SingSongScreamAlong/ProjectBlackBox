/**
 * BattleMode - Auto-detected closest battles view
 */

import React, { useEffect, useState } from 'react';
import './BattleMode.css';

interface Battle {
    id: string;
    drivers: string[];
    gapSeconds: number;
    overlapPercent: number;
    twoWide: boolean;
    threeWide: boolean;
    riskLevel: 'low' | 'medium' | 'high';
    corner: string | null;
    lap: number;
    timestamp: number;
}

interface BattleModeProps {
    sessionId: string;
    onDriverClick?: (driverId: string) => void;
}

const BattleMode: React.FC<BattleModeProps> = ({ sessionId, onDriverClick }) => {
    const [battles, setBattles] = useState<Battle[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchBattles = async () => {
            // Try real API first
            if (sessionId && sessionId !== 'current') {
                try {
                    const response = await fetch(`/api/broadcast/stats/${sessionId}/battles`);
                    if (response.ok) {
                        const contentType = response.headers.get('content-type');
                        if (contentType?.includes('application/json')) {
                            const data = await response.json();
                            if (data.battles?.length > 0) {
                                setBattles(data.battles);
                                setLoading(false);
                                return;
                            }
                        }
                    }
                } catch (err) {
                    console.log('[BattleMode] API unavailable, using mock data');
                }
            }

            // Fallback to mock battles
            const { generateMockBattles } = await import('../../services/MockDataEngine');
            const mockBattles = generateMockBattles();
            // Convert to expected format
            setBattles(mockBattles.map(b => ({
                id: b.id,
                drivers: b.drivers,
                gapSeconds: b.gapSeconds,
                overlapPercent: b.gapSeconds < 0.5 ? 0.8 : 0.3,
                twoWide: b.twoWide,
                threeWide: b.threeWide,
                riskLevel: b.riskLevel,
                corner: b.corner,
                lap: b.lap,
                timestamp: Date.now(),
            })));
            setLoading(false);
        };

        fetchBattles();
        const interval = setInterval(fetchBattles, 3000);
        return () => clearInterval(interval);
    }, [sessionId]);

    const getRiskBadge = (risk: string) => {
        const badges: Record<string, { color: string; text: string }> = {
            high: { color: '#ff3333', text: '🔥 HIGH RISK' },
            medium: { color: '#ff9900', text: '⚠️ MEDIUM' },
            low: { color: '#66cc66', text: '✓ LOW' },
        };
        return badges[risk] || badges.low;
    };

    if (loading) {
        return <div className="battle-mode battle-mode--loading">Loading battles...</div>;
    }

    if (battles.length === 0) {
        return (
            <div className="battle-mode battle-mode--empty">
                <p>No active battles detected</p>
                <small>Battles appear when drivers are within 2 seconds of each other</small>
            </div>
        );
    }

    return (
        <div className="battle-mode">
            <h3>⚔️ Active Battles</h3>
            <div className="battle-mode__list">
                {battles.slice(0, 5).map(battle => {
                    const riskBadge = getRiskBadge(battle.riskLevel);

                    return (
                        <div
                            key={battle.id}
                            className={`battle-mode__card battle-mode__card--${battle.riskLevel}`}
                        >
                            <div className="battle-mode__header">
                                <span
                                    className="battle-mode__risk"
                                    style={{ color: riskBadge.color }}
                                >
                                    {riskBadge.text}
                                </span>
                                <span className="battle-mode__gap">
                                    {battle.gapSeconds.toFixed(3)}s
                                </span>
                            </div>

                            <div className="battle-mode__drivers">
                                {battle.drivers.map((driverId, idx) => (
                                    <React.Fragment key={driverId}>
                                        <button
                                            className="battle-mode__driver"
                                            onClick={() => onDriverClick?.(driverId)}
                                        >
                                            {driverId}
                                        </button>
                                        {idx < battle.drivers.length - 1 && (
                                            <span className="battle-mode__vs">vs</span>
                                        )}
                                    </React.Fragment>
                                ))}
                            </div>

                            <div className="battle-mode__meta">
                                {battle.threeWide && (
                                    <span className="battle-mode__badge battle-mode__badge--3wide">
                                        3-WIDE
                                    </span>
                                )}
                                {battle.twoWide && !battle.threeWide && (
                                    <span className="battle-mode__badge battle-mode__badge--2wide">
                                        2-WIDE
                                    </span>
                                )}
                                {battle.corner && (
                                    <span className="battle-mode__corner">{battle.corner}</span>
                                )}
                                <span className="battle-mode__lap">Lap {battle.lap}</span>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default BattleMode;
