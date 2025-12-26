/**
 * StreamPlayer - WebRTC video player component
 * 
 * Uses the useWebRTCStream hook for actual WebRTC playback.
 */

import React, { useEffect, useState } from 'react';
import useWebRTCStream from '../../hooks/useWebRTCStream';
import './StreamPlayer.css';

interface StreamPlayerProps {
    streamId: string;
    quality?: 'auto' | 'low' | 'med' | 'high';
    muted?: boolean;
    socket?: any; // Socket.IO instance (optional for demo mode)
}

const StreamPlayer: React.FC<StreamPlayerProps> = ({
    streamId,
    quality = 'auto',
    muted = true,
    socket = null,
}) => {
    // Use the WebRTC hook for actual streaming
    const {
        videoRef,
        status,
        stats,
        connect,
        disconnect,
        error
    } = useWebRTCStream({
        streamId,
        socket,
        autoConnect: !!socket, // Only auto-connect if socket is provided
    });

    // Demo mode fallback when no socket is available
    const [demoMode, setDemoMode] = useState(!socket);

    useEffect(() => {
        setDemoMode(!socket);
    }, [socket]);

    // Display status combines real status with demo fallback
    const displayStatus = demoMode ? 'failed' : status;

    // Handle retry
    const handleRetry = () => {
        if (socket) {
            disconnect();
            connect();
        } else {
            window.location.reload();
        }
    };

    return (
        <div className="stream-player">
            <video
                ref={videoRef}
                autoPlay
                playsInline
                muted={muted}
                className="stream-player__video"
            />

            <div className="stream-player__overlay">
                {displayStatus === 'connecting' && (
                    <div className="stream-player__connecting">
                        <div className="stream-player__spinner" />
                        <span>Connecting to stream...</span>
                    </div>
                )}

                {displayStatus === 'failed' && (
                    <div className="stream-player__failed">
                        {demoMode ? (
                            <>
                                <span>📺 Demo Mode</span>
                                <p>WebRTC stream not available. Enable streaming in the relay agent with STREAM_ENABLED=true</p>
                            </>
                        ) : (
                            <>
                                <span>⚠️ Stream unavailable</span>
                                {error && <p>{error}</p>}
                                <button onClick={handleRetry}>Retry</button>
                            </>
                        )}
                    </div>
                )}
            </div>

            <div className="stream-player__controls">
                <span className="stream-player__live-badge">
                    {displayStatus === 'connected' ? '● LIVE' :
                        displayStatus === 'connecting' ? '○ CONNECTING' :
                            demoMode ? '⊘ DEMO' : '✕ OFFLINE'}
                </span>
                {stats && displayStatus === 'connected' && (
                    <span className="stream-player__stats">
                        {stats.fps}fps | {Math.round(stats.rtt || 0)}ms RTT
                    </span>
                )}
                <span className="stream-player__quality">{quality.toUpperCase()}</span>
            </div>
        </div>
    );
};

export default StreamPlayer;
