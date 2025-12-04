"""
iRacing SDK Integration
Real-time connection to iRacing for live telemetry streaming
"""

import irsdk
import time
import logging
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TelemetrySnapshot:
    """Single telemetry snapshot at 60Hz"""
    # Timestamp
    session_time: float
    timestamp: int  # Unix timestamp in ms
    
    # Lap info
    lap: int
    lap_dist: float
    lap_dist_pct: float
    
    # Speed and position
    speed: float  # m/s
    speed_kmh: float
    pos_x: float
    pos_y: float
    pos_z: float
    
    # Inputs
    throttle: float  # 0-1
    brake: float  # 0-1
    clutch: float  # 0-1
    steering: float  # radians
    gear: int
    
    # Engine
    rpm: int
    fuel_level: float
    fuel_use_per_hour: float
    
    # G-forces
    lat_accel: float
    long_accel: float
    vert_accel: float
    
    # Tire temps (surface)
    tire_temp_lf: float
    tire_temp_rf: float
    tire_temp_lr: float
    tire_temp_rr: float
    
    # Tire wear
    tire_wear_lf: float
    tire_wear_rf: float
    tire_wear_lr: float
    tire_wear_rr: float
    
    # Brake temps
    brake_temp_lf: float
    brake_temp_rf: float
    brake_temp_lr: float
    brake_temp_rr: float
    
    # Track conditions
    track_temp: float
    air_temp: float
    air_pressure: float
    relative_humidity: float
    wind_vel: float
    wind_dir: float
    
    # Session flags
    session_state: str
    session_flags: str

    # Spotter Data
    car_left_right: int # Bitfield
    car_idx_lap_dist_pct: List[float]
    car_idx_track_surface: List[int]
    car_idx_on_pit_road: List[bool]


@dataclass
class SessionInfo:
    """Complete session information"""
    session_id: str
    session_type: str  # Practice, Qualify, Race
    track_name: str
    track_config: str
    track_length: float
    car_name: str
    car_class: str
    
    # Weather
    weather_type: str
    skies: str
    
    # Session details
    session_laps: int
    session_time: float
    
    # Driver info
    driver_id: str
    driver_name: str
    car_number: str
    
    # Competitors
    num_cars: int
    competitors: List[Dict]


class iRacingSDKWrapper:
    """
    Real-time connection to iRacing
    Streams telemetry at 60Hz
    """
    
    def __init__(self):
        self.ir = irsdk.IRSDK()
        self.connected = False
        self.last_session_info = None
        self.telemetry_callbacks = []
        self.session_callbacks = []
        
    def connect(self, timeout: int = 30) -> bool:
        """
        Connect to iRacing
        
        Args:
            timeout: Seconds to wait for connection
            
        Returns:
            True if connected
        """
        logger.info("Connecting to iRacing...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.ir.startup():
                self.connected = True
                logger.info("✅ Connected to iRacing")
                
                # Get initial session info
                self.last_session_info = self.get_session_info()
                return True
            
            time.sleep(1)
        
        logger.error("❌ Failed to connect to iRacing")
        return False
    
    def disconnect(self):
        """Disconnect from iRacing"""
        if self.connected:
            self.ir.shutdown()
            self.connected = False
            logger.info("Disconnected from iRacing")
    
    def is_connected(self) -> bool:
        """Check if still connected"""
        return self.connected and self.ir.is_initialized
    
    def get_telemetry(self) -> Optional[TelemetrySnapshot]:
        """
        Get current telemetry snapshot
        
        Returns:
            TelemetrySnapshot or None if not available
        """
        if not self.is_connected():
            return None
        
        try:
            # Get all telemetry values
            snapshot = TelemetrySnapshot(
                session_time=self.ir['SessionTime'],
                timestamp=int(datetime.now().timestamp() * 1000),
                
                # Lap info
                lap=self.ir['Lap'],
                lap_dist=self.ir['LapDist'],
                lap_dist_pct=self.ir['LapDistPct'],
                
                # Speed and position
                speed=self.ir['Speed'],
                speed_kmh=self.ir['Speed'] * 3.6,  # m/s to km/h
                pos_x=self.ir['CarIdxX'][0] if self.ir['CarIdxX'] else 0,
                pos_y=self.ir['CarIdxY'][0] if self.ir['CarIdxY'] else 0,
                pos_z=self.ir['CarIdxZ'][0] if self.ir['CarIdxZ'] else 0,
                
                # Inputs
                throttle=self.ir['Throttle'],
                brake=self.ir['Brake'],
                clutch=self.ir['Clutch'],
                steering=self.ir['SteeringWheelAngle'],
                gear=self.ir['Gear'],
                
                # Engine
                rpm=self.ir['RPM'],
                fuel_level=self.ir['FuelLevel'],
                fuel_use_per_hour=self.ir['FuelUsePerHour'],
                
                # G-forces
                lat_accel=self.ir['LatAccel'],
                long_accel=self.ir['LongAccel'],
                vert_accel=self.ir['VertAccel'],
                
                # Tire temps (left front, right front, left rear, right rear)
                tire_temp_lf=self.ir['LFtempCL'],
                tire_temp_rf=self.ir['RFtempCL'],
                tire_temp_lr=self.ir['LRtempCL'],
                tire_temp_rr=self.ir['RRtempCL'],
                
                # Tire wear
                tire_wear_lf=self.ir['LFwearL'],
                tire_wear_rf=self.ir['RFwearL'],
                tire_wear_lr=self.ir['LRwearL'],
                tire_wear_rr=self.ir['RRwearL'],
                
                # Brake temps
                brake_temp_lf=self.ir['LFbrakeLinePress'],
                brake_temp_rf=self.ir['RFbrakeLinePress'],
                brake_temp_lr=self.ir['LRbrakeLinePress'],
                brake_temp_rr=self.ir['RRbrakeLinePress'],
                
                # Track conditions
                track_temp=self.ir['TrackTemp'],
                air_temp=self.ir['AirTemp'],
                air_pressure=self.ir['AirPressure'],
                relative_humidity=self.ir['RelativeHumidity'],
                wind_vel=self.ir['WindVel'],
                wind_dir=self.ir['WindDir'],
                
                # Session info
                session_state=self.ir['SessionState'],
                session_flags=str(self.ir['SessionFlags']),

                # Spotter Data
                car_left_right=self.ir['CarLeftRight'],
                car_idx_lap_dist_pct=self.ir['CarIdxLapDistPct'],
                car_idx_track_surface=self.ir['CarIdxTrackSurface'],
                car_idx_on_pit_road=self.ir['CarIdxOnPitRoad']
            )
            
            return snapshot
            
        except Exception as e:
            logger.error(f"Error getting telemetry: {e}")
            return None
    
    def get_session_info(self) -> Optional[SessionInfo]:
        """
        Get complete session information
        
        Returns:
            SessionInfo or None
        """
        if not self.is_connected():
            return None
        
        try:
            session_info_raw = self.ir['SessionInfo']
            
            # Parse session info (YAML format)
            # Simplified - would use full YAML parsing
            
            info = SessionInfo(
                session_id=str(self.ir['SessionUniqueID']),
                session_type=self.ir['SessionType'],
                track_name=self.ir['TrackName'],
                track_config=self.ir['TrackConfigName'],
                track_length=self.ir['TrackLength'],
                car_name=self.ir['CarPath'],
                car_class=self.ir['CarClassShortName'],
                
                weather_type=self.ir['WeatherType'],
                skies=self.ir['Skies'],
                
                session_laps=self.ir['SessionLaps'],
                session_time=self.ir['SessionTime'],
                
                driver_id=str(self.ir['PlayerCarIdx']),
                driver_name=self.ir['DriverInfo']['DriverUserID'] if 'DriverInfo' in self.ir else '',
                car_number=str(self.ir['PlayerCarClassPosition']),
                
                num_cars=self.ir['NumCars'],
                competitors=self._get_competitors()
            )
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting session info: {e}")
            return None
    
    def get_live_positions(self) -> Dict[str, Dict]:
        """
        Get real-time positions and gaps for all drivers
        
        Returns:
            Dict of driver_id -> {position, gap, lap, etc}
        """
        if not self.is_connected():
            return {}
        
        positions = {}
        
        try:
            for idx in range(self.ir['NumCars']):
                positions[str(idx)] = {
                    'position': self.ir['CarIdxPosition'][idx],
                    'class_position': self.ir['CarIdxClassPosition'][idx],
                    'lap': self.ir['CarIdxLap'][idx],
                    'lap_dist_pct': self.ir['CarIdxLapDistPct'][idx],
                    'on_pit_road': self.ir['CarIdxOnPitRoad'][idx],
                    'track_surface': self.ir['CarIdxTrackSurface'][idx],
                    'gear': self.ir['CarIdxGear'][idx],
                    'rpm': self.ir['CarIdxRPM'][idx],
                    'estimated_time': self.ir['CarIdxEstTime'][idx]
                }
            
            return positions
            
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return {}
    
    def _get_competitors(self) -> List[Dict]:
        """Get list of all competitors in session"""
        competitors = []
        
        try:
            for idx in range(self.ir['NumCars']):
                competitors.append({
                    'driver_id': str(idx),
                    'driver_name': f"Driver {idx}",  # Would parse from SessionInfo
                    'car_number': str(idx),
                    'car_class': '',
                    'irating': 0,
                    'license_level': ''
                })
        except:
            pass
        
        return competitors
    
    def register_telemetry_callback(self, callback: Callable[[TelemetrySnapshot], None]):
        """Register callback for telemetry updates"""
        self.telemetry_callbacks.append(callback)
    
    def register_session_callback(self, callback: Callable[[SessionInfo], None]):
        """Register callback for session changes"""
        self.session_callbacks.append(callback)
    
    def check_connection(self) -> bool:
        """
        Check if connection is still alive
        
        Returns:
            True if connected
        """
        if not self.connected:
            return False
            
        # Check if iRacing is still running and initialized
        if not self.ir.is_initialized:
            self.connected = False
            logger.warning("⚠️ Connection to iRacing lost")
            return False
            
        return True

    def reconnect(self, max_attempts: int = 5) -> bool:
        """
        Attempt to reconnect to iRacing
        
        Args:
            max_attempts: Maximum number of reconnection attempts
            
        Returns:
            True if reconnected
        """
        logger.info("🔄 Attempting to reconnect to iRacing...")
        
        for attempt in range(max_attempts):
            logger.info(f"Reconnection attempt {attempt + 1}/{max_attempts}...")
            
            if self.connect(timeout=5):
                logger.info("✅ Reconnected successfully")
                return True
                
            # Exponential backoff
            wait_time = 2 ** attempt
            logger.info(f"Waiting {wait_time}s before next attempt...")
            time.sleep(wait_time)
            
        logger.error("❌ Failed to reconnect after multiple attempts")
        return False

    async def stream_telemetry(self, hz: int = 60):
        """
        Stream telemetry at specified frequency
        Handles connection drops and automatic reconnection
        
        Args:
            hz: Frequency in Hz (default 60)
        """
        interval = 1.0 / hz
        logger.info(f"Starting telemetry stream at {hz}Hz")
        
        while True:
            # Check connection
            if not self.check_connection():
                logger.warning("Connection lost. Attempting to reconnect...")
                if not self.reconnect():
                    logger.error("Unable to restore connection. Stopping stream.")
                    break
            
            start = time.time()
            
            try:
                # Get telemetry
                telemetry = self.get_telemetry()
                
                if telemetry:
                    # Call all registered callbacks
                    for callback in self.telemetry_callbacks:
                        try:
                            if asyncio.iscoroutinefunction(callback):
                                await callback(telemetry)
                            else:
                                callback(telemetry)
                        except Exception as e:
                            logger.error(f"Error in telemetry callback: {e}")
            except Exception as e:
                logger.error(f"Error in telemetry loop: {e}")
            
            # Maintain frequency
            elapsed = time.time() - start
            sleep_time = max(0, interval - elapsed)
            await asyncio.sleep(sleep_time)
        
        logger.info("Telemetry stream stopped")


# Example usage
if __name__ == '__main__':
    async def main():
        # Create SDK wrapper
        sdk = iRacingSDKWrapper()
        
        # Connect to iRacing
        if not sdk.connect():
            print("Failed to connect to iRacing. Make sure iRacing is running.")
            return
        
        # Get session info
        session = sdk.get_session_info()
        if session:
            print(f"Session: {session.session_type}")
            print(f"Track: {session.track_name}")
            print(f"Car: {session.car_name}")
        
        # Register telemetry callback
        def on_telemetry(t: TelemetrySnapshot):
            print(f"Lap {t.lap} | Speed: {t.speed_kmh:.1f} km/h | Throttle: {t.throttle:.0%} | Brake: {t.brake:.0%}")
        
        sdk.register_telemetry_callback(on_telemetry)
        
        # Stream for 10 seconds
        try:
            await asyncio.wait_for(sdk.stream_telemetry(hz=10), timeout=10)
        except asyncio.TimeoutError:
            pass
        
        # Disconnect
        sdk.disconnect()
    
    asyncio.run(main())
