/**
 * Team Session Selector Page
 * 
 * Lists available sessions for the team pit wall view.
 * Requires BlackBox license with pitwall_view capability.
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { socketClient } from '../lib/socket-client';
import './SurfaceHome.css';

interface SessionEntry {
    sessionId: string;
    trackName: string;
    sessionType: string;
    driverCount: number;
    isLive: boolean;
}

export const TeamSessionList: React.FC = () => {
    const navigate = useNavigate();
    const [sessions, setSessions] = useState<SessionEntry[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Fetch active sessions
        const fetchSessions = async () => {
            try {
                const res = await fetch('/api/sessions/active');
                if (res.ok) {
                    const data = await res.json();
                    setSessions(data.sessions || []);
                }
            } catch (err) {
                console.error('Failed to fetch sessions:', err);
            } finally {
                setLoading(false);
            }
        };

        fetchSessions();

        // Listen for new sessions
        socketClient.on('onSessionActive', (msg: any) => {
            setSessions(prev => {
                const exists = prev.find(s => s.sessionId === msg.sessionId);
                if (exists) return prev;
                return [...prev, {
                    sessionId: msg.sessionId,
                    trackName: msg.trackName,
                    sessionType: msg.sessionType,
                    driverCount: msg.driverCount || 1,
                    isLive: true
                }];
            });
        });

        return () => {
            socketClient.off('onSessionActive');
        };
    }, []);

    return (
        <div className="surface-home">
            <header className="surface-header">
                <h1>Team Pit Wall</h1>
                <p>Select a session to monitor</p>
            </header>

            <div className="session-list">
                {loading ? (
                    <div className="loading">Loading sessions...</div>
                ) : sessions.length === 0 ? (
                    <div className="empty-state">
                        <p>No active sessions</p>
                        <p className="hint">Start recording from the relay agent to see sessions here</p>
                    </div>
                ) : (
                    sessions.map(session => (
                        <div
                            key={session.sessionId}
                            className="session-card"
                            onClick={() => navigate(`/team/${session.sessionId}`)}
                        >
                            <div className="session-info">
                                <span className="track-name">{session.trackName}</span>
                                <span className="session-type">{session.sessionType}</span>
                            </div>
                            <div className="session-meta">
                                <span className="driver-count">{session.driverCount} drivers</span>
                                {session.isLive && <span className="live-badge">● LIVE</span>}
                            </div>
                        </div>
                    ))
                )}
            </div>

            <footer className="surface-footer">
                <button onClick={() => navigate('/home')} className="back-btn">
                    ← Back to Launchpad
                </button>
            </footer>
        </div>
    );
};

export default TeamSessionList;
