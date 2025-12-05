/**
 * Mock Telemetry Data Generator
 * Generates realistic iRacing telemetry data for load testing
 */

export interface TelemetryData {
    sessionId: string;
    driverId: string;
    timestamp: number;
    lap: number;
    lapDist: number;
    speed: number;
    rpm: number;
    gear: number;
    throttle: number;
    brake: number;
    clutch: number;
    steeringAngle: number;
    lapTime: number;
    fuelLevel: number;
    tirePressure: {
        FL: number;
        FR: number;
        RL: number;
        RR: number;
    };
    tireTemp: {
        FL: number;
        FR: number;
        RL: number;
        RR: number;
    };
}

export class MockTelemetryGenerator {
    private sessionId: string;
    private driverId: string;
    private currentLap: number = 1;
    private lapDistance: number = 0;
    private trackLength: number = 5000; // meters
    private baseSpeed: number = 200; // km/h
    private baseLapTime: number = 90; // seconds

    constructor(sessionId: string, driverId: string) {
        this.sessionId = sessionId;
        this.driverId = driverId;
    }

    /**
     * Generate a single telemetry sample
     */
    generateSample(): TelemetryData {
        // Simulate realistic racing data
        const trackProgress = this.lapDistance / this.trackLength;

        // Speed varies based on track position (corners vs straights)
        const speedVariation = Math.sin(trackProgress * Math.PI * 4) * 50;
        const speed = this.baseSpeed + speedVariation + this.randomNoise(10);

        // RPM correlates with speed
        const rpm = Math.floor((speed / 300) * 8000) + this.randomNoise(200);

        // Gear based on speed
        const gear = Math.min(6, Math.max(1, Math.floor(speed / 50)));

        // Throttle and brake based on speed changes
        const isAccelerating = speedVariation > 0;
        const throttle = isAccelerating ? 0.8 + Math.random() * 0.2 : 0.3 + Math.random() * 0.3;
        const brake = isAccelerating ? 0 : Math.random() * 0.5;

        // Steering varies through corners
        const steeringAngle = Math.sin(trackProgress * Math.PI * 6) * 0.3 + this.randomNoise(0.05);

        // Fuel decreases over time
        const fuelLevel = 50 - (this.currentLap * 2.5);

        // Tire pressures and temps increase with laps
        const basePressure = 28 + (this.currentLap * 0.5);
        const baseTemp = 80 + (this.currentLap * 5);

        const telemetry: TelemetryData = {
            sessionId: this.sessionId,
            driverId: this.driverId,
            timestamp: Date.now(),
            lap: this.currentLap,
            lapDist: this.lapDistance,
            speed: Math.max(0, speed),
            rpm: Math.max(0, Math.min(9000, rpm)),
            gear,
            throttle: Math.max(0, Math.min(1, throttle)),
            brake: Math.max(0, Math.min(1, brake)),
            clutch: gear === 1 ? Math.random() * 0.5 : 0,
            steeringAngle: Math.max(-1, Math.min(1, steeringAngle)),
            lapTime: this.baseLapTime + this.randomNoise(2),
            fuelLevel: Math.max(0, fuelLevel),
            tirePressure: {
                FL: basePressure + this.randomNoise(0.5),
                FR: basePressure + this.randomNoise(0.5),
                RL: basePressure + this.randomNoise(0.5),
                RR: basePressure + this.randomNoise(0.5),
            },
            tireTemp: {
                FL: baseTemp + this.randomNoise(5),
                FR: baseTemp + this.randomNoise(5),
                RL: baseTemp + this.randomNoise(5),
                RR: baseTemp + this.randomNoise(5),
            }
        };

        // Update position for next sample
        this.lapDistance += (speed / 3.6) * (1 / 60); // Assuming 60Hz updates

        if (this.lapDistance >= this.trackLength) {
            this.lapDistance = 0;
            this.currentLap++;
        }

        return telemetry;
    }

    /**
     * Generate multiple samples
     */
    generateBatch(count: number): TelemetryData[] {
        const samples: TelemetryData[] = [];
        for (let i = 0; i < count; i++) {
            samples.push(this.generateSample());
        }
        return samples;
    }

    /**
     * Add random noise to values
     */
    private randomNoise(magnitude: number): number {
        return (Math.random() - 0.5) * 2 * magnitude;
    }

    /**
     * Reset generator state
     */
    reset(): void {
        this.currentLap = 1;
        this.lapDistance = 0;
    }
}

/**
 * Generate mock session data
 */
export function generateMockSession(driverCount: number = 1) {
    const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const generators: MockTelemetryGenerator[] = [];

    for (let i = 0; i < driverCount; i++) {
        const driverId = `driver_${i + 1}`;
        generators.push(new MockTelemetryGenerator(sessionId, driverId));
    }

    return {
        sessionId,
        generators,
        generateSamples: (samplesPerDriver: number = 1) => {
            return generators.map(gen => gen.generateBatch(samplesPerDriver));
        }
    };
}

export default MockTelemetryGenerator;
