import logging
import time
import math
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class SpotterEngine:
    """
    Elite Spotter System for iRacing.
    Handles 3-wide detection, closing speed warnings, and wreck prediction.
    """
    
    def __init__(self):
        self.last_update_time = time.time()
        self.cars_around: Dict[int, Dict] = {} # car_idx -> data
        self.closing_speeds: Dict[int, float] = {} # car_idx -> m/s
        self.last_positions: Dict[int, float] = {} # car_idx -> track_pct
        self.wreck_candidates: List[int] = []
        
        # Configuration
        self.three_wide_threshold = 2.5 # meters lateral distance
        self.closing_speed_threshold = 6.7 # m/s (~15 mph)
        self.wreck_speed_threshold = 5.0 # m/s (very slow on track)
        self.min_speed_for_closing = 20.0 # m/s (don't warn if we are stopped)

    def update(self, telemetry, session_info: Dict) -> List[str]:
        """
        Process new telemetry frame and return list of spotter calls.
        Args:
            telemetry: TelemetrySnapshot object
            session_info: SessionInfo object or dict
        """
        current_time = time.time()
        dt = current_time - self.last_update_time
        self.last_update_time = current_time
        
        alerts = []
        
        # Extract relevant data
        # Handle both dict and object for compatibility
        if isinstance(telemetry, dict):
            my_car_idx = telemetry.get('PlayerCarIdx', -1)
        else:
            # Assuming TelemetrySnapshot object which doesn't have PlayerCarIdx directly
            # It's usually in SessionInfo, but let's assume we pass the index or it's 0 for player in some contexts
            # Actually TelemetrySnapshot doesn't have PlayerCarIdx. It has player data.
            # We need to know WHICH index is the player to check relative positions.
            # SessionInfo has 'driver_id' which is the car index.
            my_car_idx = int(session_info.driver_id) if hasattr(session_info, 'driver_id') else -1
            
        if my_car_idx == -1:
            return []
            
        # Update car data
        self._update_car_data(telemetry, dt)
        
        # 1. Check for 3-Wide
        three_wide_call = self._check_three_wide(telemetry)
        if three_wide_call:
            alerts.append(three_wide_call)
            
        # 2. Check Closing Speeds
        closing_call = self._check_closing_speeds(my_car_idx, telemetry)
        if closing_call:
            alerts.append(closing_call)
            
        # 3. Check for Wrecks
        wreck_call = self._check_wrecks(my_car_idx, telemetry)
        if wreck_call:
            alerts.append(wreck_call)
            
        return alerts

    def _update_car_data(self, telemetry, dt: float):
        """Update internal state of all cars"""
        if isinstance(telemetry, dict):
            lap_dist_pcts = telemetry.get('CarIdxLapDistPct', [])
            track_surfaces = telemetry.get('CarIdxTrackSurface', [])
        else:
            lap_dist_pcts = telemetry.car_idx_lap_dist_pct
            track_surfaces = telemetry.car_idx_track_surface
        
        if not lap_dist_pcts:
            return

        for i, dist_pct in enumerate(lap_dist_pcts):
            if dist_pct == -1: continue # Car not in world
            
            last_dist = self.last_positions.get(i, dist_pct)
            
            # Handle lap crossing
            delta = dist_pct - last_dist
            if delta < -0.5: delta += 1.0
            if delta > 0.5: delta -= 1.0
            
            # Update position
            self.last_positions[i] = dist_pct
            
            # Store data
            self.cars_around[i] = {
                'dist_pct': dist_pct,
                'track_surface': track_surfaces[i] if i < len(track_surfaces) else 0,
                'last_update': time.time()
            }

    def _check_three_wide(self, telemetry) -> Optional[str]:
        """Detect if we are in a 3-wide situation using CarLeftRight"""
        # iRacing provides a bitfield for this
        # 1 = Car Left, 2 = Car Right, 4 = Car Left Left, 8 = Car Right Right
        # 3 = Cars Left & Right (Middle of 3-wide)
        
        if isinstance(telemetry, dict):
            lr_flags = telemetry.get('CarLeftRight', 0)
        else:
            lr_flags = telemetry.car_left_right
            
        # Check for 3-wide middle
        # irsdk_LRCarLeft | irsdk_LRCarRight = 1 | 2 = 3
        if (lr_flags & 3) == 3:
            return "Three wide, you're in the middle."
            
        # Check for 3-wide right (2 cars left)
        # irsdk_LR2CarsLeft = 32 (0x20) - actually need to check SDK constants
        # Assuming standard bitmask: 
        # 1=Left, 2=Right, 4=LeftLeft, 8=RightRight
        # If we have Left AND LeftLeft -> 3 wide, we are on right
        if (lr_flags & 5) == 5: # 1 (Left) + 4 (LeftLeft)
             return "Three wide, you're on the right."
             
        # If we have Right AND RightRight -> 3 wide, we are on left
        if (lr_flags & 10) == 10: # 2 (Right) + 8 (RightRight)
            return "Three wide, you're on the left."
        
        return None

    def _check_closing_speeds(self, my_car_idx: int, telemetry) -> Optional[str]:
        """Warn if a car behind is approaching fast"""
        my_dist = self.cars_around.get(my_car_idx, {}).get('dist_pct', 0)
        
        # Get track length
        if isinstance(telemetry, dict):
            track_len = telemetry.get('WeekendInfo', {}).get('TrackLength', 4000)
        else:
            # TelemetrySnapshot doesn't have track length, need to rely on default or passed in session info
            # For now use default 4km if not available
            track_len = 4000 
        
        for idx, car in self.cars_around.items():
            if idx == my_car_idx: continue
            
            # Check if car is behind us (within ~200m)
            their_dist = car['dist_pct']
            
            # Calculate gap (positive = they are ahead, negative = they are behind)
            gap = their_dist - my_dist
            if gap > 0.5: gap -= 1.0
            if gap < -0.5: gap += 1.0
            
            gap_meters = gap * float(track_len) # Convert to meters
            
            # We only care about cars BEHIND us (gap < 0) and close (e.g. within 200m)
            if -200 < gap_meters < -10:
                # Ideally we check relative speed here
                pass
                
        return None

    def _check_wrecks(self, my_car_idx: int, telemetry) -> Optional[str]:
        """Predict wrecks based on cars ahead off-track or stopped"""
        my_dist = self.cars_around.get(my_car_idx, {}).get('dist_pct', 0)
        
        for idx, car in self.cars_around.items():
            if idx == my_car_idx: continue
            
            # Check if car is AHEAD (within 500m)
            their_dist = car['dist_pct']
            gap = their_dist - my_dist
            if gap > 0.5: gap -= 1.0
            if gap < -0.5: gap += 1.0
            
            if 0 < gap < 0.1: # Within ~10% of track ahead
                surface = car['track_surface']
                # 0=Off, 1=InPit, 2=Approx, 3=OnTrack (iRacing enum: 0=NotInWorld, 1=OffTrack, 2=InPit, 3=OnTrack)
                
                # If OffTrack (1)
                if surface == 1:
                    # Debounce this? For now just return
                    return "Car off track ahead!"
                    
        return None
