/**
 * useBroadcastSync - Hook for managing broadcast companion sync
 * 
 * Provides time-shifted telemetry data based on viewer's offset setting.
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import { Socket } from 'socket.io-client';

interface SyncEvent {
    type: 'green_flag' | 'yellow_flag' | 'incident' | 'pit_entry' | 'sector';
    timestamp: number;
    description: string;
}

interface TelemetryData {
    timestamp: number;
    [key: string]: any;
}

interface UseBroadcastSyncOptions {
    sessionId: string;
    socket: Socket | null;
    bufferDurationMs?: number; // How much telemetry to buffer (default 2 mins)
}

interface UseBroadcastSyncReturn {
    offsetMs: number;
    setOffsetMs: (ms: number) => void;
    recentEvents: SyncEvent[];
    getShiftedTelemetry: (data: TelemetryData) => TelemetryData;
    getShiftedTime: (timestamp: number) => number;
    isBuffering: boolean;
    bufferHealth: number; // 0-1, how full the buffer is relative to offset
}

export function useBroadcastSync({
    sessionId,
    socket,
    bufferDurationMs = 120000, // 2 minute buffer
}: UseBroadcastSyncOptions): UseBroadcastSyncReturn {
    const [offsetMs, setOffsetMs] = useState(0);
    const [recentEvents, setRecentEvents] = useState<SyncEvent[]>([]);
    const [telemetryBuffer, setTelemetryBuffer] = useState<TelemetryData[]>([]);
    const [isBuffering, setIsBuffering] = useState(false);

    // Load saved offset
    useEffect(() => {
        const saved = localStorage.getItem('broadcastOffsets');
        if (saved) {
            const offsets = JSON.parse(saved);
            if (offsets[sessionId]) {
                setOffsetMs(offsets[sessionId]);
            }
        }
    }, [sessionId]);

    // Listen for sync events
    useEffect(() => {
        if (!socket) return;

        const handleFlagChange = (data: any) => {
            const event: SyncEvent = {
                type: data.flag === 'green' ? 'green_flag' : 'yellow_flag',
                timestamp: Date.now(),
                description: `${data.flag.toUpperCase()} flag`,
            };
            setRecentEvents(prev => [...prev.slice(-10), event]);
        };

        const handleIncident = (data: any) => {
            const event: SyncEvent = {
                type: 'incident',
                timestamp: Date.now(),
                description: `Incident: ${data.description || 'Contact detected'}`,
            };
            setRecentEvents(prev => [...prev.slice(-10), event]);
        };

        const handlePitEntry = (data: any) => {
            const event: SyncEvent = {
                type: 'pit_entry',
                timestamp: Date.now(),
                description: `Pit entry: ${data.driverName || 'Driver'}`,
            };
            setRecentEvents(prev => [...prev.slice(-10), event]);
        };

        socket.on('flag_change', handleFlagChange);
        socket.on('incident', handleIncident);
        socket.on('pit_entry', handlePitEntry);

        return () => {
            socket.off('flag_change', handleFlagChange);
            socket.off('incident', handleIncident);
            socket.off('pit_entry', handlePitEntry);
        };
    }, [socket]);

    // Buffer telemetry when offset is set
    useEffect(() => {
        if (!socket || offsetMs <= 0) {
            setTelemetryBuffer([]);
            setIsBuffering(false);
            return;
        }

        setIsBuffering(true);

        const handleTelemetry = (data: any) => {
            const now = Date.now();
            setTelemetryBuffer(prev => {
                // Add new data
                const updated = [...prev, { ...data, timestamp: now }];
                // Remove old data outside buffer window
                const cutoff = now - bufferDurationMs;
                return updated.filter(d => d.timestamp > cutoff);
            });

            // Check if buffer has enough data for the offset
            setIsBuffering(telemetryBuffer.length === 0 ||
                (now - telemetryBuffer[0]?.timestamp) < offsetMs);
        };

        socket.on('telemetry', handleTelemetry);

        return () => {
            socket.off('telemetry', handleTelemetry);
        };
    }, [socket, offsetMs, bufferDurationMs, telemetryBuffer]);

    // Calculate buffer health
    const bufferHealth = useMemo(() => {
        if (offsetMs <= 0 || telemetryBuffer.length === 0) return 1;
        const bufferSpan = telemetryBuffer[telemetryBuffer.length - 1]?.timestamp -
            telemetryBuffer[0]?.timestamp || 0;
        return Math.min(1, bufferSpan / offsetMs);
    }, [telemetryBuffer, offsetMs]);

    // Get time-shifted telemetry
    const getShiftedTelemetry = useCallback((currentData: TelemetryData): TelemetryData => {
        if (offsetMs <= 0 || telemetryBuffer.length === 0) {
            return currentData;
        }

        const targetTime = Date.now() - offsetMs;

        // Find the closest buffered data point
        let closest = telemetryBuffer[0];
        let minDiff = Math.abs(closest.timestamp - targetTime);

        for (const data of telemetryBuffer) {
            const diff = Math.abs(data.timestamp - targetTime);
            if (diff < minDiff) {
                minDiff = diff;
                closest = data;
            }
        }

        return closest;
    }, [offsetMs, telemetryBuffer]);

    // Get time-shifted timestamp
    const getShiftedTime = useCallback((timestamp: number): number => {
        return timestamp - offsetMs;
    }, [offsetMs]);

    // Save offset when it changes
    const handleSetOffsetMs = useCallback((ms: number) => {
        setOffsetMs(ms);
        // Save to server
        if (socket) {
            socket.emit('set_broadcast_offset', { sessionId, offsetMs: ms });
        }
    }, [socket, sessionId]);

    return {
        offsetMs,
        setOffsetMs: handleSetOffsetMs,
        recentEvents,
        getShiftedTelemetry,
        getShiftedTime,
        isBuffering,
        bufferHealth,
    };
}

export default useBroadcastSync;
