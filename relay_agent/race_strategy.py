"""
Race Strategy Engine for iRacing
Provides fuel calculations, tire degradation, pit stop optimization, and real-time strategy
"""

import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import statistics
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FuelData:
    """Fuel consumption and remaining laps data"""
    current_fuel: float  # Liters
    fuel_per_lap: float  # Average liters/lap
    remaining_laps: float  # Laps until empty
    total_laps_to_go: int  # Remaining race laps
    need_to_pit: bool  # Whether pit stop is required
    recommended_fuel_add: float  # Liters to add at pit stop
    fuel_saving_required: float  # % fuel saving needed (0-100)
    can_finish: bool  # Can finish race without additional fuel


@dataclass
class TireData:
    """Tire degradation and performance data"""
    laps_on_tires: int
    temps: Dict[str, float]  # LF, RF, LR, RR temperatures
    avg_temp: float
    temp_trend: str  # 'stable', 'rising', 'falling'
    optimal_window: bool  # Within optimal temp range
    degradation_rate: float  # Grip loss per lap (estimated %)
    grip_remaining: float  # Estimated grip % (100 = new)
    recommended_change_lap: Optional[int]  # When to change tires
    overheating: bool  # Tires overheating


@dataclass
class PitWindow:
    """Pit stop window calculation"""
    optimal_lap: int  # Best lap to pit
    window_start: int  # Earliest beneficial lap
    window_end: int  # Latest possible lap
    reason: str  # Why this window (fuel, tires, strategy)
    undercut_opportunity: bool  # Can undercut car ahead
    overcut_opportunity: bool  # Better to stay out longer
    time_lost_in_pit: float  # Estimated pit time loss (seconds)
    positions_at_risk: int  # Positions could lose during pit


@dataclass
class StrategyRecommendation:
    """Overall race strategy recommendation"""
    action: str  # 'pit_now', 'pit_next_lap', 'stay_out', 'fuel_save', 'push'
    reason: str  # Explanation
    priority: str  # 'critical', 'high', 'medium', 'low'
    data: Dict  # Supporting data
    timestamp: float


class RaceStrategyEngine:
    """
    Race Strategy Calculator
    Handles fuel, tires, pit stops, and real-time strategy optimization
    """

    def __init__(self):
        # Historical data tracking
        self.fuel_history: List[Dict] = []
        self.lap_times: List[float] = []
        self.tire_temps_history: List[Dict] = []
        self.pit_stops: List[Dict] = []

        # Race parameters (set by user or detected)
        self.race_laps: Optional[int] = None
        self.fuel_capacity: float = 100.0  # Default, adjust per car
        self.tire_optimal_temp_min: float = 85.0  # °C
        self.tire_optimal_temp_max: float = 95.0  # °C
        self.avg_pit_time: float = 45.0  # seconds

        # Current stint tracking
        self.stint_start_lap: int = 0
        self.stint_start_fuel: float = 0

        logger.info("Race Strategy Engine initialized")

    def update_telemetry(self, telemetry: Dict):
        """Update strategy calculations with latest telemetry"""
        current_lap = telemetry.get('lap', 0)

        # Track fuel consumption
        if 'fuel' in telemetry:
            self.fuel_history.append({
                'lap': current_lap,
                'fuel': telemetry['fuel'],
                'timestamp': time.time()
            })

        # Track lap times
        if 'last_lap_time' in telemetry and telemetry['last_lap_time'] > 0:
            self.lap_times.append(telemetry['last_lap_time'])

        # Track tire temps
        if all(key in telemetry for key in ['tire_temp_lf', 'tire_temp_rf', 'tire_temp_lr', 'tire_temp_rr']):
            self.tire_temps_history.append({
                'lap': current_lap,
                'lf': telemetry['tire_temp_lf'],
                'rf': telemetry['tire_temp_rf'],
                'lr': telemetry['tire_temp_lr'],
                'rr': telemetry['tire_temp_rr'],
                'timestamp': time.time()
            })

        # Detect pit stops (fuel increase)
        if len(self.fuel_history) >= 2:
            fuel_delta = self.fuel_history[-1]['fuel'] - self.fuel_history[-2]['fuel']
            if fuel_delta > 5.0:  # Refueled
                self.pit_stops.append({
                    'lap': current_lap,
                    'fuel_added': fuel_delta,
                    'timestamp': time.time()
                })
                self.stint_start_lap = current_lap
                self.stint_start_fuel = self.fuel_history[-1]['fuel']
                logger.info(f"Pit stop detected on lap {current_lap}, +{fuel_delta:.1f}L fuel")

    def calculate_fuel_strategy(self, current_fuel: float, current_lap: int) -> FuelData:
        """Calculate fuel consumption and remaining laps"""

        # Calculate fuel per lap
        fuel_per_lap = self._calculate_fuel_per_lap()

        # Remaining laps on current fuel
        remaining_laps = current_fuel / fuel_per_lap if fuel_per_lap > 0 else 999

        # Race laps remaining
        race_laps_to_go = (self.race_laps or 100) - current_lap

        # Can finish without pitting?
        can_finish = remaining_laps >= race_laps_to_go

        # Do we need to pit?
        need_to_pit = not can_finish

        # Recommended fuel to add
        if need_to_pit:
            fuel_needed = (race_laps_to_go * fuel_per_lap) - current_fuel
            recommended_fuel_add = min(fuel_needed, self.fuel_capacity)
        else:
            recommended_fuel_add = 0

        # Fuel saving required?
        if not can_finish and remaining_laps > 0:
            fuel_saving_pct = ((race_laps_to_go - remaining_laps) / race_laps_to_go) * 100
            fuel_saving_pct = max(0, min(100, fuel_saving_pct))
        else:
            fuel_saving_pct = 0

        return FuelData(
            current_fuel=current_fuel,
            fuel_per_lap=fuel_per_lap,
            remaining_laps=remaining_laps,
            total_laps_to_go=race_laps_to_go,
            need_to_pit=need_to_pit,
            recommended_fuel_add=recommended_fuel_add,
            fuel_saving_required=fuel_saving_pct,
            can_finish=can_finish
        )

    def _calculate_fuel_per_lap(self) -> float:
        """Calculate average fuel consumption per lap"""
        if len(self.fuel_history) < 5:
            return 2.5  # Default estimate

        # Use recent history (last 10 laps)
        recent = self.fuel_history[-10:]

        # Calculate consumption between laps
        consumptions = []
        for i in range(1, len(recent)):
            fuel_delta = recent[i-1]['fuel'] - recent[i]['fuel']
            lap_delta = recent[i]['lap'] - recent[i-1]['lap']

            # Only count normal consumption (not pit stops)
            if 0 < fuel_delta < 10 and lap_delta == 1:
                consumptions.append(fuel_delta)

        if consumptions:
            return statistics.median(consumptions)  # Use median to avoid outliers

        return 2.5  # Fallback

    def calculate_tire_strategy(self, telemetry: Dict, current_lap: int) -> TireData:
        """Calculate tire degradation and optimal pit timing"""

        # Current tire temps
        temps = {
            'LF': telemetry.get('tire_temp_lf', 0),
            'RF': telemetry.get('tire_temp_rf', 0),
            'LR': telemetry.get('tire_temp_lr', 0),
            'RR': telemetry.get('tire_temp_rr', 0)
        }

        avg_temp = sum(temps.values()) / 4 if any(temps.values()) else 0

        # Check optimal window
        optimal_window = self.tire_optimal_temp_min <= avg_temp <= self.tire_optimal_temp_max

        # Check overheating
        overheating = any(t > self.tire_optimal_temp_max + 10 for t in temps.values())

        # Temperature trend
        temp_trend = self._calculate_temp_trend()

        # Laps on current tires
        laps_on_tires = current_lap - self.stint_start_lap

        # Degradation rate (simplified model)
        degradation_rate = self._estimate_degradation_rate(laps_on_tires, avg_temp)

        # Grip remaining estimate
        grip_remaining = max(0, 100 - (laps_on_tires * degradation_rate))

        # Recommended change lap
        if grip_remaining < 40:  # Less than 40% grip
            recommended_change_lap = current_lap + 1  # Change ASAP
        elif grip_remaining < 60:  # Getting worn
            recommended_change_lap = current_lap + 3  # Soon
        else:
            recommended_change_lap = None  # Tires still good

        return TireData(
            laps_on_tires=laps_on_tires,
            temps=temps,
            avg_temp=avg_temp,
            temp_trend=temp_trend,
            optimal_window=optimal_window,
            degradation_rate=degradation_rate,
            grip_remaining=grip_remaining,
            recommended_change_lap=recommended_change_lap,
            overheating=overheating
        )

    def _calculate_temp_trend(self) -> str:
        """Calculate tire temperature trend"""
        if len(self.tire_temps_history) < 3:
            return 'stable'

        recent = self.tire_temps_history[-3:]
        temps = [sum([t['lf'], t['rf'], t['lr'], t['rr']]) / 4 for t in recent]

        if temps[-1] > temps[0] + 5:
            return 'rising'
        elif temps[-1] < temps[0] - 5:
            return 'falling'
        else:
            return 'stable'

    def _estimate_degradation_rate(self, laps: int, avg_temp: float) -> float:
        """Estimate tire degradation rate per lap"""
        base_rate = 0.5  # 0.5% per lap base

        # Higher temps = faster degradation
        if avg_temp > self.tire_optimal_temp_max:
            temp_multiplier = 1 + ((avg_temp - self.tire_optimal_temp_max) / 50)
        else:
            temp_multiplier = 1.0

        # Degradation accelerates with wear
        wear_multiplier = 1 + (laps * 0.01)  # Increases 1% per lap

        return base_rate * temp_multiplier * wear_multiplier

    def calculate_pit_window(
        self,
        current_lap: int,
        fuel_data: FuelData,
        tire_data: TireData,
        gap_ahead: float,
        gap_behind: float
    ) -> PitWindow:
        """Calculate optimal pit stop window"""

        race_laps_remaining = (self.race_laps or 100) - current_lap

        # Determine reasons to pit
        reasons = []

        # Fuel-based window
        if fuel_data.need_to_pit:
            fuel_pit_lap = current_lap + int(fuel_data.remaining_laps) - 2  # 2-lap buffer
            reasons.append(f"fuel ({fuel_pit_lap})")
        else:
            fuel_pit_lap = 999

        # Tire-based window
        if tire_data.recommended_change_lap:
            tire_pit_lap = tire_data.recommended_change_lap
            reasons.append(f"tires ({tire_pit_lap})")
        else:
            tire_pit_lap = 999

        # Optimal pit lap (earliest need)
        optimal_lap = min(fuel_pit_lap, tire_pit_lap, current_lap + race_laps_remaining)

        # Window bounds
        window_start = max(current_lap + 1, optimal_lap - 3)
        window_end = min(optimal_lap + 5, current_lap + race_laps_remaining - 1)

        # Undercut opportunity?
        # Can undercut if gap ahead < pit time loss + 3 seconds
        undercut_opportunity = 0 < gap_ahead < (self.avg_pit_time + 3)
        if undercut_opportunity:
            reasons.append("undercut")

        # Overcut opportunity?
        # Better to stay out if we're faster and can make up time
        avg_lap_time = statistics.mean(self.lap_times[-5:]) if len(self.lap_times) >= 5 else 90
        laps_can_stay = int(fuel_data.remaining_laps) - 1
        time_gain = laps_can_stay * 0.5  # Estimate 0.5s/lap gain on fresh vs worn
        overcut_opportunity = time_gain > gap_ahead and laps_can_stay > 3
        if overcut_opportunity:
            reasons.append("overcut")

        # Positions at risk
        # Estimate based on gap behind
        positions_at_risk = int(gap_behind / self.avg_pit_time) if gap_behind > 0 else 0

        return PitWindow(
            optimal_lap=optimal_lap,
            window_start=window_start,
            window_end=window_end,
            reason=", ".join(reasons) if reasons else "no immediate need",
            undercut_opportunity=undercut_opportunity,
            overcut_opportunity=overcut_opportunity,
            time_lost_in_pit=self.avg_pit_time,
            positions_at_risk=positions_at_risk
        )

    def get_strategy_recommendation(
        self,
        current_lap: int,
        telemetry: Dict
    ) -> StrategyRecommendation:
        """Get real-time strategy recommendation"""

        # Calculate all strategy components
        fuel_data = self.calculate_fuel_strategy(
            telemetry.get('fuel', 0),
            current_lap
        )

        tire_data = self.calculate_tire_strategy(telemetry, current_lap)

        pit_window = self.calculate_pit_window(
            current_lap,
            fuel_data,
            tire_data,
            telemetry.get('gap_ahead', 999),
            telemetry.get('gap_behind', 999)
        )

        # Determine recommendation
        action, reason, priority = self._determine_action(
            current_lap,
            fuel_data,
            tire_data,
            pit_window
        )

        return StrategyRecommendation(
            action=action,
            reason=reason,
            priority=priority,
            data={
                'fuel': asdict(fuel_data),
                'tires': asdict(tire_data),
                'pit_window': asdict(pit_window)
            },
            timestamp=time.time()
        )

    def _determine_action(
        self,
        current_lap: int,
        fuel: FuelData,
        tires: TireData,
        pit: PitWindow
    ) -> Tuple[str, str, str]:
        """Determine recommended action"""

        # Critical: Out of fuel soon
        if fuel.remaining_laps < 2:
            return ('pit_now', 'Critical fuel - pit immediately', 'critical')

        # Critical: Tires destroyed
        if tires.grip_remaining < 30:
            return ('pit_now', 'Tires critically worn - pit now', 'critical')

        # High: In pit window and undercut available
        if pit.window_start <= current_lap <= pit.window_end and pit.undercut_opportunity:
            return ('pit_now', f'Undercut opportunity - pit to gain position', 'high')

        # High: Next lap is optimal
        if current_lap + 1 == pit.optimal_lap:
            return ('pit_next_lap', f'Optimal pit window next lap ({pit.reason})', 'high')

        # Medium: Should save fuel
        if fuel.fuel_saving_required > 5:
            return ('fuel_save', f'Save {fuel.fuel_saving_required:.0f}% fuel to finish', 'medium')

        # Medium: Tires overheating
        if tires.overheating:
            return ('manage_tires', 'Tires overheating - manage temps', 'medium')

        # Low: Overcut opportunity
        if pit.overcut_opportunity:
            return ('stay_out', 'Stay out - overcut opportunity', 'low')

        # Low: All good, push
        if tires.optimal_window and fuel.remaining_laps > 5:
            return ('push', 'All systems good - maximize pace', 'low')

        # Default: Stay out and monitor
        return ('stay_out', 'Monitor and maintain pace', 'low')

    def set_race_parameters(self, race_laps: int = None, fuel_capacity: float = None, avg_pit_time: float = None):
        """Set race-specific parameters"""
        if race_laps:
            self.race_laps = race_laps
            logger.info(f"Race distance set: {race_laps} laps")

        if fuel_capacity:
            self.fuel_capacity = fuel_capacity
            logger.info(f"Fuel capacity set: {fuel_capacity}L")

        if avg_pit_time:
            self.avg_pit_time = avg_pit_time
            logger.info(f"Average pit time set: {avg_pit_time}s")

    def reset_stint(self):
        """Reset stint tracking (after pit stop)"""
        self.stint_start_lap = len(self.lap_times)
        if self.fuel_history:
            self.stint_start_fuel = self.fuel_history[-1]['fuel']
        logger.info("Stint reset")

    def get_session_summary(self) -> Dict:
        """Get strategy session summary"""
        return {
            'total_laps': len(self.lap_times),
            'pit_stops': len(self.pit_stops),
            'avg_lap_time': statistics.mean(self.lap_times) if self.lap_times else 0,
            'best_lap_time': min(self.lap_times) if self.lap_times else 0,
            'avg_fuel_per_lap': self._calculate_fuel_per_lap(),
            'total_fuel_used': self.stint_start_fuel - (self.fuel_history[-1]['fuel'] if self.fuel_history else 0),
            'pit_stop_history': self.pit_stops
        }


if __name__ == '__main__':
    # Test the strategy engine
    print("Race Strategy Engine Test")
    print("=" * 70)

    engine = RaceStrategyEngine()
    engine.set_race_parameters(race_laps=50, fuel_capacity=80.0, avg_pit_time=42.0)

    # Simulate race progress
    for lap in range(1, 21):
        telemetry = {
            'lap': lap,
            'fuel': 80 - (lap * 2.2),  # Consuming ~2.2L/lap
            'tire_temp_lf': 88 + (lap * 0.5),
            'tire_temp_rf': 90 + (lap * 0.5),
            'tire_temp_lr': 87 + (lap * 0.5),
            'tire_temp_rr': 89 + (lap * 0.5),
            'gap_ahead': 3.5,
            'gap_behind': 8.2,
            'last_lap_time': 92.5 - (lap * 0.1)
        }

        engine.update_telemetry(telemetry)

        if lap % 5 == 0:  # Check strategy every 5 laps
            recommendation = engine.get_strategy_recommendation(lap, telemetry)
            print(f"\nLap {lap}:")
            print(f"  Action: {recommendation.action}")
            print(f"  Reason: {recommendation.reason}")
            print(f"  Priority: {recommendation.priority}")
            print(f"  Fuel: {recommendation.data['fuel']['remaining_laps']:.1f} laps remaining")
            print(f"  Tires: {recommendation.data['tires']['grip_remaining']:.0f}% grip")

    print("\n" + "=" * 70)
    print("✓ Strategy engine working correctly")
