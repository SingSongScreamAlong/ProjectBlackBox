"""
Racing Discipline-Specific Strategy
Oval, Endurance, Formula racing with discipline-specific calculations
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import statistics
import time


# ==================== OVAL RACING ====================

@dataclass
class OvalStrategy:
    """Oval racing strategy (NASCAR, IndyCar ovals)"""
    draft_benefit: float  # Speed gain from drafting (km/h)
    fuel_window_start: int  # Green flag pit window start lap
    fuel_window_end: int  # Green flag pit window end lap
    track_position_value: float  # Value of track position (seconds)
    caution_probability: float  # Likelihood of caution (0-1)
    pit_cycle_position: int  # Position in pit cycle
    two_tire_vs_four: str  # Recommendation: '2_tire' or '4_tire'
    wave_around_eligible: bool  # Can take wave-around
    lucky_dog_eligible: bool  # Can take lucky dog
    restart_strategy: str  # 'inside' or 'outside' lane choice


class OvalRacingEngine:
    """Oval racing specific strategy calculations"""

    def __init__(self):
        self.draft_speed_gain = 8.0  # km/h typical draft gain
        self.caution_fuel_save = 0.3  # Liters saved per caution lap
        self.pit_road_speed = 80.0  # km/h pit road speed limit
        self.avg_caution_laps = 5  # Average caution duration

    def calculate_draft_strategy(self, current_speed: float, car_ahead_distance: float) -> Dict:
        """Calculate drafting strategy and benefits"""

        # Optimal drafting distance (car lengths)
        optimal_draft_distance = 2.0  # 2 car lengths

        # Current draft benefit
        if car_ahead_distance < 1.0:
            draft_benefit = self.draft_speed_gain
        elif car_ahead_distance < 3.0:
            # Linear falloff
            draft_benefit = self.draft_speed_gain * (1 - (car_ahead_distance / 3.0))
        else:
            draft_benefit = 0

        # Strategy
        if car_ahead_distance > optimal_draft_distance:
            action = 'close_gap'
            reason = f'Close to {optimal_draft_distance:.1f} car lengths for optimal draft'
        elif car_ahead_distance < 0.5:
            action = 'maintain_gap'
            reason = 'Risk of contact - maintain safe distance'
        else:
            action = 'optimal_draft'
            reason = f'In optimal draft zone - gaining {draft_benefit:.1f} km/h'

        return {
            'currentDraftBenefit': draft_benefit,
            'optimalDistance': optimal_draft_distance,
            'action': action,
            'reason': reason,
            'timeSaved': draft_benefit / current_speed if current_speed > 0 else 0
        }

    def calculate_oval_fuel_window(self, current_lap: int, fuel_remaining: float,
                                   fuel_per_lap: float, race_laps: int) -> OvalStrategy:
        """Calculate fuel strategy for oval racing"""

        # Laps remaining on fuel
        laps_on_fuel = fuel_remaining / fuel_per_lap if fuel_per_lap > 0 else 0

        # Green flag pit window
        laps_to_go = race_laps - current_lap
        fuel_window_start = current_lap + int(laps_on_fuel * 0.8)  # 80% of fuel
        fuel_window_end = current_lap + int(laps_on_fuel) - 2  # 2 lap buffer

        # Caution probability increases with laps run
        caution_prob = min(0.8, (current_lap / race_laps) * 0.5 + 0.3)

        # Track position value (seconds lost per position)
        track_position_value = 0.3  # Seconds per position on oval

        # Two-tire vs four-tire strategy
        if laps_to_go < 20:
            tire_strategy = '2_tire'  # Faster stop for track position
            reason = 'Late race - track position critical'
        elif laps_to_go > 50:
            tire_strategy = '4_tire'  # Full service early
            reason = 'Early race - optimize tire life'
        else:
            tire_strategy = '4_tire'  # Default to four
            reason = 'Mid race - full service recommended'

        return OvalStrategy(
            draft_benefit=self.draft_speed_gain,
            fuel_window_start=fuel_window_start,
            fuel_window_end=fuel_window_end,
            track_position_value=track_position_value,
            caution_probability=caution_prob,
            pit_cycle_position=0,  # Calculate from field positions
            two_tire_vs_four=tire_strategy,
            wave_around_eligible=False,  # Check lap down status
            lucky_dog_eligible=False,  # Check if first lap down
            restart_strategy='inside'  # Preferred lane
        )

    def caution_pit_strategy(self, current_fuel: float, laps_to_go: int,
                            fuel_per_lap: float) -> Dict:
        """Strategy decision during caution"""

        laps_on_fuel = current_fuel / fuel_per_lap if fuel_per_lap > 0 else 0

        # Pit if can't make it
        if laps_on_fuel < laps_to_go:
            return {
                'action': 'pit',
                'reason': f'Fuel for {laps_on_fuel:.0f} laps, need {laps_to_go}',
                'priority': 'critical'
            }

        # Pit if marginal and can gain track position
        elif laps_on_fuel < laps_to_go + 5:
            return {
                'action': 'pit',
                'reason': 'Marginal fuel - pit under caution',
                'priority': 'high'
            }

        # Stay out if comfortable
        else:
            return {
                'action': 'stay_out',
                'reason': f'Fuel for {laps_on_fuel:.0f} laps - stay for track position',
                'priority': 'low'
            }


# ==================== ENDURANCE RACING ====================

@dataclass
class EnduranceStrategy:
    """Endurance racing strategy"""
    current_stint_laps: int
    optimal_stint_length: int
    driver_fatigue_level: float  # 0-100%
    next_driver_change_lap: int
    fuel_strategy: str  # 'splash', 'full_tank', 'calculated'
    tire_strategy: str  # 'minimum', 'full_change', 'fronts_only'
    time_of_day: str  # 'day', 'dusk', 'night', 'dawn'
    traffic_density: str  # 'light', 'medium', 'heavy'
    code_60_active: bool  # Slow zone active
    total_race_time_elapsed: float  # Hours
    estimated_time_remaining: float  # Hours


class EnduranceRacingEngine:
    """Endurance racing specific strategy"""

    def __init__(self):
        self.max_stint_laps = 65  # Typical maximum stint
        self.min_stint_laps = 30  # Minimum for efficiency
        self.driver_change_time = 60.0  # Seconds
        self.fatigue_threshold = 75.0  # % fatigue for driver change

    def calculate_stint_strategy(self, current_stint_laps: int, driver_fatigue: float,
                                fuel_remaining: float, fuel_per_lap: float) -> EnduranceStrategy:
        """Calculate optimal stint length and driver change timing"""

        # Optimal stint length (balance fuel, tires, driver)
        fuel_stint_laps = int(fuel_remaining / fuel_per_lap) if fuel_per_lap > 0 else 0
        tire_optimal = 55  # Laps for tire life
        driver_optimal = 60  # Laps for driver performance

        optimal_stint = min(fuel_stint_laps, tire_optimal, driver_optimal)

        # Driver fatigue increases with stint length
        fatigue_rate = 1.2  # % per lap
        estimated_fatigue = driver_fatigue + (current_stint_laps * fatigue_rate)

        # Next driver change lap
        if estimated_fatigue > self.fatigue_threshold:
            next_change = current_stint_laps + 5  # Soon
        else:
            laps_until_fatigue = int((self.fatigue_threshold - driver_fatigue) / fatigue_rate)
            next_change = current_stint_laps + laps_until_fatigue

        # Fuel strategy for endurance
        if fuel_stint_laps < 10:
            fuel_strat = 'splash'  # Quick splash only
        elif fuel_stint_laps < 30:
            fuel_strat = 'calculated'  # Calculated amount
        else:
            fuel_strat = 'full_tank'  # Fill it up

        # Tire strategy
        if current_stint_laps > 50:
            tire_strat = 'full_change'  # New set
        elif current_stint_laps > 30:
            tire_strat = 'fronts_only'  # Fronts wear faster
        else:
            tire_strat = 'minimum'  # Leave tires on

        return EnduranceStrategy(
            current_stint_laps=current_stint_laps,
            optimal_stint_length=optimal_stint,
            driver_fatigue_level=estimated_fatigue,
            next_driver_change_lap=next_change,
            fuel_strategy=fuel_strat,
            tire_strategy=tire_strat,
            time_of_day='day',  # From telemetry
            traffic_density='medium',  # From car count
            code_60_active=False,  # From flags
            total_race_time_elapsed=0,
            estimated_time_remaining=0
        )

    def calculate_multi_class_strategy(self, car_class: str, traffic_data: List[Dict]) -> Dict:
        """Strategy for multi-class endurance racing"""

        # Separate by class
        class_order = ['LMP1', 'LMP2', 'GTE-Pro', 'GTE-Am', 'GT3']

        faster_classes = []
        slower_classes = []

        my_class_idx = class_order.index(car_class) if car_class in class_order else 2

        for i, cls in enumerate(class_order):
            if i < my_class_idx:
                faster_classes.append(cls)
            elif i > my_class_idx:
                slower_classes.append(cls)

        # Strategy based on traffic
        if faster_classes:
            traffic_strategy = 'give_room'
            reason = f'Yield to faster {faster_classes[0]} traffic'
        elif slower_classes:
            traffic_strategy = 'pass_safely'
            reason = f'Pass slower {slower_classes[0]} traffic cleanly'
        else:
            traffic_strategy = 'race_pace'
            reason = 'Same class - race normally'

        return {
            'strategy': traffic_strategy,
            'reason': reason,
            'fasterClasses': faster_classes,
            'slowerClasses': slower_classes
        }


# ==================== FORMULA RACING ====================

@dataclass
class FormulaStrategy:
    """Formula racing strategy (F1, F3, etc.)"""
    drs_available: bool
    drs_zones: List[int]  # Zone numbers where DRS available
    ers_deploy_mode: str  # 'qualifying', 'medium', 'conserve'
    ers_battery_pct: float  # 0-100%
    tire_compound: str  # 'soft', 'medium', 'hard', 'wet', 'inter'
    tire_age: int  # Laps on current tires
    push_to_pass_count: int  # Remaining P2P (IndyCar)
    fuel_mode: str  # 'lean', 'standard', 'rich'
    brake_balance: float  # Front bias %
    differential: str  # Diff setting


class FormulaRacingEngine:
    """Formula racing specific strategy"""

    def __init__(self):
        self.drs_speed_gain = 12.0  # km/h typical DRS gain
        self.ers_max_deployment = 4.0  # MJ per lap (F1)
        self.tire_degradation_rates = {
            'soft': 1.5,  # % per lap
            'medium': 1.0,
            'hard': 0.7,
            'wet': 0.5,
            'inter': 0.8
        }

    def calculate_drs_strategy(self, drs_available: bool, drs_zones: List[int],
                               gap_ahead: float, lap_sector: int) -> Dict:
        """DRS usage strategy"""

        if not drs_available:
            return {
                'action': 'not_available',
                'reason': 'DRS not enabled or no car within 1 second',
                'zones': []
            }

        # Check if in DRS zone
        in_zone = lap_sector in drs_zones

        if gap_ahead < 1.0 and in_zone:
            return {
                'action': 'activate',
                'reason': f'DRS available - {self.drs_speed_gain:.0f} km/h gain',
                'zones': drs_zones,
                'speedGain': self.drs_speed_gain
            }
        elif gap_ahead < 1.0:
            return {
                'action': 'prepare',
                'reason': 'DRS available next zone',
                'zones': drs_zones,
                'nextZone': drs_zones[0] if drs_zones else None
            }
        else:
            return {
                'action': 'push',
                'reason': f'Gap {gap_ahead:.1f}s - close to 1.0s for DRS',
                'zones': drs_zones
            }

    def calculate_ers_strategy(self, ers_battery_pct: float, lap_type: str,
                               gap_ahead: float, gap_behind: float) -> FormulaStrategy:
        """ERS deployment strategy"""

        # Deployment modes
        if lap_type == 'qualifying':
            deploy_mode = 'qualifying'  # Max deployment
            reason = 'Qualifying - maximum deployment'

        elif gap_ahead < 1.0:
            deploy_mode = 'overtake'  # Attack mode
            reason = f'Attack mode - close gap {gap_ahead:.1f}s'

        elif gap_behind < 1.5:
            deploy_mode = 'defend'  # Defend position
            reason = f'Defend mode - car behind {gap_behind:.1f}s'

        elif ers_battery_pct < 30:
            deploy_mode = 'conserve'  # Recharge
            reason = 'Low battery - conserve and recharge'

        else:
            deploy_mode = 'medium'  # Balanced
            reason = 'Balanced deployment'

        return FormulaStrategy(
            drs_available=False,  # From telemetry
            drs_zones=[],  # From track data
            ers_deploy_mode=deploy_mode,
            ers_battery_pct=ers_battery_pct,
            tire_compound='medium',  # From telemetry
            tire_age=0,  # From stint tracking
            push_to_pass_count=0,  # IndyCar specific
            fuel_mode='standard',
            brake_balance=52.0,  # %
            differential='mid'
        )

    def calculate_tire_compound_strategy(self, race_laps: int, current_lap: int,
                                        weather: str) -> Dict:
        """Tire compound strategy for formula racing"""

        laps_remaining = race_laps - current_lap

        # Wet conditions
        if weather in ['rain', 'heavy_rain']:
            return {
                'compound': 'wet',
                'reason': 'Rain - full wet tires',
                'expectedStintLaps': 50
            }
        elif weather == 'light_rain':
            return {
                'compound': 'inter',
                'reason': 'Light rain - intermediates',
                'expectedStintLaps': 40
            }

        # Dry conditions - strategic choice
        if laps_remaining > 30:
            compound = 'hard'
            stint_laps = 35
            reason = 'Long stint - hard compound'
        elif laps_remaining > 15:
            compound = 'medium'
            stint_laps = 25
            reason = 'Medium stint - balanced compound'
        else:
            compound = 'soft'
            stint_laps = 15
            reason = 'Short stint - maximum pace'

        return {
            'compound': compound,
            'reason': reason,
            'expectedStintLaps': stint_laps,
            'degradationRate': self.tire_degradation_rates.get(compound, 1.0)
        }


# ==================== TEAM PRINCIPAL MODE ====================

class TeamPrincipalEngine:
    """Multi-driver team management and strategy"""

    def __init__(self):
        self.drivers = {}
        self.team_strategy = {}

    def add_driver(self, driver_id: str, driver_data: Dict):
        """Add driver to team"""
        self.drivers[driver_id] = {
            'id': driver_id,
            'name': driver_data.get('name'),
            'current_position': driver_data.get('position', 0),
            'current_lap': driver_data.get('lap', 0),
            'fuel': driver_data.get('fuel', 0),
            'last_pit_lap': 0,
            'status': 'active'
        }

    def team_strategy_overview(self) -> Dict:
        """Get team-wide strategy overview"""

        team_positions = [d['current_position'] for d in self.drivers.values()]
        team_laps = [d['current_lap'] for d in self.drivers.values()]

        return {
            'totalDrivers': len(self.drivers),
            'bestPosition': min(team_positions) if team_positions else 0,
            'averagePosition': statistics.mean(team_positions) if team_positions else 0,
            'driversOnLead Lap': sum(1 for d in self.drivers.values() if d['current_lap'] == max(team_laps)),
            'teamStrategy': 'race_pace'  # or 'fuel_save', 'attack', etc.
        }

    def coordinate_pit_strategy(self) -> List[Dict]:
        """Coordinate pit stops across team to avoid conflicts"""

        pit_schedule = []

        for driver_id, driver in self.drivers.items():
            # Calculate when each driver should pit
            # Stagger to avoid pit box conflicts
            pit_schedule.append({
                'driverId': driver_id,
                'driverName': driver['name'],
                'recommendedPitLap': driver['current_lap'] + 10,  # Example
                'pitType': 'service',
                'priority': 'medium'
            })

        return pit_schedule


if __name__ == '__main__':
    print("Racing Disciplines Strategy Test")
    print("=" * 70)

    # Test Oval
    print("\n=== OVAL RACING ===")
    oval = OvalRacingEngine()
    draft_strat = oval.calculate_draft_strategy(200, 1.5)
    print(f"Draft strategy: {draft_strat['action']} - {draft_strat['reason']}")

    oval_strat = oval.calculate_oval_fuel_window(50, 45, 2.2, 200)
    print(f"Pit window: Lap {oval_strat.fuel_window_start}-{oval_strat.fuel_window_end}")
    print(f"Tire strategy: {oval_strat.two_tire_vs_four}")

    # Test Endurance
    print("\n=== ENDURANCE RACING ===")
    endurance = EnduranceRacingEngine()
    stint_strat = endurance.calculate_stint_strategy(45, 60, 40, 1.8)
    print(f"Current stint: {stint_strat.current_stint_laps} laps")
    print(f"Driver fatigue: {stint_strat.driver_fatigue_level:.0f}%")
    print(f"Next driver change: Lap {stint_strat.next_driver_change_lap}")

    # Test Formula
    print("\n=== FORMULA RACING ===")
    formula = FormulaRacingEngine()
    drs_strat = formula.calculate_drs_strategy(True, [1, 3], 0.8, 1)
    print(f"DRS strategy: {drs_strat['action']} - {drs_strat['reason']}")

    ers_strat = formula.calculate_ers_strategy(75, 'race', 0.9, 3.5)
    print(f"ERS mode: {ers_strat.ers_deploy_mode}")

    # Test Team Principal
    print("\n=== TEAM PRINCIPAL ===")
    team = TeamPrincipalEngine()
    team.add_driver('driver1', {'name': 'Driver 1', 'position': 3, 'lap': 45, 'fuel': 40})
    team.add_driver('driver2', {'name': 'Driver 2', 'position': 7, 'lap': 45, 'fuel': 35})

    overview = team.team_strategy_overview()
    print(f"Team: {overview['totalDrivers']} drivers")
    print(f"Best position: P{overview['bestPosition']}")
    print(f"Average position: P{overview['averagePosition']:.0f}")

    print("\n" + "=" * 70)
    print("✓ All racing disciplines ready")
