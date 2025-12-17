
export interface GradeResult {
    category: string;     // e.g. 'Consistency', 'Braking', 'Safety'
    score: number;        // 0 to 100
    confidence: number;   // 0.0 to 1.0
    feedback: string[];   // Specific feedback points
    metadata?: Record<string, any>;
}

export interface IGrader {
    /**
     * Analyze a session and return a grade
     */
    grade(sessionId: string, driverId?: string): Promise<GradeResult>;
}
