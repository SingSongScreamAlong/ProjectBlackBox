/**
 * BroadcastBox API Routes
 * 
 * REST API endpoints for stream management and stats access.
 */

import { Router, Request, Response } from 'express';
import { authenticateToken } from './auth.js';
import { apiLimiter } from './middleware/rate-limit.js';
import { getStreamRegistry } from './services/StreamRegistryService.js';
import { getTimeSync } from './services/TimeSyncService.js';
import { getNextGenStats } from './services/NextGenStatsService.js';
import type { Role } from './types/broadcast.js';

const router = Router();

// =============================================================================
// STREAM ENDPOINTS
// =============================================================================

/**
 * GET /api/broadcast/streams
 * List all available streams for a session
 */
router.get('/streams', apiLimiter, async (req: Request, res: Response) => {
    try {
        const sessionId = req.query.sessionId as string;

        if (!sessionId) {
            return res.status(400).json({ error: 'sessionId query parameter required' });
        }

        const registry = getStreamRegistry();
        const streams = registry.getStreamList(sessionId);

        return res.json({
            sessionId,
            streams,
            count: streams.length,
            timestamp: Date.now(),
        });
    } catch (error) {
        console.error('[Broadcast] Error listing streams:', error);
        return res.status(500).json({ error: 'Failed to list streams' });
    }
});

/**
 * GET /api/broadcast/streams/:streamId
 * Get details for a specific stream
 */
router.get('/streams/:streamId', apiLimiter, async (req: Request, res: Response) => {
    try {
        const { streamId } = req.params;

        const registry = getStreamRegistry();
        const stream = registry.getStream(streamId);

        if (!stream) {
            return res.status(404).json({ error: 'Stream not found' });
        }

        return res.json({
            streamId,
            registration: stream.registration,
            status: stream.status,
            health: stream.lastHealth,
            viewerCount: stream.viewerCount,
            registeredAt: stream.registeredAt,
        });
    } catch (error) {
        console.error('[Broadcast] Error getting stream:', error);
        return res.status(500).json({ error: 'Failed to get stream' });
    }
});

/**
 * POST /api/broadcast/streams/:streamId/join
 * Request to join/watch a stream (for access control tracking)
 */
router.post('/streams/:streamId/join', apiLimiter, async (req: Request, res: Response) => {
    try {
        const { streamId } = req.params;
        const { viewerId, role = 'public' } = req.body;

        if (!viewerId) {
            return res.status(400).json({ error: 'viewerId required' });
        }

        const registry = getStreamRegistry();
        const stream = registry.getStream(streamId);

        if (!stream) {
            return res.status(404).json({ error: 'Stream not found' });
        }

        const success = registry.addViewer(streamId, viewerId, role as Role);

        if (!success) {
            return res.status(403).json({ error: 'Access denied' });
        }

        return res.json({
            streamId,
            viewerId,
            joined: true,
            capabilities: stream.registration.capabilities,
        });
    } catch (error) {
        console.error('[Broadcast] Error joining stream:', error);
        return res.status(500).json({ error: 'Failed to join stream' });
    }
});

/**
 * POST /api/broadcast/streams/:streamId/leave
 * Leave/stop watching a stream
 */
router.post('/streams/:streamId/leave', apiLimiter, async (req: Request, res: Response) => {
    try {
        const { streamId } = req.params;
        const { viewerId } = req.body;

        if (!viewerId) {
            return res.status(400).json({ error: 'viewerId required' });
        }

        const registry = getStreamRegistry();
        registry.removeViewer(streamId, viewerId);

        return res.json({ streamId, viewerId, left: true });
    } catch (error) {
        console.error('[Broadcast] Error leaving stream:', error);
        return res.status(500).json({ error: 'Failed to leave stream' });
    }
});

// =============================================================================
// STATS ENDPOINTS
// =============================================================================

/**
 * GET /api/broadcast/stats/:sessionId
 * Get session-wide stats
 */
router.get('/stats/:sessionId', apiLimiter, async (req: Request, res: Response) => {
    try {
        const { sessionId } = req.params;

        const stats = getNextGenStats();
        const battles = stats.getActiveBattles(sessionId);
        const incidents = stats.getIncidentTimeline(sessionId);

        return res.json({
            sessionId,
            activeBattles: battles,
            incidentCount: incidents.length,
            recentIncidents: incidents.slice(-10),
            timestamp: Date.now(),
        });
    } catch (error) {
        console.error('[Broadcast] Error getting session stats:', error);
        return res.status(500).json({ error: 'Failed to get session stats' });
    }
});

/**
 * GET /api/broadcast/stats/:sessionId/driver/:driverId
 * Get stats for a specific driver
 */
router.get('/stats/:sessionId/driver/:driverId', apiLimiter, async (req: Request, res: Response) => {
    try {
        const { sessionId, driverId } = req.params;

        const stats = getNextGenStats();
        const driverStats = stats.getDriverStats(sessionId, driverId);

        if (!driverStats) {
            return res.status(404).json({ error: 'Driver stats not found' });
        }

        return res.json(driverStats);
    } catch (error) {
        console.error('[Broadcast] Error getting driver stats:', error);
        return res.status(500).json({ error: 'Failed to get driver stats' });
    }
});

/**
 * GET /api/broadcast/stats/:sessionId/battles
 * Get active battles
 */
router.get('/stats/:sessionId/battles', apiLimiter, async (req: Request, res: Response) => {
    try {
        const { sessionId } = req.params;

        const stats = getNextGenStats();
        const battles = stats.getActiveBattles(sessionId);

        return res.json({
            sessionId,
            battles,
            count: battles.length,
            timestamp: Date.now(),
        });
    } catch (error) {
        console.error('[Broadcast] Error getting battles:', error);
        return res.status(500).json({ error: 'Failed to get battles' });
    }
});

/**
 * GET /api/broadcast/stats/:sessionId/incidents
 * Get incident timeline
 */
router.get('/stats/:sessionId/incidents', apiLimiter, async (req: Request, res: Response) => {
    try {
        const { sessionId } = req.params;

        const stats = getNextGenStats();
        const incidents = stats.getIncidentTimeline(sessionId);

        return res.json({
            sessionId,
            incidents,
            count: incidents.length,
            timestamp: Date.now(),
        });
    } catch (error) {
        console.error('[Broadcast] Error getting incidents:', error);
        return res.status(500).json({ error: 'Failed to get incidents' });
    }
});

/**
 * GET /api/broadcast/telemetry/:sessionId/live
 * Get live telemetry for all drivers (for ticker/strip displays)
 */
router.get('/telemetry/:sessionId/live', apiLimiter, async (req: Request, res: Response) => {
    try {
        const { sessionId } = req.params;
        const driverIds = req.query.drivers ? (req.query.drivers as string).split(',') : undefined;

        const stats = getNextGenStats();
        const drivers = stats.getLiveTelemetry(sessionId, driverIds);

        return res.json({
            sessionId,
            drivers,
            count: drivers.length,
            timestamp: Date.now(),
        });
    } catch (error) {
        console.error('[Broadcast] Error getting live telemetry:', error);
        return res.status(500).json({ error: 'Failed to get live telemetry' });
    }
});

// =============================================================================
// TIME SYNC ENDPOINTS
// =============================================================================

/**
 * GET /api/broadcast/time/:sessionId
 * Get current time sync info
 */
router.get('/time/:sessionId', apiLimiter, async (req: Request, res: Response) => {
    try {
        const { sessionId } = req.params;

        const timeSync = getTimeSync();
        const sync = timeSync.getTimeSync(sessionId);

        if (!sync) {
            return res.status(404).json({ error: 'Session not found' });
        }

        const latency = timeSync.getLatencyEstimate(sessionId);

        return res.json({
            ...sync,
            latency,
        });
    } catch (error) {
        console.error('[Broadcast] Error getting time sync:', error);
        return res.status(500).json({ error: 'Failed to get time sync' });
    }
});

/**
 * POST /api/broadcast/time/:sessionId/offset
 * Set broadcast companion offset for a viewer
 */
router.post('/time/:sessionId/offset', apiLimiter, async (req: Request, res: Response) => {
    try {
        const { sessionId } = req.params;
        const { viewerId, offsetMs } = req.body;

        if (!viewerId || typeof offsetMs !== 'number') {
            return res.status(400).json({ error: 'viewerId and offsetMs required' });
        }

        const timeSync = getTimeSync();
        const offset = timeSync.setBroadcastCompanionOffset(sessionId, viewerId, offsetMs);

        return res.json(offset);
    } catch (error) {
        console.error('[Broadcast] Error setting offset:', error);
        return res.status(500).json({ error: 'Failed to set offset' });
    }
});

// =============================================================================
// HEALTH & MONITORING ENDPOINTS
// =============================================================================

/**
 * GET /api/broadcast/health
 * Get system health metrics and alerts
 */
router.get('/health', apiLimiter, async (req: Request, res: Response) => {
    try {
        // Dynamic import to avoid circular dependency issues
        const { getConnectionMonitor } = await import('./services/ConnectionMonitor.js');
        const monitor = getConnectionMonitor();

        return res.json({
            metrics: monitor.getMetrics(),
            streams: monitor.getStreamStats(),
            connections: monitor.getConnectionStats().slice(0, 50), // Limit for performance
            alerts: monitor.getAlerts(20),
            timestamp: Date.now(),
        });
    } catch (error) {
        console.error('[Broadcast] Error getting health:', error);
        return res.status(500).json({ error: 'Failed to get health data' });
    }
});

export default router;
