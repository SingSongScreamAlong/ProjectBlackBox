/**
 * TelemetryOverlay - Live telemetry strip overlay on video
 */

import React, { useEffect, useState } from 'react';
import './TelemetryOverlay.css';

interface TelemetryData {
    speed: number;
    rpm: number;
    gear: number;
    throttle: number;
    brake: number;
    steering: number;
    lap: number;
    sector: number;
    lapTime: number;
    bestLapTime: number;
}

interface TelemetryOverlayProps {
    driverId: string;
    sessionId: string;
}

const TelemetryOverlay: React.FC<TelemetryOverlayProps> = ({ driverId, sessionId }) => {
    const [telemetry, setTelemetry] = useState<TelemetryData | null>(null);

    // Animated mock telemetry for visual testing
    useEffect(() => {
        let animationFrame: number;
        let startTime = Date.now();
        let lapStartTime = Date.now();
        let currentLap = 15;
        let currentSector = 1;

        const animate = () => {
            const elapsed = (Date.now() - startTime) / 1000;
            const lapElapsed = (Date.now() - lapStartTime) / 1000;

            // Simulate speed variations (braking zones, acceleration)
            const cyclePos = (elapsed % 8) / 8; // 8-second track cycle
            let speed: number;
            let throttle: number;
            let brake: number;
            let gear: number;

            if (cyclePos < 0.15) {
                // Braking zone
                speed = 280 - (cyclePos / 0.15) * 180;
                throttle = 0;
                brake = 0.9 - cyclePos * 3;
                gear = Math.max(2, 7 - Math.floor(cyclePos / 0.03));
            } else if (cyclePos < 0.25) {
                // Corner
                speed = 100 + (cyclePos - 0.15) * 300;
                throttle = 0.3 + (cyclePos - 0.15) * 4;
                brake = 0;
                gear = 3;
            } else if (cyclePos < 0.7) {
                // Acceleration
                const accelProgress = (cyclePos - 0.25) / 0.45;
                speed = 130 + accelProgress * 170;
                throttle = 0.95 + Math.sin(elapsed * 20) * 0.05; // Slight variation
                brake = 0;
                gear = Math.min(7, 3 + Math.floor(accelProgress * 5));
            } else {
                // High-speed section
                speed = 290 + Math.sin(elapsed * 3) * 15;
                throttle = 1;
                brake = 0;
                gear = 7;
            }

            // Steering based on cycle position
            let steering = Math.sin(elapsed * 2) * 0.3;
            if (cyclePos > 0.1 && cyclePos < 0.3) {
                steering = 0.4 + Math.sin(elapsed * 4) * 0.1; // Right turn
            } else if (cyclePos > 0.5 && cyclePos < 0.6) {
                steering = -0.35; // Left turn
            }

            // RPM based on gear and speed
            const rpm = 4000 + (speed / 300) * 8000 + Math.random() * 200;

            // Lap and sector timing
            if (lapElapsed > 82) { // ~82 second laps
                lapStartTime = Date.now();
                currentLap++;
                currentSector = 1;
            } else if (lapElapsed > 55 && currentSector < 3) {
                currentSector = 3;
            } else if (lapElapsed > 28 && currentSector < 2) {
                currentSector = 2;
            }

            setTelemetry({
                speed,
                rpm: Math.min(12500, rpm),
                gear,
                throttle,
                brake,
                steering,
                lap: currentLap,
                sector: currentSector,
                lapTime: lapElapsed,
                bestLapTime: 80.123,
            });

            animationFrame = requestAnimationFrame(animate);
        };

        animate();

        return () => {
            if (animationFrame) {
                cancelAnimationFrame(animationFrame);
            }
        };
    }, [driverId, sessionId]);

    if (!telemetry) return null;

    const formatTime = (seconds: number): string => {
        if (!seconds || seconds <= 0) return '--:--.---';
        const mins = Math.floor(seconds / 60);
        const secs = (seconds % 60).toFixed(3);
        return `${mins}:${secs.padStart(6, '0')}`;
    };

    return (
        <div className="telemetry-overlay">
            <div className="telemetry-overlay__row telemetry-overlay__row--top">
                <div className="telemetry-overlay__speed">
                    <span className="value">{Math.round(telemetry.speed)}</span>
                    <span className="unit">KPH</span>
                </div>
                <div className="telemetry-overlay__gear">
                    {telemetry.gear === 0 ? 'N' : telemetry.gear === -1 ? 'R' : telemetry.gear}
                </div>
                <div className="telemetry-overlay__rpm">
                    <div
                        className="telemetry-overlay__rpm-bar"
                        style={{ width: `${(telemetry.rpm / 8000) * 100}%` }}
                    />
                </div>
            </div>

            <div className="telemetry-overlay__row telemetry-overlay__row--bottom">
                <div className="telemetry-overlay__pedals">
                    <div className="telemetry-overlay__pedal telemetry-overlay__pedal--throttle">
                        <div
                            className="telemetry-overlay__pedal-bar"
                            style={{ height: `${telemetry.throttle * 100}%` }}
                        />
                        <span>T</span>
                    </div>
                    <div className="telemetry-overlay__pedal telemetry-overlay__pedal--brake">
                        <div
                            className="telemetry-overlay__pedal-bar"
                            style={{ height: `${telemetry.brake * 100}%` }}
                        />
                        <span>B</span>
                    </div>
                </div>

                <div className="telemetry-overlay__steering">
                    <div
                        className="telemetry-overlay__steering-indicator"
                        style={{
                            transform: `rotate(${telemetry.steering * 180}deg)`
                        }}
                    />
                </div>

                <div className="telemetry-overlay__times">
                    <div className="telemetry-overlay__lap">
                        LAP {telemetry.lap} | S{telemetry.sector}
                    </div>
                    <div className="telemetry-overlay__current-time">
                        {formatTime(telemetry.lapTime)}
                    </div>
                    <div className="telemetry-overlay__best-time">
                        PB: {formatTime(telemetry.bestLapTime)}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default TelemetryOverlay;
