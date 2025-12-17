
import { IGrader, GradeResult } from './types.js';
import { pool } from '../../db.js';

export class SafetyGrader implements IGrader {
    async grade(sessionId: string, driverId?: string): Promise<GradeResult> {
        // Let's do G-Force Smoothness as proxy for Safety/Control.
        // High jerk (change in G) = bad.

        let query = `
            SELECT g_lat, g_long, g_vert 
            FROM telemetry 
            WHERE session_id = $1
        `;
        const params: any[] = [sessionId];

        if (driverId) {
            query += ` AND driver_id = $2`;
            params.push(driverId);
        }

        query += ` LIMIT 10000`; // Limit sample size for performance

        const gForceRes = await pool.query(query, params);

        // Fix potential null rowCount (though pg usually returns 0, types might say otherwise)
        const rowCount = gForceRes.rowCount || 0;

        if (rowCount < 100) {
            return {
                category: 'Safety',
                score: 0,
                confidence: 0,
                feedback: ['Insufficient telemetry for safety grading.']
            };
        }

        // Count spikes > 3G (arbitrary threshold for 'unsafe' or 'violent' in some cars, maybe high for F1)
        let spikes = 0;
        gForceRes.rows.forEach(row => {
            if (Math.abs(row.g_lat || 0) > 3.0 || Math.abs(row.g_long || 0) > 3.0) {
                spikes++;
            }
        });

        const spikeRate = spikes / rowCount; // % of time above threshold

        // Score: 0 spikes = 100. > 1% spikes = 50.
        let score = Math.max(0, 100 - (spikeRate * 100 * 50)); // If 1% (0.01), minus 50.

        return {
            category: 'Safety',
            score: Math.round(score),
            confidence: 0.5, // Low confidence proxy
            feedback: [
                score < 80 ? 'High G-force events detected. Drive smoother.' : 'Smooth driving detected.'
            ],
            metadata: { spikes, spikeRate }
        };
    }
}
