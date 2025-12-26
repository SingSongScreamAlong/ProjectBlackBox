/**
 * NextGenStatsService
 * 
 * Advanced analytics engine for BroadcastBox "Next Gen Stats".
 * Computes pace models, gap predictions, battle detection, and incident timelines.
 */

import { EventEmitter } from 'events';
import { v4 as uuidv4 } from 'uuid';
import type {
    StatsDriverUpdate,
    StatsBattleUpdate,
    StatsIncidentTimelineEvent,
    StatsConfidenceUpdate,
    StatsPitCycleUpdate,
    PaceModel,
    PredictedGap,
    TireModel,
    FuelModel,
    Battle,
    Incident,
    BattleRiskLevel,
    IncidentType,
    IncidentSeverity,
} from '../types/broadcast.js';

// Internal data structures for tracking driver performance
interface LapData {
    lapNumber: number;
    lapTime: number;
    isClean: boolean;  // No incidents, no pit stop
    sectors: number[];
    timestamp: number;
}

interface DriverStats {
    driverId: string;
    driverName: string;
    sessionId: string;
    laps: LapData[];
    currentLap: number;
    currentPosition: number;
    bestLapTime: number;
    lastLapTime: number;
    currentSector: number;
    sectorTimes: number[];
    inPit: boolean;
    pitLaps: number[];
    incidentCount: number;
    fuelLevel: number;
    fuelPerLap: number[];
    tireWear: number;
    lastUpdate: number;
}

interface ActiveBattle {
    id: string;
    drivers: string[];
    startTime: number;
    lastUpdate: number;
    maxOverlap: number;
    twoWideCount: number;
    threeWideCount: number;
}

export class NextGenStatsService extends EventEmitter {
    private driverStats: Map<string, DriverStats> = new Map(); // driverId -> stats
    private activeBattles: Map<string, ActiveBattle> = new Map();
    private incidents: Map<string, Incident[]> = new Map(); // sessionId -> incidents

    // Configuration
    private readonly CLEAN_LAP_THRESHOLD = 0.02; // 2% slower than best = still clean
    private readonly BATTLE_GAP_THRESHOLD = 2.0; // seconds
    private readonly OVERLAP_BATTLE_THRESHOLD = 0.1; // 10% overlap

    constructor() {
        super();
    }

    /**
     * Update driver telemetry data
     */
    updateTelemetry(sessionId: string, telemetry: any): void {
        const driverId = telemetry.driverId;
        if (!driverId) return;

        let stats = this.driverStats.get(driverId);
        if (!stats) {
            stats = this.initDriverStats(sessionId, driverId, telemetry.driverName || 'Unknown');
        }

        // Update current state
        stats.currentLap = telemetry.lap || stats.currentLap;
        stats.currentPosition = telemetry.racePosition || stats.currentPosition;
        stats.currentSector = telemetry.sector || stats.currentSector;
        stats.inPit = telemetry.inPitLane || false;
        stats.fuelLevel = telemetry.fuelLevel || stats.fuelLevel;
        stats.tireWear = telemetry.tireWear || stats.tireWear;
        stats.lastUpdate = Date.now();

        // Detect lap completion
        if (telemetry.lapTime && telemetry.lapTime !== stats.lastLapTime) {
            this.recordLap(stats, telemetry.lapTime, telemetry.sectorTimes || []);
        }

        this.driverStats.set(driverId, stats);
    }

    /**
     * Process overlap event for battle detection
     */
    processOverlapEvent(sessionId: string, event: any): void {
        const drivers = event.drivers || [];
        if (drivers.length < 2) return;

        const battleId = this.getBattleId(drivers);
        let battle = this.activeBattles.get(battleId);

        if (!battle) {
            battle = {
                id: battleId,
                drivers,
                startTime: Date.now(),
                lastUpdate: Date.now(),
                maxOverlap: event.overlapPercent || 0,
                twoWideCount: 0,
                threeWideCount: 0,
            };
            this.activeBattles.set(battleId, battle);
        }

        battle.lastUpdate = Date.now();
        battle.maxOverlap = Math.max(battle.maxOverlap, event.overlapPercent || 0);

        if (event.twoWide) battle.twoWideCount++;
        if (event.threeWide) battle.threeWideCount++;

        // Emit battle update
        const battleUpdate: StatsBattleUpdate = {
            type: 'STATS_BATTLE_UPDATE',
            sessionId,
            battle: {
                id: battleId,
                drivers,
                gapSeconds: event.gapSeconds || 0,
                overlapPercent: event.overlapPercent || 0,
                twoWide: event.twoWide || false,
                threeWide: event.threeWide || false,
                riskLevel: this.calculateRiskLevel(event),
                corner: event.corner || null,
                lap: event.lap || 0,
                timestamp: Date.now(),
            },
        };

        this.emit('battle_update', battleUpdate);
    }

    /**
     * Process incident event
     */
    processIncident(sessionId: string, event: any): void {
        const incident: Incident = {
            id: uuidv4(),
            timestamp: Date.now(),
            lap: event.lap || 0,
            corner: event.corner || null,
            drivers: (event.drivers || []).map((d: any) => ({
                driverId: d.driverId,
                driverName: d.driverName || 'Unknown',
                position: d.position || { x: 0, y: 0, z: 0 },
                overlapPercent: d.overlapPercent || 0,
                atFault: null, // Determined by analysis
                confidence: 0.5,
            })),
            type: this.classifyIncident(event),
            description: this.generateIncidentDescription(event),
            severity: this.classifyIncidentSeverity(event),
        };

        // Store incident
        if (!this.incidents.has(sessionId)) {
            this.incidents.set(sessionId, []);
        }
        this.incidents.get(sessionId)!.push(incident);

        // Emit incident event
        const incidentEvent: StatsIncidentTimelineEvent = {
            type: 'STATS_INCIDENT_TIMELINE_EVENT',
            sessionId,
            incident,
        };

        this.emit('incident', incidentEvent);

        // Update driver stats
        for (const driver of incident.drivers) {
            const stats = this.driverStats.get(driver.driverId);
            if (stats) {
                stats.incidentCount++;
            }
        }
    }

    /**
     * Get computed stats for a driver
     */
    getDriverStats(sessionId: string, driverId: string): StatsDriverUpdate | null {
        const stats = this.driverStats.get(driverId);
        if (!stats || stats.sessionId !== sessionId) {
            return null;
        }

        const paceModel = this.computePaceModel(stats);
        const predictedGap = this.computePredictedGap(stats, sessionId);
        const tireModel = this.computeTireModel(stats);
        const fuelModel = this.computeFuelModel(stats);

        return {
            type: 'STATS_DRIVER_UPDATE',
            driverId,
            sessionId,
            data: {
                paceModel,
                currentDelta: {
                    vsPersonalBest: stats.lastLapTime - stats.bestLapTime,
                    vsLeader: this.getDeltaToLeader(sessionId, driverId),
                    vsBehind: this.getDeltaToBehind(sessionId, driverId),
                    sector: stats.currentSector,
                },
                predictedGap,
                tireModel,
                fuelModel,
            },
            timestamp: Date.now(),
        };
    }

    /**
     * Get all active battles for a session
     */
    getActiveBattles(sessionId: string): Battle[] {
        const now = Date.now();
        const staleThreshold = 10000; // 10 seconds

        const battles: Battle[] = [];

        for (const [id, battle] of this.activeBattles) {
            // Skip stale battles
            if (now - battle.lastUpdate > staleThreshold) {
                this.activeBattles.delete(id);
                continue;
            }

            // Check if battle is in this session
            const firstDriver = this.driverStats.get(battle.drivers[0]);
            if (!firstDriver || firstDriver.sessionId !== sessionId) {
                continue;
            }

            battles.push({
                id,
                drivers: battle.drivers,
                gapSeconds: 0, // Would need live gap data
                overlapPercent: battle.maxOverlap,
                twoWide: battle.twoWideCount > 0,
                threeWide: battle.threeWideCount > 0,
                riskLevel: battle.threeWideCount > 0 ? 'high' : battle.twoWideCount > 2 ? 'medium' : 'low',
                corner: null,
                lap: firstDriver.currentLap,
                timestamp: battle.lastUpdate,
            });
        }

        // Sort by risk level (high first)
        return battles.sort((a, b) => {
            const order: Record<BattleRiskLevel, number> = { high: 0, medium: 1, low: 2 };
            return order[a.riskLevel] - order[b.riskLevel];
        });
    }

    /**
     * Get incident timeline for a session
     */
    getIncidentTimeline(sessionId: string): Incident[] {
        return this.incidents.get(sessionId) || [];
    }

    /**
     * Get live telemetry data for all or specific drivers
     * Used for ticker/strip displays and real-time overlays
     */
    getLiveTelemetry(sessionId: string, driverIds?: string[]): any[] {
        const drivers: any[] = [];

        for (const [driverId, stats] of this.driverStats) {
            // Filter by session
            if (stats.sessionId !== sessionId) continue;

            // Filter by specific drivers if requested
            if (driverIds && !driverIds.includes(driverId)) continue;

            // Calculate delta to leader/ahead
            const delta = this.getDeltaToLeader(sessionId, driverId);

            drivers.push({
                driverId,
                carNumber: driverId.slice(-2), // Simplified - would come from driver data
                driverName: stats.driverName,
                position: stats.currentPosition,
                speed: 0, // Would need live telemetry
                gear: 0,
                lastLapTime: stats.lastLapTime,
                delta,
                inPit: stats.inPit,
                currentLap: stats.currentLap,
                bestLapTime: stats.bestLapTime === Infinity ? 0 : stats.bestLapTime,
            });
        }

        // Sort by position
        return drivers.sort((a, b) => a.position - b.position);
    }

    // ==========================================================================
    // PRIVATE HELPER METHODS
    // ==========================================================================

    private initDriverStats(sessionId: string, driverId: string, driverName: string): DriverStats {
        return {
            driverId,
            driverName,
            sessionId,
            laps: [],
            currentLap: 0,
            currentPosition: 0,
            bestLapTime: Infinity,
            lastLapTime: 0,
            currentSector: 0,
            sectorTimes: [],
            inPit: false,
            pitLaps: [],
            incidentCount: 0,
            fuelLevel: 100,
            fuelPerLap: [],
            tireWear: 0,
            lastUpdate: Date.now(),
        };
    }

    private recordLap(stats: DriverStats, lapTime: number, sectorTimes: number[]): void {
        const isClean = !stats.inPit && stats.incidentCount === 0;

        stats.laps.push({
            lapNumber: stats.currentLap,
            lapTime,
            isClean,
            sectors: sectorTimes,
            timestamp: Date.now(),
        });

        stats.lastLapTime = lapTime;

        if (isClean && lapTime < stats.bestLapTime) {
            stats.bestLapTime = lapTime;
        }

        // Track fuel usage
        if (stats.laps.length >= 2) {
            const fuelUsed = stats.laps[stats.laps.length - 2].lapTime > 0
                ? (100 - stats.fuelLevel) / stats.laps.length
                : 0;
            stats.fuelPerLap.push(fuelUsed);
        }
    }

    private computePaceModel(stats: DriverStats): PaceModel {
        const cleanLaps = stats.laps.filter(l => l.isClean);

        if (cleanLaps.length === 0) {
            return {
                cleanLapAvg: 0,
                cleanLapStdDev: 0,
                lastCleanLap: null,
                cleanLapCount: 0,
                confidence: 0,
            };
        }

        const times = cleanLaps.map(l => l.lapTime);
        const avg = times.reduce((a, b) => a + b, 0) / times.length;
        const variance = times.reduce((sum, t) => sum + Math.pow(t - avg, 2), 0) / times.length;
        const stdDev = Math.sqrt(variance);

        // Confidence increases with more clean laps, maxes at ~10 laps
        const confidence = Math.min(1, cleanLaps.length / 10);

        return {
            cleanLapAvg: avg,
            cleanLapStdDev: stdDev,
            lastCleanLap: cleanLaps[cleanLaps.length - 1]?.lapTime || null,
            cleanLapCount: cleanLaps.length,
            confidence,
        };
    }

    private computePredictedGap(stats: DriverStats, sessionId: string): PredictedGap {
        // Simplified gap prediction - would be more sophisticated in production
        return {
            ahead: 0,
            behind: 0,
            inLaps: 0,
            confidence: 0.3, // Low confidence for MVP
        };
    }

    private computeTireModel(stats: DriverStats): TireModel {
        const lapsCompleted = stats.laps.length;
        const degradation = lapsCompleted > 5
            ? (stats.laps[lapsCompleted - 1].lapTime - stats.bestLapTime) / lapsCompleted
            : 0;

        return {
            estimatedWear: Math.min(100, lapsCompleted * 3), // Simple linear model
            estimatedLapsRemaining: Math.max(0, 30 - lapsCompleted),
            degradationRate: degradation,
            confidence: lapsCompleted > 10 ? 0.7 : 0.3,
        };
    }

    private computeFuelModel(stats: DriverStats): FuelModel {
        const avgFuelPerLap = stats.fuelPerLap.length > 0
            ? stats.fuelPerLap.reduce((a, b) => a + b, 0) / stats.fuelPerLap.length
            : 2.5; // Default estimate

        const lapsRemaining = avgFuelPerLap > 0 ? Math.floor(stats.fuelLevel / avgFuelPerLap) : 0;

        return {
            currentFuel: stats.fuelLevel,
            fuelPerLap: avgFuelPerLap,
            lapsRemaining,
            canFinish: lapsRemaining > 10, // Simplified
            confidence: stats.fuelPerLap.length > 3 ? 0.8 : 0.4,
        };
    }

    private getDeltaToLeader(sessionId: string, driverId: string): number {
        // Would require tracking all drivers - simplified for MVP
        return 0;
    }

    private getDeltaToBehind(sessionId: string, driverId: string): number {
        // Would require tracking all drivers - simplified for MVP
        return 0;
    }

    private getBattleId(drivers: string[]): string {
        return drivers.sort().join('-');
    }

    private calculateRiskLevel(event: any): BattleRiskLevel {
        if (event.threeWide) return 'high';
        if (event.twoWide && event.overlapPercent > 0.5) return 'high';
        if (event.twoWide) return 'medium';
        if (event.overlapPercent > 0.3) return 'medium';
        return 'low';
    }

    private classifyIncident(event: any): IncidentType {
        const type = event.type?.toLowerCase() || '';
        if (type.includes('contact')) return 'contact';
        if (type.includes('rejoin')) return 'unsafe_rejoin';
        if (type.includes('offtrack')) return 'offtrack';
        if (type.includes('block')) return 'block';
        if (type.includes('push')) return 'push';
        return 'contact';
    }

    private classifyIncidentSeverity(event: any): IncidentSeverity {
        const incidentPoints = event.incidentPoints || 0;
        if (incidentPoints >= 4) return 'major';
        if (incidentPoints >= 2) return 'moderate';
        return 'minor';
    }

    private generateIncidentDescription(event: any): string {
        const drivers = event.drivers?.map((d: any) => d.driverName).join(' and ') || 'Unknown drivers';
        const type = event.type || 'incident';
        const corner = event.corner ? ` at ${event.corner}` : '';
        return `${drivers} involved in ${type}${corner}`;
    }

    /**
     * Cleanup old data
     */
    cleanupSession(sessionId: string): void {
        // Remove driver stats for this session
        for (const [driverId, stats] of this.driverStats) {
            if (stats.sessionId === sessionId) {
                this.driverStats.delete(driverId);
            }
        }

        // Remove incidents
        this.incidents.delete(sessionId);

        console.log(`[NextGenStats] Cleaned up session ${sessionId}`);
    }
}

// Singleton instance
let instance: NextGenStatsService | null = null;

export function getNextGenStats(): NextGenStatsService {
    if (!instance) {
        instance = new NextGenStatsService();
    }
    return instance;
}

export default NextGenStatsService;
