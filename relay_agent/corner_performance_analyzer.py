"""
Corner-by-Corner Performance Analyzer
Shows drivers EXACTLY where they're losing time with actionable feedback
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CornerPerformance:
    """Performance analysis for a single corner"""
    corner_number: int
    corner_name: str
    
    # Speed metrics
    entry_speed: float
    apex_speed: float
    exit_speed: float
    min_speed: float
    
    # Comparison to reference
    entry_speed_delta: float  # vs reference
    apex_speed_delta: float
    exit_speed_delta: float
    time_delta: float  # Time lost/gained in this corner
    
    # Technique analysis
    brake_point_distance: float  # Distance from corner
    brake_point_delta: float  # vs reference (negative = too early)
    throttle_application_point: float
    throttle_delta: float  # vs reference
    
    # G-forces
    peak_lateral_g: float
    peak_longitudinal_g: float
    
    # Rating
    rating: str  # 'excellent', 'good', 'fair', 'poor'
    time_loss_category: str  # 'major', 'moderate', 'minor', 'none', 'gain'
    
    # Actionable advice
    primary_issue: Optional[str]
    specific_advice: str
    target_improvement: float  # Potential time gain


class CornerByCornerAnalyzer:
    """Analyzes lap performance corner by corner"""
    
    def __init__(self):
        self.corners_cache = {}
    
    def analyze_lap(self, 
                    lap_telemetry: List[Dict],
                    reference_telemetry: List[Dict],
                    track_corners: List[Dict]) -> List[CornerPerformance]:
        """
        Analyze a lap corner by corner vs reference
        
        Args:
            lap_telemetry: Your lap telemetry data
            reference_telemetry: Reference lap (personal best, class leader, etc.)
            track_corners: Corner definitions from track_analyzer
            
        Returns:
            List of CornerPerformance objects with actionable feedback
        """
        logger.info(f"Analyzing {len(track_corners)} corners")
        
        corner_performances = []
        
        for corner in track_corners:
            performance = self._analyze_single_corner(
                lap_telemetry,
                reference_telemetry,
                corner
            )
            
            if performance:
                corner_performances.append(performance)
        
        # Sort by time loss (worst first)
        corner_performances.sort(key=lambda x: x.time_delta)
        
        return corner_performances
    
    def _analyze_single_corner(self,
                               lap_telemetry: List[Dict],
                               reference_telemetry: List[Dict],
                               corner: Dict) -> Optional[CornerPerformance]:
        """Analyze performance in a single corner"""
        
        # Extract corner boundaries
        brake_point_dist = corner['braking_point']['distance']
        apex_dist = corner['apex']['distance']
        exit_dist = corner['exit_point']['distance']
        
        # Find telemetry samples for this corner
        your_brake = self._find_sample_at_distance(lap_telemetry, brake_point_dist)
        your_apex = self._find_sample_at_distance(lap_telemetry, apex_dist)
        your_exit = self._find_sample_at_distance(lap_telemetry, exit_dist)
        
        ref_brake = self._find_sample_at_distance(reference_telemetry, brake_point_dist)
        ref_apex = self._find_sample_at_distance(reference_telemetry, apex_dist)
        ref_exit = self._find_sample_at_distance(reference_telemetry, exit_dist)
        
        if not all([your_brake, your_apex, your_exit, ref_brake, ref_apex, ref_exit]):
            return None
        
        # Calculate actual brake point (where brake first applied)
        your_actual_brake_point = self._find_brake_application_point(
            lap_telemetry, brake_point_dist
        )
        ref_actual_brake_point = self._find_brake_application_point(
            reference_telemetry, brake_point_dist
        )
        
        # Calculate throttle application point
        your_throttle_point = self._find_throttle_application_point(
            lap_telemetry, apex_dist
        )
        ref_throttle_point = self._find_throttle_application_point(
            reference_telemetry, apex_dist
        )
        
        # Calculate time in corner
        your_time = self._calculate_corner_time(lap_telemetry, brake_point_dist, exit_dist)
        ref_time = self._calculate_corner_time(reference_telemetry, brake_point_dist, exit_dist)
        time_delta = your_time - ref_time
        
        # Speed deltas
        entry_delta = your_brake['speed'] - ref_brake['speed']
        apex_delta = your_apex['speed'] - ref_apex['speed']
        exit_delta = your_exit['speed'] - ref_exit['speed']
        
        # Brake point delta (negative = braking too early)
        brake_point_delta = your_actual_brake_point - ref_actual_brake_point
        
        # Throttle point delta (negative = too late on throttle)
        throttle_delta = your_throttle_point - ref_throttle_point
        
        # Find peak G-forces
        corner_samples = self._get_corner_samples(lap_telemetry, brake_point_dist, exit_dist)
        peak_lat_g = max([abs(s.get('g_lat', 0)) for s in corner_samples]) if corner_samples else 0
        peak_long_g = max([abs(s.get('g_long', 0)) for s in corner_samples]) if corner_samples else 0
        
        # Analyze and generate advice
        rating, category, issue, advice, target = self._generate_advice(
            time_delta=time_delta,
            entry_delta=entry_delta,
            apex_delta=apex_delta,
            exit_delta=exit_delta,
            brake_point_delta=brake_point_delta,
            throttle_delta=throttle_delta,
            corner_name=corner['name']
        )
        
        return CornerPerformance(
            corner_number=corner['number'],
            corner_name=corner['name'],
            entry_speed=your_brake['speed'],
            apex_speed=your_apex['speed'],
            exit_speed=your_exit['speed'],
            min_speed=min([s['speed'] for s in corner_samples]) if corner_samples else your_apex['speed'],
            entry_speed_delta=entry_delta,
            apex_speed_delta=apex_delta,
            exit_speed_delta=exit_delta,
            time_delta=time_delta,
            brake_point_distance=your_actual_brake_point,
            brake_point_delta=brake_point_delta,
            throttle_application_point=your_throttle_point,
            throttle_delta=throttle_delta,
            peak_lateral_g=peak_lat_g,
            peak_longitudinal_g=peak_long_g,
            rating=rating,
            time_loss_category=category,
            primary_issue=issue,
            specific_advice=advice,
            target_improvement=target
        )
    
    def _find_sample_at_distance(self, telemetry: List[Dict], distance: float) -> Optional[Dict]:
        """Find telemetry sample closest to given distance"""
        if not telemetry:
            return None
        
        closest = min(telemetry, key=lambda x: abs(x.get('distance', 0) - distance))
        return closest
    
    def _find_brake_application_point(self, telemetry: List[Dict], 
                                     corner_distance: float) -> float:
        """Find where driver first applied brakes before corner"""
        # Look backwards from corner
        for sample in reversed(telemetry):
            if sample.get('distance', 0) < corner_distance - 500:
                break
            if sample.get('brake', 0) > 0.1:
                return sample.get('distance', corner_distance)
        return corner_distance
    
    def _find_throttle_application_point(self, telemetry: List[Dict],
                                        apex_distance: float) -> float:
        """Find where driver first applied throttle after apex"""
        for sample in telemetry:
            if sample.get('distance', 0) > apex_distance:
                if sample.get('throttle', 0) > 0.5:
                    return sample.get('distance', apex_distance)
        return apex_distance
    
    def _calculate_corner_time(self, telemetry: List[Dict],
                               start_dist: float, end_dist: float) -> float:
        """Calculate time spent in corner"""
        start_sample = self._find_sample_at_distance(telemetry, start_dist)
        end_sample = self._find_sample_at_distance(telemetry, end_dist)
        
        if not start_sample or not end_sample:
            return 0.0
        
        return (end_sample.get('timestamp', 0) - start_sample.get('timestamp', 0)) / 1000.0
    
    def _get_corner_samples(self, telemetry: List[Dict],
                           start_dist: float, end_dist: float) -> List[Dict]:
        """Get all telemetry samples within corner"""
        return [s for s in telemetry 
                if start_dist <= s.get('distance', 0) <= end_dist]
    
    def _generate_advice(self, 
                        time_delta: float,
                        entry_delta: float,
                        apex_delta: float,
                        exit_delta: float,
                        brake_point_delta: float,
                        throttle_delta: float,
                        corner_name: str) -> Tuple[str, str, Optional[str], str, float]:
        """
        Generate actionable advice based on performance
        
        Returns: (rating, category, primary_issue, specific_advice, target_improvement)
        """
        
        # Determine category
        if time_delta < -0.05:
            category = 'gain'
            rating = 'excellent'
        elif time_delta < 0.05:
            category = 'none'
            rating = 'good'
        elif time_delta < 0.15:
            category = 'minor'
            rating = 'fair'
        elif time_delta < 0.3:
            category = 'moderate'
            rating = 'fair'
        else:
            category = 'major'
            rating = 'poor'
        
        # Identify primary issue and generate specific advice
        issues = []
        
        # Brake point analysis
        if brake_point_delta < -10:  # Braking too early
            issues.append({
                'severity': abs(brake_point_delta) / 10,
                'issue': 'braking_early',
                'advice': f"Brake {abs(brake_point_delta):.0f}m later. Look for a reference point closer to the corner."
            })
        elif brake_point_delta > 10:  # Braking too late
            issues.append({
                'severity': brake_point_delta / 10,
                'issue': 'braking_late',
                'advice': f"Brake {brake_point_delta:.0f}m earlier. You're overshooting the optimal line."
            })
        
        # Entry speed analysis
        if entry_delta < -5:  # Too slow on entry
            issues.append({
                'severity': abs(entry_delta) / 5,
                'issue': 'slow_entry',
                'advice': f"Carry {abs(entry_delta):.1f} km/h more into the corner. Build confidence in the braking zone."
            })
        
        # Apex speed analysis
        if apex_delta < -3:  # Too slow at apex
            issues.append({
                'severity': abs(apex_delta) / 3,
                'issue': 'slow_apex',
                'advice': f"Carry {abs(apex_delta):.1f} km/h more through the apex. Smoother steering input will help."
            })
        
        # Exit speed analysis  
        if exit_delta < -5:  # Too slow on exit
            issues.append({
                'severity': abs(exit_delta) / 5,
                'issue': 'slow_exit',
                'advice': f"Gain {abs(exit_delta):.1f} km/h on exit. Apply throttle {abs(throttle_delta):.1f}m earlier."
            })
        
        # Throttle application
        if throttle_delta < -5:  # Too late on throttle
            issues.append({
                'severity': abs(throttle_delta) / 5,
                'issue': 'late_throttle',
                'advice': f"Apply throttle {abs(throttle_delta):.0f}m earlier. Trust the car's grip."
            })
        
        # Select primary issue (highest severity)
        if issues:
            primary = max(issues, key=lambda x: x['severity'])
            primary_issue = primary['issue']
            specific_advice = primary['advice']
        else:
            primary_issue = None
            if category == 'gain':
                specific_advice = f"Excellent! You're {abs(time_delta):.3f}s faster here than reference."
            else:
                specific_advice = f"Good execution. Maintain this approach."
        
        # Calculate target improvement (potential time gain)
        target_improvement = max(0, time_delta)
        
        return rating, category, primary_issue, specific_advice, target_improvement
    
    def generate_summary_report(self, performances: List[CornerPerformance]) -> str:
        """Generate human-readable summary report"""
        
        total_time_loss = sum(p.time_delta for p in performances if p.time_delta > 0)
        total_time_gain = abs(sum(p.time_delta for p in performances if p.time_delta < 0))
        
        # Find biggest issues
        major_losses = [p for p in performances if p.time_loss_category in ['major', 'moderate']]
        
        report = []
        report.append("=" * 70)
        report.append("CORNER-BY-CORNER PERFORMANCE ANALYSIS")
        report.append("=" * 70)
        report.append("")
        report.append(f"Total Time Lost: {total_time_loss:.3f}s")
        report.append(f"Total Time Gained: {total_time_gain:.3f}s")
        report.append(f"Net Delta: {(total_time_loss - total_time_gain):.3f}s")
        report.append("")
        
        if major_losses:
            report.append("🔴 PRIORITY CORNERS (Focus Here):")
            report.append("-" * 70)
            for p in major_losses[:5]:  # Top 5 worst corners
                report.append(f"\n{p.corner_name}: {p.time_delta:+.3f}s")
                report.append(f"  Issue: {p.primary_issue or 'Multiple factors'}")
                report.append(f"  Action: {p.specific_advice}")
                report.append(f"  Potential Gain: {p.target_improvement:.3f}s")
        
        report.append("")
        report.append("=" * 70)
        report.append("DETAILED CORNER BREAKDOWN:")
        report.append("=" * 70)
        
        for p in performances:
            icon = "🔴" if p.time_loss_category in ['major', 'moderate'] else \
                   "🟡" if p.time_loss_category == 'minor' else \
                   "🟢"
            
            report.append(f"\n{icon} {p.corner_name}: {p.time_delta:+.3f}s ({p.rating})")
            report.append(f"   Entry: {p.entry_speed:.1f} km/h ({p.entry_speed_delta:+.1f})")
            report.append(f"   Apex:  {p.apex_speed:.1f} km/h ({p.apex_speed_delta:+.1f})")
            report.append(f"   Exit:  {p.exit_speed:.1f} km/h ({p.exit_speed_delta:+.1f})")
            report.append(f"   Brake Point: {p.brake_point_delta:+.0f}m")
            report.append(f"   → {p.specific_advice}")
        
        return "\n".join(report)


# Example usage
if __name__ == '__main__':
    print("Corner-by-Corner Performance Analyzer")
    print("=" * 70)
    print("\nThis tool shows EXACTLY where you're losing time.")
    print("\nExample output:")
    print("  Turn 3: -0.312s")
    print("  Issue: braking_early")
    print("  Action: Brake 15m later. Look for a reference point closer to the corner.")
    print("  Potential Gain: 0.312s")
