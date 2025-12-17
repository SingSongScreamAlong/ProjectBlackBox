/**
 * Track Learning Service
 * Records telemetry position data to build/improve track maps over time.
 * Stores learned points in localStorage and can generate SVG paths.
 */

export interface LearnedPoint {
    x: number;
    y: number;
    trackPosition: number; // 0-1 normalized position around track
    timestamp: number;
}

export interface LearnedTrack {
    trackId: string;
    trackName: string;
    points: LearnedPoint[];
    totalLaps: number;
    lastUpdated: number;
    generatedPath?: string; // SVG path 'd' attribute
}

const STORAGE_KEY = 'pitbox_learned_tracks';
const MIN_POINTS_FOR_PATH = 50; // Minimum points needed to generate a path
const SMOOTHING_FACTOR = 3; // Points to average for smoothing

class TrackLearningService {
    private learnedTracks: Map<string, LearnedTrack> = new Map();
    private isRecording: boolean = false;
    private currentTrackId: string | null = null;
    private lastRecordedPosition: number = 0;

    constructor() {
        this.loadFromStorage();
    }

    /**
     * Load learned tracks from localStorage
     */
    private loadFromStorage(): void {
        try {
            const stored = localStorage.getItem(STORAGE_KEY);
            if (stored) {
                const data = JSON.parse(stored);
                Object.entries(data).forEach(([id, track]) => {
                    this.learnedTracks.set(id, track as LearnedTrack);
                });
                console.log(`TrackLearningService: Loaded ${this.learnedTracks.size} learned tracks`);
            }
        } catch (e) {
            console.warn('TrackLearningService: Could not load from storage');
        }
    }

    /**
     * Save learned tracks to localStorage
     */
    private saveToStorage(): void {
        try {
            const data: { [key: string]: LearnedTrack } = {};
            this.learnedTracks.forEach((track, id) => {
                data[id] = track;
            });
            localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
        } catch (e) {
            console.warn('TrackLearningService: Could not save to storage');
        }
    }

    /**
     * Start recording for a specific track
     */
    startRecording(trackId: string, trackName: string): void {
        this.isRecording = true;
        this.currentTrackId = trackId;
        this.lastRecordedPosition = 0;

        if (!this.learnedTracks.has(trackId)) {
            this.learnedTracks.set(trackId, {
                trackId,
                trackName,
                points: [],
                totalLaps: 0,
                lastUpdated: Date.now(),
            });
        }
        console.log(`TrackLearningService: Started recording for ${trackName}`);
    }

    /**
     * Stop recording
     */
    stopRecording(): void {
        this.isRecording = false;
        this.currentTrackId = null;
        this.saveToStorage();
        console.log('TrackLearningService: Stopped recording');
    }

    /**
     * Record a position point from telemetry
     */
    recordPoint(x: number, y: number, trackPosition: number): void {
        if (!this.isRecording || !this.currentTrackId) return;

        const track = this.learnedTracks.get(this.currentTrackId);
        if (!track) return;

        // Detect lap completion (trackPosition wraps from ~1 to ~0)
        if (this.lastRecordedPosition > 0.9 && trackPosition < 0.1) {
            track.totalLaps++;
            console.log(`TrackLearningService: Lap completed! Total: ${track.totalLaps}`);
        }
        this.lastRecordedPosition = trackPosition;

        // Only record if position moved significantly (avoid duplicates)
        const lastPoint = track.points[track.points.length - 1];
        if (lastPoint) {
            const dist = Math.sqrt((x - lastPoint.x) ** 2 + (y - lastPoint.y) ** 2);
            if (dist < 5) return; // Skip if too close
        }

        track.points.push({
            x,
            y,
            trackPosition,
            timestamp: Date.now(),
        });

        track.lastUpdated = Date.now();

        // Regenerate path periodically
        if (track.points.length % 100 === 0 && track.points.length >= MIN_POINTS_FOR_PATH) {
            track.generatedPath = this.generatePathFromPoints(track.points);
            this.saveToStorage();
        }
    }

    /**
     * Generate an SVG path from recorded points
     */
    private generatePathFromPoints(points: LearnedPoint[]): string {
        if (points.length < MIN_POINTS_FOR_PATH) return '';

        // Sort points by trackPosition to ensure correct order
        const sorted = [...points].sort((a, b) => a.trackPosition - b.trackPosition);

        // Apply smoothing (moving average)
        const smoothed: { x: number; y: number }[] = [];
        for (let i = 0; i < sorted.length; i++) {
            let sumX = 0, sumY = 0, count = 0;
            for (let j = Math.max(0, i - SMOOTHING_FACTOR); j <= Math.min(sorted.length - 1, i + SMOOTHING_FACTOR); j++) {
                sumX += sorted[j].x;
                sumY += sorted[j].y;
                count++;
            }
            smoothed.push({ x: sumX / count, y: sumY / count });
        }

        // Generate SVG path with bezier curves for smoothness
        if (smoothed.length < 2) return '';

        let path = `M ${smoothed[0].x.toFixed(1)} ${smoothed[0].y.toFixed(1)}`;

        for (let i = 1; i < smoothed.length; i++) {
            const curr = smoothed[i];
            const prev = smoothed[i - 1];

            // Use quadratic bezier for smoother curves
            const cpX = (prev.x + curr.x) / 2;
            const cpY = (prev.y + curr.y) / 2;
            path += ` Q ${prev.x.toFixed(1)} ${prev.y.toFixed(1)} ${cpX.toFixed(1)} ${cpY.toFixed(1)}`;
        }

        // Close the path
        path += ' Z';

        return path;
    }

    /**
     * Get learned track data
     */
    getLearnedTrack(trackId: string): LearnedTrack | undefined {
        return this.learnedTracks.get(trackId);
    }

    /**
     * Get all learned tracks
     */
    getAllLearnedTracks(): LearnedTrack[] {
        return Array.from(this.learnedTracks.values());
    }

    /**
     * Check if we have a learned path for a track
     */
    hasLearnedPath(trackId: string): boolean {
        const track = this.learnedTracks.get(trackId);
        return !!track?.generatedPath;
    }

    /**
     * Get the generated SVG path for a track
     */
    getLearnedPath(trackId: string): string | undefined {
        return this.learnedTracks.get(trackId)?.generatedPath;
    }

    /**
     * Force regenerate path for a track
     */
    regeneratePath(trackId: string): string | undefined {
        const track = this.learnedTracks.get(trackId);
        if (!track || track.points.length < MIN_POINTS_FOR_PATH) return undefined;

        track.generatedPath = this.generatePathFromPoints(track.points);
        this.saveToStorage();
        return track.generatedPath;
    }

    /**
     * Clear learned data for a track
     */
    clearTrack(trackId: string): void {
        this.learnedTracks.delete(trackId);
        this.saveToStorage();
    }

    /**
     * Clear all learned data
     */
    clearAll(): void {
        this.learnedTracks.clear();
        localStorage.removeItem(STORAGE_KEY);
    }

    /**
     * Export learned tracks as JSON
     */
    exportData(): string {
        const data: { [key: string]: LearnedTrack } = {};
        this.learnedTracks.forEach((track, id) => {
            data[id] = track;
        });
        return JSON.stringify(data, null, 2);
    }

    /**
     * Import learned tracks from JSON
     */
    importData(json: string): void {
        try {
            const data = JSON.parse(json);
            Object.entries(data).forEach(([id, track]) => {
                this.learnedTracks.set(id, track as LearnedTrack);
            });
            this.saveToStorage();
        } catch (e) {
            console.error('TrackLearningService: Invalid import data');
        }
    }

    /**
     * Get recording status
     */
    isCurrentlyRecording(): boolean {
        return this.isRecording;
    }

    /**
     * Get stats for a track
     */
    getTrackStats(trackId: string): { points: number; laps: number; hasPath: boolean } | null {
        const track = this.learnedTracks.get(trackId);
        if (!track) return null;
        return {
            points: track.points.length,
            laps: track.totalLaps,
            hasPath: !!track.generatedPath,
        };
    }
}

export const trackLearningService = new TrackLearningService();
