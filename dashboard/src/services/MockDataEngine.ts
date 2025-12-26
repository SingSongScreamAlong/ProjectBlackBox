/**
 * MockDataEngine - Generates realistic racing data for UI testing
 * 
 * Toggle this on to see all BroadcastBox components with sample data
 * without needing a live iRacing connection.
 */

// Sample driver data
export const MOCK_DRIVERS = [
    { driverId: 'driver-001', driverName: 'Max Verstappen', carNumber: '1', teamName: 'Red Bull Racing' },
    { driverId: 'driver-002', driverName: 'Lewis Hamilton', carNumber: '44', teamName: 'Mercedes-AMG' },
    { driverId: 'driver-003', driverName: 'Charles Leclerc', carNumber: '16', teamName: 'Scuderia Ferrari' },
    { driverId: 'driver-004', driverName: 'Lando Norris', carNumber: '4', teamName: 'McLaren' },
    { driverId: 'driver-005', driverName: 'Carlos Sainz', carNumber: '55', teamName: 'Scuderia Ferrari' },
    { driverId: 'driver-006', driverName: 'George Russell', carNumber: '63', teamName: 'Mercedes-AMG' },
    { driverId: 'driver-007', driverName: 'Oscar Piastri', carNumber: '81', teamName: 'McLaren' },
    { driverId: 'driver-008', driverName: 'Sergio Perez', carNumber: '11', teamName: 'Red Bull Racing' },
];

// Generate mock stream
export function generateMockStream(driver: typeof MOCK_DRIVERS[0], position: number) {
    return {
        streamId: `stream-${driver.driverId}`,
        driverId: driver.driverId,
        driverName: driver.driverName,
        carNumber: driver.carNumber,
        teamName: driver.teamName,
        status: position <= 3 ? 'live' : Math.random() > 0.2 ? 'live' : 'degraded',
        resolution: '720p',
        fps: 25 + Math.floor(Math.random() * 10),
        accessLevel: 'public',
        viewerCount: Math.floor(Math.random() * 500) + 50,
        position,
        classId: 1,
        className: 'GT3',
    };
}

// Generate mock telemetry
export function generateMockTelemetry(driver: typeof MOCK_DRIVERS[0], position: number) {
    const baseSpeed = 280 - (position * 2);
    return {
        driverId: driver.driverId,
        driverName: driver.driverName,
        carNumber: driver.carNumber,
        position,
        speed: baseSpeed + Math.random() * 20,
        rpm: 8000 + Math.random() * 4000,
        rpmMax: 13000,
        gear: Math.floor(Math.random() * 4) + 4,
        throttle: Math.random(),
        brake: Math.random() * 0.3,
        clutch: 0,
        steering: (Math.random() - 0.5) * 0.4,
        lap: 15 + Math.floor(Math.random() * 3),
        lapTime: 81.5 + Math.random() * 2,
        bestLapTime: 80.123,
        lastLapTime: 81.234 + Math.random(),
        delta: (Math.random() - 0.5) * 0.5,
        inPit: false,
        gapToLeader: position > 1 ? (position - 1) * 1.5 + Math.random() : 0,
    };
}

// Generate mock battles
export function generateMockBattles() {
    return [
        {
            id: 'battle-1',
            drivers: ['driver-001', 'driver-002'],
            driverNames: ['Max Verstappen', 'Lewis Hamilton'],
            gapSeconds: 0.3 + Math.random() * 0.5,
            riskLevel: 'high' as const,
            twoWide: true,
            threeWide: false,
            corner: 'Turn 3',
            lap: 18,
        },
        {
            id: 'battle-2',
            drivers: ['driver-004', 'driver-005', 'driver-006'],
            driverNames: ['Lando Norris', 'Carlos Sainz', 'George Russell'],
            gapSeconds: 0.8,
            riskLevel: 'medium' as const,
            twoWide: false,
            threeWide: true,
            corner: 'Turn 8',
            lap: 17,
        },
        {
            id: 'battle-3',
            drivers: ['driver-007', 'driver-008'],
            driverNames: ['Oscar Piastri', 'Sergio Perez'],
            gapSeconds: 1.2,
            riskLevel: 'low' as const,
            twoWide: false,
            threeWide: false,
            corner: null,
            lap: 18,
        },
    ];
}

// Generate mock incidents
export function generateMockIncidents() {
    const now = Date.now();
    return [
        {
            id: 'incident-1',
            timestamp: now - 120000,
            lap: 12,
            corner: 'Turn 1',
            drivers: [
                { driverId: 'driver-002', driverName: 'Lewis Hamilton' },
                { driverId: 'driver-003', driverName: 'Charles Leclerc' },
            ],
            type: 'contact',
            description: 'Contact between Hamilton and Leclerc in Turn 1',
            severity: 'moderate' as const,
        },
        {
            id: 'incident-2',
            timestamp: now - 300000,
            lap: 8,
            corner: 'Turn 5',
            drivers: [
                { driverId: 'driver-006', driverName: 'George Russell' },
            ],
            type: 'offtrack',
            description: 'Russell ran wide at Turn 5',
            severity: 'minor' as const,
        },
        {
            id: 'incident-3',
            timestamp: now - 60000,
            lap: 16,
            corner: 'Pit Entry',
            drivers: [
                { driverId: 'driver-008', driverName: 'Sergio Perez' },
                { driverId: 'driver-005', driverName: 'Carlos Sainz' },
            ],
            type: 'unsafe_rejoin',
            description: 'Perez unsafe pit exit in front of Sainz',
            severity: 'major' as const,
        },
    ];
}

// Generate mock driver stats
export function generateMockDriverStats(driverId: string) {
    return {
        paceModel: {
            currentPace: 81.234 + Math.random(),
            rollingAvgPace: 81.5,
            bestPace: 80.123,
            consistency: 0.92 + Math.random() * 0.08,
            trend: Math.random() > 0.5 ? 'improving' : 'stable',
        },
        gaps: {
            toLeader: 5.2 + Math.random() * 3,
            toBehind: 1.2 + Math.random(),
            toAhead: 0.8 + Math.random(),
            predictedOvertake: Math.random() > 0.5 ? {
                inLaps: Math.floor(Math.random() * 5) + 2,
                withPaceAdvantage: 0.2,
                confidence: 0.6 + Math.random() * 0.3,
            } : null,
        },
        tireModel: {
            compound: ['Soft', 'Medium', 'Hard'][Math.floor(Math.random() * 3)],
            lapsOnTires: Math.floor(Math.random() * 20) + 5,
            estimatedGripLoss: Math.random() * 0.1,
            degradationRate: 0.002 + Math.random() * 0.003,
        },
        fuelModel: {
            currentFuel: 30 + Math.random() * 40,
            consumptionPerLap: 2.1 + Math.random() * 0.3,
            estimatedLapsRemaining: 15 + Math.floor(Math.random() * 10),
            pitWindowLap: Math.random() > 0.3 ? 25 + Math.floor(Math.random() * 5) : null,
        },
    };
}

// Mock data state manager
class MockDataEngine {
    private enabled: boolean = false;
    private updateInterval: NodeJS.Timeout | null = null;
    private listeners: Set<(data: any) => void> = new Set();

    enable() {
        this.enabled = true;
        console.log('[MockData] Engine enabled');
        this.startUpdates();
    }

    disable() {
        this.enabled = false;
        console.log('[MockData] Engine disabled');
        this.stopUpdates();
    }

    toggle() {
        if (this.enabled) {
            this.disable();
        } else {
            this.enable();
        }
        return this.enabled;
    }

    isEnabled() {
        return this.enabled;
    }

    subscribe(callback: (data: any) => void) {
        this.listeners.add(callback);
        return () => this.listeners.delete(callback);
    }

    private startUpdates() {
        if (this.updateInterval) return;

        this.updateInterval = setInterval(() => {
            const data = this.generateFullSnapshot();
            this.listeners.forEach(cb => cb(data));
        }, 1000);

        // Send initial data
        const data = this.generateFullSnapshot();
        this.listeners.forEach(cb => cb(data));
    }

    private stopUpdates() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }

    generateFullSnapshot() {
        return {
            streams: MOCK_DRIVERS.map((d, i) => generateMockStream(d, i + 1)),
            telemetry: MOCK_DRIVERS.map((d, i) => generateMockTelemetry(d, i + 1)),
            battles: generateMockBattles(),
            incidents: generateMockIncidents(),
            sessionId: 'mock-session-001',
            timestamp: Date.now(),
        };
    }

    getStreams() {
        return MOCK_DRIVERS.map((d, i) => generateMockStream(d, i + 1));
    }

    getTelemetry() {
        return MOCK_DRIVERS.map((d, i) => generateMockTelemetry(d, i + 1));
    }

    getBattles() {
        return generateMockBattles();
    }

    getIncidents() {
        return generateMockIncidents();
    }

    getDriverStats(driverId: string) {
        return generateMockDriverStats(driverId);
    }
}

// Singleton instance
export const mockDataEngine = new MockDataEngine();
export default mockDataEngine;
