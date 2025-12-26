/**
 * RaceHub - Main driver grid/list view
 * 
 * The entry point for BroadcastBox. Shows all drivers with live streams,
 * their positions, gaps, and status. Click to open Driver Hub.
 */

import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import DriverCard from './DriverCard';
import BattleMode from './BattleMode';
import './RaceHub.css';

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

interface RaceHubProps {
    sessionId?: string;
}

const RaceHub: React.FC<RaceHubProps> = ({ sessionId }) => {
    const navigate = useNavigate();
    const [streams, setStreams] = useState<DriverStream[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [filter, setFilter] = useState<string>('all');
    const [showBattles, setShowBattles] = useState(false);

    const [demoMode, setDemoMode] = useState(false);

    // Fetch available streams
    const fetchStreams = useCallback(async () => {
        if (!sessionId || sessionId === 'current') {
            // Demo mode - no real session
            setDemoMode(true);
            setLoading(false);
            return;
        }

        try {
            const response = await fetch(`/api/broadcast/streams?sessionId=${sessionId}`);

            // Check if response is JSON
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                // API not available - enter demo mode
                setDemoMode(true);
                setLoading(false);
                return;
            }

            if (!response.ok) throw new Error('Failed to fetch streams');

            const data = await response.json();
            setStreams(data.streams || []);
            setLoading(false);
        } catch (err) {
            // API error - enter demo mode instead of showing error
            console.warn('[RaceHub] API not available, entering demo mode:', err);
            setDemoMode(true);
            setLoading(false);
        }
    }, [sessionId]);

    useEffect(() => {
        fetchStreams();

        // Only poll if not in demo mode
        if (!demoMode) {
            const interval = setInterval(fetchStreams, 5000);
            return () => clearInterval(interval);
        }
    }, [fetchStreams, demoMode]);

    // Filter streams by class
    const filteredStreams = streams.filter(stream => {
        if (filter === 'all') return true;
        if (filter === 'live') return stream.status === 'live';
        return stream.className === filter;
    });

    // Get unique classes for filter
    const classSet = new Set(streams.map(s => s.className).filter(Boolean));
    const classes = Array.from(classSet);

    const handleDriverClick = (driverId: string) => {
        navigate(`/broadcast/driver/${driverId}`);
    };

    if (!sessionId) {
        return (
            <div className="race-hub race-hub--empty">
                <h1>🏎️ BroadcastBox</h1>
                <p>No active session. Waiting for race data...</p>
            </div>
        );
    }

    if (loading) {
        return (
            <div className="race-hub race-hub--loading">
                <div className="race-hub__spinner" />
                <p>Loading streams...</p>
            </div>
        );
    }

    if (demoMode && streams.length === 0) {
        // Import mock data engine dynamically
        const loadMockData = async () => {
            const { mockDataEngine } = await import('../../services/MockDataEngine');
            const mockStreams = mockDataEngine.getStreams();
            setStreams(mockStreams as unknown as DriverStream[]);
        };

        return (
            <div className="race-hub">
                <header className="race-hub__header">
                    <h1>🏎️ BroadcastBox</h1>
                    <div className="race-hub__controls">
                        <button
                            className="race-hub__mock-btn"
                            onClick={loadMockData}
                            style={{
                                background: 'linear-gradient(135deg, #ff9900, #ff6600)',
                                border: 'none',
                                padding: '0.5rem 1rem',
                                borderRadius: '6px',
                                color: '#000',
                                fontWeight: 600,
                                cursor: 'pointer',
                            }}
                        >
                            🧪 Load Mock Data
                        </button>
                    </div>
                </header>
                <div className="race-hub race-hub--empty" style={{ minHeight: '50vh' }}>
                    <div style={{ textAlign: 'center', maxWidth: '500px' }}>
                        <h2 style={{ color: '#00d4ff' }}>📺 No Live Streams</h2>
                        <p style={{ color: '#888', marginBottom: '1rem' }}>
                            Click "Load Mock Data" above to preview the UI with sample data.
                        </p>
                        <p style={{ color: '#666', fontSize: '0.85rem' }}>
                            Or connect to iRacing for real data.
                        </p>
                    </div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="race-hub race-hub--error">
                <h2>Error</h2>
                <p>{error}</p>
                <button onClick={fetchStreams}>Retry</button>
            </div>
        );
    }

    return (
        <div className="race-hub">
            <header className="race-hub__header">
                <h1>🏎️ BroadcastBox</h1>
                <div className="race-hub__controls">
                    <select
                        value={filter}
                        onChange={(e) => setFilter(e.target.value)}
                        className="race-hub__filter"
                    >
                        <option value="all">All Drivers</option>
                        <option value="live">Live Only</option>
                        {classes.map(cls => (
                            <option key={cls} value={cls}>{cls}</option>
                        ))}
                    </select>
                    <button
                        className={`race-hub__battle-btn ${showBattles ? 'active' : ''}`}
                        onClick={() => setShowBattles(!showBattles)}
                    >
                        ⚔️ Battles
                    </button>
                </div>
            </header>

            {showBattles && (
                <section className="race-hub__battles">
                    <BattleMode sessionId={sessionId} onDriverClick={handleDriverClick} />
                </section>
            )}

            <section className="race-hub__grid">
                {filteredStreams.length === 0 ? (
                    <p className="race-hub__empty">No streams available</p>
                ) : (
                    filteredStreams.map(stream => (
                        <DriverCard
                            key={stream.streamId}
                            driver={stream}
                            onClick={() => handleDriverClick(stream.driverId)}
                        />
                    ))
                )}
            </section>

            <footer className="race-hub__footer">
                <span>{streams.length} drivers</span>
                <span>•</span>
                <span>{streams.filter(s => s.status === 'live').length} live streams</span>
            </footer>
        </div>
    );
};

export default RaceHub;
