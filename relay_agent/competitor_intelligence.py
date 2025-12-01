"""
Competitor Intelligence System
Tracks all opponents, predicts strategy, detects incidents, finds opportunities
"""

import time
import statistics
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import deque
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class OpponentState:
    """Complete state of an opponent"""
    car_idx: int
    driver_name: str
    car_number: str
    car_class: str

    # Position & Timing
    position: int
    lap: int
    lap_pct: float
    last_lap_time: float
    best_lap_time: float
    average_lap_time: float
    lap_time_std_dev: float  # Consistency

    # Gaps
    gap_to_player: float
    gap_to_leader: float
    gap_to_ahead: float
    gap_to_behind: float

    # Predicted State
    predicted_fuel_remaining: float
    predicted_tire_wear: float  # 0-100%
    predicted_pit_lap: Optional[int]
    predicted_pit_window: Tuple[int, int]

    # Performance
    pace_trend: str  # 'improving', 'stable', 'degrading'
    consistency_rating: float  # 0-100%
    sector_performance: Dict[int, float]  # Sector -> avg time

    # Incidents & Mistakes
    incidents_count: int
    off_tracks_count: int
    last_incident_lap: Optional[int]
    mistake_prone_sectors: List[int]

    # Strategic Intelligence
    aggressive_rating: float  # 0-100%
    defensive_rating: float  # 0-100%
    overtake_success_rate: float  # 0-100%
    under_pressure: bool

    # Opportunities
    overtake_opportunity: bool
    overtake_confidence: float  # 0-100%
    best_attack_sector: Optional[int]
    defense_required: bool

    # Status
    on_track: bool
    in_pit: bool
    pit_stop_count: int
    laps_since_pit: int

    timestamp: float


@dataclass
class CompetitorIncident:
    """Recorded incident for an opponent"""
    car_idx: int
    driver_name: str
    incident_type: str  # 'off_track', 'spin', 'contact', 'slow'
    lap: int
    sector: int
    severity: str  # 'minor', 'moderate', 'major'
    time_lost: float  # Seconds
    timestamp: float


@dataclass
class OvertakeOpportunity:
    """Identified overtaking opportunity"""
    target_car_idx: int
    target_driver: str
    opportunity_type: str  # 'pace_advantage', 'tire_deg', 'mistake', 'pit_strategy'
    confidence: float  # 0-100%
    recommended_sector: int
    estimated_laps_to_overtake: int
    reason: str


class CompetitorIntelligence:
    """Tracks and analyzes all opponents"""

    def __init__(self):
        self.opponents: Dict[int, OpponentState] = {}
        self.lap_time_history: Dict[int, deque] = {}  # car_idx -> lap times
        self.sector_time_history: Dict[int, Dict[int, deque]] = {}  # car_idx -> sector -> times
        self.fuel_history: Dict[int, deque] = {}  # car_idx -> fuel levels
        self.position_history: Dict[int, deque] = {}  # car_idx -> positions
        self.incidents: List[CompetitorIncident] = []

        # Configuration
        self.lap_history_size = 20
        self.sector_history_size = 10
        self.fuel_history_size = 15

        # Detection thresholds
        self.off_track_speed_threshold = 0.7  # 70% of normal speed
        self.spin_yaw_rate_threshold = 2.0  # rad/s
        self.consistency_threshold = 0.5  # seconds std dev

        logger.info("Competitor Intelligence System initialized")

    def update_opponent(self, car_idx: int, telemetry: Dict):
        """Update opponent state from telemetry"""

        # Initialize tracking if new opponent
        if car_idx not in self.lap_time_history:
            self.lap_time_history[car_idx] = deque(maxlen=self.lap_history_size)
            self.sector_time_history[car_idx] = {}
            self.fuel_history[car_idx] = deque(maxlen=self.fuel_history_size)
            self.position_history[car_idx] = deque(maxlen=20)

        # Extract data
        lap = telemetry.get('lap', 0)
        lap_time = telemetry.get('last_lap_time', 0)
        position = telemetry.get('position', 0)
        fuel = telemetry.get('fuel', 0)
        sector = telemetry.get('sector', 0)

        # Track lap times
        if lap_time > 0:
            self.lap_time_history[car_idx].append(lap_time)

        # Track fuel
        if fuel > 0:
            self.fuel_history[car_idx].append({'lap': lap, 'fuel': fuel})

        # Track positions
        self.position_history[car_idx].append({'lap': lap, 'position': position})

        # Calculate metrics
        avg_lap = self._calculate_average_lap_time(car_idx)
        best_lap = self._calculate_best_lap_time(car_idx)
        consistency = self._calculate_consistency(car_idx)
        pace_trend = self._calculate_pace_trend(car_idx)

        # Predict fuel and tires
        predicted_fuel = self._predict_fuel_remaining(car_idx, lap)
        predicted_tire_wear = self._predict_tire_wear(car_idx, lap)
        predicted_pit = self._predict_pit_stop(car_idx, predicted_fuel, predicted_tire_wear)

        # Detect incidents
        self._detect_incidents(car_idx, telemetry, lap)

        # Analyze driving style
        aggression = self._analyze_aggression(car_idx)
        defensiveness = self._analyze_defensiveness(car_idx)

        # Find opportunities
        overtake_opp, attack_sector, confidence = self._identify_overtake_opportunity(
            car_idx, telemetry, predicted_tire_wear
        )

        # Create opponent state
        self.opponents[car_idx] = OpponentState(
            car_idx=car_idx,
            driver_name=telemetry.get('driver_name', f'Car {car_idx}'),
            car_number=telemetry.get('car_number', ''),
            car_class=telemetry.get('car_class', ''),

            position=position,
            lap=lap,
            lap_pct=telemetry.get('lap_pct', 0),
            last_lap_time=lap_time,
            best_lap_time=best_lap,
            average_lap_time=avg_lap,
            lap_time_std_dev=consistency,

            gap_to_player=telemetry.get('gap_to_player', 0),
            gap_to_leader=telemetry.get('gap_to_leader', 0),
            gap_to_ahead=telemetry.get('gap_ahead', 0),
            gap_to_behind=telemetry.get('gap_behind', 0),

            predicted_fuel_remaining=predicted_fuel,
            predicted_tire_wear=predicted_tire_wear,
            predicted_pit_lap=predicted_pit[0] if predicted_pit else None,
            predicted_pit_window=predicted_pit[1] if predicted_pit else (0, 0),

            pace_trend=pace_trend,
            consistency_rating=self._consistency_to_rating(consistency),
            sector_performance={},

            incidents_count=self._count_incidents(car_idx),
            off_tracks_count=self._count_off_tracks(car_idx),
            last_incident_lap=self._last_incident_lap(car_idx),
            mistake_prone_sectors=self._identify_mistake_sectors(car_idx),

            aggressive_rating=aggression,
            defensive_rating=defensiveness,
            overtake_success_rate=0,  # Track over time
            under_pressure=self._is_under_pressure(car_idx, telemetry),

            overtake_opportunity=overtake_opp,
            overtake_confidence=confidence,
            best_attack_sector=attack_sector,
            defense_required=self._should_defend(car_idx, telemetry),

            on_track=telemetry.get('on_track', True),
            in_pit=telemetry.get('in_pit', False),
            pit_stop_count=self._count_pit_stops(car_idx),
            laps_since_pit=self._laps_since_pit(car_idx, lap),

            timestamp=time.time()
        )

    def _calculate_average_lap_time(self, car_idx: int) -> float:
        """Calculate average lap time"""
        times = list(self.lap_time_history[car_idx])
        if len(times) >= 3:
            return statistics.mean(times)
        return 0

    def _calculate_best_lap_time(self, car_idx: int) -> float:
        """Get best lap time"""
        times = list(self.lap_time_history[car_idx])
        if times:
            return min(times)
        return 0

    def _calculate_consistency(self, car_idx: int) -> float:
        """Calculate lap time standard deviation"""
        times = list(self.lap_time_history[car_idx])
        if len(times) >= 5:
            return statistics.stdev(times)
        return 0

    def _consistency_to_rating(self, std_dev: float) -> float:
        """Convert std dev to 0-100 consistency rating"""
        if std_dev == 0:
            return 100
        # Lower std dev = higher consistency
        # 0.2s std dev = 95%, 0.5s = 80%, 1.0s = 50%
        rating = max(0, 100 - (std_dev * 50))
        return rating

    def _calculate_pace_trend(self, car_idx: int) -> str:
        """Determine if pace is improving, stable, or degrading"""
        times = list(self.lap_time_history[car_idx])
        if len(times) < 5:
            return 'stable'

        # Compare first half vs second half
        mid = len(times) // 2
        first_half = statistics.mean(times[:mid])
        second_half = statistics.mean(times[mid:])

        diff = second_half - first_half

        if diff < -0.2:  # Getting faster
            return 'improving'
        elif diff > 0.3:  # Getting slower (tire deg)
            return 'degrading'
        else:
            return 'stable'

    def _predict_fuel_remaining(self, car_idx: int, current_lap: int) -> float:
        """Predict opponent's fuel remaining"""
        fuel_data = list(self.fuel_history[car_idx])
        if len(fuel_data) < 3:
            return 50.0  # Unknown

        # Calculate fuel per lap
        consumptions = []
        for i in range(1, len(fuel_data)):
            if fuel_data[i]['fuel'] < fuel_data[i-1]['fuel']:  # Not a refuel
                fuel_used = fuel_data[i-1]['fuel'] - fuel_data[i]['fuel']
                laps = fuel_data[i]['lap'] - fuel_data[i-1]['lap']
                if laps > 0 and fuel_used > 0:
                    consumptions.append(fuel_used / laps)

        if consumptions:
            fuel_per_lap = statistics.median(consumptions)
            last_known_fuel = fuel_data[-1]['fuel']
            laps_since = current_lap - fuel_data[-1]['lap']
            predicted = last_known_fuel - (laps_since * fuel_per_lap)
            return max(0, predicted)

        return 50.0

    def _predict_tire_wear(self, car_idx: int, current_lap: int) -> float:
        """Predict opponent's tire wear from lap time degradation"""
        times = list(self.lap_time_history[car_idx])
        if len(times) < 5:
            return 100.0  # Unknown, assume good

        laps_on_tires = self._laps_since_pit(car_idx, current_lap)

        # Estimate wear from lap time falloff
        base_pace = min(times[:5])  # Best recent pace
        current_pace = statistics.mean(times[-3:])  # Recent 3 laps

        pace_degradation = current_pace - base_pace

        # Rough model: 0.1s slower = 10% wear
        wear_percent = min(100, pace_degradation * 100)

        # Time-based degradation
        time_wear = min(100, laps_on_tires * 1.5)  # 1.5% per lap

        # Combined estimate
        estimated_wear = max(wear_percent, time_wear)

        # Return grip remaining (100 = fresh, 0 = destroyed)
        return max(0, 100 - estimated_wear)

    def _predict_pit_stop(self, car_idx: int, fuel: float, tire_wear: float) -> Optional[Tuple[int, Tuple[int, int]]]:
        """Predict when opponent will pit"""

        # Need more data for prediction
        fuel_data = list(self.fuel_history[car_idx])
        if len(fuel_data) < 3:
            return None

        # Calculate fuel consumption
        consumptions = []
        for i in range(1, len(fuel_data)):
            if fuel_data[i]['fuel'] < fuel_data[i-1]['fuel']:
                fuel_used = fuel_data[i-1]['fuel'] - fuel_data[i]['fuel']
                laps = fuel_data[i]['lap'] - fuel_data[i-1]['lap']
                if laps > 0:
                    consumptions.append(fuel_used / laps)

        if not consumptions:
            return None

        fuel_per_lap = statistics.median(consumptions)
        laps_on_fuel = fuel / fuel_per_lap if fuel_per_lap > 0 else 999

        current_lap = fuel_data[-1]['lap']

        # Fuel-based pit lap
        fuel_pit_lap = int(current_lap + laps_on_fuel - 3)  # 3-lap buffer

        # Tire-based pit lap
        if tire_wear < 30:
            tire_pit_lap = current_lap + 2  # Soon
        elif tire_wear < 50:
            tire_pit_lap = current_lap + 5
        else:
            tire_pit_lap = 999  # Tires OK

        # Predicted pit lap = earliest need
        pit_lap = min(fuel_pit_lap, tire_pit_lap)

        if pit_lap < 999:
            window = (max(current_lap + 1, pit_lap - 3), pit_lap + 3)
            return (pit_lap, window)

        return None

    def _detect_incidents(self, car_idx: int, telemetry: Dict, lap: int):
        """Detect incidents and mistakes"""

        # Off-track detection (speed drop)
        avg_speed = self._get_average_speed(car_idx)
        current_speed = telemetry.get('speed', 0)

        if avg_speed > 0 and current_speed < avg_speed * self.off_track_speed_threshold:
            # Significant speed drop - likely off track
            self._record_incident(car_idx, 'off_track', lap, telemetry.get('sector', 0), 'moderate')

        # Spin detection (yaw rate)
        yaw_rate = abs(telemetry.get('yaw_rate', 0))
        if yaw_rate > self.spin_yaw_rate_threshold:
            self._record_incident(car_idx, 'spin', lap, telemetry.get('sector', 0), 'major')

        # Slow lap detection
        lap_time = telemetry.get('last_lap_time', 0)
        avg_lap = self._calculate_average_lap_time(car_idx)
        if lap_time > 0 and avg_lap > 0 and lap_time > avg_lap * 1.1:
            # 10% slower than average - mistake or incident
            self._record_incident(car_idx, 'slow', lap, 0, 'minor')

    def _record_incident(self, car_idx: int, incident_type: str, lap: int, sector: int, severity: str):
        """Record an incident"""
        incident = CompetitorIncident(
            car_idx=car_idx,
            driver_name=self.opponents.get(car_idx).driver_name if car_idx in self.opponents else '',
            incident_type=incident_type,
            lap=lap,
            sector=sector,
            severity=severity,
            time_lost=0,  # Calculate from lap time delta
            timestamp=time.time()
        )
        self.incidents.append(incident)
        logger.info(f"Incident detected: Car {car_idx} - {incident_type} on lap {lap}")

    def _get_average_speed(self, car_idx: int) -> float:
        """Get average speed for comparison"""
        # Simplified - would track speed history
        return 200.0  # km/h placeholder

    def _count_incidents(self, car_idx: int) -> int:
        """Count total incidents for car"""
        return sum(1 for i in self.incidents if i.car_idx == car_idx)

    def _count_off_tracks(self, car_idx: int) -> int:
        """Count off-track incidents"""
        return sum(1 for i in self.incidents if i.car_idx == car_idx and i.incident_type == 'off_track')

    def _last_incident_lap(self, car_idx: int) -> Optional[int]:
        """Get lap of last incident"""
        car_incidents = [i for i in self.incidents if i.car_idx == car_idx]
        if car_incidents:
            return car_incidents[-1].lap
        return None

    def _identify_mistake_sectors(self, car_idx: int) -> List[int]:
        """Identify sectors where driver makes mistakes"""
        car_incidents = [i for i in self.incidents if i.car_idx == car_idx]
        if not car_incidents:
            return []

        # Count incidents by sector
        sector_counts = {}
        for incident in car_incidents:
            sector = incident.sector
            sector_counts[sector] = sector_counts.get(sector, 0) + 1

        # Return sectors with multiple incidents
        return [s for s, count in sector_counts.items() if count >= 2]

    def _analyze_aggression(self, car_idx: int) -> float:
        """Analyze driver aggression (0-100)"""
        # Based on position changes, overtake attempts
        positions = list(self.position_history[car_idx])
        if len(positions) < 5:
            return 50.0  # Unknown

        # Count position gains vs losses
        gains = sum(1 for i in range(1, len(positions))
                   if positions[i]['position'] < positions[i-1]['position'])
        losses = sum(1 for i in range(1, len(positions))
                    if positions[i]['position'] > positions[i-1]['position'])

        if gains + losses == 0:
            return 50.0

        # Higher gains = more aggressive
        aggression = (gains / (gains + losses)) * 100
        return aggression

    def _analyze_defensiveness(self, car_idx: int) -> float:
        """Analyze defensive driving (0-100)"""
        # Inverse of aggression + consistency
        aggression = self._analyze_aggression(car_idx)
        consistency = self._consistency_to_rating(self._calculate_consistency(car_idx))

        # High consistency + low aggression = defensive
        defensiveness = (100 - aggression) * 0.5 + consistency * 0.5
        return defensiveness

    def _is_under_pressure(self, car_idx: int, telemetry: Dict) -> bool:
        """Determine if driver is under pressure"""
        gap_behind = telemetry.get('gap_behind', 999)
        incidents_recent = sum(1 for i in self.incidents
                             if i.car_idx == car_idx and
                             telemetry.get('lap', 0) - i.lap < 3)

        # Under pressure if car close behind or recent mistakes
        return gap_behind < 1.5 or incidents_recent > 0

    def _identify_overtake_opportunity(self, car_idx: int, telemetry: Dict,
                                      tire_wear: float) -> Tuple[bool, Optional[int], float]:
        """Identify if this car presents an overtaking opportunity"""

        gap = telemetry.get('gap_ahead', 999)

        # Not an opportunity if car is ahead
        if gap < 0:
            return (False, None, 0)

        confidence = 0
        best_sector = None

        # Opportunity factors:

        # 1. Close gap
        if 0 < gap < 2.0:
            confidence += 30

        # 2. Degraded tires
        if tire_wear < 60:
            confidence += 20
            best_sector = 3  # Attack where they're weak

        # 3. Recent mistakes
        if self._count_incidents(car_idx) > 0:
            confidence += 25
            mistake_sectors = self._identify_mistake_sectors(car_idx)
            if mistake_sectors:
                best_sector = mistake_sectors[0]

        # 4. Pace trend degrading
        if self._calculate_pace_trend(car_idx) == 'degrading':
            confidence += 15

        # 5. Low consistency
        consistency = self._consistency_to_rating(self._calculate_consistency(car_idx))
        if consistency < 70:
            confidence += 10

        opportunity = confidence > 40  # 40% confidence threshold

        return (opportunity, best_sector, min(100, confidence))

    def _should_defend(self, car_idx: int, telemetry: Dict) -> bool:
        """Determine if defense is required against this car"""
        gap_behind = telemetry.get('gap_behind', 999)

        # Defend if car within 2 seconds
        if 0 < gap_behind < 2.0:
            # Check if they're faster
            their_pace = self._calculate_average_lap_time(car_idx)
            my_pace = telemetry.get('my_average_pace', 0)

            if their_pace > 0 and my_pace > 0 and their_pace < my_pace:
                return True  # They're faster, defend

        return False

    def _count_pit_stops(self, car_idx: int) -> int:
        """Count pit stops from fuel increases"""
        fuel_data = list(self.fuel_history[car_idx])
        if len(fuel_data) < 2:
            return 0

        pit_count = 0
        for i in range(1, len(fuel_data)):
            if fuel_data[i]['fuel'] > fuel_data[i-1]['fuel'] + 5:  # Refueled
                pit_count += 1

        return pit_count

    def _laps_since_pit(self, car_idx: int, current_lap: int) -> int:
        """Laps since last pit stop"""
        fuel_data = list(self.fuel_history[car_idx])
        if len(fuel_data) < 2:
            return current_lap

        # Find last refuel
        for i in range(len(fuel_data) - 1, 0, -1):
            if fuel_data[i]['fuel'] > fuel_data[i-1]['fuel'] + 5:
                return current_lap - fuel_data[i]['lap']

        return current_lap

    def get_strategic_report(self) -> Dict:
        """Get complete strategic intelligence report"""

        # Identify key threats and opportunities
        threats = []
        opportunities = []

        for car_idx, opponent in self.opponents.items():
            if opponent.defense_required:
                threats.append({
                    'carIdx': car_idx,
                    'driver': opponent.driver_name,
                    'gap': opponent.gap_to_player,
                    'threat': 'faster_pace',
                    'recommended_action': 'defend'
                })

            if opponent.overtake_opportunity:
                opportunities.append({
                    'carIdx': car_idx,
                    'driver': opponent.driver_name,
                    'gap': opponent.gap_to_player,
                    'confidence': opponent.overtake_confidence,
                    'reason': self._get_opportunity_reason(opponent),
                    'attackSector': opponent.best_attack_sector
                })

        # Sort by priority
        threats.sort(key=lambda x: x['gap'])
        opportunities.sort(key=lambda x: x['confidence'], reverse=True)

        return {
            'totalOpponents': len(self.opponents),
            'threats': threats,
            'opportunities': opportunities[:5],  # Top 5
            'incidentsDetected': len(self.incidents),
            'recentIncidents': self._get_recent_incidents(5)
        }

    def _get_opportunity_reason(self, opponent: OpponentState) -> str:
        """Get reason for overtaking opportunity"""
        reasons = []

        if opponent.predicted_tire_wear < 60:
            reasons.append('degraded_tires')

        if opponent.incidents_count > 0:
            reasons.append('making_mistakes')

        if opponent.pace_trend == 'degrading':
            reasons.append('pace_falling_off')

        if opponent.consistency_rating < 70:
            reasons.append('inconsistent')

        return ', '.join(reasons) if reasons else 'pace_advantage'

    def _get_recent_incidents(self, count: int) -> List[Dict]:
        """Get most recent incidents"""
        recent = sorted(self.incidents, key=lambda x: x.timestamp, reverse=True)[:count]
        return [asdict(i) for i in recent]


if __name__ == '__main__':
    print("Competitor Intelligence System Test")
    print("=" * 70)

    intel = CompetitorIntelligence()

    # Simulate tracking 3 opponents
    for lap in range(1, 16):
        for car_idx in [1, 2, 3]:
            telemetry = {
                'lap': lap,
                'last_lap_time': 90 + (lap * 0.1) + (car_idx * 0.2),  # Degrading
                'position': car_idx,
                'fuel': 80 - (lap * 2.2),
                'speed': 200 - (lap * 0.5) if car_idx == 2 else 200,  # Car 2 slowing
                'gap_to_player': car_idx * 2.0,
                'gap_ahead': 2.0,
                'gap_behind': 2.0,
                'driver_name': f'Driver {car_idx}',
                'car_number': str(car_idx),
                'car_class': 'GT3',
                'on_track': True,
                'in_pit': False,
                'sector': lap % 3
            }

            intel.update_opponent(car_idx, telemetry)

    # Get strategic report
    report = intel.get_strategic_report()

    print(f"\n✓ Tracking {report['totalOpponents']} opponents")
    print(f"  Opportunities identified: {len(report['opportunities'])}")
    print(f"  Threats detected: {len(report['threats'])}")
    print(f"  Incidents detected: {report['incidentsDetected']}")

    if report['opportunities']:
        print("\n  Top Opportunity:")
        opp = report['opportunities'][0]
        print(f"    Driver: {opp['driver']}")
        print(f"    Confidence: {opp['confidence']:.0f}%")
        print(f"    Reason: {opp['reason']}")

    print("\n" + "=" * 70)
    print("✓ Competitor intelligence system ready")
