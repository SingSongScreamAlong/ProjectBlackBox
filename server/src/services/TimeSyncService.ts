/**
 * TimeSyncService
 * 
 * Manages canonical timeline for BroadcastBox sessions.
 * Provides mapping between telemetry timestamps and video presentation times.
 */

import { EventEmitter } from 'events';
import type { TimeSync, BroadcastCompanionOffset } from '../types/broadcast.js';

interface SessionTimeInfo {
    sessionId: string;
    sessionStartUnixMs: number;
    lastTelemetryMs: number;
    estimatedEncodingDelayMs: number;
    estimatedNetworkDelayMs: number;
    clockDriftMs: number;
}

interface ViewerOffset {
    viewerId: string;
    offsetMs: number;
    calibratedAt: number;
}

export class TimeSyncService extends EventEmitter {
    private sessions: Map<string, SessionTimeInfo> = new Map();
    private viewerOffsets: Map<string, Map<string, ViewerOffset>> = new Map(); // sessionId -> viewerId -> offset

    // Default delay estimates (will be refined based on actual measurements)
    private readonly DEFAULT_ENCODING_DELAY_MS = 50;
    private readonly DEFAULT_NETWORK_DELAY_MS = 100;

    constructor() {
        super();
    }

    /**
     * Initialize time tracking for a session
     */
    initSession(sessionId: string, sessionStartUnixMs?: number): void {
        if (this.sessions.has(sessionId)) {
            return;
        }

        this.sessions.set(sessionId, {
            sessionId,
            sessionStartUnixMs: sessionStartUnixMs ?? Date.now(),
            lastTelemetryMs: 0,
            estimatedEncodingDelayMs: this.DEFAULT_ENCODING_DELAY_MS,
            estimatedNetworkDelayMs: this.DEFAULT_NETWORK_DELAY_MS,
            clockDriftMs: 0,
        });

        this.viewerOffsets.set(sessionId, new Map());

        console.log(`[TimeSync] Initialized session ${sessionId} at ${new Date(sessionStartUnixMs ?? Date.now()).toISOString()}`);
    }

    /**
     * Get current time sync info for a session
     */
    getTimeSync(sessionId: string): TimeSync | null {
        const session = this.sessions.get(sessionId);
        if (!session) {
            return null;
        }

        const now = Date.now();
        return {
            sessionId,
            sessionStartUnixMs: session.sessionStartUnixMs,
            sessionTimeMs: now - session.sessionStartUnixMs,
            serverTimeMs: now,
            drift: session.clockDriftMs,
        };
    }

    /**
     * Update session time from telemetry
     */
    updateFromTelemetry(sessionId: string, telemetryTimestamp: number): void {
        const session = this.sessions.get(sessionId);
        if (!session) {
            this.initSession(sessionId);
            return;
        }

        session.lastTelemetryMs = telemetryTimestamp;

        // Estimate clock drift by comparing expected vs actual timestamps
        const expectedMs = Date.now() - session.sessionStartUnixMs;
        const drift = telemetryTimestamp - expectedMs;

        // Use exponential moving average for drift estimation
        session.clockDriftMs = session.clockDriftMs * 0.9 + drift * 0.1;
    }

    /**
     * Map telemetry timestamp to video presentation time
     */
    telemetryToVideo(sessionId: string, telemetryTimeMs: number): number {
        const session = this.sessions.get(sessionId);
        if (!session) {
            return telemetryTimeMs;
        }

        // Video is delayed relative to telemetry by encoding + network delay
        const totalDelay = session.estimatedEncodingDelayMs + session.estimatedNetworkDelayMs;
        return telemetryTimeMs + totalDelay;
    }

    /**
     * Map video presentation time back to telemetry time
     */
    videoToTelemetry(sessionId: string, videoTimeMs: number): number {
        const session = this.sessions.get(sessionId);
        if (!session) {
            return videoTimeMs;
        }

        const totalDelay = session.estimatedEncodingDelayMs + session.estimatedNetworkDelayMs;
        return videoTimeMs - totalDelay;
    }

    /**
     * Update delay estimates based on actual measurements
     */
    updateDelayEstimate(
        sessionId: string,
        encodingDelayMs: number | null,
        networkDelayMs: number | null
    ): void {
        const session = this.sessions.get(sessionId);
        if (!session) {
            return;
        }

        if (encodingDelayMs !== null) {
            // Use exponential moving average
            session.estimatedEncodingDelayMs =
                session.estimatedEncodingDelayMs * 0.8 + encodingDelayMs * 0.2;
        }

        if (networkDelayMs !== null) {
            session.estimatedNetworkDelayMs =
                session.estimatedNetworkDelayMs * 0.8 + networkDelayMs * 0.2;
        }
    }

    /**
     * Set broadcast companion offset for a viewer
     */
    setBroadcastCompanionOffset(
        sessionId: string,
        viewerId: string,
        offsetMs: number
    ): BroadcastCompanionOffset {
        let sessionOffsets = this.viewerOffsets.get(sessionId);
        if (!sessionOffsets) {
            sessionOffsets = new Map();
            this.viewerOffsets.set(sessionId, sessionOffsets);
        }

        const offset: ViewerOffset = {
            viewerId,
            offsetMs,
            calibratedAt: Date.now(),
        };

        sessionOffsets.set(viewerId, offset);

        console.log(`[TimeSync] Set broadcast offset for viewer ${viewerId}: ${offsetMs}ms`);

        return {
            sessionId,
            viewerId,
            offsetMs,
            calibratedAt: offset.calibratedAt,
        };
    }

    /**
     * Get broadcast companion offset for a viewer
     */
    getBroadcastCompanionOffset(sessionId: string, viewerId: string): number {
        const sessionOffsets = this.viewerOffsets.get(sessionId);
        if (!sessionOffsets) {
            return 0;
        }

        const offset = sessionOffsets.get(viewerId);
        return offset?.offsetMs ?? 0;
    }

    /**
     * Convert session time to external broadcast time for a viewer
     */
    sessionToBroadcastTime(sessionId: string, viewerId: string, sessionTimeMs: number): number {
        const offset = this.getBroadcastCompanionOffset(sessionId, viewerId);
        return sessionTimeMs + offset;
    }

    /**
     * Convert external broadcast time to session time for a viewer
     */
    broadcastToSessionTime(sessionId: string, viewerId: string, broadcastTimeMs: number): number {
        const offset = this.getBroadcastCompanionOffset(sessionId, viewerId);
        return broadcastTimeMs - offset;
    }

    /**
     * Get end-to-end latency estimate
     */
    getLatencyEstimate(sessionId: string): { total: number; encoding: number; network: number } {
        const session = this.sessions.get(sessionId);
        if (!session) {
            return {
                total: this.DEFAULT_ENCODING_DELAY_MS + this.DEFAULT_NETWORK_DELAY_MS,
                encoding: this.DEFAULT_ENCODING_DELAY_MS,
                network: this.DEFAULT_NETWORK_DELAY_MS,
            };
        }

        return {
            total: session.estimatedEncodingDelayMs + session.estimatedNetworkDelayMs,
            encoding: session.estimatedEncodingDelayMs,
            network: session.estimatedNetworkDelayMs,
        };
    }

    /**
     * Clean up old sessions
     */
    cleanupSession(sessionId: string): void {
        this.sessions.delete(sessionId);
        this.viewerOffsets.delete(sessionId);
        console.log(`[TimeSync] Cleaned up session ${sessionId}`);
    }

    /**
     * Get all active sessions
     */
    getActiveSessions(): string[] {
        return Array.from(this.sessions.keys());
    }
}

// Singleton instance
let instance: TimeSyncService | null = null;

export function getTimeSync(): TimeSyncService {
    if (!instance) {
        instance = new TimeSyncService();
    }
    return instance;
}

export default TimeSyncService;
