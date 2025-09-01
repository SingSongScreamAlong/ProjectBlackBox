#!/usr/bin/env python3
"""
BlackBox Relay Agent - iRacing SDK Test Script

This script tests the iRacing SDK integration with fallback simulation.
"""

import sys
import time
import logging
import random
import math
from pathlib import Path
from typing import Dict, Any, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IRacingSimulator:
    """Simulates iRacing telemetry data for testing."""

    def __init__(self):
        self.is_connected = False
        self.session_info = None
        self.telemetry_data = {}
        self.start_time = time.time()

        # Initialize simulated data
        self._init_simulated_data()

    def startup(self):
        """Simulate iRacing startup."""
        logger.info("🚗 Starting iRacing simulator...")
        time.sleep(1)  # Simulate connection delay
        self.is_connected = True
        logger.info("✅ iRacing simulator connected")

    def shutdown(self):
        """Simulate iRacing shutdown."""
        self.is_connected = False
        logger.info("🛑 iRacing simulator shutdown")

    def _init_simulated_data(self):
        """Initialize simulated telemetry data."""
        # Base telemetry values
        self.telemetry_data = {
            'Speed': 0.0,
            'RPM': 1000,
            'Gear': 1,
            'Throttle': 0.0,
            'Brake': 0.0,
            'Clutch': 0.0,
            'SteeringWheelAngle': 0.0,
            'FuelLevel': 100.0,
            'FuelUsePerHour': 0.0,
            'LapCurrentLapTime': 0.0,
            'LapDist': 0.0,
            'TrackTemp': 25.0,
            'AirTemp': 20.0,
            'SessionTime': 0.0,
            'SessionLapsRemaining': 10,
            'SessionTimeRemaining': 600.0,
            'PlayerCarPosition': 1,
            'Lap': 1,
            'LapLastLapTime': 85.5,
            'LapBestLapTime': 84.2,
            'LapLastLapNum': 0,
            'LapBestLapNum': 1,
            'LapDeltaToBestLap': 0.0,
            'CarIdxLapDistPct': [0.1, 0.2, 0.3, 0.4, 0.5],  # Positions of 5 cars
            'SessionNum': 0
        }

        # Tire data
        for i in range(4):  # FL, FR, RL, RR
            temp_base = 85 + random.uniform(-5, 5)
            wear_base = 0.1 + random.uniform(0, 0.2)

            self.telemetry_data[f'LFtempCL'] = temp_base + random.uniform(-2, 2)
            self.telemetry_data[f'LFtempCM'] = temp_base + random.uniform(-2, 2)
            self.telemetry_data[f'LFtempCR'] = temp_base + random.uniform(-2, 2)
            self.telemetry_data[f'LFwearL'] = wear_base + random.uniform(-0.05, 0.05)
            self.telemetry_data[f'LFwearM'] = wear_base + random.uniform(-0.05, 0.05)
            self.telemetry_data[f'LFwearR'] = wear_base + random.uniform(-0.05, 0.05)

        # Session info
        self.session_info = {
            'WeekendInfo': {
                'TrackName': 'Silverstone Circuit',
                'TrackLength': 5891,
                'TrackID': 1001
            },
            'DriverInfo': {
                'DriverName': 'Test Driver',
                'UserID': 12345,
                'TeamName': 'BlackBox Team',
                'CarName': 'Formula 1 Car',
                'CarID': 2001
            },
            'Sessions': [{
                'SessionType': 'Race',
                'SessionLaps': 10,
                'SessionTime': 600
            }]
        }

    def update_simulation(self):
        """Update simulated telemetry data."""
        if not self.is_connected:
            return

        # Update session time
        self.telemetry_data['SessionTime'] = time.time() - self.start_time
        self.telemetry_data['SessionTimeRemaining'] = max(0, 600.0 - self.telemetry_data['SessionTime'])

        # Simulate speed and RPM based on throttle
        throttle = self.telemetry_data.get('Throttle', 0.0)
        brake = self.telemetry_data.get('Brake', 0.0)

        # Speed simulation
        target_speed = throttle * 350  # Max speed ~350 km/h
        current_speed = self.telemetry_data.get('Speed', 0.0)
        speed_change = (target_speed - current_speed) * 0.1  # Smooth acceleration
        if brake > 0:
            speed_change -= brake * 50  # Braking effect
        self.telemetry_data['Speed'] = max(0, current_speed + speed_change)

        # RPM simulation based on speed and gear
        gear = self.telemetry_data.get('Gear', 1)
        rpm_base = (self.telemetry_data['Speed'] / 350) * 12000  # Max RPM ~12000
        rpm_variation = math.sin(time.time() * 2) * 500  # Engine vibration
        self.telemetry_data['RPM'] = max(800, min(13000, rpm_base + rpm_variation))

        # Fuel consumption
        fuel_burn = throttle * 0.1 + self.telemetry_data['RPM'] / 100000
        self.telemetry_data['FuelLevel'] = max(0, self.telemetry_data['FuelLevel'] - fuel_burn)
        self.telemetry_data['FuelUsePerHour'] = fuel_burn * 3600

        # Lap progress simulation
        self.telemetry_data['LapDist'] = (self.telemetry_data['SessionTime'] % 85.5) / 85.5 * 5891

        # Tire temperature simulation
        for tire in ['LF', 'RF', 'LR', 'RR']:
            for pos in ['L', 'M', 'R']:
                temp_key = f'{tire}tempC{pos}'
                current_temp = self.telemetry_data.get(temp_key, 85)
                # Heat from speed, cool from air
                temp_change = (self.telemetry_data['Speed'] / 100 - 0.5) * 0.1
                self.telemetry_data[temp_key] = max(60, min(120, current_temp + temp_change))

                wear_key = f'{tire}wear{pos}'
                current_wear = self.telemetry_data.get(wear_key, 0.1)
                wear_change = abs(speed_change) / 10000  # Wear from speed changes
                self.telemetry_data[wear_key] = min(1.0, current_wear + wear_change)

    def get(self, var_name: str) -> Any:
        """Get telemetry variable value."""
        self.update_simulation()
        return self.telemetry_data.get(var_name)

    def __getitem__(self, var_name: str) -> Any:
        """Get telemetry variable value using dict syntax."""
        return self.get(var_name)

    def __contains__(self, var_name: str) -> bool:
        """Check if variable exists."""
        return var_name in self.telemetry_data

def test_real_iracing():
    """Test real iRacing SDK if available."""
    try:
        import irsdk
        logger.info("🔍 Testing real iRacing SDK...")

        ir = irsdk.IRSDK()
        ir.startup()

        if ir.is_connected:
            logger.info("✅ Real iRacing SDK connected!")

            # Get some telemetry
            speed = ir['Speed']
            rpm = ir['RPM']
            logger.info(f"📈 Real telemetry - Speed: {speed}, RPM: {rpm}")

            ir.shutdown()
            return ir

        else:
            logger.warning("⚠️  Real iRacing SDK not connected")
            return None

    except ImportError:
        logger.warning("⚠️  Real iRacing SDK not available")
        return None
    except Exception as e:
        logger.error(f"❌ Error with real iRacing SDK: {e}")
        return None

def test_simulated_iracing():
    """Test simulated iRacing data."""
    logger.info("🎮 Testing simulated iRacing...")

    simulator = IRacingSimulator()
    simulator.startup()

    if simulator.is_connected:
        logger.info("✅ iRacing simulator connected!")

        # Test telemetry updates
        for i in range(5):
            simulator.update_simulation()
            speed = simulator['Speed']
            rpm = simulator['RPM']
            logger.info(f"📈 Sim telemetry - Speed: {speed:.1f}, RPM: {rpm:.0f}")
            time.sleep(0.1)

        simulator.shutdown()
        return simulator

    else:
        logger.error("❌ iRacing simulator failed to connect")
        return None

def test_telemetry_collector(ir_instance):
    """Test telemetry collector with the given iRacing instance."""
    logger.info("🔧 Testing TelemetryCollector...")

    try:
        # Mock the import to use our instance
        import sys
        from unittest.mock import MagicMock

        # Mock the irsdk module
        mock_irsdk = MagicMock()
        mock_irsdk.IRSDK.return_value = ir_instance
        sys.modules['irsdk'] = mock_irsdk

        # Now import and test
        from telemetry_collector import TelemetryCollector

        config = {
            'backend_url': 'http://localhost:4000',
            'api_key': 'test_key',
            'telemetry_protocol': 'websocket'
        }

        collector = TelemetryCollector(config)
        logger.info("✅ TelemetryCollector created successfully")

        # Test telemetry collection
        telemetry = collector._get_telemetry()
        logger.info(f"📊 Collected {len(telemetry)} telemetry variables")
        logger.info(f"   Sample: Speed={telemetry.get('Speed')}, RPM={telemetry.get('RPM')}")

        return True

    except Exception as e:
        logger.error(f"❌ Error testing TelemetryCollector: {e}")
        return False

def main():
    """Main test function."""
    print("🧪 BlackBox iRacing Integration Test (with Simulation)")
    print("=" * 60)

    tests_passed = 0
    total_tests = 3

    # Test 1: Real iRacing SDK
    ir_instance = test_real_iracing()
    if ir_instance:
        tests_passed += 1
    else:
        print("\n🎮 Falling back to simulation mode...")

        # Test 2: Simulated iRacing
        ir_instance = test_simulated_iracing()
        if ir_instance:
            tests_passed += 1

    print()

    # Test 3: TelemetryCollector
    if ir_instance and test_telemetry_collector(ir_instance):
        tests_passed += 1

    print()
    print("=" * 60)
    print(f"🧪 Test Results: {tests_passed}/{total_tests} tests passed")

    if tests_passed >= 2:  # At least simulation + collector working
        print("🎉 iRacing integration is functional!")
        if ir_instance.__class__.__name__ == 'IRacingSimulator':
            print("💡 Using simulated data - install real iRacing SDK for live racing data")
        return 0
    else:
        print("⚠️  Integration needs work. Check errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
