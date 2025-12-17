
import { pool } from '../db.js';
import LearningEngineService from '../services/LearningEngineService.js';
import { v4 as uuidv4 } from 'uuid';

async function verifyLearning() {
    const sessionId = uuidv4();
    const driverId = 'test-driver-learning';

    console.log(`[Verify] Creating session ${sessionId} for driver ${driverId}`);

    // 1. Create Session
    await pool.query('INSERT INTO sessions (id, name, track) VALUES ($1, $2, $3)', [sessionId, 'Learning Verify', 'Test Track']);

    // 2. Insert Telemetry (Simulate 3 consistent laps)
    const baseTime = Date.now();

    const insertTelemetry = async (lap: number, timeOffset: number) => {
        await pool.query(`
            INSERT INTO telemetry (session_id, driver_id, ts, lap)
            VALUES ($1, $2, to_timestamp($3 / 1000.0), $4)
        `, [sessionId, driverId, baseTime + (timeOffset * 1000), lap]);
    };

    // Lap 1
    await insertTelemetry(1, 0);
    await insertTelemetry(1, 60);

    // Lap 2
    await insertTelemetry(2, 65);
    await insertTelemetry(2, 125); // 60s later

    // Lap 3
    await insertTelemetry(3, 130);
    await insertTelemetry(3, 190.5); // 60.5s later

    console.log('[Verify] Telemetry inserted. Processing session...');

    // 3. Process
    await LearningEngineService.processSession(sessionId);

    // 4. Verify
    const res = await pool.query('SELECT * FROM skill_progression WHERE driver_id = $1', [driverId]);

    if (res.rowCount === 0) {
        console.error('[Verify] FAILURE: No skill progression found!');
        process.exit(1);
    }

    const skills = res.rows[0].skills;
    console.log('[Verify] Skills found:', JSON.stringify(skills, null, 2));

    let passed = true;
    if (skills.consistency && skills.consistency.xp > 0) {
        console.log('[Verify] SUCCESS: Consistency XP awarded!');
    } else {
        console.error('[Verify] FAILURE: Consistency XP not found or zero.');
        passed = false;
    }

    if (skills.safety && skills.safety.xp >= 0) {
        console.log('[Verify] SUCCESS: Safety XP entry exists.');
    }

    // Cleanup
    await pool.query('DELETE FROM sessions WHERE id = $1', [sessionId]);
    await pool.query('DELETE FROM telemetry WHERE session_id = $1', [sessionId]);
    // Optionally delete skill_progression if we want specific cleanup, but keeping it is fine.

    if (!passed) process.exit(1);
    process.exit(0);
}

verifyLearning().catch(e => {
    console.error(e);
    process.exit(1);
});
