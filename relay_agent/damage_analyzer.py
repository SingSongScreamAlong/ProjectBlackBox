import logging
from typing import Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class DamageEstimate:
    aero_damage_pct: float  # 0-100%
    suspension_damage_pct: float  # 0-100%
    estimated_lap_delta: float  # seconds per lap
    affected_corners: list  # Corner types affected
    severity: str  # "MINOR", "MODERATE", "SEVERE"

class DamageAnalyzer:
    """
    Analyzes car damage and estimates performance impact.
    Uses telemetry patterns to detect and quantify damage.
    """
    
    def __init__(self):
        self.baseline_speed = {}  # Track section -> baseline speed
        self.damage_thresholds = {
            'aero': 0.05,  # 5% speed loss = aero damage
            'suspension': 0.03  # 3% handling degradation
        }
        
    def analyze_damage(self, telemetry, session_info) -> Optional[DamageEstimate]:
        """
        Analyze current telemetry for damage indicators.
        
        Args:
            telemetry: Current telemetry snapshot
            session_info: Session information
        """
        # Get damage flags from iRacing
        # In real implementation, we'd parse 'PlayerCarMyIncidentCount' 
        # and correlate with speed/handling changes
        
        # For now, create a placeholder that checks for incident count changes
        if isinstance(telemetry, dict):
            incident_count = telemetry.get('PlayerCarMyIncidentCount', 0)
        else:
            # TelemetrySnapshot doesn't have this field by default
            # Would need to add it to the dataclass
            incident_count = 0
        
        if incident_count == 0:
            return None
            
        # Estimate damage based on speed loss
        aero_damage = self._estimate_aero_damage(telemetry)
        suspension_damage = self._estimate_suspension_damage(telemetry)
        
        if aero_damage == 0 and suspension_damage == 0:
            return None
            
        # Calculate lap time delta
        lap_delta = self._calculate_lap_delta(aero_damage, suspension_damage)
        
        # Determine severity
        severity = self._determine_severity(aero_damage, suspension_damage)
        
        # Identify affected corners
        affected_corners = self._identify_affected_corners(aero_damage, suspension_damage)
        
        return DamageEstimate(
            aero_damage_pct=aero_damage,
            suspension_damage_pct=suspension_damage,
            estimated_lap_delta=lap_delta,
            affected_corners=affected_corners,
            severity=severity
        )
    
    def _estimate_aero_damage(self, telemetry) -> float:
        """
        Estimate aero damage from top speed loss.
        """
        # In production, compare current top speed to baseline
        # For now, return 0 (no damage detected)
        return 0.0
    
    def _estimate_suspension_damage(self, telemetry) -> float:
        """
        Estimate suspension damage from handling changes.
        """
        # In production, analyze steering input vs. car response
        # Look for increased understeer/oversteer
        return 0.0
    
    def _calculate_lap_delta(self, aero_dmg: float, susp_dmg: float) -> float:
        """
        Calculate estimated lap time loss from damage.
        
        Rough model:
        - 10% aero damage = ~0.3s per lap
        - 10% suspension damage = ~0.2s per lap
        """
        aero_delta = (aero_dmg / 10.0) * 0.3
        susp_delta = (susp_dmg / 10.0) * 0.2
        
        return aero_delta + susp_delta
    
    def _determine_severity(self, aero_dmg: float, susp_dmg: float) -> str:
        """Classify damage severity."""
        total_dmg = aero_dmg + susp_dmg
        
        if total_dmg < 10:
            return "MINOR"
        elif total_dmg < 30:
            return "MODERATE"
        else:
            return "SEVERE"
    
    def _identify_affected_corners(self, aero_dmg: float, susp_dmg: float) -> list:
        """Identify which corner types are affected."""
        affected = []
        
        if aero_dmg > 5:
            affected.append("high_speed")
        
        if susp_dmg > 5:
            affected.extend(["medium_speed", "low_speed"])
        
        return affected
    
    def generate_voice_alert(self, damage: DamageEstimate) -> str:
        """Generate natural language damage alert."""
        if damage.severity == "MINOR":
            return f"Minor damage detected. Losing about {damage.estimated_lap_delta:.1f} seconds per lap."
        elif damage.severity == "MODERATE":
            msg = f"Moderate damage. Aero at {100-damage.aero_damage_pct:.0f}%"
            if damage.suspension_damage_pct > 5:
                msg += f", suspension compromised"
            msg += f". Expect {damage.estimated_lap_delta:.1f}s slower laps."
            return msg
        else:  # SEVERE
            return f"Severe damage! Consider pitting. Losing {damage.estimated_lap_delta:.1f} seconds per lap."
