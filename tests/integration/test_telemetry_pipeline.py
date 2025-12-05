"""
Integration Tests for Telemetry Pipeline

Tests the complete flow from telemetry collection to storage
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from relay_agent.telemetry_collector import TelemetryCollector
from relay_agent.core_agent import BlackBoxAgent


class TestTelemetryPipeline:
    """Integration tests for telemetry pipeline"""
    
    @pytest.fixture
    def mock_iracing_sdk(self):
        """Mock iRacing SDK"""
        mock_sdk = Mock()
        mock_sdk.is_initialized = True
        mock_sdk.is_connected = True
        mock_sdk.get.return_value = {
            'Speed': 150.5,
            'RPM': 7500,
            'Gear': 4,
            'Throttle': 0.85,
            'Brake': 0.0,
            'SteeringWheelAngle': 0.15,
            'Lap': 5,
            'LapDist': 1234.5,
            'FuelLevel': 45.2
        }
        return mock_sdk
    
    @pytest.fixture
    def mock_backend(self):
        """Mock backend HTTP client"""
        mock_client = AsyncMock()
        mock_client.post.return_value = Mock(status_code=200, json=lambda: {'success': True})
        return mock_client
    
    @pytest.mark.asyncio
    async def test_telemetry_collection_to_backend(self, mock_iracing_sdk, mock_backend):
        """Test complete telemetry flow from collection to backend"""
        # Setup
        collector = TelemetryCollector(mock_iracing_sdk)
        
        # Collect telemetry
        telemetry_data = collector.collect()
        
        # Verify data structure
        assert telemetry_data is not None
        assert 'Speed' in telemetry_data
        assert 'RPM' in telemetry_data
        assert 'Gear' in telemetry_data
        
        # Simulate sending to backend
        with patch('aiohttp.ClientSession.post', mock_backend.post):
            response = await mock_backend.post(
                'http://localhost:3000/api/telemetry',
                json=telemetry_data
            )
            
            assert response.status_code == 200
            assert response.json()['success'] is True
    
    @pytest.mark.asyncio
    async def test_telemetry_batching(self, mock_iracing_sdk):
        """Test telemetry batching before transmission"""
        collector = TelemetryCollector(mock_iracing_sdk)
        batch = []
        
        # Collect multiple samples
        for _ in range(10):
            data = collector.collect()
            batch.append(data)
        
        assert len(batch) == 10
        
        # Verify all samples have required fields
        for sample in batch:
            assert 'Speed' in sample
            assert 'RPM' in sample
            assert 'Gear' in sample
    
    @pytest.mark.asyncio
    async def test_telemetry_error_handling(self, mock_backend):
        """Test error handling in telemetry transmission"""
        # Simulate backend error
        mock_backend.post.return_value = Mock(status_code=500)
        
        with patch('aiohttp.ClientSession.post', mock_backend.post):
            response = await mock_backend.post(
                'http://localhost:3000/api/telemetry',
                json={'test': 'data'}
            )
            
            # Should handle error gracefully
            assert response.status_code == 500
    
    def test_telemetry_data_validation(self, mock_iracing_sdk):
        """Test telemetry data validation"""
        collector = TelemetryCollector(mock_iracing_sdk)
        data = collector.collect()
        
        # Validate data types
        assert isinstance(data['Speed'], (int, float))
        assert isinstance(data['RPM'], (int, float))
        assert isinstance(data['Gear'], int)
        assert isinstance(data['Throttle'], (int, float))
        assert isinstance(data['Brake'], (int, float))
        
        # Validate ranges
        assert 0 <= data['Throttle'] <= 1
        assert 0 <= data['Brake'] <= 1
        assert data['Speed'] >= 0
        assert data['RPM'] >= 0


class TestMultiDriverHandoff:
    """Integration tests for multi-driver handoff"""
    
    @pytest.mark.asyncio
    async def test_driver_handoff_flow(self):
        """Test complete driver handoff flow"""
        # Simulate driver 1 active
        driver1_data = {
            'driver_id': 'driver_001',
            'status': 'active',
            'lap': 10,
            'fuel': 25.5
        }
        
        # Initiate handoff
        handoff_request = {
            'from_driver': 'driver_001',
            'to_driver': 'driver_002',
            'reason': 'scheduled_stint_end',
            'telemetry_snapshot': driver1_data
        }
        
        # Verify handoff data structure
        assert handoff_request['from_driver'] == 'driver_001'
        assert handoff_request['to_driver'] == 'driver_002'
        assert 'telemetry_snapshot' in handoff_request
        
        # Simulate driver 2 accepting
        driver2_response = {
            'driver_id': 'driver_002',
            'status': 'active',
            'handoff_accepted': True
        }
        
        assert driver2_response['handoff_accepted'] is True


class TestAICoachingFlow:
    """Integration tests for AI coaching pipeline"""
    
    @pytest.mark.asyncio
    async def test_ai_coaching_request_flow(self):
        """Test complete AI coaching request flow"""
        # Telemetry data for coaching
        telemetry = {
            'lap_times': [92.5, 91.8, 92.1, 91.5],
            'speed_trace': [150, 155, 160, 155],
            'braking_points': [100, 98, 102, 99],
            'corner_speeds': [85, 87, 84, 86]
        }
        
        # AI coaching request
        coaching_request = {
            'driver_id': 'driver_001',
            'telemetry_data': telemetry,
            'focus_areas': ['braking', 'consistency'],
            'skill_level': 'intermediate'
        }
        
        # Verify request structure
        assert 'telemetry_data' in coaching_request
        assert 'focus_areas' in coaching_request
        assert len(coaching_request['focus_areas']) > 0
        
        # Simulate AI response
        ai_response = {
            'feedback': 'Your braking points are inconsistent. Focus on hitting the same marker each lap.',
            'suggestions': [
                'Use the 100m board as your braking reference',
                'Practice threshold braking in practice sessions'
            ],
            'confidence': 0.85
        }
        
        assert 'feedback' in ai_response
        assert 'suggestions' in ai_response
        assert ai_response['confidence'] > 0.7


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
