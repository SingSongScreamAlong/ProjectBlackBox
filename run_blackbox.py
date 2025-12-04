"""
Main Integration Script
Connects all components: iRacing, telemetry, database, API, voice
"""

import asyncio
import logging
import os
import sys
from typing import Optional
import signal

# Add paths
sys.path.append('./relay_agent')
sys.path.append('./database')
sys.path.append('./api')

from iracing_sdk_wrapper import iRacingSDKWrapper
from telemetry_streamer import TelemetryStreamer, SessionMonitor
from audio_pipeline import AudioPipeline
from database.manager import DatabaseManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProjectBlackBox:
    """
    Main integration class
    Connects all components and manages the complete system
    """
    
    def __init__(self):
        # Configuration
        self.database_url = os.getenv('DATABASE_URL', 'postgresql://blackbox:blackbox@localhost:5432/blackbox')
        self.api_url = os.getenv('API_URL', 'http://localhost:8000')
        self.ws_url = os.getenv('WS_URL', 'ws://localhost:8000/ws/telemetry')
        
        # API keys
        self.openai_key = os.getenv('OPENAI_API_KEY')
        self.elevenlabs_key = os.getenv('ELEVENLABS_API_KEY')
        
        # Components
        self.sdk: Optional[iRacingSDKWrapper] = None
        self.streamer: Optional[TelemetryStreamer] = None
        self.monitor: Optional[SessionMonitor] = None
        self.audio: Optional[AudioPipeline] = None
        self.db: Optional[DatabaseManager] = None
        
        self.running = False
        self.current_session_id = None
    
    async def initialize(self):
        """Initialize all components"""
        logger.info("=" * 70)
        logger.info("🏁 ProjectBlackBox - Complete Digital Race Team")
        logger.info("=" * 70)
        
        # Initialize database
        logger.info("📊 Connecting to database...")
        self.db = DatabaseManager(self.database_url)
        self.db.create_tables()
        logger.info("✅ Database connected")
        
        # Initialize iRacing SDK
        logger.info("🎮 Connecting to iRacing...")
        self.sdk = iRacingSDKWrapper()
        
        if not self.sdk.connect(timeout=30):
            logger.error("❌ Failed to connect to iRacing")
            logger.error("Make sure iRacing is running and you're in a session")
            return False
        
        logger.info("✅ iRacing connected")
        
        # Initialize telemetry streamer
        session_info = self.sdk.get_session_info()
        if session_info:
            # Create session in database
            self.current_session_id = self.db.create_session({
                'driver_id': session_info.driver_id,
                'session_type': session_info.session_type,
                'track_name': session_info.track_name,
                'car_name': session_info.car_name,
                'track_temp': 25.0,  # Would get from session_info
                'air_temp': 20.0
            })
            logger.info(f"✅ Session created: {self.current_session_id}")
        
        # Create streamer
        ws_url = f"{self.ws_url}/{self.current_session_id}"
        self.streamer = TelemetryStreamer(self.sdk, ws_url)
        
        # Create session monitor
        self.monitor = SessionMonitor(self.sdk)
        self.monitor.register_callback('lap_complete', self.on_lap_complete)
        
        # Initialize audio pipeline (if API keys available)
        if self.openai_key and self.elevenlabs_key:
            logger.info("🎙️ Initializing voice interface...")
            self.audio = AudioPipeline(self.openai_key, self.elevenlabs_key)
            await self.audio.start()
            logger.info("✅ Voice interface ready")
        else:
            logger.warning("⚠️ Voice interface disabled (API keys not set)")
        
        logger.info("=" * 70)
        logger.info("✅ ProjectBlackBox ready!")
        logger.info("=" * 70)
        
        return True
    
    async def on_lap_complete(self, data: dict):
        """Called when lap is completed"""
        lap_number = data['lap']
        logger.info(f"🏁 Lap {lap_number} complete!")
        
        # Get lap telemetry
        lap_telemetry = self.streamer.get_buffered_telemetry(lap=lap_number)
        
        if lap_telemetry:
            # Calculate lap time (simplified)
            lap_time = lap_telemetry[-1].session_time - lap_telemetry[0].session_time
            
            # Store lap in database
            self.db.create_lap({
                'session_id': self.current_session_id,
                'lap_number': lap_number,
                'lap_time': lap_time,
                'is_valid': True
            })
            
            logger.info(f"✅ Lap {lap_number} stored: {lap_time:.3f}s")
            
            # Run analysis (corner-by-corner, incidents, etc.)
            # TODO: Integrate analysis systems
            
            # Voice update
            if self.audio:
                await self.audio.send_proactive_update(
                    f"Lap {lap_number} complete. Time: {lap_time:.1f} seconds.",
                    'engineer'
                )
    
    async def run(self):
        """Main run loop"""
        self.running = True
        
        # Start telemetry streaming
        asyncio.create_task(self.streamer.stream_loop(hz=60))
        
        # Start session monitoring
        asyncio.create_task(self.monitor.monitor_loop())
        
        # Main loop
        try:
            while self.running and self.sdk.is_connected():
                # Update audio pipeline context
                if self.audio:
                    telemetry = self.sdk.get_telemetry()
                    if telemetry:
                        self.audio.update_context({
                            'current_lap': telemetry.lap,
                            'position': 5,  # Would get from positions
                            'tire_age': telemetry.lap,
                            'fuel_remaining': telemetry.fuel_level
                        })
                
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Shutdown all components"""
        logger.info("Shutting down ProjectBlackBox...")
        
        self.running = False
        
        # Stop streaming
        if self.streamer:
            self.streamer.stop_streaming()
        
        # Stop audio
        if self.audio:
            await self.audio.stop()
        
        # End session in database
        if self.current_session_id:
            self.db.end_session(self.current_session_id)
        
        # Disconnect from iRacing
        if self.sdk:
            self.sdk.disconnect()
        
        logger.info("✅ Shutdown complete")


async def main():
    """Main entry point"""
    # Create and initialize
    blackbox = ProjectBlackBox()
    
    if not await blackbox.initialize():
        logger.error("Failed to initialize ProjectBlackBox")
        return
    
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal")
        blackbox.running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Run
    await blackbox.run()


if __name__ == '__main__':
    asyncio.run(main())
