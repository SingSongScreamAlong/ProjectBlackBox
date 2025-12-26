/**
 * ConnectionMonitor - WebRTC and Socket.IO connection health monitoring
 * 
 * Tracks connection quality, detects issues, and provides metrics for alerting.
 */

import { EventEmitter } from 'events';

interface ConnectionStats {
    socketId: string;
    driverId?: string;
    viewerId?: string;
    connectedAt: number;
    lastActivity: number;
    messageCount: number;
    errorCount: number;
    avgLatencyMs: number;
    connectionQuality: 'excellent' | 'good' | 'fair' | 'poor';
}

interface StreamStats {
    streamId: string;
    driverId: string;
    viewers: number;
    avgViewerLatency: number;
    lastFrameTime: number;
    framesDropped: number;
    bitrate: number;
    fps: number;
}

interface Alert {
    id: string;
    type: 'connection_lost' | 'high_latency' | 'stream_degraded' | 'rate_limit_exceeded';
    severity: 'info' | 'warning' | 'error';
    message: string;
    timestamp: number;
    metadata: Record<string, any>;
}

export class ConnectionMonitor extends EventEmitter {
    private connections: Map<string, ConnectionStats> = new Map();
    private streams: Map<string, StreamStats> = new Map();
    private alerts: Alert[] = [];

    // Thresholds
    private readonly LATENCY_WARNING_MS = 500;
    private readonly LATENCY_ERROR_MS = 2000;
    private readonly STALE_CONNECTION_MS = 30000;
    private readonly FPS_WARNING_THRESHOLD = 20;
    private readonly MAX_ALERTS = 100;

    constructor() {
        super();

        // Start periodic health check
        setInterval(() => this.checkHealth(), 10000);
    }

    /**
     * Register a new connection
     */
    registerConnection(socketId: string, metadata?: { driverId?: string; viewerId?: string }): void {
        this.connections.set(socketId, {
            socketId,
            driverId: metadata?.driverId,
            viewerId: metadata?.viewerId,
            connectedAt: Date.now(),
            lastActivity: Date.now(),
            messageCount: 0,
            errorCount: 0,
            avgLatencyMs: 0,
            connectionQuality: 'excellent',
        });

        console.log(`[ConnectionMonitor] Registered connection ${socketId}`);
    }

    /**
     * Record activity on a connection
     */
    recordActivity(socketId: string, latencyMs?: number): void {
        const conn = this.connections.get(socketId);
        if (!conn) return;

        conn.lastActivity = Date.now();
        conn.messageCount++;

        if (latencyMs !== undefined) {
            // Exponential moving average for latency
            conn.avgLatencyMs = conn.avgLatencyMs * 0.9 + latencyMs * 0.1;
            conn.connectionQuality = this.calculateQuality(conn.avgLatencyMs, conn.errorCount);
        }
    }

    /**
     * Record an error on a connection
     */
    recordError(socketId: string, error: string): void {
        const conn = this.connections.get(socketId);
        if (!conn) return;

        conn.errorCount++;
        conn.connectionQuality = this.calculateQuality(conn.avgLatencyMs, conn.errorCount);

        if (conn.errorCount > 5) {
            this.createAlert({
                type: 'connection_lost',
                severity: 'warning',
                message: `Connection ${socketId} has ${conn.errorCount} errors`,
                metadata: { socketId, error },
            });
        }
    }

    /**
     * Unregister a connection
     */
    unregisterConnection(socketId: string): void {
        this.connections.delete(socketId);
        console.log(`[ConnectionMonitor] Unregistered connection ${socketId}`);
    }

    /**
     * Register a stream
     */
    registerStream(streamId: string, driverId: string): void {
        this.streams.set(streamId, {
            streamId,
            driverId,
            viewers: 0,
            avgViewerLatency: 0,
            lastFrameTime: Date.now(),
            framesDropped: 0,
            bitrate: 0,
            fps: 0,
        });
    }

    /**
     * Update stream stats
     */
    updateStreamStats(streamId: string, stats: Partial<StreamStats>): void {
        const stream = this.streams.get(streamId);
        if (!stream) return;

        Object.assign(stream, stats);
        stream.lastFrameTime = Date.now();

        // Check for degradation
        if (stream.fps < this.FPS_WARNING_THRESHOLD && stream.fps > 0) {
            this.createAlert({
                type: 'stream_degraded',
                severity: 'warning',
                message: `Stream ${streamId} FPS dropped to ${stream.fps}`,
                metadata: { streamId, fps: stream.fps },
            });
        }
    }

    /**
     * Add/remove viewer from stream
     */
    updateStreamViewers(streamId: string, delta: number): void {
        const stream = this.streams.get(streamId);
        if (!stream) return;

        stream.viewers = Math.max(0, stream.viewers + delta);
    }

    /**
     * Unregister a stream
     */
    unregisterStream(streamId: string): void {
        this.streams.delete(streamId);
    }

    /**
     * Get all connection stats
     */
    getConnectionStats(): ConnectionStats[] {
        return Array.from(this.connections.values());
    }

    /**
     * Get all stream stats
     */
    getStreamStats(): StreamStats[] {
        return Array.from(this.streams.values());
    }

    /**
     * Get recent alerts
     */
    getAlerts(limit = 20): Alert[] {
        return this.alerts.slice(-limit);
    }

    /**
     * Get aggregate metrics
     */
    getMetrics(): {
        totalConnections: number;
        totalStreams: number;
        totalViewers: number;
        avgLatency: number;
        alertCount: number;
        connectionQuality: Record<string, number>;
    } {
        const connections = Array.from(this.connections.values());
        const streams = Array.from(this.streams.values());

        const qualityCounts: Record<string, number> = {
            excellent: 0,
            good: 0,
            fair: 0,
            poor: 0,
        };

        let totalLatency = 0;
        for (const conn of connections) {
            qualityCounts[conn.connectionQuality]++;
            totalLatency += conn.avgLatencyMs;
        }

        return {
            totalConnections: connections.length,
            totalStreams: streams.length,
            totalViewers: streams.reduce((sum, s) => sum + s.viewers, 0),
            avgLatency: connections.length > 0 ? totalLatency / connections.length : 0,
            alertCount: this.alerts.length,
            connectionQuality: qualityCounts,
        };
    }

    /**
     * Periodic health check
     */
    private checkHealth(): void {
        const now = Date.now();

        // Check for stale connections
        for (const [socketId, conn] of this.connections) {
            if (now - conn.lastActivity > this.STALE_CONNECTION_MS) {
                this.createAlert({
                    type: 'connection_lost',
                    severity: 'info',
                    message: `Connection ${socketId} appears stale`,
                    metadata: { socketId, lastActivity: conn.lastActivity },
                });
            }
        }

        // Check for stale streams
        for (const [streamId, stream] of this.streams) {
            if (now - stream.lastFrameTime > 5000 && stream.viewers > 0) {
                this.createAlert({
                    type: 'stream_degraded',
                    severity: 'warning',
                    message: `Stream ${streamId} has no recent frames`,
                    metadata: { streamId, lastFrame: stream.lastFrameTime },
                });
            }
        }

        // Emit metrics for external monitoring
        this.emit('metrics', this.getMetrics());
    }

    /**
     * Calculate connection quality
     */
    private calculateQuality(latencyMs: number, errorCount: number): ConnectionStats['connectionQuality'] {
        if (errorCount > 10 || latencyMs > this.LATENCY_ERROR_MS) {
            return 'poor';
        }
        if (errorCount > 5 || latencyMs > this.LATENCY_WARNING_MS) {
            return 'fair';
        }
        if (latencyMs > 200) {
            return 'good';
        }
        return 'excellent';
    }

    /**
     * Create an alert
     */
    private createAlert(alert: Omit<Alert, 'id' | 'timestamp'>): void {
        const fullAlert: Alert = {
            ...alert,
            id: `alert-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            timestamp: Date.now(),
        };

        this.alerts.push(fullAlert);

        // Trim old alerts
        if (this.alerts.length > this.MAX_ALERTS) {
            this.alerts = this.alerts.slice(-this.MAX_ALERTS);
        }

        // Emit alert for external handlers
        this.emit('alert', fullAlert);

        console.log(`[ConnectionMonitor] Alert: ${alert.severity} - ${alert.message}`);
    }
}

// Singleton instance
let instance: ConnectionMonitor | null = null;

export function getConnectionMonitor(): ConnectionMonitor {
    if (!instance) {
        instance = new ConnectionMonitor();
    }
    return instance;
}

export default ConnectionMonitor;
