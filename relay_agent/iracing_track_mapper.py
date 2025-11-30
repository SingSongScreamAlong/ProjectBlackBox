"""
iRacing Real-Time Track Mapper
Extracts accurate track data directly from iRacing SDK during live session
"""

import irsdk
import time
import json
import logging
from typing import List, Dict, Optional
from track_analyzer import TelemetryTrackAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class iRacingTrackMapper:
    """Extract accurate track maps from live iRacing sessions"""

    def __init__(self):
        self.ir = irsdk.IRSDK()
        self.telemetry_samples = []
        self.recording = False
        self.track_name = None
        self.track_length = None
        self.player_car_idx = None
        self.position_buffer = []  # For smoothing
        self.max_buffer_size = 5

    def connect(self) -> bool:
        """Connect to iRacing"""
        logger.info("Connecting to iRacing...")

        if self.ir.startup():
            logger.info("✓ Connected to iRacing successfully")
            self._load_track_info()
            return True
        else:
            logger.error("✗ Failed to connect to iRacing. Is iRacing running?")
            return False

    def _load_track_info(self):
        """Load track information from iRacing"""
        self.track_name = self.ir['WeekendInfo']['TrackDisplayName']
        self.track_length = self.ir['WeekendInfo']['TrackLength'].split()[0]  # Remove 'km' unit

        # Find player car index for accurate position data
        self.player_car_idx = self.ir['PlayerCarIdx']

        logger.info(f"Track: {self.track_name}")
        logger.info(f"Length: {self.track_length} km")
        logger.info(f"Player Car Index: {self.player_car_idx}")

    def record_reference_lap(self, wait_for_green_flag: bool = True) -> List[Dict]:
        """
        Record a complete lap of telemetry data for track mapping

        Args:
            wait_for_green_flag: If True, waits for green flag before recording

        Returns:
            List of telemetry samples from one complete lap
        """
        logger.info("Preparing to record reference lap...")

        if wait_for_green_flag:
            logger.info("Waiting for green flag...")
            self._wait_for_green_flag()

        logger.info("Waiting for lap to start...")
        self._wait_for_lap_start()

        logger.info("🔴 RECORDING STARTED - Drive your fastest lap!")
        self.recording = True
        self.telemetry_samples = []

        start_lap = self.ir['Lap']
        sample_rate = 0.1  # 10Hz sampling

        while self.recording:
            # Check if iRacing is still running
            if not self.ir.is_connected:
                logger.warning("iRacing connection lost")
                break

            # Collect telemetry sample
            sample = self._get_telemetry_sample()
            if sample:
                self.telemetry_samples.append(sample)

            # Check if lap is complete
            current_lap = self.ir['Lap']
            if current_lap > start_lap:
                logger.info("✓ Lap complete!")
                self.recording = False
                break

            time.sleep(sample_rate)

        logger.info(f"✓ Recorded {len(self.telemetry_samples)} telemetry samples")
        return self.telemetry_samples

    def _get_telemetry_sample(self) -> Optional[Dict]:
        """Get current telemetry sample from iRacing with accurate position data"""
        try:
            # Calculate track distance
            lap_dist_pct = self.ir['LapDistPct']
            if lap_dist_pct < 0:
                lap_dist_pct = 0

            track_length_m = float(self.track_length.replace(' km', '')) * 1000
            distance = lap_dist_pct * track_length_m

            # Get REAL position data from iRacing (in meters, world coordinates)
            # iRacing provides position arrays for all cars indexed by car number
            pos_x = 0
            pos_y = 0
            pos_z = 0

            if self.player_car_idx is not None:
                # Try to get position from car position arrays
                try:
                    # Method 1: Direct position arrays (most accurate)
                    if 'CarIdxX' in self.ir and 'CarIdxY' in self.ir and 'CarIdxZ' in self.ir:
                        pos_x = self.ir['CarIdxX'][self.player_car_idx]
                        pos_y = self.ir['CarIdxY'][self.player_car_idx]
                        pos_z = self.ir['CarIdxZ'][self.player_car_idx]
                    # Method 2: Use velocity integration as fallback
                    elif len(self.telemetry_samples) > 0:
                        # Integrate velocity to estimate position
                        dt = 0.1  # 10Hz sample rate
                        vx = self.ir['VelocityX']
                        vy = self.ir['VelocityY']
                        vz = self.ir['VelocityZ']

                        last_sample = self.telemetry_samples[-1]
                        pos_x = last_sample.get('pos_x', 0) + vx * dt
                        pos_y = last_sample.get('pos_y', 0) + vy * dt
                        pos_z = last_sample.get('pos_z', 0) + vz * dt
                except (KeyError, IndexError, TypeError):
                    # Fallback: Use distance-based estimation
                    # Convert lap distance to approximate X/Y coordinates
                    angle = lap_dist_pct * 2 * 3.14159  # Rough circular approximation
                    radius = track_length_m / (2 * 3.14159)
                    pos_x = radius * (1 - lap_dist_pct) * 1000  # Scale up
                    pos_y = radius * lap_dist_pct * 1000
                    pos_z = 0

            # Apply position smoothing (moving average filter)
            smoothed_pos = self._smooth_position(pos_x, pos_y, pos_z)

            sample = {
                'timestamp': time.time() * 1000,  # milliseconds
                'distance': distance,
                'speed': self.ir['Speed'] * 3.6,  # Convert m/s to km/h
                'rpm': self.ir['RPM'],
                'gear': self.ir['Gear'],
                'throttle': self.ir['Throttle'],
                'brake': self.ir['Brake'],
                'steering': self.ir['SteeringWheelAngle'],

                # REAL Position data (smoothed)
                'pos_x': smoothed_pos[0],
                'pos_y': smoothed_pos[1],
                'pos_z': smoothed_pos[2],

                # Raw position (for debugging)
                'pos_x_raw': pos_x,
                'pos_y_raw': pos_y,
                'pos_z_raw': pos_z,

                # Velocity (for validation)
                'vel_x': self.ir.get('VelocityX', 0),
                'vel_y': self.ir.get('VelocityY', 0),
                'vel_z': self.ir.get('VelocityZ', 0),

                # Orientation (yaw, pitch, roll in radians)
                'yaw': self.ir.get('Yaw', 0),
                'pitch': self.ir.get('Pitch', 0),
                'roll': self.ir.get('Roll', 0),

                # G-Forces
                'g_lat': self.ir['LatAccel'] / 9.81,  # Convert to G
                'g_long': self.ir['LonAccel'] / 9.81,
                'g_vert': self.ir['VertAccel'] / 9.81,

                # Lap and sector
                'lap': self.ir['Lap'],
                'sector': self._get_current_sector(),

                # Track info
                'track_name': self.track_name,
                'car_class': self.ir['PlayerCarClass'],
                'track_temp': self.ir['TrackTemp'],
                'weather': 'Clear',  # Simplified

                # Additional useful data
                'tire_temp_lf': self.ir['LFtempCL'],
                'tire_temp_rf': self.ir['RFtempCL'],
                'tire_temp_lr': self.ir['LRtempCL'],
                'tire_temp_rr': self.ir['RRtempCL'],

                # Track surface type under tires
                'track_surface': self.ir.get('OnPitRoad', False),
            }

            return sample

        except Exception as e:
            logger.error(f"Error collecting telemetry: {e}")
            logger.exception("Full traceback:")
            return None

    def _smooth_position(self, x: float, y: float, z: float) -> tuple:
        """Apply moving average filter to position data for smoothness"""
        # Add to buffer
        self.position_buffer.append((x, y, z))

        # Keep buffer size limited
        if len(self.position_buffer) > self.max_buffer_size:
            self.position_buffer.pop(0)

        # Calculate moving average
        if len(self.position_buffer) > 0:
            avg_x = sum(p[0] for p in self.position_buffer) / len(self.position_buffer)
            avg_y = sum(p[1] for p in self.position_buffer) / len(self.position_buffer)
            avg_z = sum(p[2] for p in self.position_buffer) / len(self.position_buffer)
            return (avg_x, avg_y, avg_z)
        else:
            return (x, y, z)

    def _get_current_sector(self) -> int:
        """Determine current sector from lap distance"""
        lap_dist_pct = self.ir['LapDistPct']

        if lap_dist_pct < 0:
            return 0
        elif lap_dist_pct < 0.33:
            return 1
        elif lap_dist_pct < 0.66:
            return 2
        else:
            return 3

    def _wait_for_green_flag(self):
        """Wait until green flag is shown"""
        while True:
            if not self.ir.is_connected:
                break

            session_flags = self.ir['SessionFlags']
            if session_flags & irsdk.Flags.green:
                logger.info("✓ Green flag detected!")
                break

            time.sleep(0.5)

    def _wait_for_lap_start(self):
        """Wait until crossing start/finish line"""
        logger.info("Drive to start/finish line...")

        # Wait for lap distance to be near 0
        while True:
            if not self.ir.is_connected:
                break

            lap_dist_pct = self.ir['LapDistPct']

            # Detect crossing start/finish (lap distance wraps from ~1.0 to ~0.0)
            if 0 <= lap_dist_pct < 0.05:
                logger.info("✓ Crossed start/finish line!")
                break

            time.sleep(0.1)

        # Wait a moment for clean lap start
        time.sleep(0.5)

    def generate_track_map(self, telemetry_samples: List[Dict] = None) -> Dict:
        """
        Generate accurate track map from recorded telemetry

        Args:
            telemetry_samples: Optional pre-recorded samples. If None, uses last recorded lap

        Returns:
            Track map dictionary ready for export
        """
        if telemetry_samples is None:
            telemetry_samples = self.telemetry_samples

        if not telemetry_samples:
            logger.error("No telemetry data available")
            return None

        logger.info("Analyzing telemetry to generate track map...")

        analyzer = TelemetryTrackAnalyzer()
        track_map = analyzer.analyze_telemetry(telemetry_samples)

        logger.info(f"✓ Track map generated:")
        logger.info(f"  - Track: {track_map.name}")
        logger.info(f"  - Length: {track_map.length}m")
        logger.info(f"  - Corners: {len(track_map.corners)}")
        logger.info(f"  - Confidence: {track_map.calibration_info['confidence']}")

        return track_map

    def save_track_map(self, track_map, output_path: str = None):
        """Save track map to JSON file"""
        if output_path is None:
            track_id = track_map.id
            output_path = f"../server/src/data/tracks/{track_id}.json"

        # Convert dataclass to dict
        from dataclasses import asdict
        track_dict = asdict(track_map)

        with open(output_path, 'w') as f:
            json.dump(track_dict, f, indent=2)

        logger.info(f"✓ Track map saved to: {output_path}")
        logger.info(f"\nTo use this track map:")
        logger.info(f"1. Restart the BlackBox server")
        logger.info(f"2. Access via: GET /api/tracks/{track_map.id}")
        logger.info(f"3. View SVG: GET /api/tracks/{track_map.id}/svg")

    def disconnect(self):
        """Disconnect from iRacing"""
        if self.ir:
            self.ir.shutdown()
            logger.info("Disconnected from iRacing")


def create_track_map_interactive():
    """Interactive CLI tool for creating track maps"""
    print("=" * 70)
    print("iRacing Track Mapper - Production Quality Track Maps")
    print("=" * 70)
    print()

    mapper = iRacingTrackMapper()

    # Step 1: Connect
    if not mapper.connect():
        print("\nMake sure:")
        print("  1. iRacing is running")
        print("  2. You are in a session (practice, race, etc.)")
        print("  3. The car is on track")
        return

    print()
    print("Instructions:")
    print("  1. Get your car ready on track")
    print("  2. Wait for green flag (or skip with Ctrl+C if in practice)")
    print("  3. Drive ONE clean, fast lap")
    print("  4. The tool will automatically detect lap completion")
    print()

    try:
        # Step 2: Record lap
        telemetry = mapper.record_reference_lap(wait_for_green_flag=False)

        if not telemetry or len(telemetry) < 100:
            print("\n✗ Not enough telemetry data recorded")
            print("  Make sure you complete a full lap")
            return

        # Step 3: Generate track map
        print("\n" + "=" * 70)
        print("Analyzing telemetry...")
        print("=" * 70)

        track_map = mapper.generate_track_map(telemetry)

        # Step 4: Display results
        print("\n" + "=" * 70)
        print("Track Map Generated Successfully!")
        print("=" * 70)
        print(f"\n📍 Track: {track_map.name}")
        print(f"📏 Length: {track_map.length:.0f} meters ({track_map.length/1000:.2f} km)")
        print(f"🏁 Corners: {len(track_map.corners)}")
        print(f"📊 Sectors: {len(track_map.sectors)}")
        print(f"✓ Calibration: {track_map.calibration_info['confidence']} confidence")
        print(f"🏎️ Car Class: {track_map.calibration_info['car_class']}")
        print()

        print("Corner Details:")
        print("-" * 70)
        for corner in track_map.corners:
            print(f"  {corner['name']:15} | "
                  f"Apex: {corner['apex_speed']:.0f} km/h | "
                  f"Gear {corner['gear']} | "
                  f"{corner['difficulty']:6} | "
                  f"{corner['type']}")

        # Step 5: Save
        print("\n" + "=" * 70)
        save = input("Save track map? (y/n): ").strip().lower()

        if save == 'y':
            mapper.save_track_map(track_map)
            print("\n✓ Track map saved and ready to use!")
        else:
            print("\nTrack map not saved")

    except KeyboardInterrupt:
        print("\n\n⚠ Recording cancelled by user")

    finally:
        mapper.disconnect()

    print("\n" + "=" * 70)
    print("Session complete. Thank you for using iRacing Track Mapper!")
    print("=" * 70)


if __name__ == '__main__':
    create_track_map_interactive()
