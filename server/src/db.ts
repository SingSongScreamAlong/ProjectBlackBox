import 'dotenv/config';
import { Pool } from 'pg';

const connectionString = process.env.PG_CONNECTION_STRING || process.env.DATABASE_URL || 'postgres://localhost:5432/blackbox_telemetry';

export const pool = new Pool({
  connectionString,
  // Fail fast if DB is unreachable instead of hanging
  connectionTimeoutMillis: Number(process.env.PG_CONN_TIMEOUT_MS ?? 5000),
  idleTimeoutMillis: Number(process.env.PG_IDLE_TIMEOUT_MS ?? 30000),
  max: Number(process.env.PG_POOL_MAX ?? 10),
});

export async function ping(): Promise<boolean> {
  try {
    const res = await pool.query('SELECT 1 as ok');
    return res.rows?.[0]?.ok === 1;
  } catch (e) {
    // eslint-disable-next-line no-console
    console.error('[DB] ping failed', e);
    return false;
  }
}

export async function withTx<T>(fn: (client: import('pg').PoolClient) => Promise<T>): Promise<T> {
  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    const result = await fn(client);
    await client.query('COMMIT');
    return result;
  } catch (e) {
    await client.query('ROLLBACK');
    throw e;
  } finally {
    client.release();
  }
}

export async function setStatementTimeout(ms: number): Promise<void> {
  // Use parameterized query for SQL injection protection
  const timeoutMs = Math.max(0, Math.floor(ms));
  await pool.query('SET statement_timeout = $1', [timeoutMs]);
}
