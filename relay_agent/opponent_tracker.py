import logging
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class OpponentProfile:
    car_idx: int
    driver_name: str = "Unknown"
    aggression_score: float = 0.0 # 0.0 to 10.0
    mistake_count: int = 0
    clean_laps: int = 0
    last_lap_time: float = 0.0
    
    # Internal state
    last_dist_pct: float = 0.0
    last_update: float = 0.0
    incident_history: List[float] = field(default_factory=list) # Timestamps

class OpponentTracker:
    """
    Tracks opponent behavior to build psychological profiles.
    Predicts aggression and warns of dangerous drivers.
    """
    
    def __init__(self):
        self.opponents: Dict[int, OpponentProfile] = {}
        self.last_check_time = time.time()
        
        # Configuration
        self.aggression_decay = 0.99 # Decay score over time
        self.mistake_threshold = 3 # Warn after this many mistakes
        self.high_aggression_threshold = 7.0

    def update(self, telemetry, session_info) -> List[str]:
        """
        Update opponent stats and return predictive alerts.
        """
        current_time = time.time()
        dt = current_time - self.last_check_time
        
        # Only run logic every 1 second to save CPU
        if dt < 1.0:
            return []
            
        self.last_check_time = current_time
        alerts = []
        
        # Update roster from session info
        self._update_roster(session_info)
        
        # Analyze behavior
        for idx, profile in self.opponents.items():
            # Skip player
            if isinstance(telemetry, dict):
                player_idx = telemetry.get('PlayerCarIdx', -1)
            else:
                player_idx = int(session_info.driver_id) if hasattr(session_info, 'driver_id') else -1
                
            if idx == player_idx:
                continue
                
            # Update metrics
            self._analyze_behavior(profile, telemetry)
            
            # Generate alerts
            alert = self._generate_alert(profile, player_idx, telemetry)
            if alert:
                alerts.append(alert)
                
        return alerts

    def _update_roster(self, session_info):
        """Ensure all drivers are tracked"""
        if not session_info: return
        
        # Handle both object and dict
        competitors = []
        if hasattr(session_info, 'competitors'):
            competitors = session_info.competitors
        elif isinstance(session_info, dict):
            competitors = session_info.get('competitors', [])
            
        for driver in competitors:
            try:
                idx = int(driver.get('driver_id', -1))
                if idx != -1 and idx not in self.opponents:
                    self.opponents[idx] = OpponentProfile(
                        car_idx=idx,
                        driver_name=driver.get('driver_name', f"Car {idx}")
                    )
            except:
                pass

    def _analyze_behavior(self, profile: OpponentProfile, telemetry):
        """Analyze telemetry for aggression and mistakes"""
        # Get car data
        if isinstance(telemetry, dict):
            surfaces = telemetry.get('CarIdxTrackSurface', [])
        else:
            surfaces = telemetry.car_idx_track_surface
            
        if profile.car_idx >= len(surfaces):
            return
            
        surface = surfaces[profile.car_idx]
        
        # Detect mistakes (OffTrack or Lost Control)
        # 0=NotInWorld, 1=OffTrack, 2=InPit, 3=OnTrack
        if surface == 1: # OffTrack
            # Debounce: only count if 5s passed since last incident
            if not profile.incident_history or (time.time() - profile.incident_history[-1] > 5.0):
                profile.mistake_count += 1
                profile.incident_history.append(time.time())
                # Going off track increases aggression/erratic score
                profile.aggression_score += 1.0

    def _generate_alert(self, profile: OpponentProfile, player_idx: int, telemetry) -> Optional[str]:
        """Generate alert if dangerous opponent is close"""
        # Check proximity
        if isinstance(telemetry, dict):
            my_dist = telemetry.get('CarIdxLapDistPct', [])[player_idx]
            their_dist = telemetry.get('CarIdxLapDistPct', [])[profile.car_idx]
        else:
            my_dist = telemetry.car_idx_lap_dist_pct[player_idx]
            their_dist = telemetry.car_idx_lap_dist_pct[profile.car_idx]
            
        # Calculate gap
        gap = their_dist - my_dist
        if gap > 0.5: gap -= 1.0
        if gap < -0.5: gap += 1.0
        
        # If they are close (within 5% of track)
        if abs(gap) < 0.05:
            # High Aggression Warning
            if profile.aggression_score > self.high_aggression_threshold:
                # Only warn once per minute
                if not hasattr(profile, 'last_warn_time') or (time.time() - profile.last_warn_time > 60):
                    profile.last_warn_time = time.time()
                    return f"Careful with {profile.driver_name}, they are driving aggressively."
            
            # High Mistake Warning
            if profile.mistake_count >= self.mistake_threshold:
                if not hasattr(profile, 'last_mistake_warn') or (time.time() - profile.last_mistake_warn > 60):
                    profile.last_mistake_warn = time.time()
                    return f"Watch out for {profile.driver_name}, they've gone off {profile.mistake_count} times."
                    
        return None
