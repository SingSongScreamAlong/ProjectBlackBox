#!/usr/bin/env python3
"""
BlackBox Relay Agent - iRacing SDK Test Script

This script tests the iRacing SDK integration to ensure it's working properly.
"""

import sys
import time
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_pyirsdk_import():
    """Test if pyirsdk can be imported successfully."""
    try:
        import irsdk
        logger.info(f"✅ pyirsdk imported successfully (version: {irsdk.__version__ if hasattr(irsdk, '__version__') else 'unknown'})")
        return True
    except ImportError as e:
        logger.error(f"❌ Failed to import pyirsdk: {e}")
        logger.error("Please install pyirsdk: pip install pyirsdk")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error importing pyirsdk: {e}")
        return False

def test_iracing_connection():
    """Test connection to iRacing."""
    try:
        import irsdk

        logger.info("🔍 Testing iRacing connection...")

        # Create iRacing SDK instance
        ir = irsdk.IRSDK()

        # Try to startup
        ir.startup()

        if ir.is_connected:
            logger.info("✅ Successfully connected to iRacing!")

            # Get some basic info
            try:
                if ir.session_info:
                    logger.info("📊 Session Info Available:")
                    logger.info(f"   Track: {ir.session_info.get('WeekendInfo', {}).get('TrackName', 'Unknown')}")
                    logger.info(f"   Session: {ir.session_info.get('Sessions', [{}])[0].get('SessionType', 'Unknown')}")

                # Test telemetry access
                speed = ir.get('Speed')
                rpm = ir.get('RPM')
                gear = ir.get('Gear')

                logger.info(f"📈 Current Telemetry:")
                logger.info(f"   Speed: {speed}")
                logger.info(f"   RPM: {rpm}")
                logger.info(f"   Gear: {gear}")

            except Exception as e:
                logger.warning(f"⚠️  Could not get session/telemetry info: {e}")

            # Clean up
            ir.shutdown()
            return True
        else:
            logger.warning("⚠️  iRacing is not running or not connected")
            logger.info("💡 Make sure iRacing is running and you're on a track")
            return False

    except Exception as e:
        logger.error(f"❌ Error testing iRacing connection: {e}")
        return False

def test_telemetry_collector():
    """Test the telemetry collector with mock data."""
    try:
        from telemetry_collector import TelemetryCollector

        logger.info("🔧 Testing TelemetryCollector initialization...")

        # Mock config for testing
        test_config = {
            'backend_url': 'http://localhost:4000',
            'api_key': 'test_key',
            'telemetry_protocol': 'websocket',
            'compress_telemetry': False,
            'max_telemetry_rate': 5
        }

        # Create collector
        collector = TelemetryCollector(test_config)

        logger.info("✅ TelemetryCollector created successfully")
        logger.info(f"   Session ID: {collector.session_id}")
        logger.info(f"   Sample Rate: {collector.sample_rate} Hz")

        # Test telemetry collection (without actual iRacing)
        logger.info("🧪 Testing telemetry data structure...")
        test_telemetry = collector._get_telemetry()
        logger.info(f"   Telemetry keys: {len(test_telemetry)}")

        return True

    except Exception as e:
        logger.error(f"❌ Error testing TelemetryCollector: {e}")
        return False

def main():
    """Main test function."""
    print("🧪 BlackBox iRacing SDK Integration Test")
    print("=" * 50)

    tests_passed = 0
    total_tests = 3

    # Test 1: pyirsdk import
    if test_pyirsdk_import():
        tests_passed += 1

    print()

    # Test 2: iRacing connection
    if test_iracing_connection():
        tests_passed += 1

    print()

    # Test 3: TelemetryCollector
    if test_telemetry_collector():
        tests_passed += 1

    print()
    print("=" * 50)
    print(f"🧪 Test Results: {tests_passed}/{total_tests} tests passed")

    if tests_passed == total_tests:
        print("🎉 All tests passed! iRacing SDK integration is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
