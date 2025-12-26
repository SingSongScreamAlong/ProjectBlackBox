/**
 * BroadcastBoxService
 * 
 * Manages WebSocket connections for BroadcastBox streams and stats.
 */

import { io, Socket } from 'socket.io-client';

interface StreamInfo {
    streamId: string;
    driverId: string;
    driverName: string;
    status: 'live' | 'starting' | 'offline' | 'degraded';
    resolution: string;
    fps: number;
    viewerCount: number;
}

interface BattleInfo {
    id: string;
    drivers: string[];
    gapSeconds: number;
    riskLevel: 'low' | 'medium' | 'high';
    twoWide: boolean;
    threeWide: boolean;
}

type StreamListCallback = (streams: StreamInfo[]) => void;
type BattleCallback = (battles: BattleInfo[]) => void;
type StatsCallback = (driverId: string, stats: any) => void;

class BroadcastBoxService {
    private socket: Socket | null = null;
    private sessionId: string | null = null;
    private streamCallbacks: StreamListCallback[] = [];
    private battleCallbacks: BattleCallback[] = [];
    private statsCallbacks: StatsCallback[] = [];

    private streams: Map<string, StreamInfo> = new Map();
    private battles: BattleInfo[] = [];

    /**
     * Connect to BroadcastBox via existing Socket.IO connection
     */
    connect(socket: Socket, sessionId: string): void {
        this.socket = socket;
        this.sessionId = sessionId;

        this.setupEventHandlers();

        // Join session room
        this.socket.emit('join_session', sessionId);

        console.log(`[BroadcastBox] Connected to session: ${sessionId}`);
    }

    /**
     * Disconnect from BroadcastBox
     */
    disconnect(): void {
        if (this.socket && this.sessionId) {
            this.socket.emit('leave_session', this.sessionId);
        }

        this.streams.clear();
        this.battles = [];
        this.socket = null;
        this.sessionId = null;
    }

    /**
     * Subscribe to stream list updates
     */
    onStreamListUpdate(callback: StreamListCallback): () => void {
        this.streamCallbacks.push(callback);

        // Immediately send current streams
        callback(Array.from(this.streams.values()));

        // Return unsubscribe function
        return () => {
            const idx = this.streamCallbacks.indexOf(callback);
            if (idx !== -1) this.streamCallbacks.splice(idx, 1);
        };
    }

    /**
     * Subscribe to battle updates
     */
    onBattleUpdate(callback: BattleCallback): () => void {
        this.battleCallbacks.push(callback);
        callback(this.battles);

        return () => {
            const idx = this.battleCallbacks.indexOf(callback);
            if (idx !== -1) this.battleCallbacks.splice(idx, 1);
        };
    }

    /**
     * Subscribe to driver stats updates
     */
    onDriverStats(callback: StatsCallback): () => void {
        this.statsCallbacks.push(callback);

        return () => {
            const idx = this.statsCallbacks.indexOf(callback);
            if (idx !== -1) this.statsCallbacks.splice(idx, 1);
        };
    }

    /**
     * Join a specific stream for WebRTC signaling
     */
    joinStream(streamId: string): void {
        if (!this.socket) return;
        this.socket.emit('join_stream', streamId);
    }

    /**
     * Leave a stream room
     */
    leaveStream(streamId: string): void {
        if (!this.socket) return;
        this.socket.emit('leave_stream', streamId);
    }

    /**
     * Get current stream list
     */
    getStreams(): StreamInfo[] {
        return Array.from(this.streams.values());
    }

    /**
     * Get stream by ID
     */
    getStream(streamId: string): StreamInfo | undefined {
        return this.streams.get(streamId);
    }

    /**
     * Get stream by driver ID
     */
    getStreamByDriver(driverId: string): StreamInfo | undefined {
        const streamArray = Array.from(this.streams.values());
        return streamArray.find(stream => stream.driverId === driverId);
    }

    /**
     * Set up socket event handlers
     */
    private setupEventHandlers(): void {
        if (!this.socket) return;

        // Stream list updates
        this.socket.on('stream_list_update', (data: { streams: StreamInfo[] }) => {
            this.streams.clear();
            for (const stream of data.streams) {
                this.streams.set(stream.streamId, stream);
            }
            this.notifyStreamListeners();
        });

        // Individual stream updates
        this.socket.on('stream_health', (data: any) => {
            const stream = this.streams.get(data.streamId);
            if (stream) {
                stream.status = data.metrics?.warnings?.length > 0 ? 'degraded' : 'live';
                this.notifyStreamListeners();
            }
        });

        // Stream deregistration
        this.socket.on('stream_deregistered', (data: { streamId: string }) => {
            this.streams.delete(data.streamId);
            this.notifyStreamListeners();
        });

        // Battle updates
        this.socket.on('battle_update', (data: { battle: BattleInfo }) => {
            // Update or add battle
            const idx = this.battles.findIndex(b => b.id === data.battle.id);
            if (idx !== -1) {
                this.battles[idx] = data.battle;
            } else {
                this.battles.push(data.battle);
            }

            // Sort by risk level
            this.battles.sort((a, b) => {
                const order = { high: 0, medium: 1, low: 2 };
                return order[a.riskLevel] - order[b.riskLevel];
            });

            this.notifyBattleListeners();
        });

        // Driver stats updates
        this.socket.on('stats_driver_update', (data: any) => {
            for (const callback of this.statsCallbacks) {
                callback(data.driverId, data.data);
            }
        });

        // Incident events
        this.socket.on('incident', (data: any) => {
            console.log('[BroadcastBox] Incident:', data);
            // Could emit to a separate incident listener
        });
    }

    private notifyStreamListeners(): void {
        const streams = Array.from(this.streams.values());
        for (const callback of this.streamCallbacks) {
            callback(streams);
        }
    }

    private notifyBattleListeners(): void {
        for (const callback of this.battleCallbacks) {
            callback(this.battles);
        }
    }
}

// Singleton instance
export const broadcastBoxService = new BroadcastBoxService();
export default broadcastBoxService;
