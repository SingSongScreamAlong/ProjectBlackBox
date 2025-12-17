/**
 * Production Health Load Test for ProjectBlackBox
 * Tests public endpoints to verify server capacity
 * 
 * Usage:
 *   k6 run -e BASE_URL=https://coral-app-x988a.ondigitalocean.app tests/load/health-load-test.js
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
const healthSuccessRate = new Rate('health_success_rate');
const healthLatency = new Trend('health_latency');
const apiErrors = new Counter('api_errors');

// Configuration
const BASE_URL = __ENV.BASE_URL || 'http://localhost:3000';

// Test stages - progressive load increase
export const options = {
    stages: [
        { duration: '10s', target: 5 },    // Ramp to 5 users
        { duration: '20s', target: 5 },    // Stay at 5 users
        { duration: '10s', target: 10 },   // Ramp to 10 users
        { duration: '20s', target: 10 },   // Stay at 10 users
        { duration: '10s', target: 20 },   // Ramp to 20
        { duration: '20s', target: 20 },   // Stay at 20
        { duration: '10s', target: 50 },   // Ramp to 50
        { duration: '30s', target: 50 },   // Stay at 50
        { duration: '10s', target: 0 },    // Ramp down
    ],
    thresholds: {
        http_req_duration: ['p(95)<500', 'p(99)<1000'],
        http_req_failed: ['rate<0.05'],
        health_success_rate: ['rate>0.95'],
        health_latency: ['p(95)<300'],
    },
};

/**
 * Setup function - runs once
 */
export function setup() {
    console.log('🏁 Starting ProjectBlackBox Production Load Test');
    console.log(`Base URL: ${BASE_URL}`);

    // Verify server is reachable
    const healthRes = http.get(`${BASE_URL}/health`);
    if (healthRes.status !== 200) {
        console.error(`❌ Server health check failed: ${healthRes.status}`);
        throw new Error('Server not reachable');
    }
    console.log('✅ Server is reachable');
    return {};
}

/**
 * Main test function - runs for each VU iteration
 */
export default function () {
    // Test 1: Health endpoint
    group('Health Check', () => {
        const startTime = Date.now();
        const res = http.get(`${BASE_URL}/health`);
        const latency = Date.now() - startTime;

        healthLatency.add(latency);

        const success = check(res, {
            'health status 200': (r) => r.status === 200,
            'health latency < 300ms': () => latency < 300,
        });

        healthSuccessRate.add(success);

        if (!success) {
            apiErrors.add(1);
        }
    });

    sleep(0.5);

    // Test 2: Ready endpoint
    group('Ready Check', () => {
        const res = http.get(`${BASE_URL}/health/ready`);

        check(res, {
            'ready status 200 or 503': (r) => r.status === 200 || r.status === 503,
        });
    });

    sleep(0.5);

    // Test 3: Metrics endpoint
    group('Metrics', () => {
        const res = http.get(`${BASE_URL}/health/metrics`);

        check(res, {
            'metrics status 200': (r) => r.status === 200,
        });
    });

    sleep(0.5);
}

/**
 * Teardown function
 */
export function teardown() {
    console.log(`\n🏁 Production Load Test Complete`);
}
