import logging
import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class StrategyRecommendation:
    action: str  # "BOX_NOW", "STAY_OUT", "BOX_NEXT_LAP"
    confidence: float  # 0.0 to 1.0
    reasoning: str
    projected_position: int
    fuel_laps_remaining: float
    tire_life_remaining: float

class StrategySimulator:
    """
    Advanced race strategy simulation using Monte Carlo methods.
    Calculates optimal pit windows, fuel strategy, and tire management.
    """
    
    def __init__(self):
        # Track-specific data (would be loaded from database in production)
        self.pit_loss_time = 25.0  # seconds lost in pit lane
        self.tire_deg_per_lap = 0.05  # % performance loss per lap
        self.fuel_consumption_rate = 2.5  # liters per lap (average)
        
        # Simulation parameters
        self.num_simulations = 100
        self.traffic_variance = 2.0  # seconds of random traffic delay
        
    def analyze_strategy(self, race_state: Dict) -> StrategyRecommendation:
        """
        Analyze current race state and recommend strategy.
        
        Args:
            race_state: Dict containing:
                - current_lap: int
                - total_laps: int
                - fuel_level: float (liters)
                - tire_age: int (laps)
                - current_position: int
                - gap_ahead: float (seconds)
                - gap_behind: float (seconds)
                - fuel_tank_capacity: float
        """
        current_lap = race_state.get('current_lap', 0)
        total_laps = race_state.get('total_laps', 0)
        fuel_level = race_state.get('fuel_level', 0)
        tire_age = race_state.get('tire_age', 0)
        
        # Calculate fuel strategy
        laps_remaining = total_laps - current_lap
        fuel_laps_remaining = fuel_level / self.fuel_consumption_rate
        
        # Critical fuel check
        if fuel_laps_remaining < laps_remaining:
            return StrategyRecommendation(
                action="BOX_NOW",
                confidence=1.0,
                reasoning="Fuel critical - will not finish without refueling",
                projected_position=race_state.get('current_position', 0) + 1,
                fuel_laps_remaining=fuel_laps_remaining,
                tire_life_remaining=self._calculate_tire_life(tire_age)
            )
        
        # Run Monte Carlo simulation
        best_strategy = self._monte_carlo_simulation(race_state)
        
        return best_strategy
    
    def _monte_carlo_simulation(self, race_state: Dict) -> StrategyRecommendation:
        """
        Run Monte Carlo simulation to find optimal strategy.
        """
        current_lap = race_state.get('current_lap', 0)
        total_laps = race_state.get('total_laps', 0)
        tire_age = race_state.get('tire_age', 0)
        current_position = race_state.get('current_position', 1)
        
        # Simulate different pit strategies
        strategies = [
            {'pit_lap': current_lap, 'name': 'BOX_NOW'},
            {'pit_lap': current_lap + 1, 'name': 'BOX_NEXT_LAP'},
            {'pit_lap': current_lap + 5, 'name': 'STAY_OUT'}
        ]
        
        results = []
        
        for strategy in strategies:
            total_time = 0
            position_sum = 0
            
            for _ in range(self.num_simulations):
                # Simulate race with this strategy
                sim_result = self._simulate_race(race_state, strategy['pit_lap'])
                total_time += sim_result['total_time']
                position_sum += sim_result['final_position']
            
            avg_time = total_time / self.num_simulations
            avg_position = position_sum / self.num_simulations
            
            results.append({
                'strategy': strategy['name'],
                'avg_time': avg_time,
                'avg_position': avg_position,
                'pit_lap': strategy['pit_lap']
            })
        
        # Find best strategy (lowest average time)
        best = min(results, key=lambda x: x['avg_time'])
        
        # Calculate confidence based on time delta to next best
        results_sorted = sorted(results, key=lambda x: x['avg_time'])
        if len(results_sorted) > 1:
            time_delta = results_sorted[1]['avg_time'] - results_sorted[0]['avg_time']
            confidence = min(1.0, time_delta / 5.0)  # 5s delta = 100% confidence
        else:
            confidence = 0.8
        
        return StrategyRecommendation(
            action=best['strategy'],
            confidence=confidence,
            reasoning=f"Simulation predicts P{int(best['avg_position'])} with this strategy",
            projected_position=int(best['avg_position']),
            fuel_laps_remaining=race_state.get('fuel_level', 0) / self.fuel_consumption_rate,
            tire_life_remaining=self._calculate_tire_life(tire_age)
        )
    
    def _simulate_race(self, race_state: Dict, pit_lap: int) -> Dict:
        """
        Simulate a single race scenario.
        """
        current_lap = race_state.get('current_lap', 0)
        total_laps = race_state.get('total_laps', 0)
        tire_age = race_state.get('tire_age', 0)
        base_lap_time = 90.0  # seconds (would be calculated from actual data)
        
        total_time = 0
        current_tire_age = tire_age
        
        for lap in range(current_lap, total_laps + 1):
            # Tire degradation
            tire_delta = current_tire_age * self.tire_deg_per_lap
            
            # Add random traffic
            traffic = random.uniform(-self.traffic_variance, self.traffic_variance)
            
            lap_time = base_lap_time + tire_delta + traffic
            total_time += lap_time
            
            # Pit stop
            if lap == pit_lap:
                total_time += self.pit_loss_time
                current_tire_age = 0  # Fresh tires
            else:
                current_tire_age += 1
        
        # Estimate final position (simplified)
        final_position = race_state.get('current_position', 1)
        
        return {
            'total_time': total_time,
            'final_position': final_position
        }
    
    def _calculate_tire_life(self, tire_age: int) -> float:
        """
        Calculate remaining tire life as percentage.
        """
        max_tire_life = 30  # laps
        remaining = max(0, max_tire_life - tire_age)
        return (remaining / max_tire_life) * 100.0
    
    def calculate_undercut_opportunity(self, race_state: Dict) -> Optional[str]:
        """
        Determine if an undercut is viable.
        """
        gap_ahead = race_state.get('gap_ahead', 999)
        tire_age = race_state.get('tire_age', 0)
        
        # Undercut viable if:
        # 1. Gap ahead is < pit loss time
        # 2. Our tires are old enough that fresh tires give advantage
        
        if gap_ahead < self.pit_loss_time and tire_age > 10:
            return "Undercut opportunity - box now to jump car ahead"
        
        return None
