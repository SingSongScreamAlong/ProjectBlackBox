/**
 * Data Transformation Adapters
 * Bridges WebSocket data structures to Visualization Component interfaces
 */

import {
  TelemetryData,
  CompetitorData,
  StrategyData,
  SessionInfo,
} from '../services/WebSocketService';
import {
  TrackCoordinate,
  DriverPosition,
} from '../components/Track3D/Track3DRenderer';
import {
  DriverTiming,
  SectorTime,
} from '../components/TimingTower/TimingTower';
import {
  TelemetryDataPoint,
} from '../components/Telemetry/TelemetryGraphs';
import {
  DriverStrategy,
  TireCompound,
  TireStint,
  PitStop,
} from '../components/Strategy/TireStrategyVisualization';
import {
  TrackPoint,
  DriverMapPosition,
} from '../components/TrackMap/TrackMapGenerator';

/**
 * Convert WebSocket telemetry to 3D track coordinates
 */
export function telemetryToTrackCoordinate(
  telemetry: TelemetryData,
  index: number
): TrackCoordinate {
  return {
    x: telemetry.position.x,
    y: telemetry.position.y,
    z: telemetry.position.z,
    sectorIndex: telemetry.sector - 1, // Convert 1-based to 0-based
  };
}

/**
 * Convert WebSocket telemetry to driver position for 3D visualization
 */
export function telemetryToDriverPosition(
  telemetry: TelemetryData,
  teamColor: string = '#3b82f6'
): DriverPosition {
  return {
    driverId: telemetry.driverId || 'player',
    driverName: telemetry.driverName || 'Player',
    position: telemetry.racePosition,
    x: telemetry.position.x,
    y: telemetry.position.y,
    z: telemetry.position.z,
    speed: telemetry.speed,
    teamColor: teamColor,
  };
}

/**
 * Convert WebSocket telemetry to timing tower data
 */
export function telemetryToDriverTiming(
  telemetry: TelemetryData,
  competitorData?: CompetitorData,
  teamColor: string = '#3b82f6',
  tireCompound: TireCompound = 'MEDIUM',
  tireLaps: number = 0,
  pitStops: number = 0
): DriverTiming {
  // Calculate sector times from telemetry
  const sectorTimes: SectorTime = {
    sector1: telemetry.bestSectorTimes[0] || undefined,
    sector2: telemetry.bestSectorTimes[1] || undefined,
    sector3: telemetry.bestSectorTimes[2] || undefined,
    sector1Status: 'normal',
    sector2Status: 'normal',
    sector3Status: 'normal',
  };

  // Determine gap
  let gap: number | 'LEADER' | 'LAP' = 'LEADER';
  if (telemetry.racePosition > 1) {
    gap = telemetry.gapAhead;
  }

  return {
    position: telemetry.racePosition,
    driverId: telemetry.driverId || 'player',
    driverName: telemetry.driverName || 'Player',
    driverNumber: telemetry.racePosition.toString(),
    teamName: 'Team',
    teamColor: teamColor,
    lastLapTime: telemetry.lapTime,
    bestLapTime: telemetry.bestLapTime,
    gap: gap,
    interval: telemetry.gapBehind,
    sectorTimes: sectorTimes,
    currentSector: telemetry.sector,
    pitStops: pitStops,
    tireCompound: tireCompound,
    tireLaps: tireLaps,
    positionChange: 0, // Would need historical data
    isInPit: false, // Would need pit lane detection
    isRetired: false,
  };
}

/**
 * Convert WebSocket telemetry to telemetry graph data point
 */
export function telemetryToGraphDataPoint(
  telemetry: TelemetryData,
  distance: number
): TelemetryDataPoint {
  return {
    timestamp: telemetry.timestamp,
    distance: distance,
    speed: telemetry.speed,
    throttle: telemetry.throttle * 100, // Convert to percentage
    brake: telemetry.brake * 100, // Convert to percentage
    steering: telemetry.steering * 45, // Convert to degrees (assuming -1 to 1 range)
    gear: telemetry.gear,
    rpm: telemetry.rpm,
    lapTime: telemetry.lapTime,
    sector: telemetry.sector,
  };
}

/**
 * Convert WebSocket telemetry to track map point
 */
export function telemetryToTrackPoint(
  telemetry: TelemetryData,
  distance: number
): TrackPoint {
  return {
    x: telemetry.position.x,
    y: telemetry.position.y,
    distance: distance,
    sectorIndex: telemetry.sector - 1, // Convert 1-based to 0-based
  };
}

/**
 * Convert WebSocket telemetry to driver map position
 */
export function telemetryToDriverMapPosition(
  telemetry: TelemetryData,
  teamColor: string = '#3b82f6'
): DriverMapPosition {
  return {
    driverId: telemetry.driverId || 'player',
    driverName: telemetry.driverName || 'Player',
    driverNumber: telemetry.racePosition.toString(),
    position: telemetry.racePosition,
    teamColor: teamColor,
    x: telemetry.position.x,
    y: telemetry.position.y,
    distance: telemetry.trackPosition,
    speed: telemetry.speed,
  };
}

/**
 * Generate team color based on driver ID or position
 */
export function generateTeamColor(driverId: string, position: number): string {
  const colors = [
    '#3b82f6', // Blue
    '#ef4444', // Red
    '#22c55e', // Green
    '#eab308', // Yellow
    '#9333ea', // Purple
    '#06b6d4', // Cyan
    '#f59e0b', // Orange
    '#ec4899', // Pink
    '#8b5cf6', // Violet
    '#10b981', // Emerald
  ];

  // Use position to determine color for consistency
  return colors[(position - 1) % colors.length];
}

/**
 * Determine tire compound from tire temperatures (heuristic)
 */
export function determineTireCompound(tireTemps: {
  frontLeft: { temp: number };
  frontRight: { temp: number };
  rearLeft: { temp: number };
  rearRight: { temp: number };
}): TireCompound {
  const avgTemp =
    (tireTemps.frontLeft.temp +
      tireTemps.frontRight.temp +
      tireTemps.rearLeft.temp +
      tireTemps.rearRight.temp) /
    4;

  // Heuristic: higher temps might indicate softer compound
  if (avgTemp > 90) return 'SOFT';
  if (avgTemp > 80) return 'MEDIUM';
  if (avgTemp < 60) return 'WET';
  if (avgTemp < 70) return 'INTERMEDIATE';
  return 'HARD';
}

/**
 * Build track data from accumulated telemetry history
 */
export class TrackDataBuilder {
  private trackPoints: Map<number, TrackCoordinate> = new Map();
  private maxPoints: number = 2000;

  addTelemetryPoint(telemetry: TelemetryData): void {
    const distance = Math.floor(telemetry.trackPosition);

    // Only add if we don't have this distance yet (prevent duplicates)
    if (!this.trackPoints.has(distance)) {
      this.trackPoints.set(distance, telemetryToTrackCoordinate(telemetry, distance));
    }

    // Limit the number of points
    if (this.trackPoints.size > this.maxPoints) {
      const firstKey = this.trackPoints.keys().next().value;
      if (firstKey !== undefined) {
        this.trackPoints.delete(firstKey);
      }
    }
  }

  getTrackData(): TrackCoordinate[] {
    return Array.from(this.trackPoints.values()).sort((a, b) => {
      // Sort by distance if available, otherwise by insertion order
      const distA = a.sectorIndex !== undefined ? a.sectorIndex : 0;
      const distB = b.sectorIndex !== undefined ? b.sectorIndex : 0;
      return distA - distB;
    });
  }

  clear(): void {
    this.trackPoints.clear();
  }
}

/**
 * Build telemetry history for graphs
 */
export class TelemetryHistoryBuilder {
  private dataPoints: TelemetryDataPoint[] = [];
  private maxPoints: number = 1000;
  private currentDistance: number = 0;

  addTelemetryPoint(telemetry: TelemetryData): void {
    this.currentDistance += telemetry.speed * 0.01; // Rough distance calculation

    const dataPoint = telemetryToGraphDataPoint(telemetry, this.currentDistance);
    this.dataPoints.push(dataPoint);

    // Limit the number of points
    if (this.dataPoints.length > this.maxPoints) {
      this.dataPoints.shift();
    }
  }

  getTelemetryData(): TelemetryDataPoint[] {
    return [...this.dataPoints];
  }

  clear(): void {
    this.dataPoints = [];
    this.currentDistance = 0;
  }
}

/**
 * Build strategy data from session history
 */
export class StrategyDataBuilder {
  private stints: Map<string, TireStint[]> = new Map();
  private pitStops: Map<string, PitStop[]> = new Map();
  private currentLap: number = 1;

  addPitStop(
    driverId: string,
    lap: number,
    duration: number,
    oldCompound: TireCompound,
    newCompound: TireCompound
  ): void {
    const stops = this.pitStops.get(driverId) || [];
    stops.push({
      lap,
      duration,
      reason: 'tire-change',
      oldCompound,
      newCompound,
    });
    this.pitStops.set(driverId, stops);

    // Update stints
    const stints = this.stints.get(driverId) || [];
    if (stints.length > 0) {
      const lastStint = stints[stints.length - 1];
      lastStint.endLap = lap;
      lastStint.lapCount = lap - lastStint.startLap;
      lastStint.isCurrentStint = false;
    }

    // Start new stint
    stints.push({
      compound: newCompound,
      startLap: lap,
      endLap: this.currentLap,
      lapCount: this.currentLap - lap,
      isCurrentStint: true,
    });
    this.stints.set(driverId, stints);
  }

  updateCurrentLap(lap: number): void {
    this.currentLap = lap;

    // Update current stint lap counts
    Array.from(this.stints.entries()).forEach(([driverId, stints]) => {
      if (stints.length > 0) {
        const lastStint = stints[stints.length - 1];
        if (lastStint.isCurrentStint) {
          lastStint.endLap = lap;
          lastStint.lapCount = lap - lastStint.startLap;
        }
      }
    });
  }

  getDriverStrategy(
    driverId: string,
    driverName: string,
    teamColor: string
  ): DriverStrategy {
    const stints = this.stints.get(driverId) || [];
    const stops = this.pitStops.get(driverId) || [];

    return {
      driverId,
      driverName,
      driverNumber: '1', // Would need to be tracked
      teamColor,
      stints,
      pitStops: stops,
      totalPitStops: stops.length,
    };
  }

  clear(): void {
    this.stints.clear();
    this.pitStops.clear();
    this.currentLap = 1;
  }
}

/**
 * Multi-driver data aggregator
 */
export class MultiDriverAggregator {
  private drivers: Map<string, TelemetryData> = new Map();
  private teamColors: Map<string, string> = new Map();

  updateDriver(telemetry: TelemetryData): void {
    const driverId = telemetry.driverId || 'player';
    this.drivers.set(driverId, telemetry);

    // Assign team color if not already assigned
    if (!this.teamColors.has(driverId)) {
      this.teamColors.set(
        driverId,
        generateTeamColor(driverId, telemetry.racePosition)
      );
    }
  }

  getAllDriverPositions(): DriverPosition[] {
    return Array.from(this.drivers.entries()).map(([driverId, telemetry]) => {
      const teamColor = this.teamColors.get(driverId) || '#3b82f6';
      return telemetryToDriverPosition(telemetry, teamColor);
    });
  }

  getAllDriverTimings(): DriverTiming[] {
    return Array.from(this.drivers.entries()).map(([driverId, telemetry]) => {
      const teamColor = this.teamColors.get(driverId) || '#3b82f6';
      const tireCompound = determineTireCompound(telemetry.tires);
      return telemetryToDriverTiming(telemetry, undefined, teamColor, tireCompound, telemetry.lap);
    });
  }

  getAllDriverMapPositions(): DriverMapPosition[] {
    return Array.from(this.drivers.entries()).map(([driverId, telemetry]) => {
      const teamColor = this.teamColors.get(driverId) || '#3b82f6';
      return telemetryToDriverMapPosition(telemetry, teamColor);
    });
  }

  getDriver(driverId: string): TelemetryData | undefined {
    return this.drivers.get(driverId);
  }

  clear(): void {
    this.drivers.clear();
    this.teamColors.clear();
  }
}

export default {
  telemetryToTrackCoordinate,
  telemetryToDriverPosition,
  telemetryToDriverTiming,
  telemetryToGraphDataPoint,
  telemetryToTrackPoint,
  telemetryToDriverMapPosition,
  generateTeamColor,
  determineTireCompound,
  TrackDataBuilder,
  TelemetryHistoryBuilder,
  StrategyDataBuilder,
  MultiDriverAggregator,
};
