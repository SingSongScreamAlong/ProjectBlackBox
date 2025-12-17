
import { pool } from '../db.js';
import { IGrader, GradeResult } from './grading/types.js';
import { ConsistencyGrader } from './grading/ConsistencyGrader.js';
import { SafetyGrader } from './grading/SafetyGrader.js';

export class LearningEngineService {
    private graders: IGrader[] = [
        new ConsistencyGrader(),
        new SafetyGrader()
    ];

    /**
     * Analyze a completed session and update all drivers' skills
     */
    async processSession(sessionId: string): Promise<void> {
        console.log(`[LearningEngine] Processing session ${sessionId}`);

        // 1. Identify drivers
        const driversRes = await pool.query(`
            SELECT DISTINCT driver_id FROM telemetry WHERE session_id = $1
        `, [sessionId]);

        for (const row of driversRes.rows) {
            const driverId = row.driver_id;
            if (!driverId) continue;

            await this.processDriverSession(sessionId, driverId);
        }
    }

    private async processDriverSession(sessionId: string, driverId: string) {
        console.log(`[LearningEngine] Grading driver ${driverId} for session ${sessionId}`);

        const results: GradeResult[] = [];

        // Run all graders
        for (const grader of this.graders) {
            try {
                const result = await grader.grade(sessionId, driverId);
                results.push(result);
            } catch (e) {
                console.error(`[LearningEngine] Grader failed for ${driverId}`, e);
            }
        }

        if (results.length > 0) {
            await this.updateDriverSkills(driverId, results);
        }
    }

    private async updateDriverSkills(driverId: string, grades: GradeResult[]) {
        try {
            // Fetch current skills
            const res = await pool.query(`
                SELECT skills, overall FROM skill_progression WHERE driver_id = $1
            `, [driverId]);

            let skills: any = {};
            let overall: any = { level: 1, experience: 0 };

            if (res.rowCount > 0) {
                skills = res.rows[0].skills || {};
                overall = res.rows[0].overall || overall;
            }

            // Update skills based on grades
            // Simple MVP Logic: 
            // - Each Grade (0-100) adds XP to that skill category.
            // - XP = Grade * 10 (e.g. 90 score -> 900 XP)
            // - Level up every 2000 XP (arbitrary)

            for (const grade of grades) {
                const category = grade.category.toLowerCase(); // 'consistency', 'safety'

                if (!skills[category]) {
                    skills[category] = { level: 1, xp: 0 };
                }

                // Award XP
                const xpEarned = Math.round(grade.score * 10 * grade.confidence);
                skills[category].xp += xpEarned;

                // Level up logic (simple)
                while (skills[category].xp >= 1000 * skills[category].level) {
                    skills[category].level++;
                }

                // Add to overall XP
                overall.experience += xpEarned;
            }

            // Overall Level up
            while (overall.experience >= 2000 * overall.level) {
                overall.level++;
            }

            // Upsert DB
            await pool.query(`
                INSERT INTO skill_progression (driver_id, skills, overall, updated_at)
                VALUES ($1, $2, $3, now())
                ON CONFLICT (driver_id) 
                DO UPDATE SET 
                    skills = EXCLUDED.skills,
                    overall = EXCLUDED.overall,
                    updated_at = now()
            `, [driverId, skills, overall]);

            console.log(`[LearningEngine] Updated skills for ${driverId}:`, skills);

        } catch (e) {
            console.error(`[LearningEngine] Failed to update skills for ${driverId}`, e);
        }
    }
}

export default new LearningEngineService();
