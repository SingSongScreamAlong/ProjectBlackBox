"""
Setup Analyzer
Tracks setup changes and correlates with performance
Shows if setup changes actually helped or hurt
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SetupChange:
    """A single setup change"""
    timestamp: float
    component: str  # 'front_wing', 'rear_wing', 'front_arb', etc.
    parameter: str  # 'angle', 'stiffness', 'pressure', etc.
    old_value: float
    new_value: float
    delta: float  # new - old
    unit: str  # 'clicks', 'psi', 'degrees', etc.


@dataclass
class SetupAnalysis:
    """Analysis of setup change impact"""
    change: SetupChange
    
    # Performance impact
    lap_time_before: float
    lap_time_after: float
    lap_time_delta: float  # Negative = improvement
    
    # Consistency impact
    consistency_before: float  # Std dev of lap times
    consistency_after: float
    consistency_delta: float
    
    # Handling impact
    understeer_before: float  # -1 to 1 scale
    understeer_after: float
    understeer_delta: float
    
    oversteer_before: float
    oversteer_after: float
    oversteer_delta: float
    
    # Tire impact
    tire_wear_before: float
    tire_wear_after: float
    tire_temp_delta: Dict[str, float]  # Per tire
    
    # Overall assessment
    was_improvement: bool
    confidence: float  # 0-1, based on sample size
    recommendation: str
    keep_or_revert: str  # 'keep', 'revert', 'uncertain'


class SetupAnalyzer:
    """Analyzes setup changes and their impact"""
    
    def __init__(self):
        self.setup_history = []
        self.baseline_telemetry = None
        
    def track_setup_change(self,
                          component: str,
                          parameter: str,
                          old_value: float,
                          new_value: float,
                          unit: str = 'clicks') -> SetupChange:
        """
        Record a setup change
        
        Args:
            component: What was changed (e.g., 'front_wing')
            parameter: What parameter (e.g., 'angle')
            old_value: Previous value
            new_value: New value
            unit: Unit of measurement
            
        Returns:
            SetupChange object
        """
        change = SetupChange(
            timestamp=datetime.now().timestamp(),
            component=component,
            parameter=parameter,
            old_value=old_value,
            new_value=new_value,
            delta=new_value - old_value,
            unit=unit
        )
        
        self.setup_history.append(change)
        logger.info(f"Tracked: {component} {parameter} {old_value} → {new_value} {unit}")
        
        return change
    
    def analyze_setup_change(self,
                            change: SetupChange,
                            telemetry_before: List[Dict],
                            telemetry_after: List[Dict]) -> SetupAnalysis:
        """
        Analyze the impact of a setup change
        
        Args:
            change: The setup change to analyze
            telemetry_before: Telemetry from laps before change
            telemetry_after: Telemetry from laps after change
            
        Returns:
            SetupAnalysis with detailed impact assessment
        """
        logger.info(f"Analyzing impact of {change.component} change")
        
        # Calculate lap time impact
        lap_times_before = self._extract_lap_times(telemetry_before)
        lap_times_after = self._extract_lap_times(telemetry_after)
        
        avg_before = np.mean(lap_times_before) if lap_times_before else 0
        avg_after = np.mean(lap_times_after) if lap_times_after else 0
        lap_time_delta = avg_after - avg_before
        
        # Calculate consistency impact
        consistency_before = np.std(lap_times_before) if len(lap_times_before) > 1 else 0
        consistency_after = np.std(lap_times_after) if len(lap_times_after) > 1 else 0
        consistency_delta = consistency_after - consistency_before
        
        # Analyze handling balance
        understeer_before, oversteer_before = self._analyze_handling_balance(telemetry_before)
        understeer_after, oversteer_after = self._analyze_handling_balance(telemetry_after)
        
        # Analyze tire impact
        tire_wear_before = self._calculate_tire_wear(telemetry_before)
        tire_wear_after = self._calculate_tire_wear(telemetry_after)
        tire_temp_delta = self._calculate_tire_temp_delta(telemetry_before, telemetry_after)
        
        # Determine if it was an improvement
        was_improvement = lap_time_delta < -0.05  # At least 0.05s faster
        
        # Calculate confidence based on sample size
        confidence = min(1.0, (len(lap_times_before) + len(lap_times_after)) / 20)
        
        # Generate recommendation
        recommendation, keep_or_revert = self._generate_setup_recommendation(
            change=change,
            lap_time_delta=lap_time_delta,
            consistency_delta=consistency_delta,
            understeer_delta=understeer_after - understeer_before,
            oversteer_delta=oversteer_after - oversteer_before,
            confidence=confidence
        )
        
        return SetupAnalysis(
            change=change,
            lap_time_before=avg_before,
            lap_time_after=avg_after,
            lap_time_delta=lap_time_delta,
            consistency_before=consistency_before,
            consistency_after=consistency_after,
            consistency_delta=consistency_delta,
            understeer_before=understeer_before,
            understeer_after=understeer_after,
            understeer_delta=understeer_after - understeer_before,
            oversteer_before=oversteer_before,
            oversteer_after=oversteer_after,
            oversteer_delta=oversteer_after - oversteer_before,
            tire_wear_before=tire_wear_before,
            tire_wear_after=tire_wear_after,
            tire_temp_delta=tire_temp_delta,
            was_improvement=was_improvement,
            confidence=confidence,
            recommendation=recommendation,
            keep_or_revert=keep_or_revert
        )
    
    def recommend_setup_for_issue(self, issue: str, current_setup: Dict) -> List[Dict]:
        """
        Recommend setup changes to fix a specific issue
        
        Args:
            issue: The problem (e.g., 'understeer', 'oversteer', 'tire_wear')
            current_setup: Current setup configuration
            
        Returns:
            List of recommended changes with expected effects
        """
        recommendations = []
        
        if issue.lower() == 'understeer':
            recommendations.extend([
                {
                    'component': 'front_wing',
                    'parameter': 'angle',
                    'change': -1,
                    'unit': 'clicks',
                    'expected_effect': 'Reduce front downforce, shift balance rearward',
                    'confidence': 0.9
                },
                {
                    'component': 'front_arb',
                    'parameter': 'stiffness',
                    'change': +1,
                    'unit': 'clicks',
                    'expected_effect': 'Increase front roll stiffness, improve turn-in',
                    'confidence': 0.8
                },
                {
                    'component': 'rear_wing',
                    'parameter': 'angle',
                    'change': +1,
                    'unit': 'clicks',
                    'expected_effect': 'Increase rear downforce, improve rear grip',
                    'confidence': 0.85
                }
            ])
        
        elif issue.lower() == 'oversteer':
            recommendations.extend([
                {
                    'component': 'rear_wing',
                    'parameter': 'angle',
                    'change': +1,
                    'unit': 'clicks',
                    'expected_effect': 'Increase rear downforce, reduce oversteer',
                    'confidence': 0.9
                },
                {
                    'component': 'rear_arb',
                    'parameter': 'stiffness',
                    'change': -1,
                    'unit': 'clicks',
                    'expected_effect': 'Reduce rear roll stiffness, improve rear grip',
                    'confidence': 0.85
                },
                {
                    'component': 'front_wing',
                    'parameter': 'angle',
                    'change': +1,
                    'unit': 'clicks',
                    'expected_effect': 'Increase front downforce, shift balance forward',
                    'confidence': 0.8
                }
            ])
        
        elif issue.lower() == 'tire_wear':
            recommendations.extend([
                {
                    'component': 'tire_pressure',
                    'parameter': 'all',
                    'change': +1,
                    'unit': 'psi',
                    'expected_effect': 'Reduce tire flex, decrease wear',
                    'confidence': 0.7
                },
                {
                    'component': 'camber',
                    'parameter': 'front',
                    'change': -0.5,
                    'unit': 'degrees',
                    'expected_effect': 'More contact patch, reduce inside edge wear',
                    'confidence': 0.75
                }
            ])
        
        elif issue.lower() == 'inconsistency':
            recommendations.extend([
                {
                    'component': 'dampers',
                    'parameter': 'bump',
                    'change': +1,
                    'unit': 'clicks',
                    'expected_effect': 'Improve platform stability, reduce variance',
                    'confidence': 0.6
                },
                {
                    'component': 'tire_pressure',
                    'parameter': 'all',
                    'change': +0.5,
                    'unit': 'psi',
                    'expected_effect': 'More predictable handling',
                    'confidence': 0.65
                }
            ])
        
        return recommendations
    
    def _extract_lap_times(self, telemetry: List[Dict]) -> List[float]:
        """Extract lap times from telemetry"""
        lap_times = []
        current_lap = None
        lap_start_time = None
        
        for sample in telemetry:
            lap = sample.get('lap', 0)
            
            if current_lap is None:
                current_lap = lap
                lap_start_time = sample.get('timestamp', 0)
            elif lap != current_lap:
                # Lap changed, calculate lap time
                lap_end_time = sample.get('timestamp', 0)
                lap_time = (lap_end_time - lap_start_time) / 1000.0
                
                if 60 < lap_time < 300:  # Valid lap time (1-5 minutes)
                    lap_times.append(lap_time)
                
                current_lap = lap
                lap_start_time = sample.get('timestamp', 0)
        
        return lap_times
    
    def _analyze_handling_balance(self, telemetry: List[Dict]) -> Tuple[float, float]:
        """
        Analyze handling balance from telemetry
        
        Returns:
            (understeer_metric, oversteer_metric) on -1 to 1 scale
        """
        if not telemetry:
            return 0.0, 0.0
        
        # Analyze cornering behavior
        # Understeer: Low lateral G despite steering input
        # Oversteer: High lateral G with small steering input, or sudden G changes
        
        understeer_samples = []
        oversteer_samples = []
        
        for sample in telemetry:
            steering = abs(sample.get('steering', 0))
            g_lat = abs(sample.get('g_lat', 0))
            speed = sample.get('speed', 0)
            
            # Only analyze in corners (steering > 10%, speed > 50 km/h)
            if steering > 0.1 and speed > 50:
                # Expected lateral G based on steering input
                expected_g = steering * 2.5  # Rough approximation
                
                # Understeer: Less G than expected
                if g_lat < expected_g * 0.7:
                    understeer_samples.append(1.0)
                
                # Oversteer: More G than expected or sudden changes
                if g_lat > expected_g * 1.3:
                    oversteer_samples.append(1.0)
        
        understeer = np.mean(understeer_samples) if understeer_samples else 0.0
        oversteer = np.mean(oversteer_samples) if oversteer_samples else 0.0
        
        return understeer, oversteer
    
    def _calculate_tire_wear(self, telemetry: List[Dict]) -> float:
        """Calculate average tire wear rate"""
        if not telemetry:
            return 0.0
        
        # Simplified: Use tire temp as proxy for wear
        # Higher temps = more wear
        tire_temps = []
        for sample in telemetry:
            avg_temp = (
                sample.get('tire_temp_lf', 0) +
                sample.get('tire_temp_rf', 0) +
                sample.get('tire_temp_lr', 0) +
                sample.get('tire_temp_rr', 0)
            ) / 4
            tire_temps.append(avg_temp)
        
        return np.mean(tire_temps) if tire_temps else 0.0
    
    def _calculate_tire_temp_delta(self, before: List[Dict], after: List[Dict]) -> Dict[str, float]:
        """Calculate change in tire temperatures"""
        def avg_tire_temps(telemetry):
            temps = {'lf': [], 'rf': [], 'lr': [], 'rr': []}
            for sample in telemetry:
                temps['lf'].append(sample.get('tire_temp_lf', 0))
                temps['rf'].append(sample.get('tire_temp_rf', 0))
                temps['lr'].append(sample.get('tire_temp_lr', 0))
                temps['rr'].append(sample.get('tire_temp_rr', 0))
            return {k: np.mean(v) if v else 0 for k, v in temps.items()}
        
        temps_before = avg_tire_temps(before)
        temps_after = avg_tire_temps(after)
        
        return {
            k: temps_after[k] - temps_before[k]
            for k in temps_before.keys()
        }
    
    def _generate_setup_recommendation(self,
                                      change: SetupChange,
                                      lap_time_delta: float,
                                      consistency_delta: float,
                                      understeer_delta: float,
                                      oversteer_delta: float,
                                      confidence: float) -> Tuple[str, str]:
        """Generate recommendation based on analysis"""
        
        # Determine if change should be kept
        if lap_time_delta < -0.1:  # Significant improvement
            keep_or_revert = 'keep'
            recommendation = f"✅ KEEP: Gained {abs(lap_time_delta):.3f}s per lap"
        elif lap_time_delta > 0.1:  # Significant degradation
            keep_or_revert = 'revert'
            recommendation = f"❌ REVERT: Lost {lap_time_delta:.3f}s per lap"
        else:
            keep_or_revert = 'uncertain'
            recommendation = f"⚠️ MARGINAL: Only {lap_time_delta:+.3f}s change"
        
        # Add handling feedback
        if abs(understeer_delta) > 0.2:
            if understeer_delta > 0:
                recommendation += f". Increased understeer by {understeer_delta:.1%}"
            else:
                recommendation += f". Reduced understeer by {abs(understeer_delta):.1%}"
        
        if abs(oversteer_delta) > 0.2:
            if oversteer_delta > 0:
                recommendation += f". Increased oversteer by {oversteer_delta:.1%}"
            else:
                recommendation += f". Reduced oversteer by {abs(oversteer_delta):.1%}"
        
        # Add consistency feedback
        if abs(consistency_delta) > 0.05:
            if consistency_delta < 0:
                recommendation += f". Improved consistency (±{abs(consistency_delta):.3f}s)"
            else:
                recommendation += f". Reduced consistency (±{consistency_delta:.3f}s)"
        
        # Add confidence qualifier
        if confidence < 0.5:
            recommendation += ". ⚠️ Low confidence - need more laps"
        
        return recommendation, keep_or_revert
    
    def generate_setup_report(self, analyses: List[SetupAnalysis]) -> str:
        """Generate human-readable setup analysis report"""
        
        report = []
        report.append("=" * 70)
        report.append("SETUP ANALYSIS REPORT")
        report.append("=" * 70)
        report.append(f"\nTotal Changes Analyzed: {len(analyses)}")
        
        improvements = [a for a in analyses if a.was_improvement]
        degradations = [a for a in analyses if not a.was_improvement and a.lap_time_delta > 0.05]
        
        report.append(f"Improvements: {len(improvements)}")
        report.append(f"Degradations: {len(degradations)}")
        report.append("")
        
        for i, analysis in enumerate(analyses, 1):
            icon = "✅" if analysis.was_improvement else "❌" if analysis.lap_time_delta > 0.05 else "⚠️"
            
            report.append(f"\n{icon} Change #{i}: {analysis.change.component} {analysis.change.parameter}")
            report.append(f"   {analysis.change.old_value} → {analysis.change.new_value} {analysis.change.unit}")
            report.append(f"   Lap Time: {analysis.lap_time_before:.3f}s → {analysis.lap_time_after:.3f}s ({analysis.lap_time_delta:+.3f}s)")
            report.append(f"   Consistency: ±{analysis.consistency_before:.3f}s → ±{analysis.consistency_after:.3f}s")
            report.append(f"   Handling: U={analysis.understeer_delta:+.2f}, O={analysis.oversteer_delta:+.2f}")
            report.append(f"   Confidence: {analysis.confidence:.0%}")
            report.append(f"\n   💡 {analysis.recommendation}")
            report.append(f"   → {analysis.keep_or_revert.upper()}")
        
        return "\n".join(report)


# Example usage
if __name__ == '__main__':
    print("Setup Analyzer")
    print("=" * 70)
    print("\nTracks setup changes and shows if they helped or hurt:")
    print("\n✅ KEEP: Front wing -1 click")
    print("   Lap Time: 1:32.456 → 1:32.234 (-0.222s)")
    print("   Reduced understeer by 15%")
    print("   Improved consistency (±0.045s)")
    print("\n❌ REVERT: Rear ARB +2 clicks")
    print("   Lap Time: 1:32.234 → 1:32.567 (+0.333s)")
    print("   Increased oversteer by 25%")
    print("   Reduced consistency (±0.112s)")
