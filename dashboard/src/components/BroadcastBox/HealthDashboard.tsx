/**
 * HealthDashboard - Admin view for BroadcastBox system health
 * 
 * Shows connection stats, stream health, alerts, and metrics.
 */

import React, { useEffect, useState } from 'react';
import './HealthDashboard.css';

interface ConnectionStats {
    socketId: string;
    driverId?: string;
    viewerId?: string;
    connectionQuality: 'excellent' | 'good' | 'fair' | 'poor';
    avgLatencyMs: number;
    errorCount: number;
}

interface StreamStats {
    streamId: string;
    driverId: string;
    viewers: number;
    fps: number;
    bitrate: number;
}

interface Alert {
    id: string;
    type: string;
    severity: 'info' | 'warning' | 'error';
    message: string;
    timestamp: number;
}

interface Metrics {
    totalConnections: number;
    totalStreams: number;
    totalViewers: number;
    avgLatency: number;
    alertCount: number;
    connectionQuality: Record<string, number>;
}

interface HealthDashboardProps {
    refreshInterval?: number;
}

const HealthDashboard: React.FC<HealthDashboardProps> = ({ refreshInterval = 5000 }) => {
    const [metrics, setMetrics] = useState<Metrics | null>(null);
    const [connections, setConnections] = useState<ConnectionStats[]>([]);
    const [streams, setStreams] = useState<StreamStats[]>([]);
    const [alerts, setAlerts] = useState<Alert[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchHealth = async () => {
            try {
                const response = await fetch('/api/broadcast/health');
                if (response.ok) {
                    const data = await response.json();
                    setMetrics(data.metrics);
                    setConnections(data.connections || []);
                    setStreams(data.streams || []);
                    setAlerts(data.alerts || []);
                }
            } catch (err) {
                console.error('Failed to fetch health data:', err);
            } finally {
                setLoading(false);
            }
        };

        fetchHealth();
        const interval = setInterval(fetchHealth, refreshInterval);
        return () => clearInterval(interval);
    }, [refreshInterval]);

    const getQualityColor = (quality: string): string => {
        switch (quality) {
            case 'excellent': return '#00ff00';
            case 'good': return '#88ff00';
            case 'fair': return '#ffff00';
            case 'poor': return '#ff3333';
            default: return '#888';
        }
    };

    const getSeverityColor = (severity: string): string => {
        switch (severity) {
            case 'error': return '#ff3333';
            case 'warning': return '#ff9900';
            default: return '#00d4ff';
        }
    };

    if (loading) {
        return <div className="health-dashboard health-dashboard--loading">Loading health data...</div>;
    }

    return (
        <div className="health-dashboard">
            <header className="health-dashboard__header">
                <h1>🔧 BroadcastBox Health</h1>
                <span className="refresh-indicator">Refreshing every {refreshInterval / 1000}s</span>
            </header>

            {/* Metrics Summary */}
            {metrics && (
                <section className="health-dashboard__metrics">
                    <div className="metric-card">
                        <span className="value">{metrics.totalConnections}</span>
                        <span className="label">Connections</span>
                    </div>
                    <div className="metric-card">
                        <span className="value">{metrics.totalStreams}</span>
                        <span className="label">Active Streams</span>
                    </div>
                    <div className="metric-card">
                        <span className="value">{metrics.totalViewers}</span>
                        <span className="label">Total Viewers</span>
                    </div>
                    <div className="metric-card">
                        <span className="value">{metrics.avgLatency.toFixed(0)}ms</span>
                        <span className="label">Avg Latency</span>
                    </div>
                    <div className="metric-card alerts">
                        <span className={`value ${metrics.alertCount > 0 ? 'has-alerts' : ''}`}>
                            {metrics.alertCount}
                        </span>
                        <span className="label">Alerts</span>
                    </div>
                </section>
            )}

            {/* Connection Quality Distribution */}
            {metrics && (
                <section className="health-dashboard__quality">
                    <h3>Connection Quality</h3>
                    <div className="quality-bars">
                        {Object.entries(metrics.connectionQuality).map(([quality, count]) => (
                            <div key={quality} className="quality-bar">
                                <div
                                    className="bar-fill"
                                    style={{
                                        width: `${(count / metrics.totalConnections) * 100 || 0}%`,
                                        backgroundColor: getQualityColor(quality),
                                    }}
                                />
                                <span className="quality-label">{quality}: {count}</span>
                            </div>
                        ))}
                    </div>
                </section>
            )}

            <div className="health-dashboard__grid">
                {/* Active Streams */}
                <section className="health-dashboard__streams">
                    <h3>Active Streams ({streams.length})</h3>
                    {streams.length === 0 ? (
                        <p className="empty">No active streams</p>
                    ) : (
                        <table>
                            <thead>
                                <tr>
                                    <th>Driver</th>
                                    <th>Viewers</th>
                                    <th>FPS</th>
                                    <th>Bitrate</th>
                                </tr>
                            </thead>
                            <tbody>
                                {streams.map(stream => (
                                    <tr key={stream.streamId}>
                                        <td>{stream.driverId}</td>
                                        <td>{stream.viewers}</td>
                                        <td className={stream.fps < 20 ? 'warn' : ''}>
                                            {stream.fps}
                                        </td>
                                        <td>{(stream.bitrate / 1000).toFixed(1)} Mbps</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </section>

                {/* Recent Alerts */}
                <section className="health-dashboard__alerts">
                    <h3>Recent Alerts ({alerts.length})</h3>
                    {alerts.length === 0 ? (
                        <p className="empty">No alerts</p>
                    ) : (
                        <div className="alert-list">
                            {alerts.slice(-10).reverse().map(alert => (
                                <div
                                    key={alert.id}
                                    className={`alert-item severity-${alert.severity}`}
                                    style={{ borderLeftColor: getSeverityColor(alert.severity) }}
                                >
                                    <span className="alert-type">{alert.type}</span>
                                    <span className="alert-message">{alert.message}</span>
                                    <span className="alert-time">
                                        {new Date(alert.timestamp).toLocaleTimeString()}
                                    </span>
                                </div>
                            ))}
                        </div>
                    )}
                </section>
            </div>

            {/* Connections Table */}
            <section className="health-dashboard__connections">
                <h3>Connections ({connections.length})</h3>
                {connections.length > 0 && (
                    <table>
                        <thead>
                            <tr>
                                <th>Socket</th>
                                <th>Type</th>
                                <th>Quality</th>
                                <th>Latency</th>
                                <th>Errors</th>
                            </tr>
                        </thead>
                        <tbody>
                            {connections.slice(0, 20).map(conn => (
                                <tr key={conn.socketId}>
                                    <td className="socket-id">{conn.socketId.slice(0, 8)}...</td>
                                    <td>{conn.driverId ? '📹 Driver' : '👁️ Viewer'}</td>
                                    <td>
                                        <span
                                            className="quality-badge"
                                            style={{ backgroundColor: getQualityColor(conn.connectionQuality) }}
                                        >
                                            {conn.connectionQuality}
                                        </span>
                                    </td>
                                    <td>{conn.avgLatencyMs.toFixed(0)}ms</td>
                                    <td className={conn.errorCount > 0 ? 'has-errors' : ''}>
                                        {conn.errorCount}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </section>
        </div>
    );
};

export default HealthDashboard;
