"""
BroadcastBox WebRTC Streamer

Low-overhead WebRTC video streaming from the relay agent to viewers.
Uses aiortc for Python WebRTC implementation with hardware encoding support.

Note: This module requires aiortc and av packages:
  pip install aiortc av

For hardware encoding, ensure you have:
  - NVIDIA GPU with NVENC: NVIDIA drivers + ffmpeg with nvenc support
  - AMD GPU with AMF: AMD drivers + amf-encoder support
  - Intel GPU with QSV: Intel Media SDK
"""

import asyncio
import logging
import json
import time
import fractions
import os
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass

import config

logger = logging.getLogger(__name__)

# Try to import WebRTC dependencies
try:
    from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate
    from aiortc.contrib.media import MediaStreamTrack
    from av import VideoFrame
    import numpy as np
    WEBRTC_AVAILABLE = True
except ImportError as e:
    WEBRTC_AVAILABLE = False
    logger.warning(f"WebRTC dependencies not available: {e}")
    logger.warning("Install with: pip install aiortc av numpy")


@dataclass
class StreamConfig:
    """Configuration for the WebRTC stream"""
    enabled: bool = False
    fps: int = 60
    resolution: str = '720p'
    bitrate: int = 4000  # kbps
    codec: str = 'H264'
    stun_servers: list = None
    
    def __post_init__(self):
        if self.stun_servers is None:
            self.stun_servers = [
                'stun:stun.l.google.com:19302',
                'stun:stun1.l.google.com:19302',
            ]
    
    @property
    def width(self) -> int:
        return {'480p': 854, '720p': 1280, '1080p': 1920}.get(self.resolution, 1280)
    
    @property
    def height(self) -> int:
        return {'480p': 480, '720p': 720, '1080p': 1080}.get(self.resolution, 720)

    @classmethod
    def from_env(cls) -> 'StreamConfig':
        """Load configuration from environment variables"""
        return cls(
            enabled=os.getenv('STREAM_ENABLED', 'false').lower() == 'true',
            fps=int(os.getenv('STREAM_FPS', '60')),
            resolution=os.getenv('STREAM_RESOLUTION', '720p'),
            bitrate=int(os.getenv('STREAM_BITRATE', '4000')),
            codec=os.getenv('STREAM_CODEC', 'H264'),
        )


class VideoStreamTrack(MediaStreamTrack):
    """
    Custom video track that captures frames from the game window.
    Embeds timestamp metadata for sync with telemetry.
    """
    kind = "video"
    
    def __init__(self, config: StreamConfig, frame_source: Callable):
        super().__init__()
        self.config = config
        self.frame_source = frame_source  # Function that returns numpy array
        self.session_start = time.time()
        self._frame_count = 0
        self._timestamp = 0
        
    async def recv(self):
        """Receive the next video frame"""
        pts, time_base = await self.next_timestamp()
        
        # Get frame from source (game capture)
        frame_data = self.frame_source()
        
        if frame_data is None:
            # Return black frame if no data
            frame_data = np.zeros(
                (self.config.height, self.config.width, 3), 
                dtype=np.uint8
            )
        
        # Convert to VideoFrame
        frame = VideoFrame.from_ndarray(frame_data, format="bgr24")
        frame.pts = pts
        frame.time_base = time_base
        
        # Embed session timestamp for sync
        session_time_ms = int((time.time() - self.session_start) * 1000)
        # Note: Custom metadata would need to be handled separately
        # as VideoFrame doesn't support arbitrary metadata
        
        self._frame_count += 1
        
        return frame
    
    async def next_timestamp(self):
        """Generate next timestamp for frame"""
        if self.readyState != "live":
            raise Exception("Track ended")
        
        frame_duration = 1.0 / self.config.fps
        await asyncio.sleep(frame_duration)
        
        self._timestamp += int(90000 / self.config.fps)  # 90kHz clock
        return self._timestamp, fractions.Fraction(1, 90000)


class WebRTCStreamer:
    """
    Manages WebRTC peer connections for streaming video to viewers.
    Handles signaling via the ControlBox server.
    """
    
    def __init__(
        self, 
        config: StreamConfig,
        socket_client: Any,
        frame_source: Callable,
        driver_id: str,
        session_id: str,
    ):
        self.config = config
        self.socket = socket_client
        self.frame_source = frame_source
        self.driver_id = driver_id
        self.session_id = session_id
        
        self.stream_id = f"{session_id}_{driver_id}_{int(time.time())}"
        self.peer_connections: Dict[str, RTCPeerConnection] = {}
        self.running = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        
        # Hardware encoder detection
        self.hardware_encoder = self._detect_hardware_encoder()
        
        logger.info(f"[WebRTC] Initialized streamer for {driver_id}")
        logger.info(f"[WebRTC]   Stream ID: {self.stream_id}")
        logger.info(f"[WebRTC]   Resolution: {config.resolution} ({config.width}x{config.height})")
        logger.info(f"[WebRTC]   FPS: {config.fps}, Bitrate: {config.bitrate}kbps")
        logger.info(f"[WebRTC]   Hardware encoder: {self.hardware_encoder or 'SOFTWARE'}")
    
    def _detect_hardware_encoder(self) -> Optional[str]:
        """Detect available hardware encoder"""
        try:
            import subprocess
            
            # Check for NVENC (NVIDIA)
            result = subprocess.run(
                ['ffmpeg', '-hide_banner', '-encoders'],
                capture_output=True, text=True, timeout=5
            )
            if 'h264_nvenc' in result.stdout:
                return 'NVENC'
            if 'h264_amf' in result.stdout:
                return 'AMF'
            if 'h264_qsv' in result.stdout:
                return 'QSV'
        except Exception:
            pass
        
        return None
    
    def start(self):
        """Start the WebRTC streamer"""
        if not WEBRTC_AVAILABLE:
            logger.error("[WebRTC] Cannot start: aiortc not installed")
            return False
        
        if self.running:
            return True
        
        self.running = True
        
        # Set up signaling handlers
        self._setup_signaling()
        
        # Register stream with server
        self._register_stream()
        
        logger.info("[WebRTC] Streamer started")
        return True
    
    def stop(self):
        """Stop the WebRTC streamer"""
        self.running = False
        
        # Close all peer connections
        for peer_id, pc in self.peer_connections.items():
            asyncio.run_coroutine_threadsafe(
                pc.close(), 
                self._loop or asyncio.get_event_loop()
            )
        
        self.peer_connections.clear()
        
        # Deregister stream
        self._deregister_stream()
        
        logger.info("[WebRTC] Streamer stopped")
    
    def _register_stream(self):
        """Register stream with the ControlBox server"""
        registration = {
            'driverId': self.driver_id,
            'driverName': getattr(config, 'DRIVER_NAME', 'Unknown Driver'),
            'sessionId': self.session_id,
            'streamId': self.stream_id,
            'capabilities': {
                'video': True,
                'audio': False,  # Audio in Phase 2
                'resolution': self.config.resolution,
                'fps': self.config.fps,
                'codec': self.config.codec,
                'hardwareEncoder': self.hardware_encoder,
            },
            'accessLevel': 'public',  # TODO: Make configurable
        }
        
        self.socket.emit('stream_registration', registration)
        logger.info(f"[WebRTC] Registered stream: {self.stream_id}")
    
    def _deregister_stream(self):
        """Deregister stream from the server"""
        self.socket.emit('stream_deregistration', {
            'streamId': self.stream_id,
            'reason': 'user_stopped',
        })
        logger.info(f"[WebRTC] Deregistered stream: {self.stream_id}")
    
    def _setup_signaling(self):
        """Set up Socket.IO handlers for WebRTC signaling"""
        
        @self.socket.on('webrtc_offer')
        async def on_offer(data):
            """Handle incoming offer from a viewer"""
            if data.get('streamId') != self.stream_id:
                return
            
            viewer_id = data.get('fromPeer')
            sdp = data.get('sdp')
            
            logger.info(f"[WebRTC] Received offer from viewer: {viewer_id}")
            
            try:
                # Create peer connection for this viewer
                pc = await self._create_peer_connection(viewer_id)
                
                # Set remote description (the offer)
                await pc.setRemoteDescription(
                    RTCSessionDescription(sdp=sdp, type='offer')
                )
                
                # Create and set local description (the answer)
                answer = await pc.createAnswer()
                await pc.setLocalDescription(answer)
                
                # Send answer back
                self.socket.emit('webrtc_answer', {
                    'streamId': self.stream_id,
                    'sdp': pc.localDescription.sdp,
                    'fromPeer': self.stream_id,
                    'toPeer': viewer_id,
                })
                
                logger.info(f"[WebRTC] Sent answer to viewer: {viewer_id}")
                
            except Exception as e:
                logger.error(f"[WebRTC] Error handling offer: {e}")
        
        @self.socket.on('webrtc_ice_candidate')
        async def on_ice_candidate(data):
            """Handle incoming ICE candidate"""
            if data.get('streamId') != self.stream_id:
                return
            
            viewer_id = data.get('fromPeer')
            candidate_data = data.get('candidate')
            
            if viewer_id in self.peer_connections and candidate_data:
                try:
                    candidate = RTCIceCandidate(
                        sdpMid=candidate_data.get('sdpMid'),
                        sdpMLineIndex=candidate_data.get('sdpMLineIndex'),
                        candidate=candidate_data.get('candidate'),
                    )
                    await self.peer_connections[viewer_id].addIceCandidate(candidate)
                except Exception as e:
                    logger.error(f"[WebRTC] Error adding ICE candidate: {e}")
    
    async def _create_peer_connection(self, viewer_id: str) -> RTCPeerConnection:
        """Create a new peer connection for a viewer"""
        
        # ICE servers configuration
        ice_servers = [
            {'urls': server} for server in self.config.stun_servers
        ]
        
        pc = RTCPeerConnection(configuration={'iceServers': ice_servers})
        
        # Track ICE connection state changes
        @pc.on('iceconnectionstatechange')
        async def on_ice_state_change():
            logger.info(f"[WebRTC] ICE state ({viewer_id}): {pc.iceConnectionState}")
            if pc.iceConnectionState == 'failed':
                await pc.close()
                self.peer_connections.pop(viewer_id, None)
        
        # Send ICE candidates to viewer
        @pc.on('icecandidate')
        async def on_ice_candidate(candidate):
            if candidate:
                self.socket.emit('webrtc_ice_candidate', {
                    'streamId': self.stream_id,
                    'candidate': {
                        'sdpMid': candidate.sdpMid,
                        'sdpMLineIndex': candidate.sdpMLineIndex,
                        'candidate': candidate.candidate,
                    },
                    'fromPeer': self.stream_id,
                    'toPeer': viewer_id,
                })
        
        # Add video track
        video_track = VideoStreamTrack(self.config, self.frame_source)
        pc.addTrack(video_track)
        
        self.peer_connections[viewer_id] = pc
        return pc
    
    def send_health_update(self, metrics: Dict[str, Any]):
        """Send stream health update to server"""
        self.socket.emit('stream_health', {
            'streamId': self.stream_id,
            'metrics': metrics,
            'warnings': [],
        })


# Factory function for creating streamer
def create_webrtc_streamer(
    socket_client: Any,
    frame_source: Callable,
    driver_id: str,
    session_id: str,
) -> Optional[WebRTCStreamer]:
    """
    Create a WebRTC streamer if enabled and dependencies available.
    
    Args:
        socket_client: Socket.IO client connected to ControlBox server
        frame_source: Callable that returns numpy array of current frame
        driver_id: Unique identifier for the driver
        session_id: Current session ID
    
    Returns:
        WebRTCStreamer instance or None if disabled/unavailable
    """
    stream_config = StreamConfig.from_env()
    
    if not stream_config.enabled:
        logger.info("[WebRTC] Streaming disabled (STREAM_ENABLED != 'true')")
        return None
    
    if not WEBRTC_AVAILABLE:
        logger.warning("[WebRTC] Cannot create streamer: aiortc not installed")
        return None
    
    return WebRTCStreamer(
        config=stream_config,
        socket_client=socket_client,
        frame_source=frame_source,
        driver_id=driver_id,
        session_id=session_id,
    )
