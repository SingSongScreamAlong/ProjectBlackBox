#!/usr/bin/env python3
"""
BlackBox Relay Agent - Telemetry Collector Module

This module handles the collection of telemetry data from iRacing using pyirsdk,
and transmits it to the BlackBox backend server.
"""

import os
import sys
import time
import json
import logging
import threading
import socket
import websocket
import zlib
import irsdk
import random
from typing import Dict, List, Optional, Tuple, Union, Any
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.expanduser("~"), "BlackBoxRelay", "logs", "telemetry.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TelemetryCollector")

# Constants
TELEMETRY_VARS = [
    # Core telemetry
    'Speed', 'RPM', 'Gear', 'Throttle', 'Brake', 'Clutch', 'SteeringWheelAngle',
    'FuelLevel', 'FuelUsePerHour', 'LapCurrentLapTime', 'LapDist', 'TrackTemp', 'AirTemp',
    'SessionTime', 'SessionLapsRemaining', 'SessionTimeRemaining',
    
    # Tire data
    'LFtempCL', 'LFtempCM', 'LFtempCR',  # Left Front tire temps (Left, Middle, Right)
    'RFtempCL', 'RFtempCM', 'RFtempCR',  # Right Front tire temps
    'LRtempCL', 'LRtempCM', 'LRtempCR',  # Left Rear tire temps
    'RRtempCL', 'RRtempCM', 'RRtempCR',  # Right Rear tire temps
    'LFpressure', 'RFpressure', 'LRpressure', 'RRpressure',  # Tire pressures
    'LFwearL', 'LFwearM', 'LFwearR',     # Left Front tire wear
    'RFwearL', 'RFwearM', 'RFwearR',     # Right Front tire wear
    'LRwearL', 'LRwearM', 'LRwearR',     # Left Rear tire wear
    'RRwearL', 'RRwearM', 'RRwearR',     # Right Rear tire wear
    
    # Position and timing data
    'PlayerCarPosition', 'Lap', 'LapLastLapTime', 'LapBestLapTime',
    'LapLastLapNum', 'LapBestLapNum',
    'LapDeltaToBestLap', 'LapDeltaToBestLap_DD',
    'CarIdxLapDistPct',  # Car positions around track
]

# Events to detect and send
EVENTS = {
    'lap_completed': lambda old, new: old['Lap'] != new['Lap'],
    'pit_entry': lambda old, new: not old.get('OnPitRoad', False) and new.get('OnPitRoad', False),
    'pit_exit': lambda old, new: old.get('OnPitRoad', False) and not new.get('OnPitRoad', False),
    'sector_change': lambda old, new: int(old.get('LapDist', 0) / 100) != int(new.get('LapDist', 0) / 100),
}


class TelemetryCollector:
    """
    Collects telemetry data from iRacing and transmits it to the BlackBox backend.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the TelemetryCollector.
        
        Args:
            config: Configuration dictionary from CoreAgent
        """
        self.config = config
        self.running = False
        self.ir = None
        self.last_telemetry = {}
        self.last_send_time = 0
        self.session_info = None
        self.driver_info = None
        self.track_info = None
        self.session_id = None
        self.websocket = None
        self.udp_socket = None
        self.connection_thread = None
        self.telemetry_thread = None
        self.reconnect_delay = 1.0
        self.sample_rate = 10  # Hz
        self.last_sample_time = 0
        self.connected_to_backend = False
        self.last_connection_attempt = 0
        self.connection_retry_delay = 5.0  # seconds
        
        # Generate a unique session ID
        self.session_id = f"{int(time.time())}_{random.randint(1000, 9999)}"
        
        logger.info("TelemetryCollector initialized")
    
    def start(self) -> None:
        """Start the telemetry collector."""
        if self.running:
            logger.warning("TelemetryCollector is already running")
            return
        
        self.running = True
        logger.info("Starting TelemetryCollector")
        
        # Start the connection thread
        self.connection_thread = threading.Thread(target=self._maintain_connection, daemon=True)
        self.connection_thread.start()
        
        # Start the telemetry thread
        self.telemetry_thread = threading.Thread(target=self._collect_telemetry, daemon=True)
        self.telemetry_thread.start()
    
    def stop(self) -> None:
        """Stop the telemetry collector."""
        if not self.running:
            return
        
        logger.info("Stopping TelemetryCollector")
        self.running = False
        
        # Close connections
        self._close_connections()
        
        # Wait for threads to finish
        if self.connection_thread and self.connection_thread.is_alive():
            self.connection_thread.join(timeout=5.0)
        
        if self.telemetry_thread and self.telemetry_thread.is_alive():
            self.telemetry_thread.join(timeout=5.0)
        
        logger.info("TelemetryCollector stopped")
    
    def _maintain_connection(self) -> None:
        """Maintain connection to the backend server."""
        while self.running:
            try:
                if not self.connected_to_backend:
                    current_time = time.time()
                    if current_time - self.last_connection_attempt >= self.connection_retry_delay:
                        self.last_connection_attempt = current_time
                        self._connect_to_backend()
                
                # Sleep before checking again
                time.sleep(1.0)
                
            except Exception as e:
                logger.error(f"Error in connection maintenance: {e}")
                time.sleep(5.0)
    
    def _connect_to_backend(self) -> bool:
        """
        Connect to the backend server.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        # Close any existing connections
        self._close_connections()
        
        try:
            # Determine connection type (WebSocket or UDP)
            if self.config.get("telemetry_protocol", "websocket").lower() == "websocket":
                return self._connect_websocket()
            else:
                return self._connect_udp()
        except Exception as e:
            logger.error(f"Error connecting to backend: {e}")
            self.connected_to_backend = False
            return False
    
    def _connect_websocket(self) -> bool:
        """
        Connect to the backend using WebSocket.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Format WebSocket URL
            ws_url = f"{self.config['backend_url'].replace('http://', 'ws://').replace('https://', 'wss://')}/api/v1/telemetry"
            
            # Connect to WebSocket server
            self.websocket = websocket.create_connection(
                ws_url,
                header={"Authorization": f"Bearer {self.config['api_key']}"},
                timeout=10
            )
            
            # Send initial connection message with session info
            self._send_session_info()
            
            logger.info(f"Connected to backend via WebSocket: {ws_url}")
            self.connected_to_backend = True
            return True
            
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            self.websocket = None
            self.connected_to_backend = False
            return False
    
    def _connect_udp(self) -> bool:
        """
        Connect to the backend using UDP.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Parse backend URL for host and port
            backend_url = self.config['backend_url']
            if "://" in backend_url:
                backend_url = backend_url.split("://")[1]
            
            host = backend_url.split(":")[0] if ":" in backend_url else backend_url
            port = int(backend_url.split(":")[1]) if ":" in backend_url else 10000  # Default UDP port
            
            # Create UDP socket
            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_socket.settimeout(5.0)
            
            # Store connection info
            self.udp_host = host
            self.udp_port = port
            
            # Send initial connection message with session info
            self._send_session_info()
            
            logger.info(f"Connected to backend via UDP: {host}:{port}")
            self.connected_to_backend = True
            return True
            
        except Exception as e:
            logger.error(f"UDP connection failed: {e}")
            if self.udp_socket:
                self.udp_socket.close()
            self.udp_socket = None
            self.connected_to_backend = False
            return False
    
    def _close_connections(self) -> None:
        """Close all connections to the backend."""
        if self.websocket:
            try:
                self.websocket.close()
            except Exception as e:
                logger.error(f"Error closing WebSocket: {e}")
            self.websocket = None
        
        if self.udp_socket:
            try:
                self.udp_socket.close()
            except Exception as e:
                logger.error(f"Error closing UDP socket: {e}")
            self.udp_socket = None
        
        self.connected_to_backend = False
    
    def _collect_telemetry(self) -> None:
        """Collect telemetry data from iRacing."""
        logger.info("Starting telemetry collection")
        
        # Initialize iRacing SDK
        self.ir = irsdk.IRSDK()
        
        connection_retry_count = 0
        
        while self.running:
            try:
                # Check if we're connected to iRacing
                if not self.ir.is_connected:
                    if connection_retry_count % 30 == 0:  # Log only every 30 attempts
                        logger.info("Waiting for iRacing connection...")
                    
                    # Try to connect
                    self.ir.startup()
                    
                    if not self.ir.is_connected:
                        connection_retry_count += 1
                        time.sleep(1.0)
                        continue
                    else:
                        logger.info("Connected to iRacing")
                        connection_retry_count = 0
                        
                        # Get initial session info
                        self._update_session_info()
                
                # Throttle the collection rate
                current_time = time.time()
                if current_time - self.last_sample_time < (1.0 / self.sample_rate):
                    time.sleep(0.001)  # Short sleep to prevent CPU hogging
                    continue
                
                self.last_sample_time = current_time
                
                # Collect telemetry data
                telemetry = self._get_telemetry()
                
                # Check for events
                events = self._detect_events(self.last_telemetry, telemetry)
                
                # Send telemetry to backend
                if self.connected_to_backend:
                    self._send_telemetry(telemetry, events)
                
                # Update last telemetry
                self.last_telemetry = telemetry
                
                # Check if session info needs updating
                if self.ir.session_info_update:
                    self._update_session_info()
                
            except Exception as e:
                logger.error(f"Error collecting telemetry: {e}")
                time.sleep(1.0)
    
    def _get_telemetry(self) -> Dict[str, Any]:
        """
        Get current telemetry data from iRacing.
        
        Returns:
            Dict[str, Any]: Dictionary of telemetry values
        """
        if not self.ir or not self.ir.is_connected:
            return {}
        
        # Get all requested telemetry variables
        telemetry = {}
        for var in TELEMETRY_VARS:
            if var in self.ir:
                telemetry[var] = self.ir[var]
        
        # Add additional calculated values
        telemetry['Timestamp'] = time.time()
        telemetry['SessionId'] = self.session_id
        
        # Add session type
        if self.session_info:
            telemetry['SessionType'] = self.session_info.get('SessionType', 'Unknown')
        
        return telemetry
    
    def _detect_events(self, old_telemetry: Dict[str, Any], new_telemetry: Dict[str, Any]) -> List[str]:
        """
        Detect events based on telemetry changes.
        
        Args:
            old_telemetry: Previous telemetry data
            new_telemetry: Current telemetry data
            
        Returns:
            List[str]: List of detected events
        """
        if not old_telemetry:
            return []
        
        events = []
        for event_name, condition in EVENTS.items():
            try:
                if condition(old_telemetry, new_telemetry):
                    events.append(event_name)
            except Exception:
                pass  # Skip events that can't be evaluated
        
        return events
    
    def _update_session_info(self) -> None:
        """Update session information from iRacing."""
        if not self.ir or not self.ir.is_connected:
            return
        
        try:
            # Get session info
            session_info = {}
            
            # Get session type
            session_num = self.ir['SessionNum']
            if session_num is not None and self.ir.session_info and self.ir.session_info.get('Sessions', []):
                if session_num < len(self.ir.session_info['Sessions']):
                    session = self.ir.session_info['Sessions'][session_num]
                    session_info['SessionType'] = session.get('SessionType', 'Unknown')
                    session_info['SessionLaps'] = session.get('SessionLaps', -1)
                    session_info['SessionTime'] = session.get('SessionTime', -1)
            
            # Get track info
            if self.ir.session_info and self.ir.session_info.get('WeekendInfo', {}):
                weekend_info = self.ir.session_info['WeekendInfo']
                session_info['TrackName'] = weekend_info.get('TrackName', 'Unknown')
                session_info['TrackLength'] = weekend_info.get('TrackLength', 0)
                session_info['TrackID'] = weekend_info.get('TrackID', 0)
            
            # Get driver info
            if self.ir.session_info and self.ir.session_info.get('DriverInfo', {}):
                driver_info = self.ir.session_info['DriverInfo']
                session_info['DriverName'] = driver_info.get('DriverName', 'Unknown')
                session_info['DriverID'] = driver_info.get('UserID', 0)
                session_info['TeamName'] = driver_info.get('TeamName', '')
                session_info['CarName'] = driver_info.get('CarName', 'Unknown')
                session_info['CarID'] = driver_info.get('CarID', 0)
            
            self.session_info = session_info
            
            # Send updated session info to backend
            if self.connected_to_backend:
                self._send_session_info()
            
            logger.info(f"Updated session info: {session_info['TrackName']} - {session_info['SessionType']}")
            
        except Exception as e:
            logger.error(f"Error updating session info: {e}")
    
    def _send_session_info(self) -> None:
        """Send session information to the backend."""
        if not self.session_info:
            return
        
        try:
            # Create message
            message = {
                'type': 'session_info',
                'session_id': self.session_id,
                'timestamp': time.time(),
                'data': self.session_info,
                'api_key': self.config['api_key'],
                'user_id': self.config.get('user_id', ''),
                'team_id': self.config.get('team_id', '')
            }
            
            # Send message
            self._send_message(message)
            
            logger.info("Sent session info to backend")
            
        except Exception as e:
            logger.error(f"Error sending session info: {e}")
    
    def _send_telemetry(self, telemetry: Dict[str, Any], events: List[str]) -> None:
        """
        Send telemetry data to the backend.
        
        Args:
            telemetry: Telemetry data to send
            events: List of detected events
        """
        # Throttle sending rate if needed
        current_time = time.time()
        min_send_interval = 1.0 / self.config.get('max_telemetry_rate', 10)  # Default: 10 Hz max
        
        if current_time - self.last_send_time < min_send_interval and not events:
            return
        
        self.last_send_time = current_time
        
        try:
            # Create message
            message = {
                'type': 'telemetry',
                'session_id': self.session_id,
                'timestamp': current_time,
                'data': telemetry,
                'events': events
            }
            
            # Send message
            self._send_message(message)
            
            # Log events if any
            if events:
                logger.info(f"Sent telemetry with events: {events}")
            
        except Exception as e:
            logger.error(f"Error sending telemetry: {e}")
    
    def _send_message(self, message: Dict[str, Any]) -> None:
        """
        Send a message to the backend.
        
        Args:
            message: Message to send
        """
        if not self.connected_to_backend:
            return
        
        try:
            # Convert message to JSON
            json_data = json.dumps(message)
            
            # Compress data if enabled
            if self.config.get('compress_telemetry', True):
                compressed_data = zlib.compress(json_data.encode('utf-8'))
                
                if self.websocket:
                    self.websocket.send_binary(compressed_data)
                elif self.udp_socket:
                    self.udp_socket.sendto(compressed_data, (self.udp_host, self.udp_port))
            else:
                if self.websocket:
                    self.websocket.send(json_data)
                elif self.udp_socket:
                    self.udp_socket.sendto(json_data.encode('utf-8'), (self.udp_host, self.udp_port))
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            self.connected_to_backend = False
            # Will trigger reconnection in the connection maintenance thread


def create_telemetry_collector(config: Dict[str, Any]) -> TelemetryCollector:
    """
    Create and return a TelemetryCollector instance.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        TelemetryCollector: Initialized telemetry collector
    """
    return TelemetryCollector(config)


# For testing purposes
if __name__ == "__main__":
    # Test configuration
    test_config = {
        'backend_url': 'http://localhost:8000',
        'api_key': 'test_api_key',
        'telemetry_protocol': 'websocket',
        'compress_telemetry': True,
        'max_telemetry_rate': 10
    }
    
    # Create and start collector
    collector = create_telemetry_collector(test_config)
    
    try:
        collector.start()
        # Keep running for testing
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        collector.stop()
        print("Test stopped by user")
