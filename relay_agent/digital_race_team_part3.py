"""
DIGITAL RACE TEAM - PART 3
Intelligence Analyst - Competitor Analysis & Race Prediction

The "team intel guy" that watches other drivers and collects all data
"""

import numpy as np
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


# ============================================================================
# PART 4: INTELLIGENCE ANALYST
# ============================================================================

@dataclass
class CompetitorProfile:
    """Complete competitor profile"""
    driver_id: str
    driver_name: str
    irating: int
    safety_rating: float
    
    # Performance characteristics
    qualifying_pace: float  # Average quali position
    race_pace: float  # Average race pace vs field
    consistency: float  # Lap time std dev
    tire_management: float  # 0-10 rating
    overtaking_ability: float
    defending_ability: float
    
    # Strengths and weaknesses
    strong_corners: List[int]  # Corner numbers where they excel
    weak_corners: List[int]  # Corner numbers where they struggle
    strong_tracks: List[str]
    weak_tracks: List[str]
    
    # Behavioral patterns
    aggressive_rating: float  # 0-10
    incident_rate: float  # Incidents per race
    typical_strategies: List[str]
    pit_stop_timing_pattern: str  # 'early', 'standard', 'late'
    
    # Head-to-head stats
    races_against_you: int
    wins_against_you: int
    avg_finishing_delta: float  # positions
    
    # Exploitable weaknesses
    how_to_beat_them: List[str]


@dataclass
class RacePrediction:
    """Predicted race outcome"""
    driver_id: str
    driver_name: str
    predicted_finish_position: int
    confidence: float
    predicted_lap_times: List[float]
    predicted_pit_laps: List[int]
    predicted_tire_strategy: str
    threat_level: str  # 'high', 'medium', 'low'


@dataclass
class LiveRaceIntelligence:
    """Real-time race intelligence"""
    lap: int
    timestamp: float
    
    # Competitor status
    competitor_positions: Dict[str, int]
    competitor_gaps: Dict[str, float]  # seconds
    competitor_tire_ages: Dict[str, int]
    competitor_pit_status: Dict[str, str]  # 'in', 'out', 'due'
    
    # Threats and opportunities
    immediate_threats: List[str]  # Drivers closing in
    overtaking_targets: List[str]  # Drivers you can catch
    strategic_opportunities: List[str]  # Undercut/overcut chances
    
    # Predictions
    predicted_pit_stops_next_5_laps: List[Tuple[str, int]]
    predicted_position_changes: List[str]


class IntelligenceAnalyst:
    """Complete intelligence and competitor analysis system"""
    
    def __init__(self):
        self.competitor_database = {}
        self.historical_races = []
        self.live_tracking = {}
        
    def build_competitor_profile(self,
                                driver_id: str,
                                historical_data: List[Dict],
                                telemetry_data: List[Dict],
                                head_to_head_data: List[Dict]) -> CompetitorProfile:
        """
        Build comprehensive competitor profile
        
        Analyzes everything about a competitor:
        - Performance characteristics
        - Strengths and weaknesses
        - Behavioral patterns
        - How to beat them
        """
        
        # Performance metrics
        quali_positions = [r.get('quali_position', 10) for r in historical_data]
        race_positions = [r.get('race_position', 10) for r in historical_data]
        
        qualifying_pace = np.mean(quali_positions) if quali_positions else 10
        race_pace = np.mean(race_positions) if race_positions else 10
        
        # Lap time consistency
        all_lap_times = []
        for race in historical_data:
            all_lap_times.extend(race.get('lap_times', []))
        
        consistency = np.std(all_lap_times) if len(all_lap_times) > 10 else 1.0
        consistency_rating = max(0, 10 - consistency * 10)
        
        # Analyze corner performance
        strong_corners = []
        weak_corners = []
        
        if telemetry_data:
            corner_performance = self._analyze_corner_performance(telemetry_data)
            strong_corners = [c['number'] for c in corner_performance[:3]]  # Top 3
            weak_corners = [c['number'] for c in corner_performance[-3:]]  # Bottom 3
        
        # Behavioral analysis
        incident_count = sum(r.get('incidents', 0) for r in historical_data)
        races_count = len(historical_data)
        incident_rate = incident_count / races_count if races_count > 0 else 0
        
        aggressive_rating = min(10, incident_rate * 20)  # More incidents = more aggressive
        
        # Pit strategy patterns
        pit_laps = [r.get('first_pit_lap', 15) for r in historical_data if r.get('first_pit_lap')]
        avg_pit_lap = np.mean(pit_laps) if pit_laps else 15
        
        if avg_pit_lap < 12:
            pit_pattern = 'early'
        elif avg_pit_lap > 18:
            pit_pattern = 'late'
        else:
            pit_pattern = 'standard'
        
        # Head-to-head analysis
        h2h_races = len(head_to_head_data)
        h2h_wins = sum(1 for r in head_to_head_data if r.get('you_finished_ahead', False))
        
        position_deltas = [
            r.get('your_position', 10) - r.get('their_position', 10)
            for r in head_to_head_data
        ]
        avg_delta = np.mean(position_deltas) if position_deltas else 0
        
        # Generate "how to beat them" strategies
        how_to_beat = self._generate_beating_strategy(
            strong_corners, weak_corners, pit_pattern, aggressive_rating, avg_delta
        )
        
        return CompetitorProfile(
            driver_id=driver_id,
            driver_name=f"Driver {driver_id}",
            irating=2500,  # Would fetch from API
            safety_rating=3.5,
            qualifying_pace=qualifying_pace,
            race_pace=race_pace,
            consistency=consistency_rating,
            tire_management=7.5,
            overtaking_ability=8.0 if aggressive_rating > 6 else 6.0,
            defending_ability=7.0,
            strong_corners=strong_corners,
            weak_corners=weak_corners,
            strong_tracks=["Spa", "Monza"],  # Would analyze from data
            weak_tracks=["Monaco", "Singapore"],
            aggressive_rating=aggressive_rating,
            incident_rate=incident_rate,
            typical_strategies=['standard_2_stop', 'aggressive_undercut'],
            pit_stop_timing_pattern=pit_pattern,
            races_against_you=h2h_races,
            wins_against_you=h2h_wins,
            avg_finishing_delta=avg_delta,
            how_to_beat_them=how_to_beat
        )
    
    def predict_race_outcome(self,
                            competitors: List[CompetitorProfile],
                            track_name: str,
                            weather: str,
                            your_quali_position: int) -> List[RacePrediction]:
        """
        Predict race outcome before it starts
        
        Uses:
        - Competitor profiles
        - Track characteristics
        - Weather conditions
        - Historical data
        - Machine learning (simplified here)
        """
        predictions = []
        
        for comp in competitors:
            # Adjust pace for track
            track_adjustment = 0
            if track_name in comp.strong_tracks:
                track_adjustment = -1.5  # Better position
            elif track_name in comp.weak_tracks:
                track_adjustment = +1.5  # Worse position
            
            # Adjust for weather
            weather_adjustment = 0
            if weather == 'wet':
                # Aggressive drivers struggle in wet
                if comp.aggressive_rating > 7:
                    weather_adjustment = +2
            
            # Predict finish position
            predicted_position = int(
                comp.qualifying_pace + track_adjustment + weather_adjustment
            )
            predicted_position = max(1, min(30, predicted_position))
            
            # Predict strategy
            if comp.pit_stop_timing_pattern == 'early':
                predicted_strategy = 'soft_medium_hard'
                predicted_pit_laps = [12, 24]
            elif comp.pit_stop_timing_pattern == 'late':
                predicted_strategy = 'medium_soft'
                predicted_pit_laps = [20]
            else:
                predicted_strategy = 'medium_medium'
                predicted_pit_laps = [15, 30]
            
            # Determine threat level
            if predicted_position < your_quali_position:
                threat = 'high'
            elif predicted_position == your_quali_position:
                threat = 'medium'
            else:
                threat = 'low'
            
            # Confidence based on data quality
            confidence = min(1.0, comp.races_against_you / 10)
            
            predictions.append(RacePrediction(
                driver_id=comp.driver_id,
                driver_name=comp.driver_name,
                predicted_finish_position=predicted_position,
                confidence=confidence,
                predicted_lap_times=[90.5, 90.3, 90.4],  # Simplified
                predicted_pit_laps=predicted_pit_laps,
                predicted_tire_strategy=predicted_strategy,
                threat_level=threat
            ))
        
        # Sort by predicted position
        predictions.sort(key=lambda x: x.predicted_finish_position)
        
        return predictions
    
    def generate_live_race_intelligence(self,
                                       current_lap: int,
                                       live_positions: Dict[str, int],
                                       live_gaps: Dict[str, float],
                                       tire_ages: Dict[str, int],
                                       competitor_profiles: List[CompetitorProfile]) -> LiveRaceIntelligence:
        """
        Generate real-time race intelligence
        
        Monitors:
        - Competitor positions and gaps
        - Tire ages and pit predictions
        - Threats and opportunities
        - Strategic situations
        """
        
        # Identify immediate threats (drivers within 2 seconds behind)
        your_position = live_positions.get('you', 10)
        threats = []
        for driver_id, gap in live_gaps.items():
            if gap < 2.0 and live_positions.get(driver_id, 20) > your_position:
                threats.append(driver_id)
        
        # Identify overtaking targets (drivers within 3 seconds ahead)
        targets = []
        for driver_id, gap in live_gaps.items():
            if gap < 3.0 and live_positions.get(driver_id, 0) < your_position:
                targets.append(driver_id)
        
        # Predict pit stops in next 5 laps
        predicted_pits = []
        for driver_id, tire_age in tire_ages.items():
            # Find their typical pit timing
            profile = next((p for p in competitor_profiles if p.driver_id == driver_id), None)
            if profile:
                if profile.pit_stop_timing_pattern == 'early' and tire_age >= 10:
                    predicted_pits.append((driver_id, current_lap + 2))
                elif profile.pit_stop_timing_pattern == 'standard' and tire_age >= 15:
                    predicted_pits.append((driver_id, current_lap + 3))
                elif profile.pit_stop_timing_pattern == 'late' and tire_age >= 20:
                    predicted_pits.append((driver_id, current_lap + 4))
        
        # Identify strategic opportunities
        opportunities = []
        for driver_id, predicted_lap in predicted_pits:
            if driver_id in targets:
                opportunities.append(f"UNDERCUT opportunity: {driver_id} pitting lap {predicted_lap}")
        
        # Predict position changes
        position_predictions = []
        for threat in threats:
            position_predictions.append(f"WARNING: {threat} closing fast, potential overtake")
        
        return LiveRaceIntelligence(
            lap=current_lap,
            timestamp=datetime.now().timestamp(),
            competitor_positions=live_positions,
            competitor_gaps=live_gaps,
            competitor_tire_ages=tire_ages,
            competitor_pit_status={},  # Would track in real-time
            immediate_threats=threats,
            overtaking_targets=targets,
            strategic_opportunities=opportunities,
            predicted_pit_stops_next_5_laps=predicted_pits,
            predicted_position_changes=position_predictions
        )
    
    def generate_pre_race_briefing(self,
                                  competitors: List[CompetitorProfile],
                                  race_predictions: List[RacePrediction],
                                  your_quali_position: int) -> str:
        """
        Generate comprehensive pre-race intelligence briefing
        
        Like a real team would brief the driver before the race
        """
        briefing = []
        briefing.append("=" * 70)
        briefing.append("PRE-RACE INTELLIGENCE BRIEFING")
        briefing.append("=" * 70)
        briefing.append(f"\nYour Qualifying Position: P{your_quali_position}")
        briefing.append("\nKEY COMPETITORS:")
        
        # Focus on nearby competitors
        nearby = [p for p in race_predictions 
                 if abs(p.predicted_finish_position - your_quali_position) <= 3]
        
        for pred in nearby[:5]:
            comp = next((c for c in competitors if c.driver_id == pred.driver_id), None)
            if comp:
                briefing.append(f"\n{pred.driver_name} (P{pred.predicted_finish_position} predicted):")
                briefing.append(f"  Threat Level: {pred.threat_level.upper()}")
                briefing.append(f"  Strengths: Corners {', '.join(map(str, comp.strong_corners))}")
                briefing.append(f"  Weaknesses: Corners {', '.join(map(str, comp.weak_corners))}")
                briefing.append(f"  Style: {'Aggressive' if comp.aggressive_rating > 6 else 'Defensive'}")
                briefing.append(f"  Pit Strategy: {pred.predicted_tire_strategy}")
                briefing.append(f"  HOW TO BEAT:")
                for strategy in comp.how_to_beat_them:
                    briefing.append(f"    • {strategy}")
        
        briefing.append("\nRACE STRATEGY RECOMMENDATIONS:")
        briefing.append("  1. Defend position at start")
        briefing.append("  2. Watch for early undercuts from aggressive drivers")
        briefing.append("  3. Attack weak corners of drivers ahead")
        briefing.append("  4. Be ready for safety car opportunities")
        
        return "\n".join(briefing)
    
    def generate_intel_radio_messages(self,
                                     intel: LiveRaceIntelligence,
                                     competitor_profiles: List[CompetitorProfile]) -> List[str]:
        """Generate real-time intelligence radio messages"""
        messages = []
        
        # Threats
        if intel.immediate_threats:
            for threat in intel.immediate_threats[:2]:
                profile = next((p for p in competitor_profiles if p.driver_id == threat), None)
                if profile:
                    messages.append(
                        f"THREAT: {profile.driver_name} closing. "
                        f"Aggressive rating {profile.aggressive_rating:.0f}/10. "
                        f"Defend {', '.join(map(str, profile.strong_corners[:2]))}."
                    )
        
        # Opportunities
        if intel.strategic_opportunities:
            messages.append(intel.strategic_opportunities[0])
        
        # Pit predictions
        if intel.predicted_pit_stops_next_5_laps:
            driver_id, lap = intel.predicted_pit_stops_next_5_laps[0]
            messages.append(f"Intel: {driver_id} expected to pit lap {lap}")
        
        return messages
    
    # Helper methods
    def _analyze_corner_performance(self, telemetry: List[Dict]) -> List[Dict]:
        """Analyze performance by corner"""
        # Simplified - would do full corner-by-corner analysis
        return [
            {'number': 1, 'performance': 8.5},
            {'number': 3, 'performance': 9.2},
            {'number': 5, 'performance': 6.8},
        ]
    
    def _generate_beating_strategy(self,
                                  strong_corners: List[int],
                                  weak_corners: List[int],
                                  pit_pattern: str,
                                  aggressive_rating: float,
                                  avg_delta: float) -> List[str]:
        """Generate specific strategies to beat this competitor"""
        strategies = []
        
        # Exploit weak corners
        if weak_corners:
            strategies.append(
                f"Attack in corners {', '.join(map(str, weak_corners[:2]))} - their weak spots"
            )
        
        # Defend strong corners
        if strong_corners:
            strategies.append(
                f"Defend position before corners {', '.join(map(str, strong_corners[:2]))} - their strengths"
            )
        
        # Counter pit strategy
        if pit_pattern == 'early':
            strategies.append("Expect early pit stop (lap 10-12). Consider overcut strategy")
        elif pit_pattern == 'late':
            strategies.append("Expect late pit stop (lap 18-20). Consider undercut strategy")
        
        # Handle aggression
        if aggressive_rating > 7:
            strategies.append("Aggressive driver - be defensive, let them make mistakes")
        else:
            strategies.append("Defensive driver - pressure them, they may crack")
        
        # Historical performance
        if avg_delta > 0:
            strategies.append(f"You typically finish {abs(avg_delta):.1f} positions ahead - maintain advantage")
        elif avg_delta < 0:
            strategies.append(f"They typically finish {abs(avg_delta):.1f} positions ahead - need to improve")
        
        return strategies


# Example usage
if __name__ == '__main__':
    print("INTELLIGENCE ANALYST")
    print("=" * 70)
    print("\nComprehensive competitor intelligence:")
    print("  • Complete competitor profiles")
    print("  • Strengths and weaknesses analysis")
    print("  • Behavioral pattern recognition")
    print("  • Race outcome prediction")
    print("  • Live race intelligence")
    print("  • 'How to beat them' strategies")
    print("\nExample output:")
    print("  Driver 'FastGuy123':")
    print("    Strong: Corners 3, 7, 12")
    print("    Weak: Corners 5, 9")
    print("    Style: Aggressive (8/10)")
    print("    Pit pattern: Early (lap 10-12)")
    print("    HOW TO BEAT:")
    print("      • Attack in Turn 5 and Turn 9")
    print("      • Defend before Turn 3 and Turn 7")
    print("      • Consider overcut strategy")
    print("      • Let them make mistakes under pressure")
