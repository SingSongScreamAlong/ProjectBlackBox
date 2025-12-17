
import { IGrader, GradeResult } from './types.js';
import { pool } from '../../db.js';

export class ConsistencyGrader implements IGrader {
    async grade(sessionId: string, driverId?: string): Promise<GradeResult> {
        // Fetch lap times
        let query = `
            WITH lap_boundaries AS (
                SELECT lap, MIN(ts) as lap_start, MAX(ts) as lap_end
                FROM telemetry
                WHERE session_id = $1 AND lap > 0
        `;
        const params: any[] = [sessionId];

        if (driverId) {
            query += ` AND driver_id = $2`;
            params.push(driverId);
        }

        query += `
                GROUP BY lap
            )
            SELECT 
                lap, 
                EXTRACT(EPOCH FROM (lap_end - lap_start)) as lap_time
            FROM lap_boundaries
            ORDER BY lap
        `;

        const lapTimesRes = await pool.query(query, params);

        const allLaps = lapTimesRes.rows.map(r => parseFloat(r.lap_time));

        // Filter out short/long laps (outliers, in/out laps)
        // Simple heuristic: laps between 10s and 600s
        const validLaps = allLaps.filter(t => t > 10 && t < 600);

        if (validLaps.length < 3) {
            return {
                category: 'Consistency',
                score: 0,
                confidence: 0, // Not enough data
                feedback: ['Not enough valid laps to grade consistency.']
            };
        }

        const avg = validLaps.reduce((a, b) => a + b, 0) / validLaps.length;
        const squareDiffs = validLaps.map(v => Math.pow(v - avg, 2));
        const stdDev = Math.sqrt(squareDiffs.reduce((a, b) => a + b, 0) / validLaps.length);

        // Coefficient of Variation (CV) as percentage
        const cv = (stdDev / avg) * 100;

        // Score: CV < 0.5% => 100
        // CV > 5% => 0
        // Linear interpolation
        // Score = 100 - ( (CV - 0.5) / (5 - 0.5) ) * 100
        // Clamp 0-100

        let score = 100;
        if (cv > 0.5) {
            score = Math.max(0, 100 - ((cv - 0.5) * 20)); // *20 is roughly (100/5)
        }

        const feedback: string[] = [];
        if (score > 90) feedback.push('Excellent consistency!');
        else if (score > 70) feedback.push('Good consistency, keeping laps within a small window.');
        else if (score < 50) feedback.push('Lap times are varying significantly. Focus on hitting marks consistently.');

        return {
            category: 'Consistency',
            score: Math.round(score),
            confidence: 1.0,
            feedback,
            metadata: {
                lapCount: validLaps.length,
                stdDev: Math.round(stdDev * 1000) / 1000,
                cv: Math.round(cv * 100) / 100
            }
        };
    }
}
