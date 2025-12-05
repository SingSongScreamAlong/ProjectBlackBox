/**
 * SQL Injection Protection Tests
 */

import { SafeDB, sanitizeInputs, validateInput } from '../src/middleware/sql-injection-guard';
import express, { Express } from 'express';
import request from 'supertest';

describe('SQL Injection Protection', () => {
    describe('SafeDB', () => {
        let mockPool: any;
        let safeDB: SafeDB;

        beforeEach(() => {
            mockPool = {
                query: jest.fn().mockResolvedValue({ rows: [], rowCount: 0 })
            };
            safeDB = new SafeDB(mockPool);
        });

        it('should execute parameterized queries safely', async () => {
            await safeDB.query('SELECT * FROM users WHERE id = $1', [123]);

            expect(mockPool.query).toHaveBeenCalledWith(
                'SELECT * FROM users WHERE id = $1',
                [123]
            );
        });

        it('should reject queries with string interpolation patterns', async () => {
            const maliciousQuery = "SELECT * FROM users WHERE id = '${userId}'";

            await expect(
                safeDB.query(maliciousQuery, [])
            ).rejects.toThrow('Potential SQL injection detected');
        });

        it('should allow safe queries without parameters', async () => {
            await safeDB.query('SELECT COUNT(*) FROM users', []);

            expect(mockPool.query).toHaveBeenCalled();
        });
    });

    describe('validateInput', () => {
        it('should detect SQL injection patterns', () => {
            const maliciousInputs = [
                "'; DROP TABLE users; --",
                "1' OR '1'='1",
                "admin'--",
                "1; DELETE FROM users",
                "UNION SELECT * FROM passwords"
            ];

            maliciousInputs.forEach(input => {
                expect(validateInput(input)).toBe(false);
            });
        });

        it('should allow safe inputs', () => {
            const safeInputs = [
                'john.doe@example.com',
                'User123',
                'My safe comment',
                '12345'
            ];

            safeInputs.forEach(input => {
                expect(validateInput(input)).toBe(true);
            });
        });
    });

    describe('sanitizeInputs middleware', () => {
        let app: Express;

        beforeEach(() => {
            app = express();
            app.use(express.json());
            app.use(sanitizeInputs);
            app.post('/api/test', (req, res) => res.json({ success: true }));
        });

        it('should block requests with SQL injection in body', async () => {
            await request(app)
                .post('/api/test')
                .send({ username: "'; DROP TABLE users; --" })
                .expect(400);
        });

        it('should block requests with SQL injection in query params', async () => {
            await request(app)
                .post('/api/test?id=1%27%20OR%20%271%27%3D%271')
                .expect(400);
        });

        it('should allow safe requests', async () => {
            const response = await request(app)
                .post('/api/test')
                .send({ username: 'john.doe' })
                .expect(200);

            expect(response.body).toEqual({ success: true });
        });
    });
});
