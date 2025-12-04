import unittest
from unittest.mock import MagicMock
import sys
import os

# Add relay_agent to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../relay_agent')))

from spotter_engine import SpotterEngine

class MockTelemetry:
    def __init__(self):
        self.car_left_right = 0
        self.car_idx_lap_dist_pct = [-1] * 64
        self.car_idx_track_surface = [3] * 64 # 3 = OnTrack
        self.weekend_info = {'TrackLength': 4000}
        
    def get(self, key, default=None):
        if key == 'WeekendInfo': return self.weekend_info
        return default

class TestSpotterEngine(unittest.TestCase):
    
    def setUp(self):
        self.spotter = SpotterEngine()
        self.session_info = MagicMock()
        self.session_info.driver_id = "0" # Player is car 0

    def test_three_wide_middle(self):
        """Test 3-wide middle detection"""
        telemetry = MockTelemetry()
        # 1 (Left) | 2 (Right) = 3
        telemetry.car_left_right = 3
        
        alerts = self.spotter.update(telemetry, self.session_info)
        self.assertIn("Three wide, you're in the middle.", alerts)

    def test_three_wide_right(self):
        """Test 3-wide right detection (2 cars on left)"""
        telemetry = MockTelemetry()
        # 1 (Left) | 4 (LeftLeft) = 5
        telemetry.car_left_right = 5
        
        alerts = self.spotter.update(telemetry, self.session_info)
        self.assertIn("Three wide, you're on the right.", alerts)

    def test_wreck_ahead(self):
        """Test wreck detection ahead"""
        telemetry = MockTelemetry()
        
        # Player at 0.5
        telemetry.car_idx_lap_dist_pct[0] = 0.5
        
        # Car 1 ahead at 0.55 (gap 0.05) and OffTrack (1)
        telemetry.car_idx_lap_dist_pct[1] = 0.55
        telemetry.car_idx_track_surface[1] = 1 # OffTrack
        
        # First update to initialize positions
        self.spotter.update(telemetry, self.session_info)
        
        # Second update to trigger logic
        alerts = self.spotter.update(telemetry, self.session_info)
        self.assertIn("Car off track ahead!", alerts)

if __name__ == '__main__':
    unittest.main()
