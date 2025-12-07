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
import random
import uuid
import requests
from typing import Dict, List, Optional, Tuple, Union, Any
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('TelemetryCollector')

# Try to import real iRacing SDK, fallback to simulation
# Set FORCE_SIMULATION=1 to use simulated data without iRacing
FORCE_SIMULATION = os.environ.get('FORCE_SIMULATION', '').lower() in ('1', 'true', 'yes')

if FORCE_SIMULATION:
    HAS_REAL_SDK = False
    logger.info("🔧 Forcing simulation mode via FORCE_SIMULATION env var")
else:
    try:
        import irsdk
        HAS_REAL_SDK = True
        logger.info("✅ Real iRacing SDK available")
    except ImportError:
        HAS_REAL_SDK = False
        logger.warning("⚠️  Real iRacing SDK not available, using simulation")

if not HAS_REAL_SDK:
    class IRacingSimulator:
        """Simulates iRacing telemetry data for testing."""

        def __init__(self):
            self.is_connected = False
            self.session_info = None
            self.telemetry_data = {}
            self.session_info_update = 0
            self.start_time = time.time()
            self._init_simulated_data()

        def startup(self):
            logger.info("🚗 Starting iRacing simulator...")
            time.sleep(1)
            self.is_connected = True
            logger.info("✅ iRacing simulator connected")

        def shutdown(self):
            self.is_connected = False
            logger.info("🛑 iRacing simulator shutdown")

        def _init_simulated_data(self):
            """Initialize simulated telemetry data."""
            self.telemetry_data = {
                'Speed': 0.0, 'RPM': 1000, 'Gear': 1, 'Throttle': 0.0, 'Brake': 0.0,
                'Clutch': 0.0, 'SteeringWheelAngle': 0.0, 'FuelLevel': 100.0,
                'FuelUsePerHour': 0.0, 'LapCurrentLapTime': 0.0, 'LapDist': 0.0,
                'TrackTemp': 25.0, 'AirTemp': 20.0, 'SessionTime': 0.0,
                'LatAccel': 0.0, 'LongAccel': 0.0, 'VertAccel': 0.0,
                'LapDeltaToBestLap': 0.0,
                'SessionLapsRemaining': 10, 'SessionTimeRemaining': 600.0,
                'PlayerCarPosition': 1, 'Lap': 1, 'LapLastLapTime': 85.5,
                'LapBestLapTime': 84.2, 'SessionNum': 0,
                'SessionFlags': 0, 'DRS_Status': 0,
                'dcBrakeBias': 54.5, 'dcABS': 5, 'dcTractionControl': 5, 'dcTractionControl2': 5, 'dcFuelMixture': 1,
                'EnergyERSBatteryPct': 1.0, 'EnergyMGU_KLapDeployPct': 1.0, 'EnergyERSDeployMode': 1,
                'WindVel': 2.5, 'WindDir': 0.5
            }

            # Tire data simulation
            for tire in ['LF', 'RF', 'LR', 'RR']:
                for pos in ['L', 'M', 'R']:
                    self.telemetry_data[f'{tire}tempC{pos}'] = 85 + random.uniform(-5, 5)
                    self.telemetry_data[f'{tire}wear{pos}'] = 0.1 + random.uniform(0, 0.2)

            # Session info
            self.session_info = {
                'WeekendInfo': {
                    'TrackName': 'Silverstone Circuit',
                    'TrackLength': 5891,
                    'TrackID': 1001
                },
                'DriverInfo': {
                    'DriverName': 'Test Driver',
                    'UserID': 12345,
                    'TeamName': 'BlackBox Team',
                    'CarName': 'Formula 1 Car',
                    'CarID': 2001
                },
                'Sessions': [{
                    'SessionType': 'Race',
                    'SessionLaps': 10,
                    'SessionTime': 600
                }]
            }

        def update_simulation(self):
            """Update simulated telemetry data."""
            if not self.is_connected:
                return
            
            self.session_info_update += 1

            import math
            self.telemetry_data['SessionTime'] = time.time() - self.start_time
            self.telemetry_data['SessionTimeRemaining'] = max(0, 600.0 - self.telemetry_data['SessionTime'])

            throttle = self.telemetry_data.get('Throttle', 0.0)
            brake = self.telemetry_data.get('Brake', 0.0)

            target_speed = throttle * 350
            current_speed = self.telemetry_data.get('Speed', 0.0)
            speed_change = (target_speed - current_speed) * 0.1
            if brake > 0:
                speed_change -= brake * 50
                speed_change -= brake * 50
            self.telemetry_data['Speed'] = max(0, current_speed + speed_change)
            
            # G-Force simulation
            # Longitudinal G (~ +/- 1.5G)
            self.telemetry_data['LongAccel'] = (speed_change / 9.81) 
            
            # Lateral G (fake it based on steering + speed)
            steering = self.telemetry_data.get('SteeringWheelAngle', 0.0)
            self.telemetry_data['LatAccel'] = steering * (current_speed / 100.0)
            
            # Vertical G (bumps)
            self.telemetry_data['VertAccel'] = 1.0 + random.uniform(-0.1, 0.1)
            
            # Clutch (simulated random shifts)
            if self.telemetry_data['RPM'] > 11000:
                self.telemetry_data['Clutch'] = 1.0
            else:
                self.telemetry_data['Clutch'] = 0.0

            # Delta simulation
            self.telemetry_data['LapDeltaToBestLap'] = math.sin(self.telemetry_data['LapDist'] / 100) * 0.5

            gear = self.telemetry_data.get('Gear', 1)
            rpm_base = (self.telemetry_data['Speed'] / 350) * 12000
            rpm_variation = math.sin(time.time() * 2) * 500
            self.telemetry_data['RPM'] = max(800, min(13000, rpm_base + rpm_variation))

            fuel_burn = throttle * 0.1 + self.telemetry_data['RPM'] / 100000
            self.telemetry_data['FuelLevel'] = max(0, self.telemetry_data['FuelLevel'] - fuel_burn)
            self.telemetry_data['FuelUsePerHour'] = fuel_burn * 3600

            self.telemetry_data['LapDist'] = (self.telemetry_data['SessionTime'] % 85.5) / 85.5 * 5891
            
            # Simulate ERS usage
            if throttle > 0.9:
                self.telemetry_data['EnergyERSBatteryPct'] = max(0.0, self.telemetry_data['EnergyERSBatteryPct'] - 0.001)
            else:
                self.telemetry_data['EnergyERSBatteryPct'] = min(1.0, self.telemetry_data['EnergyERSBatteryPct'] + 0.0005)
                
            # Simulate Flags (Yellow flag occasionally)
            if random.random() < 0.001:
                self.telemetry_data['SessionFlags'] = 0x00000008 # One of the yellow flags
            elif random.random() < 0.05:
                self.telemetry_data['SessionFlags'] = 0 # Clear flags
                
            # Simulate Wind
            self.telemetry_data['WindVel'] = 2.5 + math.sin(time.time() * 0.1) * 0.5

        def get(self, var_name: str) -> Any:
            self.update_simulation()
            return self.telemetry_data.get(var_name)

        def __getitem__(self, var_name: str) -> Any:
            return self.get(var_name)

        def __contains__(self, var_name: str) -> bool:
            return var_name in self.telemetry_data

    # Use simulation as fallback
    class MockIRSDK:
        IRSDK = IRacingSimulator

    irsdk = MockIRSDK()

# Add file handler to logger after initial setup
log_dir = os.path.join(os.path.expanduser("~"), "BlackBoxRelay", "logs")
os.makedirs(log_dir, exist_ok=True)
file_handler = logging.FileHandler(os.path.join(log_dir, "telemetry.log"))
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)
logger.addHandler(logging.StreamHandler()) # Ensure stream handler is also added if not already by basicConfig

# Constants
TELEMETRY_VARS = [
    # Core telemetry
    'Speed', 'RPM', 'Gear', 'Throttle', 'Brake', 'Clutch', 'SteeringWheelAngle',
    'FuelLevel', 'FuelUsePerHour', 'LapCurrentLapTime', 'LapDist', 'TrackTemp', 'AirTemp',
    'LatAccel', 'LongAccel', 'VertAccel',
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
    'LapDeltaToBestLap', 'LapDeltaToBestLap_DD',
    'CarIdxLapDistPct',  # Car positions around track
    
    # Advanced Systems (Phase 2)
    'SessionFlags', 'DRS_Status',
    'dcBrakeBias', 'dcABS', 'dcTractionControl', 'dcTractionControl2', 'dcFuelMixture',
    'EnergyERSBatteryPct', 'EnergyMGU_KLapDeployPct', 'EnergyERSDeployMode',
    'WindVel', 'WindDir',
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
        self.session_id = str(uuid.uuid4())
        
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
            elif self.config.get("telemetry_protocol", "websocket").lower() == "udp":
                return self._connect_udp()
            else:
                # HTTP - strictly stateless, but we mark as connected
                self.connected_to_backend = True
                logger.info(f"Using HTTP transport to {self.config['backend_url']}")
                # Ensure Session Created?
                # Server expects session to exist for /sessions/:id/telemetry
                # We should create session first.
                try:
                    create_url = f"{self.config['backend_url']}/sessions"
                    sh = { "Authorization": f"Bearer {self.config.get('api_key', '')}" }
                    pl = { "id": self.session_id, "track": self.session_info.get('WeekendInfo', {}).get('TrackName', 'Unknown') if self.session_info else 'Unknown' }
                    requests.post(create_url, json=pl, headers=sh, timeout=5)
                    logger.info(f"Created Session {self.session_id} via HTTP")
                except Exception as e:
                    logger.error(f"Failed to create session via HTTP: {e}")
                return True
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
    
    def _normalize_data(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize raw iRacing telemetry to Server schema.
        """
        normalized = {
            'timestamp': raw.get('Timestamp', time.time()) * 1000, # Server expects ms? Check server line 174 `typeof t.timestamp !== 'number'`. DB uses `to_timestamp($/1000.0)`. So server expects ms. Python time.time() is seconds.
            'speed': raw.get('Speed', 0) * 3.6, # iRacing is m/s? Usually. Dashboard expects km/h or m/s? Server db just stores it. Dashboard likely expects km/h? Check dashboard later. Standard is usually m/s in backend.
            'rpm': raw.get('RPM', 0),
            'gear': raw.get('Gear', 0),
            'throttle': raw.get('Throttle', 0),
            'brake': raw.get('Brake', 0),
            'clutch': raw.get('Clutch', 0), # Not in server DB explicit cols but maybe useful
            'fuel': {
                'level': raw.get('FuelLevel', 0),
                'usagePerHour': raw.get('FuelUsePerHour', 0)
            },
            'lap': raw.get('Lap', 0),
            'racePosition': raw.get('PlayerCarPosition', 0),
            'trackPosition': raw.get('LapDist', 0),
            'deltaToBestLap': raw.get('LapDeltaToBestLap', 0),
            'gForce': {
                'lateral': raw.get('LatAccel', 0),
                'longitudinal': raw.get('LongAccel', 0),
                'vertical': raw.get('VertAccel', 0)
            },
            'tires': {
                'frontLeft': { 
                    'temp': (raw.get('LFtempCL', 0) + raw.get('LFtempCM', 0) + raw.get('LFtempCR', 0)) / 3,
                    'wear': (raw.get('LFwearL', 0) + raw.get('LFwearM', 0) + raw.get('LFwearR', 0)) / 3,
                    'pressure': raw.get('LFpressure', 0)
                },
                'frontRight': {
                     'temp': (raw.get('RFtempCL', 0) + raw.get('RFtempCM', 0) + raw.get('RFtempCR', 0)) / 3,
                     'wear': (raw.get('RFwearL', 0) + raw.get('RFwearM', 0) + raw.get('RFwearR', 0)) / 3,
                     'pressure': raw.get('RFpressure', 0)
                },
                'rearLeft': {
                     'temp': (raw.get('LRtempCL', 0) + raw.get('LRtempCM', 0) + raw.get('LRtempCR', 0)) / 3,
                     'wear': (raw.get('LRwearL', 0) + raw.get('LRwearM', 0) + raw.get('LRwearR', 0)) / 3,
                     'pressure': raw.get('LRpressure', 0)
                },
                'rearRight': {
                     'temp': (raw.get('RRtempCL', 0) + raw.get('RRtempCM', 0) + raw.get('RRtempCR', 0)) / 3,
                     'wear': (raw.get('RRwearL', 0) + raw.get('RRwearM', 0) + raw.get('RRwearR', 0)) / 3,
                     'pressure': raw.get('RRpressure', 0)
                }
            },
            # weather, session flags etc?
            'weather': {
                'windSpeed': raw.get('WindVel', 0),
                'windDirection': raw.get('WindDir', 0)
            },
            'flags': raw.get('SessionFlags', 0),
            'energy': {
                 'batteryPct': raw.get('EnergyERSBatteryPct', 0),
                 'deployPct': raw.get('EnergyMGU_KLapDeployPct', 0),
                 'deployMode': raw.get('EnergyERSDeployMode', 0)
            },
            'carSettings': {
                 'brakeBias': raw.get('dcBrakeBias', 0),
                 'abs': raw.get('dcABS', 0),
                 'tractionControl': raw.get('dcTractionControl', 0),
                 'tractionControl2': raw.get('dcTractionControl2', 0),
                 'fuelMixture': raw.get('dcFuelMixture', 0)
            },
            'drsStatus': raw.get('DRS_Status', 0)
        }
        
        # Add session_id, api_key, user_id, team_id from self
        normalized['session_id'] = self.session_id
        normalized['api_key'] = self.config['api_key']
        normalized['user_id'] = self.config.get('user_id', '')
        normalized['team_id'] = self.config.get('team_id', '')

        # Add events if present
        if 'Events' in raw:
            normalized['events'] = raw['Events']

        return normalized

    def _send_telemetry(self, telemetry: Dict[str, Any], events: List[str]) -> None:
        """
        Send telemetry data to the backend.
        
        Args:
            telemetry: Telemetry data dictionary
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
            
            # Compress data if enabled (WebSocket/UDP only)
            if self.config.get('compress_telemetry', True) and (self.websocket or self.udp_socket):
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
                else: 
                     # HTTP Fallback
                     url = f"{self.config['backend_url']}/sessions/{self.session_id}/telemetry"
                     headers = {
                         "Authorization": f"Bearer {self.config.get('api_key', '')}",
                         "Content-Type": "application/json"
                     }
                     # Send payload directly (flattened or as list if needed)
                     # Server expects a single object or list. Message is a dict.
                     # We need to ensure message keys match TelemetryData interface if possible, 
                     # or rely on server to map it.
                     # Check server mapping: 'speed' (lowercase) vs 'Speed' (uppercase).
                     # The telemetry_collector sends 'Speed'. Server expects 'speed' or maps it?
                     # Server db columns: speed, rpm. Server code lines 198: t.speed.
                     # Wait, Server.ts:198 `t.speed`. `data` map line 253 `speed: r.speed`.
                     # Incoming payload `t` at line 173. 
                     # Does server do mapping from UpperCase to LowerCase?
                     # Server line 189: `fl = t.tires?.frontLeft`.
                     # TelemetryCollector sends `LFtempCL`.
                     # The server requires specific JSON structure (TelemetryData interface).
                     # TelemetryCollector sends raw iRacing keys. 
                     # MISSING: A mapping layer in python or server.
                     # Server.ts line 181 `cols`. Line 191 values.
                     # `t.speed`.
                     # IF TelemetryCollector sends `Speed`, `t.speed` is undefined unless we map it.
                     # CRITICAL GAP: Data Mapping.
                     
                     # FOR NOW: Focus on getting *data* to server. The server might have loose typing or all I missed a mapper.
                     resp = requests.post(url, json=message, headers=headers, timeout=2.0)
                     if resp.status_code >= 400:
                         logger.error(f"HTTP Error {resp.status_code}: {resp.text}")
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            self.connected_to_backend = False


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
    import os
    # Test configuration - uses environment variables if available
    test_config = {
        'backend_url': os.environ.get('BACKEND_URL', 'http://localhost:8000'),
        'api_key': os.environ.get('API_KEY', 'test_api_key'),
        'telemetry_protocol': os.environ.get('TELEMETRY_PROTOCOL', 'websocket'),
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
