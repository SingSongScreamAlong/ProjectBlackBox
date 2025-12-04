"""
Telemetry Streamer
Streams telemetry from iRacing to backend via WebSocket
Buffers data for analysis
"""

import asyncio
import websockets
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
from collections import deque
from dataclasses import asdict

from .iracing_sdk_wrapper import iRacingSDKWrapper, TelemetrySnapshot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TelemetryStreamer:
    """
    Stream telemetry to backend at 60Hz
    Buffer for local analysis
    """
    
    def __init__(self, 
                 sdk: iRacingSDKWrapper,
                 websocket_url: str,
                 buffer_size: int = 3600):  # 60 seconds at 60Hz
        self.sdk = sdk
        self.websocket_url = websocket_url
        self.buffer = deque(maxlen=buffer_size)
        self.websocket = None
        self.streaming = False
        
        # Statistics
        self.samples_sent = 0
        self.samples_buffered = 0
        self.connection_errors = 0
        
    async def connect_websocket(self):
        """Connect to backend WebSocket"""
        try:
            self.websocket = await websockets.connect(self.websocket_url)
            logger.info(f"✅ Connected to WebSocket: {self.websocket_url}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to WebSocket: {e}")
            self.connection_errors += 1
            return False
    
    async def disconnect_websocket(self):
        """Disconnect from WebSocket"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            logger.info("Disconnected from WebSocket")
    
    async def send_telemetry(self, telemetry: TelemetrySnapshot):
        """Send telemetry to backend"""
        if not self.websocket:
            return False
        
        try:
            # Convert to dict
            data = asdict(telemetry)
            
            # Send as JSON
            await self.websocket.send(json.dumps(data))
            self.samples_sent += 1
            return True
            
        except Exception as e:
            logger.error(f"Error sending telemetry: {e}")
            self.connection_errors += 1
            return False
    
    def buffer_telemetry(self, telemetry: TelemetrySnapshot):
        """Buffer telemetry for local analysis"""
        self.buffer.append(telemetry)
        self.samples_buffered += 1
    
    def get_buffered_telemetry(self, 
                               lap: Optional[int] = None,
                               last_n: Optional[int] = None) -> List[TelemetrySnapshot]:
        """
        Get buffered telemetry
        
        Args:
            lap: Get telemetry for specific lap
            last_n: Get last N samples
            
        Returns:
            List of telemetry snapshots
        """
        if last_n:
            return list(self.buffer)[-last_n:]
        
        if lap is not None:
            return [t for t in self.buffer if t.lap == lap]
        
        return list(self.buffer)
    
    def clear_buffer(self):
        """Clear telemetry buffer"""
        self.buffer.clear()
        logger.info("Telemetry buffer cleared")
    
    async def stream_loop(self, hz: int = 60):
        """
        Main streaming loop
        
        Args:
            hz: Streaming frequency (default 60Hz)
        """
        interval = 1.0 / hz
        logger.info(f"Starting telemetry stream at {hz}Hz")
        self.streaming = True
        
        # Connect to WebSocket
        await self.connect_websocket()
        
        while self.streaming and self.sdk.is_connected():
            start = time.time()
            
            # Get telemetry from iRacing
            telemetry = self.sdk.get_telemetry()
            
            if telemetry:
                # Buffer locally
                self.buffer_telemetry(telemetry)
                
                # Send to backend
                if self.websocket:
                    await self.send_telemetry(telemetry)
            
            # Maintain frequency
            elapsed = time.time() - start
            sleep_time = max(0, interval - elapsed)
            await asyncio.sleep(sleep_time)
        
        # Disconnect
        await self.disconnect_websocket()
        logger.info("Telemetry stream stopped")
    
    def start_streaming(self, hz: int = 60):
        """Start streaming in background task"""
        asyncio.create_task(self.stream_loop(hz))
    
    def stop_streaming(self):
        """Stop streaming"""
        self.streaming = False
    
    def get_statistics(self) -> Dict:
        """Get streaming statistics"""
        return {
            'samples_sent': self.samples_sent,
            'samples_buffered': self.samples_buffered,
            'buffer_size': len(self.buffer),
            'connection_errors': self.connection_errors,
            'streaming': self.streaming
        }


class SessionMonitor:
    """
    Monitor session state and trigger events
    """
    
    def __init__(self, sdk: iRacingSDKWrapper):
        self.sdk = sdk
        self.current_session = None
        self.current_lap = 0
        self.in_pit = False
        
        # Event callbacks
        self.on_session_start = []
        self.on_session_end = []
        self.on_lap_complete = []
        self.on_incident = []
        self.on_pit_entry = []
        self.on_pit_exit = []
    
    def register_callback(self, event: str, callback):
        """Register event callback"""
        if event == 'session_start':
            self.on_session_start.append(callback)
        elif event == 'session_end':
            self.on_session_end.append(callback)
        elif event == 'lap_complete':
            self.on_lap_complete.append(callback)
        elif event == 'incident':
            self.on_incident.append(callback)
        elif event == 'pit_entry':
            self.on_pit_entry.append(callback)
        elif event == 'pit_exit':
            self.on_pit_exit.append(callback)
    
    async def monitor_loop(self):
        """Main monitoring loop"""
        logger.info("Starting session monitor")
        
        while self.sdk.is_connected():
            # Get current session info
            session = self.sdk.get_session_info()
            
            if session and session != self.current_session:
                # Session changed
                if self.current_session:
                    await self._trigger_event('session_end', self.current_session)
                
                self.current_session = session
                await self._trigger_event('session_start', session)
            
            # Get current telemetry
            telemetry = self.sdk.get_telemetry()
            
            if telemetry:
                # Check for lap change
                if telemetry.lap != self.current_lap and self.current_lap > 0:
                    await self._trigger_event('lap_complete', {
                        'lap': self.current_lap,
                        'session': self.current_session
                    })
                self.current_lap = telemetry.lap
                
                # Check for pit entry/exit
                # Simplified - would check actual pit road status
                
                # Check for incidents
                # Would analyze telemetry for sudden speed loss, high G-forces, etc.
            
            await asyncio.sleep(0.1)  # 10Hz monitoring
        
        logger.info("Session monitor stopped")
    
    async def _trigger_event(self, event: str, data):
        """Trigger event callbacks"""
        callbacks = getattr(self, f'on_{event}', [])
        
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)
            except Exception as e:
                logger.error(f"Error in {event} callback: {e}")


# Example usage
if __name__ == '__main__':
    import time
    
    async def main():
        # Create SDK and streamer
        sdk = iRacingSDKWrapper()
        
        if not sdk.connect():
            print("Failed to connect to iRacing")
            return
        
        # Create streamer
        streamer = TelemetryStreamer(
            sdk=sdk,
            websocket_url="ws://localhost:8000/ws/telemetry/test-session"
        )
        
        # Create session monitor
        monitor = SessionMonitor(sdk)
        
        # Register callbacks
        def on_lap_complete(data):
            print(f"✅ Lap {data['lap']} complete!")
            
            # Get lap telemetry
            lap_data = streamer.get_buffered_telemetry(lap=data['lap'])
            print(f"   Captured {len(lap_data)} telemetry samples")
        
        monitor.register_callback('lap_complete', on_lap_complete)
        
        # Start streaming and monitoring
        asyncio.create_task(streamer.stream_loop(hz=60))
        asyncio.create_task(monitor.monitor_loop())
        
        # Run for 60 seconds
        await asyncio.sleep(60)
        
        # Stop
        streamer.stop_streaming()
        
        # Print statistics
        stats = streamer.get_statistics()
        print(f"\nStatistics:")
        print(f"  Samples sent: {stats['samples_sent']}")
        print(f"  Samples buffered: {stats['samples_buffered']}")
        print(f"  Connection errors: {stats['connection_errors']}")
        
        sdk.disconnect()
    
    asyncio.run(main())
