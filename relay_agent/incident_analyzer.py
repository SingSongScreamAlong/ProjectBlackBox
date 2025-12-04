"""
Incident Analysis System
Auto-detects incidents and analyzes WHY they happened with prevention advice
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IncidentType(Enum):
    """Types of incidents we can detect"""
    SPIN = "spin"
    LOCKUP = "lockup"
    OFF_TRACK = "off_track"
    CONTACT = "contact"
    OVERSTEER = "oversteer"
    UNDERSTEER = "understeer"
    LOSS_OF_CONTROL = "loss_of_control"


@dataclass
class Incident:
    """Detected incident with analysis"""
    # When and where
    timestamp: float
    lap: int
    distance: float
    corner_name: Optional[str]
    
    # What happened
    incident_type: IncidentType
    severity: str  # 'minor', 'moderate', 'severe'
    
    # Telemetry at incident
    speed_before: float
    speed_after: float
    speed_loss: float
    throttle: float
    brake: float
    steering: float
    g_lat: float
    g_long: float
    
    # Analysis
    root_cause: str
    contributing_factors: List[str]
    was_avoidable: bool
    
    # Actionable advice
    prevention_advice: str
    specific_technique_fix: str
    
    # Impact
    time_lost: float
    positions_lost: int
    incident_points: int  # iRacing penalty points


class IncidentDetector:
    """Detects and analyzes incidents from telemetry"""
    
    def __init__(self):
        # Detection thresholds
        self.spin_rotation_threshold = 45  # degrees
        self.lockup_speed_loss_threshold = 15  # km/h in 0.5s
        self.contact_damage_threshold = 0.01
        
    def analyze_session(self, 
                       telemetry: List[Dict],
                       track_corners: Optional[List[Dict]] = None) -> List[Incident]:
        """
        Analyze entire session for incidents
        
        Args:
            telemetry: Session telemetry data
            track_corners: Optional corner definitions for context
            
        Returns:
            List of detected incidents with analysis
        """
        logger.info(f"Analyzing {len(telemetry)} samples for incidents")
        
        incidents = []
        
        # Scan through telemetry
        i = 0
        while i < len(telemetry) - 10:
            incident = self._detect_incident_at_index(telemetry, i, track_corners)
            
            if incident:
                incidents.append(incident)
                logger.info(f"Detected {incident.incident_type.value} at lap {incident.lap}")
                # Skip ahead past this incident
                i += 20
            else:
                i += 1
        
        logger.info(f"Found {len(incidents)} incidents")
        return incidents
    
    def _detect_incident_at_index(self,
                                  telemetry: List[Dict],
                                  idx: int,
                                  track_corners: Optional[List[Dict]]) -> Optional[Incident]:
        """Check if incident occurred at this index"""
        
        sample = telemetry[idx]
        
        # Get samples before and after
        samples_before = telemetry[max(0, idx-5):idx]
        samples_after = telemetry[idx:min(idx+10, len(telemetry))]
        
        # Check for spin (sudden rotation)
        spin = self._detect_spin(sample, samples_before, samples_after)
        if spin:
            return self._analyze_spin(telemetry, idx, track_corners)
        
        # Check for lockup (sudden speed loss with heavy braking)
        lockup = self._detect_lockup(sample, samples_before, samples_after)
        if lockup:
            return self._analyze_lockup(telemetry, idx, track_corners)
        
        # Check for off-track
        off_track = self._detect_off_track(sample, samples_before)
        if off_track:
            return self._analyze_off_track(telemetry, idx, track_corners)
        
        # Check for loss of control (high G-forces + speed loss)
        loss_of_control = self._detect_loss_of_control(sample, samples_before, samples_after)
        if loss_of_control:
            return self._analyze_loss_of_control(telemetry, idx, track_corners)
        
        return None
    
    def _detect_spin(self, sample: Dict, before: List[Dict], after: List[Dict]) -> bool:
        """Detect spin from rotation and speed loss"""
        if not before or not after:
            return False
        
        # Check for sudden speed loss
        speed_before = np.mean([s.get('speed', 0) for s in before])
        speed_after = np.mean([s.get('speed', 0) for s in after])
        speed_loss = speed_before - speed_after
        
        # Check for high lateral G-forces (car rotating)
        g_lat = abs(sample.get('g_lat', 0))
        
        # Spin indicators:
        # - Significant speed loss (>30 km/h)
        # - High lateral G (>2.5)
        # - Not braking heavily (rules out lockup)
        if (speed_loss > 30 and 
            g_lat > 2.5 and 
            sample.get('brake', 0) < 0.8):
            return True
        
        return False
    
    def _detect_lockup(self, sample: Dict, before: List[Dict], after: List[Dict]) -> bool:
        """Detect wheel lockup from braking and speed loss"""
        if not before or not after:
            return False
        
        # Heavy braking
        if sample.get('brake', 0) < 0.9:
            return False
        
        # Sudden speed loss
        speed_before = np.mean([s.get('speed', 0) for s in before[-3:]])
        speed_current = sample.get('speed', 0)
        speed_loss_rate = (speed_before - speed_current) / 0.3  # Over 0.3s
        
        # Lockup indicators:
        # - Full braking (>90%)
        # - Rapid speed loss (>50 km/h per second)
        # - High longitudinal G (>3.0)
        if (sample.get('brake', 0) > 0.9 and
            speed_loss_rate > 50 and
            abs(sample.get('g_long', 0)) > 3.0):
            return True
        
        return False
    
    def _detect_off_track(self, sample: Dict, before: List[Dict]) -> bool:
        """Detect off-track excursion"""
        # Check if track surface changed (would need track surface data)
        # For now, detect from sudden speed loss + no braking
        
        if not before:
            return False
        
        speed_before = np.mean([s.get('speed', 0) for s in before])
        speed_loss = speed_before - sample.get('speed', 0)
        
        # Off-track indicators:
        # - Speed loss without braking
        # - Could add: track surface type check
        if (speed_loss > 20 and 
            sample.get('brake', 0) < 0.3):
            return True
        
        return False
    
    def _detect_loss_of_control(self, sample: Dict, before: List[Dict], after: List[Dict]) -> bool:
        """Detect general loss of control"""
        if not before or not after:
            return False
        
        # High G-forces in multiple directions
        g_lat = abs(sample.get('g_lat', 0))
        g_long = abs(sample.get('g_long', 0))
        
        # Erratic steering
        steering = abs(sample.get('steering', 0))
        
        # Speed instability
        speeds = [s.get('speed', 0) for s in before + [sample] + after]
        speed_variance = np.std(speeds) if speeds else 0
        
        if (g_lat > 2.0 and g_long > 2.0 and 
            steering > 0.8 and 
            speed_variance > 15):
            return True
        
        return False
    
    def _analyze_spin(self, telemetry: List[Dict], idx: int, 
                     track_corners: Optional[List[Dict]]) -> Incident:
        """Analyze why spin occurred"""
        
        sample = telemetry[idx]
        samples_before = telemetry[max(0, idx-10):idx]
        
        # Get telemetry leading up to spin
        throttle_before = [s.get('throttle', 0) for s in samples_before[-5:]]
        avg_throttle = np.mean(throttle_before) if throttle_before else 0
        
        # Determine root cause
        root_cause = "Unknown"
        contributing_factors = []
        prevention_advice = ""
        technique_fix = ""
        
        # Excessive throttle application
        if avg_throttle > 0.8 and sample.get('throttle', 0) > 0.9:
            root_cause = "Excessive throttle application"
            contributing_factors.append("Too aggressive on throttle")
            prevention_advice = f"Reduce throttle application to {int(avg_throttle * 70)}% initially, then build up gradually"
            technique_fix = "Apply throttle progressively: 50% → 70% → 100% over 0.5 seconds"
        
        # Cold tires
        tire_temp = sample.get('tire_temp_avg', 80)
        if tire_temp < 70:
            contributing_factors.append("Cold tires (low grip)")
            prevention_advice += ". Warm tires with gentle weaving before pushing"
        
        # Oversteer setup
        if sample.get('g_lat', 0) > 2.0:
            contributing_factors.append("High lateral load (oversteer)")
            technique_fix += ". Consider rear wing +1 or rear ARB -1"
        
        # Find corner context
        corner_name = self._find_corner_at_distance(
            sample.get('distance', 0), 
            track_corners
        )
        
        # Calculate impact
        speed_before = np.mean([s.get('speed', 0) for s in samples_before])
        speed_after = sample.get('speed', 0)
        time_lost = self._estimate_time_lost(speed_before, speed_after, 50)  # 50m to recover
        
        return Incident(
            timestamp=sample.get('timestamp', 0),
            lap=sample.get('lap', 0),
            distance=sample.get('distance', 0),
            corner_name=corner_name,
            incident_type=IncidentType.SPIN,
            severity='severe' if time_lost > 3 else 'moderate',
            speed_before=speed_before,
            speed_after=speed_after,
            speed_loss=speed_before - speed_after,
            throttle=sample.get('throttle', 0),
            brake=sample.get('brake', 0),
            steering=sample.get('steering', 0),
            g_lat=sample.get('g_lat', 0),
            g_long=sample.get('g_long', 0),
            root_cause=root_cause,
            contributing_factors=contributing_factors,
            was_avoidable=True,
            prevention_advice=prevention_advice,
            specific_technique_fix=technique_fix,
            time_lost=time_lost,
            positions_lost=self._estimate_positions_lost(time_lost),
            incident_points=4  # iRacing 4x for spin
        )
    
    def _analyze_lockup(self, telemetry: List[Dict], idx: int,
                       track_corners: Optional[List[Dict]]) -> Incident:
        """Analyze why lockup occurred"""
        
        sample = telemetry[idx]
        samples_before = telemetry[max(0, idx-5):idx]
        
        # Determine cause
        root_cause = "Brake application too aggressive"
        contributing_factors = []
        prevention_advice = ""
        technique_fix = ""
        
        # Check brake application rate
        if samples_before:
            brake_increase = sample.get('brake', 0) - samples_before[-1].get('brake', 0)
            if brake_increase > 0.5:  # Went from <50% to 100% too fast
                root_cause = "Brake application too sudden"
                prevention_advice = "Apply brakes progressively: 50% → 80% → 100% over 0.3 seconds"
                technique_fix = "Squeeze brakes, don't stab them"
        
        # Cold brakes
        brake_temp = sample.get('brake_temp_avg', 400)
        if brake_temp < 300:
            contributing_factors.append("Cold brakes (reduced grip)")
            prevention_advice += ". Warm brakes with light applications before heavy braking zone"
        
        # Downhill braking
        if sample.get('pos_z', 0) < samples_before[0].get('pos_z', 0):
            contributing_factors.append("Downhill section (weight transfer)")
            technique_fix += ". Brake earlier on downhill sections"
        
        corner_name = self._find_corner_at_distance(sample.get('distance', 0), track_corners)
        
        speed_before = np.mean([s.get('speed', 0) for s in samples_before])
        speed_after = sample.get('speed', 0)
        time_lost = self._estimate_time_lost(speed_before, speed_after, 30)
        
        return Incident(
            timestamp=sample.get('timestamp', 0),
            lap=sample.get('lap', 0),
            distance=sample.get('distance', 0),
            corner_name=corner_name,
            incident_type=IncidentType.LOCKUP,
            severity='minor' if time_lost < 0.5 else 'moderate',
            speed_before=speed_before,
            speed_after=speed_after,
            speed_loss=speed_before - speed_after,
            throttle=sample.get('throttle', 0),
            brake=sample.get('brake', 0),
            steering=sample.get('steering', 0),
            g_lat=sample.get('g_lat', 0),
            g_long=sample.get('g_long', 0),
            root_cause=root_cause,
            contributing_factors=contributing_factors,
            was_avoidable=True,
            prevention_advice=prevention_advice,
            specific_technique_fix=technique_fix,
            time_lost=time_lost,
            positions_lost=self._estimate_positions_lost(time_lost),
            incident_points=0  # Lockups don't get iRacing penalties
        )
    
    def _analyze_off_track(self, telemetry: List[Dict], idx: int,
                          track_corners: Optional[List[Dict]]) -> Incident:
        """Analyze off-track excursion"""
        
        sample = telemetry[idx]
        samples_before = telemetry[max(0, idx-10):idx]
        
        root_cause = "Exceeded track limits"
        contributing_factors = []
        prevention_advice = "Stay within track limits"
        technique_fix = "Use visual reference points for track edges"
        
        # Check if it was from overspeed
        speed = sample.get('speed', 0)
        if speed > 150:
            root_cause = "Corner entry speed too high"
            prevention_advice = "Reduce entry speed by 5-10 km/h"
            technique_fix = "Brake 5-10m earlier"
        
        corner_name = self._find_corner_at_distance(sample.get('distance', 0), track_corners)
        
        speed_before = np.mean([s.get('speed', 0) for s in samples_before])
        time_lost = 1.5  # Typical off-track penalty
        
        return Incident(
            timestamp=sample.get('timestamp', 0),
            lap=sample.get('lap', 0),
            distance=sample.get('distance', 0),
            corner_name=corner_name,
            incident_type=IncidentType.OFF_TRACK,
            severity='moderate',
            speed_before=speed_before,
            speed_after=sample.get('speed', 0),
            speed_loss=speed_before - sample.get('speed', 0),
            throttle=sample.get('throttle', 0),
            brake=sample.get('brake', 0),
            steering=sample.get('steering', 0),
            g_lat=sample.get('g_lat', 0),
            g_long=sample.get('g_long', 0),
            root_cause=root_cause,
            contributing_factors=contributing_factors,
            was_avoidable=True,
            prevention_advice=prevention_advice,
            specific_technique_fix=technique_fix,
            time_lost=time_lost,
            positions_lost=self._estimate_positions_lost(time_lost),
            incident_points=1  # iRacing 1x for off-track
        )
    
    def _analyze_loss_of_control(self, telemetry: List[Dict], idx: int,
                                 track_corners: Optional[List[Dict]]) -> Incident:
        """Analyze general loss of control"""
        
        sample = telemetry[idx]
        
        # Generic analysis for unclassified incidents
        corner_name = self._find_corner_at_distance(sample.get('distance', 0), track_corners)
        
        return Incident(
            timestamp=sample.get('timestamp', 0),
            lap=sample.get('lap', 0),
            distance=sample.get('distance', 0),
            corner_name=corner_name,
            incident_type=IncidentType.LOSS_OF_CONTROL,
            severity='moderate',
            speed_before=sample.get('speed', 0),
            speed_after=sample.get('speed', 0),
            speed_loss=0,
            throttle=sample.get('throttle', 0),
            brake=sample.get('brake', 0),
            steering=sample.get('steering', 0),
            g_lat=sample.get('g_lat', 0),
            g_long=sample.get('g_long', 0),
            root_cause="Loss of control",
            contributing_factors=["High G-forces", "Erratic inputs"],
            was_avoidable=True,
            prevention_advice="Smooth inputs, progressive throttle/brake",
            specific_technique_fix="Practice consistency in this corner",
            time_lost=1.0,
            positions_lost=0,
            incident_points=2
        )
    
    def _find_corner_at_distance(self, distance: float, 
                                 corners: Optional[List[Dict]]) -> Optional[str]:
        """Find which corner this distance is in"""
        if not corners:
            return None
        
        for corner in corners:
            brake_dist = corner.get('braking_point', {}).get('distance', 0)
            exit_dist = corner.get('exit_point', {}).get('distance', 0)
            
            if brake_dist <= distance <= exit_dist:
                return corner.get('name', f"Turn {corner.get('number', '?')}")
        
        return None
    
    def _estimate_time_lost(self, speed_before: float, speed_after: float, 
                           recovery_distance: float) -> float:
        """Estimate time lost from incident"""
        # Simple physics: time = distance / avg_speed
        avg_speed_normal = speed_before / 3.6  # km/h to m/s
        avg_speed_incident = (speed_before + speed_after) / 2 / 3.6
        
        time_normal = recovery_distance / avg_speed_normal if avg_speed_normal > 0 else 0
        time_incident = recovery_distance / avg_speed_incident if avg_speed_incident > 0 else 0
        
        return max(0, time_incident - time_normal)
    
    def _estimate_positions_lost(self, time_lost: float) -> int:
        """Estimate positions lost based on time"""
        # Rough estimate: 1 second = 1 position in close racing
        return int(time_lost)
    
    def generate_incident_report(self, incidents: List[Incident]) -> str:
        """Generate human-readable incident report"""
        
        if not incidents:
            return "✅ Clean session - No incidents detected!"
        
        report = []
        report.append("=" * 70)
        report.append("INCIDENT ANALYSIS REPORT")
        report.append("=" * 70)
        report.append(f"\nTotal Incidents: {len(incidents)}")
        report.append(f"Total Time Lost: {sum(i.time_lost for i in incidents):.1f}s")
        report.append(f"Total Incident Points: {sum(i.incident_points for i in incidents)}x")
        report.append("")
        
        for i, incident in enumerate(incidents, 1):
            severity_icon = "🔴" if incident.severity == 'severe' else \
                          "🟡" if incident.severity == 'moderate' else "🟢"
            
            report.append(f"\n{severity_icon} Incident #{i}: {incident.incident_type.value.upper()}")
            report.append(f"   Lap {incident.lap}, {incident.corner_name or 'Unknown location'}")
            report.append(f"   Speed: {incident.speed_before:.0f} → {incident.speed_after:.0f} km/h")
            report.append(f"   Time Lost: {incident.time_lost:.2f}s")
            report.append(f"   Penalty: {incident.incident_points}x")
            report.append(f"\n   ROOT CAUSE: {incident.root_cause}")
            if incident.contributing_factors:
                report.append(f"   Contributing: {', '.join(incident.contributing_factors)}")
            report.append(f"\n   ⚠️  PREVENTION: {incident.prevention_advice}")
            report.append(f"   🔧 TECHNIQUE: {incident.specific_technique_fix}")
            report.append(f"   {'✅ Avoidable' if incident.was_avoidable else '❌ Unavoidable'}")
        
        return "\n".join(report)


# Example usage
if __name__ == '__main__':
    print("Incident Analysis System")
    print("=" * 70)
    print("\nAuto-detects and analyzes:")
    print("  • Spins - WHY did you spin?")
    print("  • Lockups - WHY did wheels lock?")
    print("  • Off-tracks - WHY did you go off?")
    print("  • Loss of control - What went wrong?")
    print("\nProvides specific prevention advice:")
    print("  'Reduce throttle to 70% initially, build up over 0.5s'")
    print("  NOT: 'Be smoother'")
