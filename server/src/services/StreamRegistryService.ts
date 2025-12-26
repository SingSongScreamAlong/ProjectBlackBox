/**
 * StreamRegistryService
 * 
 * Manages active driver streams for BroadcastBox.
 * Tracks registrations, health, and viewer counts.
 */

import { EventEmitter } from 'events';
import type {
    StreamRegistration,
    StreamHealth,
    StreamDeregistration,
    DriverStream,
    StreamListUpdate,
    StreamStatus,
    StreamAccessLevel,
    Role,
} from '../types/broadcast.js';

interface RegisteredStream {
    registration: StreamRegistration;
    lastHealth: StreamHealth | null;
    status: StreamStatus;
    viewerCount: number;
    registeredAt: number;
    lastHeartbeat: number;
}

interface ViewerInfo {
    viewerId: string;
    streamId: string;
    role: Role;
    connectedAt: number;
}

export class StreamRegistryService extends EventEmitter {
    private streams: Map<string, RegisteredStream> = new Map();
    private viewers: Map<string, ViewerInfo[]> = new Map(); // streamId -> viewers
    private healthCheckInterval: NodeJS.Timeout | null = null;

    // Configuration
    private readonly HEALTH_TIMEOUT_MS = 10000;  // 10 seconds without heartbeat = degraded
    private readonly OFFLINE_TIMEOUT_MS = 30000; // 30 seconds = offline

    constructor() {
        super();
        this.startHealthCheck();
    }

    /**
     * Register a new stream from a relay agent
     */
    registerStream(registration: StreamRegistration): void {
        const existing = this.streams.get(registration.streamId);

        if (existing) {
            // Update existing registration
            existing.registration = registration;
            existing.lastHeartbeat = Date.now();
            existing.status = 'live';
            console.log(`[StreamRegistry] Updated stream: ${registration.streamId} (${registration.driverName})`);
        } else {
            // New registration
            this.streams.set(registration.streamId, {
                registration,
                lastHealth: null,
                status: 'starting',
                viewerCount: 0,
                registeredAt: Date.now(),
                lastHeartbeat: Date.now(),
            });
            console.log(`[StreamRegistry] Registered stream: ${registration.streamId} (${registration.driverName})`);
        }

        this.broadcastStreamList(registration.sessionId);
    }

    /**
     * Update stream health from relay agent heartbeat
     */
    updateHealth(health: StreamHealth): void {
        const stream = this.streams.get(health.streamId);
        if (!stream) {
            console.warn(`[StreamRegistry] Health update for unknown stream: ${health.streamId}`);
            return;
        }

        stream.lastHealth = health;
        stream.lastHeartbeat = Date.now();

        // Update status based on health
        if (health.warnings.length > 0) {
            stream.status = 'degraded';
        } else {
            stream.status = 'live';
        }

        // Check for critical performance issues
        if (health.metrics.iracingFps < 30) {
            console.warn(`[StreamRegistry] Critical: ${stream.registration.driverName} iRacing FPS at ${health.metrics.iracingFps}`);
        }

        this.emit('health_update', health);
    }

    /**
     * Deregister a stream
     */
    deregisterStream(deregistration: StreamDeregistration): void {
        const stream = this.streams.get(deregistration.streamId);
        if (!stream) {
            return;
        }

        const sessionId = stream.registration.sessionId;
        this.streams.delete(deregistration.streamId);

        // Clean up viewers
        this.viewers.delete(deregistration.streamId);

        console.log(`[StreamRegistry] Deregistered stream: ${deregistration.streamId} (reason: ${deregistration.reason})`);

        this.broadcastStreamList(sessionId);
        this.emit('stream_deregistered', deregistration);
    }

    /**
     * Get list of all streams for a session
     */
    getStreamList(sessionId: string): DriverStream[] {
        const list: DriverStream[] = [];

        for (const [streamId, stream] of this.streams) {
            if (stream.registration.sessionId !== sessionId) {
                continue;
            }

            list.push({
                driverId: stream.registration.driverId,
                driverName: stream.registration.driverName,
                carNumber: '', // Will be populated from telemetry
                teamName: '', // Will be populated from telemetry
                streamId,
                status: stream.status,
                resolution: stream.registration.capabilities.resolution,
                fps: stream.registration.capabilities.fps,
                accessLevel: stream.registration.accessLevel,
                viewerCount: stream.viewerCount,
                position: 0, // Will be populated from telemetry
                classId: 0,
                className: '',
            });
        }

        // Sort by position (if available) then by driver name
        return list.sort((a, b) => {
            if (a.position !== b.position) {
                return a.position - b.position;
            }
            return a.driverName.localeCompare(b.driverName);
        });
    }

    /**
     * Add a viewer to a stream
     */
    addViewer(streamId: string, viewerId: string, role: Role): boolean {
        const stream = this.streams.get(streamId);
        if (!stream) {
            return false;
        }

        // Check access control
        if (!this.canAccess(stream.registration.accessLevel, role)) {
            return false;
        }

        // Add viewer
        if (!this.viewers.has(streamId)) {
            this.viewers.set(streamId, []);
        }

        const viewerList = this.viewers.get(streamId)!;
        if (!viewerList.find(v => v.viewerId === viewerId)) {
            viewerList.push({
                viewerId,
                streamId,
                role,
                connectedAt: Date.now(),
            });
            stream.viewerCount = viewerList.length;
        }

        return true;
    }

    /**
     * Remove a viewer from a stream
     */
    removeViewer(streamId: string, viewerId: string): void {
        const stream = this.streams.get(streamId);
        const viewerList = this.viewers.get(streamId);

        if (viewerList) {
            const idx = viewerList.findIndex(v => v.viewerId === viewerId);
            if (idx !== -1) {
                viewerList.splice(idx, 1);
                if (stream) {
                    stream.viewerCount = viewerList.length;
                }
            }
        }
    }

    /**
     * Get stream by ID
     */
    getStream(streamId: string): RegisteredStream | undefined {
        return this.streams.get(streamId);
    }

    /**
     * Get stream by driver ID and session
     */
    getStreamByDriver(sessionId: string, driverId: string): RegisteredStream | undefined {
        for (const stream of this.streams.values()) {
            if (stream.registration.sessionId === sessionId &&
                stream.registration.driverId === driverId) {
                return stream;
            }
        }
        return undefined;
    }

    /**
     * Check if a role can access a stream
     */
    private canAccess(accessLevel: StreamAccessLevel, role: Role): boolean {
        const hierarchy: Record<Role, number> = {
            'guest': 0,
            'public': 1,
            'subscriber': 2,
            'team_member': 3,
            'team_admin': 4,
            'league_admin': 5,
        };

        const required: Record<StreamAccessLevel, number> = {
            'public': 1,
            'team': 3,
            'league': 2,
            'private': 5,
        };

        return hierarchy[role] >= required[accessLevel];
    }

    /**
     * Broadcast updated stream list to all connected clients
     */
    private broadcastStreamList(sessionId: string): void {
        const update: StreamListUpdate = {
            type: 'STREAM_LIST_UPDATE',
            sessionId,
            streams: this.getStreamList(sessionId),
            timestamp: Date.now(),
        };

        this.emit('stream_list_update', update);
    }

    /**
     * Periodic health check to detect disconnected streams
     */
    private startHealthCheck(): void {
        this.healthCheckInterval = setInterval(() => {
            const now = Date.now();
            const sessionsToUpdate = new Set<string>();

            for (const [streamId, stream] of this.streams) {
                const timeSinceHeartbeat = now - stream.lastHeartbeat;

                if (timeSinceHeartbeat > this.OFFLINE_TIMEOUT_MS) {
                    // Stream is offline - remove it
                    console.log(`[StreamRegistry] Stream ${streamId} timed out (${timeSinceHeartbeat}ms)`);
                    sessionsToUpdate.add(stream.registration.sessionId);
                    this.streams.delete(streamId);
                    this.viewers.delete(streamId);
                } else if (timeSinceHeartbeat > this.HEALTH_TIMEOUT_MS && stream.status === 'live') {
                    // Stream is degraded
                    stream.status = 'degraded';
                    sessionsToUpdate.add(stream.registration.sessionId);
                }
            }

            // Broadcast updates for affected sessions
            for (const sessionId of sessionsToUpdate) {
                this.broadcastStreamList(sessionId);
            }
        }, 5000);
    }

    /**
     * Cleanup
     */
    destroy(): void {
        if (this.healthCheckInterval) {
            clearInterval(this.healthCheckInterval);
        }
        this.streams.clear();
        this.viewers.clear();
    }
}

// Singleton instance
let instance: StreamRegistryService | null = null;

export function getStreamRegistry(): StreamRegistryService {
    if (!instance) {
        instance = new StreamRegistryService();
    }
    return instance;
}

export default StreamRegistryService;
