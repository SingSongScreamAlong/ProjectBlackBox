/**
 * BroadcastBox Protocol Types
 * 
 * Types for the BroadcastBox streaming and stats system.
 * All timestamps are in milliseconds since session start unless otherwise noted.
 */

// =============================================================================
// STREAM REGISTRATION & HEALTH
// =============================================================================

export type StreamResolution = '480p' | '720p' | '1080p';
export type StreamCodec = 'H264' | 'VP8' | 'VP9' | 'AV1';
export type HardwareEncoder = 'NVENC' | 'AMF' | 'QSV' | 'SOFTWARE' | null;
export type StreamAccessLevel = 'public' | 'team' | 'league' | 'private';
export type StreamStatus = 'live' | 'starting' | 'offline' | 'degraded';

export interface StreamCapabilities {
  video: boolean;
  audio: boolean;
  resolution: StreamResolution;
  fps: 30 | 60 | 120;
  codec: StreamCodec;
  hardwareEncoder: HardwareEncoder;
}

export interface StreamRegistration {
  type: 'STREAM_REGISTRATION';
  driverId: string;
  driverName: string;
  sessionId: string;
  streamId: string;
  capabilities: StreamCapabilities;
  accessLevel: StreamAccessLevel;
  timestamp: number;
}

export interface StreamHealthMetrics {
  cpuPercent: number;
  ramPercent: number;
  encodeFps: number;
  targetFps: number;
  droppedFrames: number;
  bitrate: number;
  rttMs: number;
  iracingFps: number;
}

export interface StreamHealth {
  type: 'STREAM_HEALTH';
  streamId: string;
  metrics: StreamHealthMetrics;
  warnings: string[];
  timestamp: number;
}

export interface StreamDeregistration {
  type: 'STREAM_DEREGISTRATION';
  streamId: string;
  reason: 'user_stopped' | 'performance_failsafe' | 'session_ended' | 'error';
  timestamp: number;
}

// =============================================================================
// STREAM LIST (Server -> Webapp)
// =============================================================================

export interface DriverStream {
  driverId: string;
  driverName: string;
  carNumber: string;
  teamName: string;
  streamId: string;
  status: StreamStatus;
  resolution: StreamResolution;
  fps: number;
  accessLevel: StreamAccessLevel;
  viewerCount: number;
  position: number;  // Current race position
  classId: number;
  className: string;
}

export interface StreamListUpdate {
  type: 'STREAM_LIST_UPDATE';
  sessionId: string;
  streams: DriverStream[];
  timestamp: number;
}

// =============================================================================
// NEXT GEN STATS EVENTS
// =============================================================================

export interface PaceModel {
  cleanLapAvg: number;
  cleanLapStdDev: number;
  lastCleanLap: number | null;
  cleanLapCount: number;
  confidence: number;  // 0-1
}

export interface CurrentDelta {
  vsPersonalBest: number;  // seconds, negative = faster
  vsLeader: number;
  vsBehind: number;
  sector: number;
}

export interface PredictedGap {
  ahead: number;     // seconds
  behind: number;    // seconds
  inLaps: number;    // laps until position change (estimated)
  confidence: number;
}

export interface TireModel {
  estimatedWear: number;        // 0-100%
  estimatedLapsRemaining: number;
  degradationRate: number;      // seconds per lap loss
  confidence: number;
}

export interface FuelModel {
  currentFuel: number;          // liters or gallons
  fuelPerLap: number;
  lapsRemaining: number;
  canFinish: boolean;
  confidence: number;
}

export interface StatsDriverUpdate {
  type: 'STATS_DRIVER_UPDATE';
  driverId: string;
  sessionId: string;
  data: {
    paceModel: PaceModel;
    currentDelta: CurrentDelta;
    predictedGap: PredictedGap;
    tireModel: TireModel;
    fuelModel: FuelModel;
  };
  timestamp: number;
}

export type BattleRiskLevel = 'low' | 'medium' | 'high';

export interface Battle {
  id: string;
  drivers: string[];  // driver IDs (2-3 drivers)
  gapSeconds: number;
  overlapPercent: number;
  twoWide: boolean;
  threeWide: boolean;
  riskLevel: BattleRiskLevel;
  corner: string | null;
  lap: number;
  timestamp: number;
}

export interface StatsBattleUpdate {
  type: 'STATS_BATTLE_UPDATE';
  sessionId: string;
  battle: Battle;
}

export type IncidentType = 'contact' | 'unsafe_rejoin' | 'offtrack' | 'block' | 'push';
export type IncidentSeverity = 'minor' | 'moderate' | 'major';

export interface IncidentDriver {
  driverId: string;
  driverName: string;
  position: { x: number; y: number; z: number };
  overlapPercent: number;
  atFault: boolean | null;
  confidence: number;
}

export interface Incident {
  id: string;
  timestamp: number;
  lap: number;
  corner: string | null;
  drivers: IncidentDriver[];
  type: IncidentType;
  description: string;
  severity: IncidentSeverity;
}

export interface StatsIncidentTimelineEvent {
  type: 'STATS_INCIDENT_TIMELINE_EVENT';
  sessionId: string;
  incident: Incident;
}

export interface StatsConfidenceUpdate {
  type: 'STATS_CONFIDENCE_UPDATE';
  sessionId: string;
  driverId: string;
  metrics: {
    paceConfidence: number;
    gapConfidence: number;
    tireConfidence: number;
    fuelConfidence: number;
  };
  reason: string;
  timestamp: number;
}

export interface PitStop {
  inLap: number;
  outLap: number;
  pitLaneTime: number;      // seconds in pit lane
  stationaryTime: number;   // seconds stationary
  positionBefore: number;
  positionAfter: number;
  estimatedTimeToRecoverPosition: number;
  confidence: number;
}

export interface StatsPitCycleUpdate {
  type: 'STATS_PIT_CYCLE_UPDATE';
  sessionId: string;
  driverId: string;
  pitStop: PitStop;
  timestamp: number;
}

// =============================================================================
// WEBRTC SIGNALING
// =============================================================================

export interface WebRTCOffer {
  type: 'WEBRTC_OFFER';
  streamId: string;
  sdp: string;
  fromPeer: string;
}

export interface WebRTCAnswer {
  type: 'WEBRTC_ANSWER';
  streamId: string;
  sdp: string;
  fromPeer: string;
}

export interface WebRTCIceCandidate {
  type: 'WEBRTC_ICE_CANDIDATE';
  streamId: string;
  candidate: RTCIceCandidateInit;
  fromPeer: string;
}

export interface WebRTCDisconnect {
  type: 'WEBRTC_DISCONNECT';
  streamId: string;
  fromPeer: string;
  reason: string;
}

export type WebRTCSignalingMessage = 
  | WebRTCOffer 
  | WebRTCAnswer 
  | WebRTCIceCandidate 
  | WebRTCDisconnect;

// =============================================================================
// TIME SYNCHRONIZATION
// =============================================================================

export interface TimeSync {
  sessionId: string;
  sessionStartUnixMs: number;   // Unix epoch when session started
  sessionTimeMs: number;        // Milliseconds since session start
  serverTimeMs: number;         // Server's current Unix time
  drift: number;                // Estimated clock drift in ms
}

export interface BroadcastCompanionOffset {
  sessionId: string;
  viewerId: string;
  offsetMs: number;             // broadcastTime - sessionTime
  calibratedAt: number;
}

// =============================================================================
// ACCESS CONTROL
// =============================================================================

export type Role = 'guest' | 'public' | 'subscriber' | 'team_member' | 'team_admin' | 'league_admin';

export interface StreamAccessRule {
  streamId: string;
  minRole: Role;
  allowedTeams: string[];       // Empty = all teams allowed
  allowedLeagues: string[];     // Empty = all leagues allowed
}

export interface ViewerSession {
  viewerId: string;
  sessionId: string;
  role: Role;
  teamId: string | null;
  leagueId: string | null;
  activeStreams: string[];      // Stream IDs currently watching
  connectedAt: number;
}

// =============================================================================
// UNION TYPES FOR ALL BROADCAST EVENTS
// =============================================================================

export type BroadcastEvent =
  | StreamRegistration
  | StreamHealth
  | StreamDeregistration
  | StreamListUpdate
  | StatsDriverUpdate
  | StatsBattleUpdate
  | StatsIncidentTimelineEvent
  | StatsConfidenceUpdate
  | StatsPitCycleUpdate
  | WebRTCOffer
  | WebRTCAnswer
  | WebRTCIceCandidate
  | WebRTCDisconnect;

// =============================================================================
// CONFIGURATION
// =============================================================================

export interface StreamConfig {
  enabled: boolean;
  fps: 30 | 60 | 120;
  resolution: StreamResolution;
  bitrate: number;              // kbps
  transport: 'webrtc' | 'srt' | 'rtmp';
  stunServers: string[];
  turnServer: string | null;
  turnUsername: string | null;
  turnCredential: string | null;
}

export interface PerformanceThresholds {
  failsafeFpsMin: number;       // Min iRacing FPS before degradation
  failsafeCpuMax: number;       // Max CPU % before degradation
  failsaseEncodeLagMs: number;  // Max encoding delay
  degradeLevels: Array<{
    bitrate: number;
    fps: number;
    resolution: StreamResolution | 'disabled';
  }>;
}

export const DEFAULT_STREAM_CONFIG: StreamConfig = {
  enabled: false,
  fps: 60,
  resolution: '720p',
  bitrate: 4000,
  transport: 'webrtc',
  stunServers: [
    'stun:stun.l.google.com:19302',
    'stun:stun1.l.google.com:19302',
  ],
  turnServer: null,
  turnUsername: null,
  turnCredential: null,
};

export const DEFAULT_PERFORMANCE_THRESHOLDS: PerformanceThresholds = {
  failsafeFpsMin: 55,
  failsafeCpuMax: 85,
  failsaseEncodeLagMs: 50,
  degradeLevels: [
    { bitrate: 4000, fps: 60, resolution: '720p' },
    { bitrate: 2500, fps: 30, resolution: '720p' },
    { bitrate: 1500, fps: 30, resolution: '480p' },
    { bitrate: 0, fps: 0, resolution: 'disabled' },
  ],
};
