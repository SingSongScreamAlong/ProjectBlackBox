
import { pool } from '../db.js';

export interface DriverContext {
    skills: {
        consistency: { level: number; xp: number };
        safety: { level: number; xp: number };
        braking?: { level: number; xp: number };
        cornering?: { level: number; xp: number };
    };
    goals: string[]; // e.g. "Focus on late braking"
    overallLevel: number;
}

class DriverContextService {

    /**
     * Fetch all relevant context for a driver to inform AI generation.
     */
    async getDriverContext(driverId: string): Promise<DriverContext | null> {
        try {
            // 1. Fetch Skills
            const skillsRes = await pool.query(`
                SELECT skills, overall FROM skill_progression WHERE driver_id = $1
            `, [driverId]);

            let skills = { consistency: { level: 1, xp: 0 }, safety: { level: 1, xp: 0 } };
            let overallLevel = 1;

            if (skillsRes.rowCount > 0) {
                skills = skillsRes.rows[0].skills || skills;
                overallLevel = skillsRes.rows[0].overall?.level || 1;
            }

            // 2. Fetch Active Goals
            // Using `completed_at IS NULL` to determine active status
            const goalsRes = await pool.query(`
                SELECT type, title, description FROM training_goals 
                WHERE driver_id = $1 AND completed_at IS NULL
            `, [driverId]);

            const goals = goalsRes.rows.map(r => `${r.title}: ${r.description}`);

            return {
                skills,
                goals,
                overallLevel
            };

        } catch (error) {
            console.error(`[DriverContext] Failed to fetch context for ${driverId}`, error);
            return null;
        }
    }
}

export default new DriverContextService();
