"""
PitBox Relay Agent - Server Client
Socket.IO client for connecting to PitBox Server
"""
import base64
import logging
import time
from typing import Callable, Optional, Dict, Any
import socketio

import config

logger = logging.getLogger(__name__)


class PitBoxClient:
    """
    Socket.IO client for communicating with PitBox Server
    """
    
    def __init__(self, url: str = None):
        self.url = url or config.CLOUD_URL
        self.sio = socketio.Client(
            reconnection=True,
            reconnection_attempts=10,
            reconnection_delay=1,
            reconnection_delay_max=30,
            logger=False,
            engineio_logger=False
        )
        self.connected = False
        self.session_id: Optional[str] = None
        
        # Voice callbacks
        self.on_voice_response: Optional[Callable[[bytes], None]] = None  # TTS audio
        self.on_engineer_text: Optional[Callable[[str], None]] = None     # Response text
        
        # Set up event handlers
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up Socket.IO event handlers"""
        
        @self.sio.event
        def connect():
            self.connected = True
            logger.info(f"✅ Connected to PitBox Server at {self.url}")
        
        @self.sio.event
        def disconnect():
            self.connected = False
            logger.warning("⚠️ Disconnected from PitBox Server")
        
        @self.sio.event
        def connect_error(error):
            logger.error(f"❌ Connection error: {error}")
        
        @self.sio.on('recommendation')
        def on_recommendation(data):
            logger.info(f"📥 RECOMMENDATION: {data.get('action')} - {data.get('details')}")
            logger.info(f"   Confidence: {data.get('confidence', 0) * 100:.0f}%")
        
        @self.sio.on('profile_loaded')
        def on_profile_loaded(data):
            logger.info(f"📖 Profile loaded: {data.get('profileName')} [{data.get('category')}]")
        
        @self.sio.on('ack')
        def on_ack(data):
            logger.debug(f"   ✓ {data.get('originalType')} acknowledged")
        
        @self.sio.on('steward_command')
        def on_steward_command(data):
            logger.info(f"⚡ STEWARD COMMAND: {data.get('command')}")
            logger.info(f"   Reason: {data.get('reason')}")
            # TODO: Implement command execution in iRacing
        
        @self.sio.on('voice_response')
        def on_voice_response(data):
            """Receive TTS audio response from server"""
            logger.info("🔊 Received voice response from engineer")
            audio_b64 = data.get('audio')
            text = data.get('text', '')
            
            if audio_b64 and self.on_voice_response:
                try:
                    audio_bytes = base64.b64decode(audio_b64)
                    self.on_voice_response(audio_bytes)
                except Exception as e:
                    logger.error(f"Failed to decode audio: {e}")
            
            if text and self.on_engineer_text:
                self.on_engineer_text(text)
        
        @self.sio.on('engineer_text')
        def on_engineer_text(data):
            """Receive text-only response from engineer"""
            text = data.get('text', '')
            logger.info(f"💬 Engineer: {text}")
            if text and self.on_engineer_text:
                self.on_engineer_text(text)
    
    def connect(self) -> bool:
        """
        Connect to PitBox Cloud
        Returns True if connected successfully
        """
        if self.connected:
            return True
        
        try:
            print(f"🔌 Connecting to: {self.url}")
            logger.info(f"🔌 Connecting to PitBox Server at {self.url}...")
            self.sio.connect(
                self.url,
                wait=True,
                wait_timeout=15
            )
            print(f"✅ Connected: {self.connected}")
            return self.connected
        except Exception as e:
            print(f"❌ Connection FAILED: {e}")
            logger.error(f"Failed to connect: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from PitBox Cloud"""
        if self.sio.connected:
            self.sio.disconnect()
        self.connected = False
        logger.info("🔌 Disconnected from PitBox Server")
    
    def is_connected(self) -> bool:
        """Check if connected"""
        return self.connected and self.sio.connected
    
    def emit(self, event: str, data: Dict[str, Any]):
        """
        Emit an event to PitBox Cloud
        """
        if not self.is_connected():
            logger.warning(f"Cannot emit {event}: not connected")
            return False
        
        try:
            self.sio.emit(event, data)
            logger.debug(f"📤 Sent {event}")
            return True
        except Exception as e:
            logger.error(f"Failed to emit {event}: {e}")
            return False
    
    def send_session_metadata(self, metadata: Dict[str, Any]):
        """Send session metadata message"""
        self.session_id = metadata.get('sessionId')
        return self.emit('session_metadata', metadata)
    
    def send_telemetry(self, telemetry: Dict[str, Any]):
        """Send telemetry snapshot"""
        return self.emit('telemetry', telemetry)
    
    def send_race_event(self, event: Dict[str, Any]):
        """Send race event (flag change, etc.)"""
        return self.emit('race_event', event)
    
    def send_incident(self, incident: Dict[str, Any]):
        """Send incident report"""
        return self.emit('incident', incident)
    
    def send_driver_update(self, update: Dict[str, Any]):
        """Send driver join/leave update"""
        return self.emit('driver_update', update)
    
    def send_video_frame(self, frame_data: str):
        """
        Send base64 encoded video frame
        Optimize: fire and forget, don't wait for ack to keep latency low
        """
        # We use a specific event for video that the server expects
        if self.connected and self.session_id:
            payload = {
                'sessionId': self.session_id,
                'image': frame_data
            }
            self.sio.emit('video_frame', payload)
            return True
        return False

    def wait(self, seconds: float = 0.1):
        """
        Wait while processing events
        Use this in the main loop to allow receiving events
        """
        self.sio.sleep(seconds)
    
    def send_voice_command(self, audio_data: bytes, context: Optional[Dict[str, Any]] = None):
        """
        Send voice command audio to server for transcription and AI response
        
        Args:
            audio_data: WAV audio bytes
            context: Optional race context (lap, position, etc.)
        """
        if not self.is_connected():
            logger.warning("Cannot send voice command: not connected")
            return False
        
        try:
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')
            payload = {
                'sessionId': self.session_id,
                'audio': audio_b64,
                'format': 'wav',
                'context': context or {}
            }
            self.sio.emit('voice_command', payload)
            logger.info("🎤 Voice command sent to server")
            return True
        except Exception as e:
            logger.error(f"Failed to send voice command: {e}")
            return False
