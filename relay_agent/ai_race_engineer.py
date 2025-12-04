"""
AI Race Engineer - Complete Driver Assessment & Coaching System
Acts as race engineer, strategist, and team principal
Proactively identifies what driver needs to work on
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SkillArea(Enum):
    """Driver skill areas to assess"""
    BRAKING = "braking"
    CORNER_ENTRY = "corner_entry"
    APEX_SPEED = "apex_speed"
    CORNER_EXIT = "corner_exit"
    THROTTLE_CONTROL = "throttle_control"
    CONSISTENCY = "consistency"
    RACECRAFT = "racecraft"
    TIRE_MANAGEMENT = "tire_management"
    FUEL_MANAGEMENT = "fuel_management"
    SETUP_KNOWLEDGE = "setup_knowledge"
    RACE_STRATEGY = "race_strategy"
    QUALIFYING = "qualifying"
    WET_WEATHER = "wet_weather"


@dataclass
class SkillAssessment:
    """Assessment of a specific skill"""
    skill: SkillArea
    rating: float  # 0-10 scale
    percentile: float  # vs other drivers (0-100)
    
    # Evidence
    data_points: int
    confidence: float
    
    # Analysis
    strengths: List[str]
    weaknesses: List[str]
    specific_issues: List[str]
    
    # Improvement plan
    priority: str  # 'critical', 'high', 'medium', 'low'
    target_rating: float
    estimated_lap_time_gain: float
    training_exercises: List[str]
    focus_corners: List[str]


@dataclass
class DriverProfile:
    """Complete driver profile and assessment"""
    driver_id: str
    driver_name: str
    
    # Overall metrics
    overall_rating: float  # 0-10
    irating: int
    safety_rating: float
    
    # Skill assessments
    skills: Dict[SkillArea, SkillAssessment] = field(default_factory=dict)
    
    # Current focus areas
    primary_weakness: Optional[SkillArea] = None
    secondary_weakness: Optional[SkillArea] = None
    biggest_strength: Optional[SkillArea] = None
    
    # Development plan
    short_term_goals: List[str] = field(default_factory=list)
    long_term_goals: List[str] = field(default_factory=list)
    current_training_focus: Optional[str] = None
    
    # Performance trends
    lap_time_trend: str = "stable"  # 'improving', 'stable', 'declining'
    consistency_trend: str = "stable"
    incident_trend: str = "stable"


class AIRaceEngineer:
    """Complete AI race engineer and coaching system"""
    
    def __init__(self):
        self.driver_profiles = {}
        
    def assess_driver(self,
                     driver_id: str,
                     session_history: List[Dict],
                     telemetry_data: List[Dict],
                     corner_analyses: List[Dict],
                     incident_analyses: List[Dict],
                     setup_analyses: List[Dict]) -> DriverProfile:
        """
        Comprehensive driver assessment
        
        Args:
            driver_id: Driver identifier
            session_history: Historical session data
            telemetry_data: Recent telemetry
            corner_analyses: Corner-by-corner performance
            incident_analyses: Incident history
            setup_analyses: Setup change history
            
        Returns:
            Complete driver profile with assessments and recommendations
        """
        logger.info(f"Assessing driver {driver_id}")
        
        profile = DriverProfile(
            driver_id=driver_id,
            driver_name=self._get_driver_name(driver_id),
            overall_rating=0.0,
            irating=self._get_irating(driver_id),
            safety_rating=self._get_safety_rating(driver_id)
        )
        
        # Assess each skill area
        profile.skills[SkillArea.BRAKING] = self._assess_braking(
            corner_analyses, telemetry_data
        )
        
        profile.skills[SkillArea.CORNER_ENTRY] = self._assess_corner_entry(
            corner_analyses, telemetry_data
        )
        
        profile.skills[SkillArea.APEX_SPEED] = self._assess_apex_speed(
            corner_analyses
        )
        
        profile.skills[SkillArea.CORNER_EXIT] = self._assess_corner_exit(
            corner_analyses, telemetry_data
        )
        
        profile.skills[SkillArea.THROTTLE_CONTROL] = self._assess_throttle_control(
            telemetry_data, incident_analyses
        )
        
        profile.skills[SkillArea.CONSISTENCY] = self._assess_consistency(
            session_history, telemetry_data
        )
        
        profile.skills[SkillArea.TIRE_MANAGEMENT] = self._assess_tire_management(
            telemetry_data, session_history
        )
        
        profile.skills[SkillArea.SETUP_KNOWLEDGE] = self._assess_setup_knowledge(
            setup_analyses
        )
        
        profile.skills[SkillArea.RACECRAFT] = self._assess_racecraft(
            incident_analyses, session_history
        )
        
        # Calculate overall rating
        profile.overall_rating = np.mean([
            s.rating for s in profile.skills.values()
        ])
        
        # Identify strengths and weaknesses
        sorted_skills = sorted(
            profile.skills.items(),
            key=lambda x: x[1].rating
        )
        
        profile.primary_weakness = sorted_skills[0][0]
        profile.secondary_weakness = sorted_skills[1][0]
        profile.biggest_strength = sorted_skills[-1][0]
        
        # Generate development plan
        profile = self._generate_development_plan(profile)
        
        # Analyze trends
        profile = self._analyze_trends(profile, session_history)
        
        return profile
    
    def _assess_braking(self, corner_analyses: List[Dict], 
                       telemetry: List[Dict]) -> SkillAssessment:
        """Assess braking skill"""
        
        issues = []
        strengths = []
        
        # Analyze brake points from corner data
        brake_point_errors = []
        for corner in corner_analyses:
            if corner.get('brake_point_delta'):
                brake_point_errors.append(abs(corner['brake_point_delta']))
                
                if corner['brake_point_delta'] < -10:
                    issues.append(f"{corner['corner_name']}: Braking {abs(corner['brake_point_delta']):.0f}m too early")
                elif corner['brake_point_delta'] > 10:
                    issues.append(f"{corner['corner_name']}: Braking {corner['brake_point_delta']:.0f}m too late")
        
        # Calculate rating
        avg_error = np.mean(brake_point_errors) if brake_point_errors else 0
        rating = max(0, 10 - (avg_error / 5))  # 5m error = 1 point deduction
        
        # Determine priority
        if rating < 6:
            priority = 'critical'
            target = 8.0
            gain = 0.5
        elif rating < 7.5:
            priority = 'high'
            target = 8.5
            gain = 0.3
        else:
            priority = 'medium'
            target = 9.0
            gain = 0.1
        
        training = [
            "Practice brake marker recognition",
            "Focus on consistent brake pressure application",
            "Work on trail braking technique"
        ]
        
        if rating > 8:
            strengths.append("Excellent brake point accuracy")
        
        return SkillAssessment(
            skill=SkillArea.BRAKING,
            rating=rating,
            percentile=self._rating_to_percentile(rating),
            data_points=len(brake_point_errors),
            confidence=min(1.0, len(brake_point_errors) / 20),
            strengths=strengths,
            weaknesses=issues[:3],  # Top 3 issues
            specific_issues=issues,
            priority=priority,
            target_rating=target,
            estimated_lap_time_gain=gain,
            training_exercises=training,
            focus_corners=[c['corner_name'] for c in corner_analyses[:5]]
        )
    
    def _assess_corner_entry(self, corner_analyses: List[Dict],
                            telemetry: List[Dict]) -> SkillAssessment:
        """Assess corner entry skill"""
        
        entry_speed_errors = []
        issues = []
        
        for corner in corner_analyses:
            if corner.get('entry_speed_delta'):
                entry_speed_errors.append(corner['entry_speed_delta'])
                
                if corner['entry_speed_delta'] < -5:
                    issues.append(f"{corner['corner_name']}: {abs(corner['entry_speed_delta']):.1f} km/h too slow on entry")
        
        avg_error = np.mean([abs(e) for e in entry_speed_errors]) if entry_speed_errors else 0
        rating = max(0, 10 - (avg_error / 3))
        
        return SkillAssessment(
            skill=SkillArea.CORNER_ENTRY,
            rating=rating,
            percentile=self._rating_to_percentile(rating),
            data_points=len(entry_speed_errors),
            confidence=min(1.0, len(entry_speed_errors) / 20),
            strengths=["Good entry speed"] if rating > 8 else [],
            weaknesses=issues[:3],
            specific_issues=issues,
            priority='high' if rating < 7 else 'medium',
            target_rating=8.5,
            estimated_lap_time_gain=0.3 if rating < 7 else 0.1,
            training_exercises=[
                "Practice carrying more speed into corners",
                "Work on late apex technique",
                "Build confidence in braking zones"
            ],
            focus_corners=[c['corner_name'] for c in corner_analyses[:5]]
        )
    
    def _assess_apex_speed(self, corner_analyses: List[Dict]) -> SkillAssessment:
        """Assess minimum/apex speed skill"""
        
        apex_speed_errors = []
        issues = []
        
        for corner in corner_analyses:
            if corner.get('apex_speed_delta'):
                apex_speed_errors.append(corner['apex_speed_delta'])
                
                if corner['apex_speed_delta'] < -3:
                    issues.append(f"{corner['corner_name']}: {abs(corner['apex_speed_delta']):.1f} km/h too slow at apex")
        
        avg_error = np.mean([abs(e) for e in apex_speed_errors]) if apex_speed_errors else 0
        rating = max(0, 10 - (avg_error / 2))
        
        return SkillAssessment(
            skill=SkillArea.APEX_SPEED,
            rating=rating,
            percentile=self._rating_to_percentile(rating),
            data_points=len(apex_speed_errors),
            confidence=min(1.0, len(apex_speed_errors) / 20),
            strengths=["Excellent apex speed"] if rating > 8.5 else [],
            weaknesses=issues[:3],
            specific_issues=issues,
            priority='critical' if rating < 6 else 'high' if rating < 7.5 else 'medium',
            target_rating=9.0,
            estimated_lap_time_gain=0.4 if rating < 7 else 0.2,
            training_exercises=[
                "Practice smooth steering inputs through apex",
                "Work on finding the geometric apex",
                "Improve vision and look-ahead"
            ],
            focus_corners=[c['corner_name'] for c in corner_analyses[:5]]
        )
    
    def _assess_corner_exit(self, corner_analyses: List[Dict],
                           telemetry: List[Dict]) -> SkillAssessment:
        """Assess corner exit skill"""
        
        exit_speed_errors = []
        throttle_timing_errors = []
        issues = []
        
        for corner in corner_analyses:
            if corner.get('exit_speed_delta'):
                exit_speed_errors.append(corner['exit_speed_delta'])
                
                if corner['exit_speed_delta'] < -5:
                    issues.append(f"{corner['corner_name']}: {abs(corner['exit_speed_delta']):.1f} km/h lost on exit")
            
            if corner.get('throttle_delta'):
                throttle_timing_errors.append(corner['throttle_delta'])
                
                if corner['throttle_delta'] < -5:
                    issues.append(f"{corner['corner_name']}: Throttle {abs(corner['throttle_delta']):.0f}m too late")
        
        avg_speed_error = np.mean([abs(e) for e in exit_speed_errors]) if exit_speed_errors else 0
        rating = max(0, 10 - (avg_speed_error / 3))
        
        return SkillAssessment(
            skill=SkillArea.CORNER_EXIT,
            rating=rating,
            percentile=self._rating_to_percentile(rating),
            data_points=len(exit_speed_errors),
            confidence=min(1.0, len(exit_speed_errors) / 20),
            strengths=["Strong corner exits"] if rating > 8 else [],
            weaknesses=issues[:3],
            specific_issues=issues,
            priority='critical' if rating < 6.5 else 'high',
            target_rating=8.5,
            estimated_lap_time_gain=0.5 if rating < 7 else 0.3,
            training_exercises=[
                "Practice progressive throttle application",
                "Work on unwinding steering while accelerating",
                "Focus on exit onto straights (most important)"
            ],
            focus_corners=[c['corner_name'] for c in corner_analyses[:5]]
        )
    
    def _assess_throttle_control(self, telemetry: List[Dict],
                                 incidents: List[Dict]) -> SkillAssessment:
        """Assess throttle control and smoothness"""
        
        # Count throttle-related incidents
        throttle_incidents = [
            i for i in incidents 
            if 'throttle' in i.get('root_cause', '').lower() or
               'oversteer' in i.get('root_cause', '').lower()
        ]
        
        # Analyze throttle smoothness from telemetry
        throttle_changes = []
        for i in range(1, len(telemetry)):
            throttle_delta = abs(telemetry[i].get('throttle', 0) - 
                               telemetry[i-1].get('throttle', 0))
            throttle_changes.append(throttle_delta)
        
        avg_change = np.mean(throttle_changes) if throttle_changes else 0
        
        # Rating based on incidents and smoothness
        incident_penalty = len(throttle_incidents) * 0.5
        smoothness_penalty = avg_change * 10
        rating = max(0, 10 - incident_penalty - smoothness_penalty)
        
        issues = [f"Spin due to aggressive throttle" for _ in throttle_incidents[:3]]
        
        return SkillAssessment(
            skill=SkillArea.THROTTLE_CONTROL,
            rating=rating,
            percentile=self._rating_to_percentile(rating),
            data_points=len(throttle_incidents) + len(throttle_changes),
            confidence=0.8,
            strengths=["Smooth throttle control"] if rating > 8 else [],
            weaknesses=issues,
            specific_issues=issues,
            priority='critical' if rating < 6 else 'high' if rating < 7.5 else 'medium',
            target_rating=8.5,
            estimated_lap_time_gain=0.3,
            training_exercises=[
                "Practice progressive throttle: 50% → 70% → 100%",
                "Work on throttle modulation in low-grip corners",
                "Use telemetry overlay to see throttle trace"
            ],
            focus_corners=[]
        )
    
    def _assess_consistency(self, sessions: List[Dict],
                           telemetry: List[Dict]) -> SkillAssessment:
        """Assess lap-to-lap consistency"""
        
        # Extract lap times
        lap_times = []
        for session in sessions:
            lap_times.extend(session.get('lap_times', []))
        
        if len(lap_times) < 5:
            return self._default_assessment(SkillArea.CONSISTENCY)
        
        # Calculate consistency (std dev)
        std_dev = np.std(lap_times)
        mean_time = np.mean(lap_times)
        consistency_pct = (std_dev / mean_time) * 100
        
        # Rating: <0.5% = 10, >2% = 0
        rating = max(0, 10 - (consistency_pct * 5))
        
        issues = []
        if consistency_pct > 1.0:
            issues.append(f"High variance: ±{std_dev:.3f}s ({consistency_pct:.1f}%)")
        
        return SkillAssessment(
            skill=SkillArea.CONSISTENCY,
            rating=rating,
            percentile=self._rating_to_percentile(rating),
            data_points=len(lap_times),
            confidence=min(1.0, len(lap_times) / 30),
            strengths=["Excellent consistency"] if rating > 8.5 else [],
            weaknesses=issues,
            specific_issues=issues,
            priority='high' if rating < 7 else 'medium',
            target_rating=8.5,
            estimated_lap_time_gain=0.2,
            training_exercises=[
                "Focus on reference points for consistency",
                "Practice same brake/throttle points every lap",
                "Work on mental discipline and focus"
            ],
            focus_corners=[]
        )
    
    def _assess_tire_management(self, telemetry: List[Dict],
                               sessions: List[Dict]) -> SkillAssessment:
        """Assess tire management skill"""
        
        # Analyze tire temps and wear patterns
        tire_temps = []
        for sample in telemetry:
            avg_temp = (
                sample.get('tire_temp_lf', 0) +
                sample.get('tire_temp_rf', 0) +
                sample.get('tire_temp_lr', 0) +
                sample.get('tire_temp_rr', 0)
            ) / 4
            tire_temps.append(avg_temp)
        
        # Good tire management = stable temps in optimal range (80-100°C)
        if tire_temps:
            temp_variance = np.std(tire_temps)
            avg_temp = np.mean(tire_temps)
            
            # Rating based on temp control
            if 80 <= avg_temp <= 100 and temp_variance < 10:
                rating = 9.0
            elif 70 <= avg_temp <= 110 and temp_variance < 15:
                rating = 7.5
            else:
                rating = 6.0
        else:
            rating = 7.0
        
        return SkillAssessment(
            skill=SkillArea.TIRE_MANAGEMENT,
            rating=rating,
            percentile=self._rating_to_percentile(rating),
            data_points=len(tire_temps),
            confidence=0.7,
            strengths=["Good tire management"] if rating > 8 else [],
            weaknesses=["Inconsistent tire temps"] if rating < 7 else [],
            specific_issues=[],
            priority='medium',
            target_rating=8.0,
            estimated_lap_time_gain=0.1,
            training_exercises=[
                "Practice smooth inputs to preserve tires",
                "Learn optimal tire temperature windows",
                "Work on long-run pace vs qualifying pace"
            ],
            focus_corners=[]
        )
    
    def _assess_setup_knowledge(self, setup_analyses: List[Dict]) -> SkillAssessment:
        """Assess setup knowledge and ability"""
        
        if not setup_analyses:
            return self._default_assessment(SkillArea.SETUP_KNOWLEDGE)
        
        # Count successful vs unsuccessful changes
        successful = sum(1 for s in setup_analyses if s.get('was_improvement', False))
        total = len(setup_analyses)
        success_rate = successful / total if total > 0 else 0.5
        
        rating = success_rate * 10
        
        issues = []
        if success_rate < 0.4:
            issues.append(f"Only {success_rate:.0%} of setup changes improved performance")
        
        return SkillAssessment(
            skill=SkillArea.SETUP_KNOWLEDGE,
            rating=rating,
            percentile=self._rating_to_percentile(rating),
            data_points=total,
            confidence=min(1.0, total / 10),
            strengths=["Good setup intuition"] if rating > 7 else [],
            weaknesses=issues,
            specific_issues=issues,
            priority='medium',
            target_rating=7.5,
            estimated_lap_time_gain=0.2,
            training_exercises=[
                "Study setup fundamentals (aero, suspension)",
                "Use setup analyzer to learn cause-effect",
                "Start with small, single-variable changes"
            ],
            focus_corners=[]
        )
    
    def _assess_racecraft(self, incidents: List[Dict],
                         sessions: List[Dict]) -> SkillAssessment:
        """Assess racecraft and wheel-to-wheel ability"""
        
        # Count contact incidents
        contact_incidents = [
            i for i in incidents
            if i.get('incident_type') == 'contact'
        ]
        
        # Calculate incident rate
        total_laps = sum(s.get('total_laps', 0) for s in sessions)
        incident_rate = len(contact_incidents) / total_laps if total_laps > 0 else 0
        
        # Rating: 0 incidents = 10, >0.1 per lap = 0
        rating = max(0, 10 - (incident_rate * 100))
        
        return SkillAssessment(
            skill=SkillArea.RACECRAFT,
            rating=rating,
            percentile=self._rating_to_percentile(rating),
            data_points=len(contact_incidents),
            confidence=0.7,
            strengths=["Clean racing"] if rating > 8 else [],
            weaknesses=[f"{len(contact_incidents)} contact incidents"] if contact_incidents else [],
            specific_issues=[],
            priority='high' if rating < 6 else 'medium',
            target_rating=8.0,
            estimated_lap_time_gain=0.0,  # Doesn't directly improve lap time
            training_exercises=[
                "Practice defensive driving",
                "Work on spatial awareness",
                "Study racing rules and etiquette"
            ],
            focus_corners=[]
        )
    
    def _generate_development_plan(self, profile: DriverProfile) -> DriverProfile:
        """Generate personalized development plan"""
        
        # Identify top 3 areas to work on
        sorted_skills = sorted(
            profile.skills.items(),
            key=lambda x: (x[1].priority == 'critical', x[1].estimated_lap_time_gain),
            reverse=True
        )
        
        top_3 = sorted_skills[:3]
        
        # Short-term goals (next 2-4 weeks)
        profile.short_term_goals = [
            f"Improve {skill.value}: {assessment.rating:.1f} → {assessment.target_rating:.1f} "
            f"(potential {assessment.estimated_lap_time_gain:.2f}s gain)"
            for skill, assessment in top_3
        ]
        
        # Long-term goals (2-6 months)
        profile.long_term_goals = [
            f"Achieve {skill.value} rating of 9.0+",
            "Reduce lap time variance to <0.3%",
            "Increase iRating by 500 points"
        ]
        
        # Current training focus
        primary_skill, primary_assessment = top_3[0]
        profile.current_training_focus = (
            f"PRIMARY FOCUS: {primary_skill.value.upper()}\n"
            f"Current: {primary_assessment.rating:.1f}/10\n"
            f"Target: {primary_assessment.target_rating:.1f}/10\n"
            f"Potential gain: {primary_assessment.estimated_lap_time_gain:.2f}s\n\n"
            f"Training:\n" + "\n".join(f"  • {ex}" for ex in primary_assessment.training_exercises)
        )
        
        return profile
    
    def _analyze_trends(self, profile: DriverProfile,
                       sessions: List[Dict]) -> DriverProfile:
        """Analyze performance trends"""
        
        if len(sessions) < 3:
            return profile
        
        # Analyze lap time trend
        recent_times = []
        for session in sessions[-5:]:
            recent_times.extend(session.get('lap_times', []))
        
        if len(recent_times) > 10:
            first_half = np.mean(recent_times[:len(recent_times)//2])
            second_half = np.mean(recent_times[len(recent_times)//2:])
            
            if second_half < first_half - 0.1:
                profile.lap_time_trend = "improving"
            elif second_half > first_half + 0.1:
                profile.lap_time_trend = "declining"
        
        return profile
    
    def generate_engineer_briefing(self, profile: DriverProfile) -> str:
        """Generate race engineer briefing"""
        
        briefing = []
        briefing.append("=" * 70)
        briefing.append("RACE ENGINEER BRIEFING")
        briefing.append("=" * 70)
        briefing.append(f"\nDriver: {profile.driver_name}")
        briefing.append(f"Overall Rating: {profile.overall_rating:.1f}/10")
        briefing.append(f"iRating: {profile.irating}")
        briefing.append(f"Safety Rating: {profile.safety_rating:.2f}")
        briefing.append("")
        
        briefing.append("STRENGTHS:")
        briefing.append(f"  ✅ {profile.biggest_strength.value.upper()}: "
                       f"{profile.skills[profile.biggest_strength].rating:.1f}/10")
        
        briefing.append("\nAREAS FOR IMPROVEMENT:")
        briefing.append(f"  🔴 PRIMARY: {profile.primary_weakness.value.upper()}: "
                       f"{profile.skills[profile.primary_weakness].rating:.1f}/10")
        briefing.append(f"     Potential gain: {profile.skills[profile.primary_weakness].estimated_lap_time_gain:.2f}s")
        
        briefing.append(f"\n  🟡 SECONDARY: {profile.secondary_weakness.value.upper()}: "
                       f"{profile.skills[profile.secondary_weakness].rating:.1f}/10")
        briefing.append(f"     Potential gain: {profile.skills[profile.secondary_weakness].estimated_lap_time_gain:.2f}s")
        
        briefing.append("\nDEVELOPMENT PLAN:")
        briefing.append("\nShort-term goals (2-4 weeks):")
        for i, goal in enumerate(profile.short_term_goals, 1):
            briefing.append(f"  {i}. {goal}")
        
        briefing.append("\nCurrent Training Focus:")
        briefing.append(profile.current_training_focus)
        
        briefing.append("\nPERFORMANCE TRENDS:")
        briefing.append(f"  Lap Time: {profile.lap_time_trend}")
        briefing.append(f"  Consistency: {profile.consistency_trend}")
        briefing.append(f"  Incidents: {profile.incident_trend}")
        
        return "\n".join(briefing)
    
    def _rating_to_percentile(self, rating: float) -> float:
        """Convert 0-10 rating to percentile"""
        return min(100, rating * 10)
    
    def _default_assessment(self, skill: SkillArea) -> SkillAssessment:
        """Default assessment when no data"""
        return SkillAssessment(
            skill=skill,
            rating=7.0,
            percentile=70.0,
            data_points=0,
            confidence=0.0,
            strengths=[],
            weaknesses=["Insufficient data"],
            specific_issues=[],
            priority='medium',
            target_rating=8.0,
            estimated_lap_time_gain=0.1,
            training_exercises=["Gather more data"],
            focus_corners=[]
        )
    
    def _get_driver_name(self, driver_id: str) -> str:
        return f"Driver {driver_id}"
    
    def _get_irating(self, driver_id: str) -> int:
        return 2000  # Placeholder
    
    def _get_safety_rating(self, driver_id: str) -> float:
        return 3.5  # Placeholder


# Example usage
if __name__ == '__main__':
    print("AI Race Engineer - Complete Driver Assessment")
    print("=" * 70)
    print("\nProactively identifies what driver needs to work on:")
    print("\n🔴 PRIMARY WEAKNESS: Corner Exit (5.2/10)")
    print("   Potential gain: 0.5s per lap")
    print("   Training:")
    print("     • Practice progressive throttle application")
    print("     • Focus on exits onto straights")
    print("\n🟡 SECONDARY: Braking (6.8/10)")
    print("   Potential gain: 0.3s per lap")
    print("\n✅ STRENGTH: Consistency (8.9/10)")
