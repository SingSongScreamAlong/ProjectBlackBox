/**
 * useWebRTCStream - React hook for WebRTC stream playback
 * 
 * Manages the WebRTC peer connection lifecycle for viewing a driver stream.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { Socket } from 'socket.io-client';

interface UseWebRTCStreamOptions {
    streamId: string;
    socket: Socket | null;
    autoConnect?: boolean;
}

interface WebRTCStats {
    fps: number;
    bitrate: number;
    packetsLost: number;
    jitter: number;
    rtt: number;
}

interface UseWebRTCStreamReturn {
    videoRef: React.RefObject<HTMLVideoElement | null>;
    status: 'idle' | 'connecting' | 'connected' | 'failed';
    stats: WebRTCStats | null;
    connect: () => Promise<void>;
    disconnect: () => void;
    error: string | null;
}

const ICE_SERVERS = [
    { urls: 'stun:stun.l.google.com:19302' },
    { urls: 'stun:stun1.l.google.com:19302' },
];

export function useWebRTCStream({
    streamId,
    socket,
    autoConnect = true,
}: UseWebRTCStreamOptions): UseWebRTCStreamReturn {
    const videoRef = useRef<HTMLVideoElement>(null);
    const pcRef = useRef<RTCPeerConnection | null>(null);
    const [status, setStatus] = useState<'idle' | 'connecting' | 'connected' | 'failed'>('idle');
    const [stats, setStats] = useState<WebRTCStats | null>(null);
    const [error, setError] = useState<string | null>(null);

    // Generate unique viewer ID
    const viewerIdRef = useRef<string>(`viewer-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`);

    const connect = useCallback(async () => {
        if (!socket || !streamId) {
            setError('Socket or stream ID not available');
            return;
        }

        if (pcRef.current) {
            // Already connected
            return;
        }

        setStatus('connecting');
        setError(null);

        try {
            // Create peer connection
            const pc = new RTCPeerConnection({ iceServers: ICE_SERVERS });
            pcRef.current = pc;

            // Handle incoming video track
            pc.ontrack = (event) => {
                console.log('[WebRTC] Received track:', event.track.kind);
                if (videoRef.current && event.streams[0]) {
                    videoRef.current.srcObject = event.streams[0];
                    setStatus('connected');
                }
            };

            // Handle ICE connection state
            pc.oniceconnectionstatechange = () => {
                console.log('[WebRTC] ICE state:', pc.iceConnectionState);
                switch (pc.iceConnectionState) {
                    case 'connected':
                        setStatus('connected');
                        break;
                    case 'failed':
                    case 'disconnected':
                        setStatus('failed');
                        setError('Connection lost');
                        break;
                }
            };

            // Handle ICE candidates
            pc.onicecandidate = (event) => {
                if (event.candidate) {
                    socket.emit('webrtc_ice_candidate', {
                        streamId,
                        candidate: {
                            sdpMid: event.candidate.sdpMid,
                            sdpMLineIndex: event.candidate.sdpMLineIndex,
                            candidate: event.candidate.candidate,
                        },
                        fromPeer: viewerIdRef.current,
                    });
                }
            };

            // Set up socket handlers for signaling
            const handleAnswer = (data: { streamId: string; sdp: string; toPeer: string }) => {
                if (data.streamId === streamId && data.toPeer === viewerIdRef.current) {
                    console.log('[WebRTC] Received answer');
                    pc.setRemoteDescription({ type: 'answer', sdp: data.sdp });
                }
            };

            const handleIceCandidate = (data: { streamId: string; candidate: any; toPeer?: string }) => {
                if (data.streamId === streamId && (!data.toPeer || data.toPeer === viewerIdRef.current)) {
                    console.log('[WebRTC] Received ICE candidate');
                    pc.addIceCandidate(new RTCIceCandidate(data.candidate));
                }
            };

            socket.on('webrtc_answer', handleAnswer);
            socket.on('webrtc_ice_candidate', handleIceCandidate);

            // Join stream room
            socket.emit('join_stream', streamId);

            // Create offer (for receiving video)
            // Add transceiver for receiving video
            pc.addTransceiver('video', { direction: 'recvonly' });

            const offer = await pc.createOffer();
            await pc.setLocalDescription(offer);

            // Send offer to stream publisher
            socket.emit('webrtc_offer', {
                streamId,
                sdp: offer.sdp,
                fromPeer: viewerIdRef.current,
            });

            console.log('[WebRTC] Sent offer for stream:', streamId);

        } catch (err) {
            console.error('[WebRTC] Connection error:', err);
            setStatus('failed');
            setError(err instanceof Error ? err.message : 'Unknown error');
        }
    }, [socket, streamId]);

    const disconnect = useCallback(() => {
        if (pcRef.current) {
            pcRef.current.close();
            pcRef.current = null;
        }

        if (videoRef.current) {
            videoRef.current.srcObject = null;
        }

        if (socket && streamId) {
            socket.emit('leave_stream', streamId);
        }

        setStatus('idle');
        setStats(null);
    }, [socket, streamId]);

    // Collect stats periodically
    useEffect(() => {
        if (status !== 'connected' || !pcRef.current) {
            return;
        }

        const interval = setInterval(async () => {
            if (!pcRef.current) return;

            try {
                const report = await pcRef.current.getStats();
                let statsData: Partial<WebRTCStats> = {
                    fps: 0,
                    bitrate: 0,
                    packetsLost: 0,
                    jitter: 0,
                    rtt: 0,
                };

                report.forEach((stat) => {
                    if (stat.type === 'inbound-rtp' && stat.kind === 'video') {
                        statsData.fps = stat.framesPerSecond || 0;
                        statsData.packetsLost = stat.packetsLost || 0;
                        statsData.jitter = stat.jitter || 0;
                    }
                    if (stat.type === 'candidate-pair' && stat.state === 'succeeded') {
                        statsData.rtt = stat.currentRoundTripTime ? stat.currentRoundTripTime * 1000 : 0;
                    }
                });

                setStats(statsData as WebRTCStats);
            } catch (err) {
                console.warn('[WebRTC] Error getting stats:', err);
            }
        }, 1000);

        return () => clearInterval(interval);
    }, [status]);

    // Auto-connect on mount if enabled
    useEffect(() => {
        if (autoConnect && socket && streamId) {
            connect();
        }

        return () => {
            disconnect();
        };
    }, [autoConnect, socket, streamId, connect, disconnect]);

    return {
        videoRef,
        status,
        stats,
        connect,
        disconnect,
        error,
    };
}

export default useWebRTCStream;
