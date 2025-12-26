/**
 * BroadcastBox Rate Limiter
 * 
 * Enhanced rate limiting for BroadcastBox endpoints and WebSocket events.
 */

import rateLimit from 'express-rate-limit';
import { Request, Response, NextFunction } from 'express';

// Rate limit configurations
export const RATE_LIMITS = {
    // Stream listing - moderate rate (polling)
    STREAM_LIST: {
        windowMs: 60 * 1000, // 1 minute
        max: 60, // 1 per second average
        message: 'Too many stream list requests',
    },

    // Stats API - higher rate (dashboard updates)
    STATS_API: {
        windowMs: 60 * 1000,
        max: 120, // 2 per second average
        message: 'Too many stats requests',
    },

    // WebRTC signaling - lower rate (one-time per connection)
    WEBRTC_SIGNALING: {
        windowMs: 60 * 1000,
        max: 30,
        message: 'Too many signaling requests',
    },

    // Stream registration - very low (driver publishing)
    STREAM_REGISTER: {
        windowMs: 60 * 1000,
        max: 10,
        message: 'Too many stream registration attempts',
    },

    // Broadcast sync offset - low (calibration)
    SYNC_OFFSET: {
        windowMs: 60 * 1000,
        max: 20,
        message: 'Too many sync offset changes',
    },
};

// Create rate limiter for stream list
export const streamListLimiter = rateLimit({
    ...RATE_LIMITS.STREAM_LIST,
    standardHeaders: true,
    legacyHeaders: false,
    keyGenerator: (req: Request) => {
        return req.ip || req.headers['x-forwarded-for'] as string || 'unknown';
    },
});

// Create rate limiter for stats API
export const statsLimiter = rateLimit({
    ...RATE_LIMITS.STATS_API,
    standardHeaders: true,
    legacyHeaders: false,
});

// Create rate limiter for WebRTC signaling
export const signalingLimiter = rateLimit({
    ...RATE_LIMITS.WEBRTC_SIGNALING,
    standardHeaders: true,
    legacyHeaders: false,
});

// Create rate limiter for stream registration
export const streamRegisterLimiter = rateLimit({
    ...RATE_LIMITS.STREAM_REGISTER,
    standardHeaders: true,
    legacyHeaders: false,
});

// Socket.IO event rate limiter
interface SocketRateLimitState {
    events: Map<string, number[]>; // eventName -> timestamps
}

const socketStates = new Map<string, SocketRateLimitState>();

export function createSocketRateLimiter(limits: Record<string, { windowMs: number; max: number }>) {
    return (socketId: string, eventName: string): boolean => {
        let state = socketStates.get(socketId);
        if (!state) {
            state = { events: new Map() };
            socketStates.set(socketId, state);
        }

        const now = Date.now();
        const limit = limits[eventName] || { windowMs: 60000, max: 60 };

        let timestamps = state.events.get(eventName) || [];

        // Remove old timestamps
        timestamps = timestamps.filter(t => now - t < limit.windowMs);

        if (timestamps.length >= limit.max) {
            return false; // Rate limited
        }

        timestamps.push(now);
        state.events.set(eventName, timestamps);

        return true; // Allowed
    };
}

// Clean up socket state on disconnect
export function cleanupSocketRateLimit(socketId: string): void {
    socketStates.delete(socketId);
}

// Socket event limits
export const SOCKET_EVENT_LIMITS: Record<string, { windowMs: number; max: number }> = {
    'stream_register': { windowMs: 60000, max: 5 },
    'stream_health': { windowMs: 1000, max: 2 }, // Max 2 per second
    'webrtc_offer': { windowMs: 60000, max: 10 },
    'webrtc_answer': { windowMs: 60000, max: 10 },
    'webrtc_ice_candidate': { windowMs: 1000, max: 5 }, // Max 5 per second
    'join_stream': { windowMs: 60000, max: 30 },
    'leave_stream': { windowMs: 60000, max: 30 },
    'telemetry': { windowMs: 100, max: 5 }, // Max 50/sec
    'set_broadcast_offset': { windowMs: 5000, max: 5 },
};

// Create the socket rate limiter with our limits
export const socketRateLimiter = createSocketRateLimiter(SOCKET_EVENT_LIMITS);

export default {
    streamListLimiter,
    statsLimiter,
    signalingLimiter,
    streamRegisterLimiter,
    socketRateLimiter,
    cleanupSocketRateLimit,
    RATE_LIMITS,
    SOCKET_EVENT_LIMITS,
};
