/**
 * CoachingService - Real-time AI coaching for race insights
 * 
 * Buffers incoming telemetry data and periodically triggers AI analysis
 * to generate coaching insights that are pushed to connected dashboards.
 */

import { Server as SocketIOServer } from 'socket.io';
import { OpenAIService, CoachingAnalysis } from '../openai-service.js';

interface TelemetrySample {
    timestamp: number;
    speed: number;
    rpm: number;
    gear: number;
    throttle: number;
    brake: number;
    lap: number;
    sector: number;
    tires?: {
        frontLeft: { temp: number; wear: number };
        frontRight: { temp: number; wear: number };
        rearLeft: { temp: number; wear: number };
        rearRight: { temp: number; wear: number };
    };
    gForce?: { lateral: number; longitudinal: number };
    trackPosition?: number;
    racePosition?: number;
}

interface CoachingInsight {
    id: string;
    title: string;
    description: string;
    priority: 'low' | 'medium' | 'high' | 'critical';
    category: string;
    confidence: number;
    impact: string;
    timestamp: number;
}

interface DriverSkillAnalysis {
    strengths: Array<{ skill: string; rating: number }>;
    focusAreas: Array<{ skill: string; rating: number }>;
    overallRating: number;
}

export class CoachingService {
    private io: SocketIOServer;
    private openaiService: OpenAIService;
    private telemetryBuffer: Map<string, TelemetrySample[]> = new Map();
    private lastAnalysis: Map<string, number> = new Map();
    private analysisInterval: number = 30000; // 30 seconds between analyses
    private bufferDuration: number = 30000; // Keep 30 seconds of data
    private enabled: boolean = false;
    private sessionInfo: Map<string, { track?: string; driverName?: string }> = new Map();

    constructor(io: SocketIOServer) {
        this.io = io;
        this.openaiService = new OpenAIService();
        this.enabled = this.openaiService.isEnabled();

        if (this.enabled) {
            console.log('🧠 CoachingService initialized - Real-time AI insights enabled');
        } else {
            console.log('⚠️  CoachingService disabled - OPENAI_API_KEY not configured');
        }
    }

    /**
     * Update session info (track, driver name) for better context
     */
    setSessionInfo(sessionId: string, info: { track?: string; driverName?: string }): void {
        this.sessionInfo.set(sessionId, info);
    }

    /**
     * Ingest telemetry data from relay
     * Called for each telemetry update received
     */
    async ingestTelemetry(sessionId: string, data: TelemetrySample): Promise<void> {
        if (!this.enabled) return;

        // Get or create buffer for this session
        if (!this.telemetryBuffer.has(sessionId)) {
            this.telemetryBuffer.set(sessionId, []);
        }

        const buffer = this.telemetryBuffer.get(sessionId)!;

        // Add sample with timestamp
        buffer.push({
            ...data,
            timestamp: data.timestamp || Date.now()
        });

        // Trim old samples (keep only bufferDuration worth)
        const cutoff = Date.now() - this.bufferDuration;
        while (buffer.length > 0 && buffer[0].timestamp < cutoff) {
            buffer.shift();
        }

        // Check if it's time for analysis
        await this.maybeAnalyze(sessionId);
    }

    /**
     * Check if enough time has passed since last analysis
     */
    private async maybeAnalyze(sessionId: string): Promise<void> {
        const lastTime = this.lastAnalysis.get(sessionId) || 0;
        const now = Date.now();

        // Need at least analysisInterval since last analysis
        if (now - lastTime < this.analysisInterval) {
            return;
        }

        // Need at least 10 samples to analyze
        const buffer = this.telemetryBuffer.get(sessionId);
        if (!buffer || buffer.length < 10) {
            return;
        }

        // Mark analysis time before async call to prevent duplicates
        this.lastAnalysis.set(sessionId, now);

        try {
            await this.runAnalysis(sessionId, buffer);
        } catch (error) {
            console.error(`[CoachingService] Analysis error for ${sessionId}:`, error);
        }
    }

    /**
     * Run AI analysis on buffered telemetry
     */
    private async runAnalysis(sessionId: string, buffer: TelemetrySample[]): Promise<void> {
        console.log(`🧠 [CoachingService] Running analysis for session ${sessionId} (${buffer.length} samples)`);

        const sessionInfo = this.sessionInfo.get(sessionId) || {};

        // Format data for OpenAI
        const telemetryData = buffer.map(sample => ({
            timestamp: sample.timestamp,
            lap: sample.lap || 0,
            sector: sample.sector || 0,
            speed: sample.speed || 0,
            rpm: sample.rpm || 0,
            gear: sample.gear || 0,
            throttle: sample.throttle || 0,
            brake: sample.brake || 0,
            tires: sample.tires ? {
                temp: {
                    fl: sample.tires.frontLeft?.temp || 0,
                    fr: sample.tires.frontRight?.temp || 0,
                    rl: sample.tires.rearLeft?.temp || 0,
                    rr: sample.tires.rearRight?.temp || 0
                },
                wear: {
                    fl: sample.tires.frontLeft?.wear || 0,
                    fr: sample.tires.frontRight?.wear || 0,
                    rl: sample.tires.rearLeft?.wear || 0,
                    rr: sample.tires.rearRight?.wear || 0
                }
            } : undefined,
            gForce: sample.gForce,
            trackPosition: sample.trackPosition || 0,
            racePosition: sample.racePosition || 0
        }));

        try {
            const analysis: CoachingAnalysis = await this.openaiService.analyzeTelemetryData(
                telemetryData,
                { track: sessionInfo.track, sessionId },
                { id: sessionId, name: sessionInfo.driverName }
            );

            // Convert to coaching insights format
            const insights = this.formatInsights(analysis);
            const skillAnalysis = this.formatSkillAnalysis(analysis);

            // Emit to all connected clients
            console.log(`📤 [CoachingService] Emitting ${insights.length} insights`);

            this.io.emit('coaching', insights);
            this.io.emit('skill_analysis', skillAnalysis);

        } catch (error) {
            console.error('[CoachingService] OpenAI analysis failed:', error);
        }
    }

    /**
     * Format CoachingAnalysis into CoachingInsight array for dashboard
     */
    private formatInsights(analysis: CoachingAnalysis): CoachingInsight[] {
        const insights: CoachingInsight[] = [];
        const now = Date.now();

        // Add performance as a main insight
        if (analysis.analysis.performance) {
            insights.push({
                id: `insight-${now}-0`,
                title: 'Performance Update',
                description: analysis.analysis.performance,
                priority: analysis.analysis.riskLevel === 'high' ? 'high' : 'medium',
                category: 'Performance',
                confidence: 85,
                impact: 'Current driving assessment',
                timestamp: now
            });
        }

        // Add recommendations as insights
        analysis.analysis.recommendations.forEach((rec, index) => {
            insights.push({
                id: `insight-${now}-rec-${index}`,
                title: 'Recommendation',
                description: rec,
                priority: this.getPriorityFromIndex(index),
                category: 'Technique',
                confidence: 80 - (index * 5),
                impact: 'Potential lap time improvement',
                timestamp: now
            });
        });

        // Add key insights
        analysis.analysis.keyInsights.forEach((insight, index) => {
            insights.push({
                id: `insight-${now}-key-${index}`,
                title: 'Key Insight',
                description: insight,
                priority: 'low',
                category: 'Analysis',
                confidence: 75,
                impact: 'Data pattern detected',
                timestamp: now
            });
        });

        // Limit to top 5 insights
        return insights.slice(0, 5);
    }

    /**
     * Format skill analysis for dashboard
     */
    private formatSkillAnalysis(analysis: CoachingAnalysis): DriverSkillAnalysis {
        // Generate skill ratings based on analysis content
        const riskLevel = analysis.analysis.riskLevel;

        return {
            strengths: [
                { skill: 'Consistency', rating: riskLevel === 'low' ? 85 : riskLevel === 'medium' ? 70 : 55 },
                { skill: 'Track Knowledge', rating: 75 }
            ],
            focusAreas: [
                { skill: 'Braking Points', rating: 65 },
                { skill: 'Corner Exit', rating: 60 }
            ],
            overallRating: riskLevel === 'low' ? 80 : riskLevel === 'medium' ? 65 : 50
        };
    }

    /**
     * Get priority based on recommendation order
     */
    private getPriorityFromIndex(index: number): 'low' | 'medium' | 'high' | 'critical' {
        if (index === 0) return 'high';
        if (index === 1) return 'medium';
        return 'low';
    }

    /**
     * Clear session data
     */
    clearSession(sessionId: string): void {
        this.telemetryBuffer.delete(sessionId);
        this.lastAnalysis.delete(sessionId);
        this.sessionInfo.delete(sessionId);
    }

    /**
     * Check if service is enabled
     */
    isEnabled(): boolean {
        return this.enabled;
    }
}

export default CoachingService;
