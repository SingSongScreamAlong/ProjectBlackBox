/**
 * BroadcastSyncPanel - Broadcast Companion Offset Calibration
 * 
 * Allows viewers to sync BroadcastBox telemetry with an external broadcast
 * (e.g., YouTube/Twitch stream) that has a delay.
 */

import React, { useState, useEffect, useCallback } from 'react';
import './BroadcastSyncPanel.css';

interface SyncEvent {
    type: 'green_flag' | 'yellow_flag' | 'incident' | 'pit_entry' | 'sector';
    timestamp: number;
    description: string;
}

interface BroadcastSyncPanelProps {
    sessionId: string;
    onOffsetChange: (offsetMs: number) => void;
    currentOffset?: number;
    recentEvents?: SyncEvent[];
}

const BroadcastSyncPanel: React.FC<BroadcastSyncPanelProps> = ({
    sessionId,
    onOffsetChange,
    currentOffset = 0,
    recentEvents = [],
}) => {
    const [offsetMs, setOffsetMs] = useState(currentOffset);
    const [isCalibrating, setIsCalibrating] = useState(false);
    const [savedOffsets, setSavedOffsets] = useState<Record<string, number>>({});
    const [lastSyncEvent, setLastSyncEvent] = useState<SyncEvent | null>(null);

    // Load saved offset from localStorage
    useEffect(() => {
        const saved = localStorage.getItem('broadcastOffsets');
        if (saved) {
            const offsets = JSON.parse(saved);
            setSavedOffsets(offsets);
            if (offsets[sessionId]) {
                setOffsetMs(offsets[sessionId]);
                onOffsetChange(offsets[sessionId]);
            }
        }
    }, [sessionId, onOffsetChange]);

    // Save offset to localStorage
    const saveOffset = useCallback(() => {
        const newOffsets = { ...savedOffsets, [sessionId]: offsetMs };
        localStorage.setItem('broadcastOffsets', JSON.stringify(newOffsets));
        setSavedOffsets(newOffsets);
    }, [sessionId, offsetMs, savedOffsets]);

    // Handle slider change
    const handleSliderChange = (value: number) => {
        setOffsetMs(value);
        onOffsetChange(value);
    };

    // Quick adjust buttons
    const quickAdjust = (delta: number) => {
        const newOffset = offsetMs + delta;
        setOffsetMs(newOffset);
        onOffsetChange(newOffset);
    };

    // Start calibration mode
    const startCalibration = () => {
        setIsCalibrating(true);
    };

    // Mark sync point (user sees event on external broadcast)
    const markSyncPoint = (event: SyncEvent) => {
        const now = Date.now();
        const eventTime = event.timestamp;
        const detectedOffset = now - eventTime;

        setOffsetMs(detectedOffset);
        onOffsetChange(detectedOffset);
        setLastSyncEvent(event);
        setIsCalibrating(false);
    };

    // Format offset for display
    const formatOffset = (ms: number): string => {
        const sign = ms >= 0 ? '+' : '-';
        const abs = Math.abs(ms);
        const seconds = (abs / 1000).toFixed(1);
        return `${sign}${seconds}s`;
    };

    return (
        <div className="broadcast-sync">
            <header className="broadcast-sync__header">
                <h3>📡 Broadcast Sync</h3>
                <span className="current-offset">{formatOffset(offsetMs)}</span>
            </header>

            <p className="broadcast-sync__description">
                Sync telemetry with an external broadcast (YouTube, Twitch, etc.)
            </p>

            {/* Offset Slider */}
            <div className="broadcast-sync__slider-container">
                <label>
                    Delay Offset
                    <span className="value">{formatOffset(offsetMs)}</span>
                </label>
                <input
                    type="range"
                    min="-60000"
                    max="120000"
                    step="100"
                    value={offsetMs}
                    onChange={(e) => handleSliderChange(Number(e.target.value))}
                    className="broadcast-sync__slider"
                />
                <div className="slider-labels">
                    <span>-60s</span>
                    <span>0</span>
                    <span>+60s</span>
                    <span>+120s</span>
                </div>
            </div>

            {/* Quick Adjust */}
            <div className="broadcast-sync__quick-adjust">
                <button onClick={() => quickAdjust(-5000)}>-5s</button>
                <button onClick={() => quickAdjust(-1000)}>-1s</button>
                <button onClick={() => quickAdjust(-100)}>-0.1s</button>
                <button onClick={() => quickAdjust(100)}>+0.1s</button>
                <button onClick={() => quickAdjust(1000)}>+1s</button>
                <button onClick={() => quickAdjust(5000)}>+5s</button>
            </div>

            {/* Calibration Mode */}
            {!isCalibrating ? (
                <button
                    className="broadcast-sync__calibrate-btn"
                    onClick={startCalibration}
                >
                    🎯 Auto-Calibrate
                </button>
            ) : (
                <div className="broadcast-sync__calibration">
                    <p>When you see one of these events on your broadcast, click it:</p>
                    <div className="event-buttons">
                        {recentEvents.length > 0 ? (
                            recentEvents.slice(-5).map((event, i) => (
                                <button
                                    key={i}
                                    className={`event-btn event-${event.type}`}
                                    onClick={() => markSyncPoint(event)}
                                >
                                    {event.type === 'green_flag' && '🟢'}
                                    {event.type === 'yellow_flag' && '🟡'}
                                    {event.type === 'incident' && '💥'}
                                    {event.type === 'pit_entry' && '🅿️'}
                                    {event.description}
                                </button>
                            ))
                        ) : (
                            <p className="no-events">Waiting for sync events...</p>
                        )}
                    </div>
                    <button
                        className="cancel-btn"
                        onClick={() => setIsCalibrating(false)}
                    >
                        Cancel
                    </button>
                </div>
            )}

            {/* Last Sync Info */}
            {lastSyncEvent && (
                <div className="broadcast-sync__last-sync">
                    <span className="label">Last synced to:</span>
                    <span className="event">{lastSyncEvent.description}</span>
                </div>
            )}

            {/* Actions */}
            <div className="broadcast-sync__actions">
                <button onClick={saveOffset} className="save-btn">
                    💾 Save Offset
                </button>
                <button onClick={() => { setOffsetMs(0); onOffsetChange(0); }} className="reset-btn">
                    Reset
                </button>
            </div>

            {/* Tips */}
            <div className="broadcast-sync__tips">
                <h4>Tips:</h4>
                <ul>
                    <li>Most Twitch streams have ~20-40s delay</li>
                    <li>YouTube Live typically has ~30-60s delay</li>
                    <li>Use flag changes for most accurate sync</li>
                </ul>
            </div>
        </div>
    );
};

export default BroadcastSyncPanel;
