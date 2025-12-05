/**
 * k6 Load Testing Script for ProjectBlackBox
 * Tests system scalability with increasing concurrent users
 * 
 * Usage:
 *   k6 run --vus 10 --duration 30s scaling-test.js
 *   k6 run scaling-test.js  (uses built-in stages)
 */

import http from 'k6/http';
import ws from 'k6/ws';
import { check, sleep, group } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
const telemetryRate = new Rate('telemetry_success_rate');
const telemetryLatency = new Trend('telemetry_latency');
const wsConnections = new Counter('websocket_connections');
const wsMessages = new Counter('websocket_messages');
const apiErrors = new Counter('api_errors');

// Configuration
const BASE_URL = __ENV.BASE_URL || 'http://localhost:3000';
const WS_URL = __ENV.WS_URL || 'ws://localhost:3000';

// Test stages - progressive load increase
export const options = {
    stages: [
        // Warm-up
        { duration: '30s', target: 1 },    // 1 user
        { duration: '30s', target: 5 },    // Ramp to 5 users
        { duration: '1m', target: 5 },     // Stay at 5 users

        // Scale up
        { duration: '30s', target: 10 },   // Ramp to 10 users
        { duration: '1m', target: 10 },    // Stay at 10 users

        { duration: '30s', target: 20 },   // Ramp to 20 users
        { duration: '1m', target: 20 },    // Stay at 20 users

        { duration: '30s', target: 50 },   // Ramp to 50 users
        { duration: '2m', target: 50 },    // Stay at 50 users

        { duration: '1m', target: 100 },   // Ramp to 100 users
        { duration: '2m', target: 100 },   // Stay at 100 users

        // Stress test
        { duration: '1m', target: 200 },   // Ramp to 200 users
        { duration: '2m', target: 200 },   // Stay at 200 users

        // Cool down
        { duration: '1m', target: 0 },     // Ramp down
    ],
    thresholds: {
        http_req_duration: ['p(95)<500', 'p(99)<1000'], // 95% under 500ms, 99% under 1s
        http_req_failed: ['rate<0.01'],                  // Error rate < 1%
        telemetry_success_rate: ['rate>0.95'],          // 95% success rate
        telemetry_latency: ['p(95)<200'],               // 95% under 200ms
        websocket_messages: ['count>1000'],             // At least 1000 messages
    },
};

/**
 * Generate mock telemetry data
 */
function generateTelemetryData(driverId) {
    const lap = Math.floor(Math.random() * 20) + 1;
    const trackProgress = Math.random();

    return {
        sessionId: `session_${__VU}`,
        driverId: `driver_${driverId}`,
        timestamp: Date.now(),
        lap: lap,
        lapDist: trackProgress * 5000,
        speed: 150 + Math.random() * 100,
        rpm: 5000 + Math.random() * 3000,
        gear: Math.floor(Math.random() * 6) + 1,
        throttle: Math.random(),
        brake: Math.random() * 0.5,
        clutch: Math.random() * 0.2,
        steeringAngle: (Math.random() - 0.5) * 0.6,
        lapTime: 90 + Math.random() * 10,
        fuelLevel: 50 - (lap * 2),
        tirePressure: {
            FL: 28 + Math.random() * 2,
            FR: 28 + Math.random() * 2,
            RL: 28 + Math.random() * 2,
            RR: 28 + Math.random() * 2,
        },
        tireTemp: {
            FL: 85 + Math.random() * 10,
            FR: 85 + Math.random() * 10,
            RL: 85 + Math.random() * 10,
            RR: 85 + Math.random() * 10,
        }
    };
}

/**
 * Setup function - runs once per VU
 */
export function setup() {
    console.log('🏁 Starting ProjectBlackBox Load Test');
    console.log(`Base URL: ${BASE_URL}`);
    console.log(`WebSocket URL: ${WS_URL}`);

    // Check if server is up
    const healthCheck = http.get(`${BASE_URL}/health`);
    check(healthCheck, {
        'server is healthy': (r) => r.status === 200,
    });

    return { startTime: Date.now() };
}

/**
 * Main test function - runs for each VU iteration
 */
export default function (data) {
    const driverId = __VU; // Virtual User ID as driver ID

    group('Health Checks', () => {
        const res = http.get(`${BASE_URL}/health`);
        check(res, {
            'health check status 200': (r) => r.status === 200,
            'health check has uptime': (r) => r.json('uptime') !== undefined,
        });
    });

    group('Telemetry Upload', () => {
        const telemetry = generateTelemetryData(driverId);
        const startTime = Date.now();

        const res = http.post(
            `${BASE_URL}/api/telemetry`,
            JSON.stringify(telemetry),
            {
                headers: { 'Content-Type': 'application/json' },
                tags: { name: 'TelemetryUpload' },
            }
        );

        const latency = Date.now() - startTime;
        telemetryLatency.add(latency);

        const success = check(res, {
            'telemetry upload status 200': (r) => r.status === 200 || r.status === 201,
            'telemetry upload latency < 500ms': () => latency < 500,
        });

        telemetryRate.add(success);

        if (!success) {
            apiErrors.add(1);
            console.error(`Telemetry upload failed: ${res.status} - ${res.body}`);
        }
    });

    group('WebSocket Connection', () => {
        const url = `${WS_URL}/ws`;

        const res = ws.connect(url, {}, function (socket) {
            wsConnections.add(1);

            socket.on('open', () => {
                console.log(`VU ${__VU}: WebSocket connected`);

                // Send telemetry via WebSocket
                for (let i = 0; i < 10; i++) {
                    const telemetry = generateTelemetryData(driverId);
                    socket.send(JSON.stringify(telemetry));
                    wsMessages.add(1);
                    socket.setTimeout(() => { }, 100); // 100ms between messages (10Hz)
                }
            });

            socket.on('message', (data) => {
                wsMessages.add(1);
                check(data, {
                    'received message': (d) => d.length > 0,
                });
            });

            socket.on('close', () => {
                console.log(`VU ${__VU}: WebSocket closed`);
            });

            socket.on('error', (e) => {
                console.error(`VU ${__VU}: WebSocket error: ${e.error()}`);
                apiErrors.add(1);
            });

            // Keep connection open for 5 seconds
            socket.setTimeout(() => {
                socket.close();
            }, 5000);
        });

        check(res, {
            'websocket connection successful': (r) => r && r.status === 101,
        });
    });

    // Simulate realistic user behavior - pause between actions
    sleep(Math.random() * 2 + 1); // 1-3 seconds
}

/**
 * Teardown function - runs once at the end
 */
export function teardown(data) {
    const duration = (Date.now() - data.startTime) / 1000;
    console.log(`\n🏁 Load Test Complete`);
    console.log(`Total Duration: ${duration.toFixed(2)}s`);
    console.log(`Check detailed metrics above`);
}
