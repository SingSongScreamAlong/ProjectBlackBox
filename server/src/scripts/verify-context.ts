
import { pool } from '../db.js';
import DriverContextService from '../services/DriverContextService.js';
import { v4 as uuidv4 } from 'uuid';

async function verifyContext() {
    const driverId = `test-driver-${uuidv4()}`;

    console.log(`[Verify] Creating test driver ${driverId} with specific goals...`);

    // 1. Setup Test Data
    // Create Driver Skills
    await pool.query(`
        INSERT INTO skill_progression (driver_id, skills, overall, updated_at)
        VALUES ($1, $2, $3, now())
    `, [
        driverId,
        {
            consistency: { level: 5, xp: 5000 },
            safety: { level: 2, xp: 1200 }
        },
        { level: 3, experience: 6200 }
    ]);

    // Create Active Goal (Correct Schema)
    // type, difficulty, track_id, target_value are NOT NULL
    await pool.query(`
        INSERT INTO training_goals (
            id, driver_id, title, description, type, 
            difficulty, track_id, target_value, created_at
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, now())
    `, [
        uuidv4(),
        driverId,
        'Late Braking Mastery',
        'Improve late braking consistency at Turn 1',
        'braking',
        'intermediate',
        'test-track',
        0.8 // target_value placeholder
    ]);

    // 2. Fetch Context (Test Service)
    const context = await DriverContextService.getDriverContext(driverId);
    console.log('[Verify] Fetched Context:', JSON.stringify(context, null, 2));

    // Expect "Title: Description" format
    const expectedGoal = 'Late Braking Mastery: Improve late braking consistency at Turn 1';

    if (!context || context.goals[0] !== expectedGoal) {
        console.error(`[Verify] FAILURE: Context fetch failed or mismatch. Expected "${expectedGoal}", got "${context?.goals[0]}"`);
        process.exit(1);
    }

    console.log('[Verify] SUCCESS: DriverContextService correctly resolves skills and goals.');

    // Cleanup
    await pool.query('DELETE FROM skill_progression WHERE driver_id = $1', [driverId]);
    await pool.query('DELETE FROM training_goals WHERE driver_id = $1', [driverId]);

    process.exit(0);
}

verifyContext().catch(e => {
    console.error(e);
    process.exit(1);
});
