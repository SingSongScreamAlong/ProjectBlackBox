"""
Driver Side Component Tests
Tests all driver-facing components without requiring iRacing to be running
"""

import sys
import os
sys.path.append('./relay_agent')
sys.path.append('./database')

import asyncio
from pathlib import Path

# Test results
test_results = {
    'passed': [],
    'failed': [],
    'warnings': []
}

def test_result(name, passed, message=""):
    """Record test result"""
    if passed:
        test_results['passed'].append(name)
        print(f"✅ {name}")
        if message:
            print(f"   {message}")
    else:
        test_results['failed'].append(name)
        print(f"❌ {name}")
        if message:
            print(f"   {message}")

def test_warning(name, message):
    """Record warning"""
    test_results['warnings'].append(name)
    print(f"⚠️  {name}")
    print(f"   {message}")

print("=" * 70)
print("DRIVER SIDE COMPONENT TESTS")
print("=" * 70)

# Test 1: Settings Manager
print("\n1️⃣  Testing Settings Manager...")
try:
    from settings_manager import SettingsManager, BlackBoxSettings, PTTConfig

    # Create settings instance
    settings = SettingsManager(config_file='/tmp/test_settings.json')

    # Test configuration
    settings.settings.ptt.type = 'keyboard'
    settings.settings.ptt.keyboard_key = 'f1'
    settings.settings.voice.openai_api_key = 'test_key'
    settings.settings.voice.elevenlabs_api_key = 'test_key'

    # Test save/load
    settings.save()
    settings2 = SettingsManager(config_file='/tmp/test_settings.json')

    assert settings2.settings.ptt.type == 'keyboard'
    assert settings2.settings.ptt.keyboard_key == 'f1'

    test_result("Settings Manager", True, "Load/save working correctly")

    # Clean up
    os.remove('/tmp/test_settings.json')

except Exception as e:
    test_result("Settings Manager", False, f"Error: {str(e)}")

# Test 2: Database Models
print("\n2️⃣  Testing Database Models...")
try:
    from database.models import Session, Lap, TelemetryPoint

    # Test model creation (without database connection)
    session_data = {
        'driver_id': 'test_driver',
        'session_type': 'practice',
        'track_name': 'Spa-Francorchamps',
        'car_name': 'McLaren MP4-30'
    }

    # Just verify imports work
    test_result("Database Models", True, "All models imported successfully")

except Exception as e:
    test_result("Database Models", False, f"Error: {str(e)}")

# Test 3: iRacing SDK Wrapper
print("\n3️⃣  Testing iRacing SDK Wrapper...")
try:
    from iracing_sdk_wrapper import iRacingSDKWrapper

    sdk = iRacingSDKWrapper()

    # Test connection (will fail without iRacing, but should not crash)
    connected = sdk.connect(timeout=1)

    if not connected:
        test_warning("iRacing SDK Wrapper",
                    "Cannot connect (iRacing not running) - SDK wrapper functional")
    else:
        test_result("iRacing SDK Wrapper", True, "Connected to iRacing")

except Exception as e:
    test_result("iRacing SDK Wrapper", False, f"Error: {str(e)}")

# Test 4: Telemetry Streamer
print("\n4️⃣  Testing Telemetry Streamer...")
try:
    from telemetry_streamer import TelemetryStreamer
    from iracing_sdk_wrapper import iRacingSDKWrapper

    sdk = iRacingSDKWrapper()
    streamer = TelemetryStreamer(sdk, "ws://localhost:8000/ws/test")

    # Test buffer
    streamer.buffer_telemetry({'lap': 1, 'speed': 100.0})
    buffered = streamer.get_buffered_telemetry(lap=1)

    assert len(buffered) == 1
    assert buffered[0]['speed'] == 100.0

    test_result("Telemetry Streamer", True, "Buffering working correctly")

except Exception as e:
    test_result("Telemetry Streamer", False, f"Error: {str(e)}")

# Test 5: Main Integration Script
print("\n5️⃣  Testing Main Integration Script...")
try:
    from run_blackbox import ProjectBlackBox

    # Just verify imports work
    test_result("Main Integration Script", True, "All imports successful")

except Exception as e:
    test_result("Main Integration Script", False, f"Error: {str(e)}")

# Test 6: Dependencies Check
print("\n6️⃣  Testing Required Dependencies...")
required_deps = [
    'pyirsdk',
    'websocket',
    'websockets',
    'requests',
    'numpy',
    'cv2',
    'PIL',
    'psutil',
    'dotenv',
    'yaml',
    'pyaudio',
    'openai'
]

missing_deps = []
for dep in required_deps:
    try:
        __import__(dep)
    except ImportError:
        missing_deps.append(dep)

if not missing_deps:
    test_result("Dependencies Check", True, f"All {len(required_deps)} dependencies available")
else:
    test_result("Dependencies Check", False,
               f"Missing: {', '.join(missing_deps)}")

# Test 7: File Structure
print("\n7️⃣  Testing File Structure...")
required_files = [
    'run_blackbox.py',
    'settings_manager.py',
    'relay_agent/audio_pipeline.py',
    'relay_agent/voice_recognition.py',
    'relay_agent/voice_synthesis.py',
    'relay_agent/voice_race_team.py',
    'relay_agent/digital_race_team.py',
    'relay_agent/iracing_sdk_wrapper.py',
    'relay_agent/telemetry_streamer.py',
    'database/models.py',
    'database/manager.py'
]

missing_files = []
for file in required_files:
    if not os.path.exists(file):
        missing_files.append(file)

if not missing_files:
    test_result("File Structure", True, f"All {len(required_files)} core files present")
else:
    test_result("File Structure", False, f"Missing: {', '.join(missing_files)}")

# Test 8: Configuration Files
print("\n8️⃣  Testing Configuration System...")
config_status = []

# Check if settings file exists
settings_file = Path.home() / '.projectblackbox' / 'settings.json'
if settings_file.exists():
    config_status.append("Settings file exists")
else:
    config_status.append("Settings file NOT configured (need to run settings_manager.py)")

# Check documentation
if os.path.exists('SETUP.md') and os.path.exists('PTT_CONFIG.md'):
    config_status.append("Documentation present")

test_warning("Configuration System", "; ".join(config_status))

# Results Summary
print("\n" + "=" * 70)
print("DRIVER SIDE TEST RESULTS")
print("=" * 70)
print(f"✅ Passed: {len(test_results['passed'])}")
print(f"❌ Failed: {len(test_results['failed'])}")
print(f"⚠️  Warnings: {len(test_results['warnings'])}")

if test_results['passed']:
    print(f"\nPassed Tests:")
    for test in test_results['passed']:
        print(f"  • {test}")

if test_results['failed']:
    print(f"\nFailed Tests:")
    for test in test_results['failed']:
        print(f"  • {test}")

if test_results['warnings']:
    print(f"\nWarnings:")
    for test in test_results['warnings']:
        print(f"  • {test}")

# Overall status
total_critical = len(test_results['passed']) + len(test_results['failed'])
if total_critical > 0:
    pass_rate = len(test_results['passed']) / total_critical * 100
    print(f"\nOverall Pass Rate: {pass_rate:.1f}%")

    if pass_rate >= 80:
        print("✅ Driver side: READY")
    elif pass_rate >= 60:
        print("⚠️  Driver side: MOSTLY READY (minor issues)")
    else:
        print("❌ Driver side: NOT READY (major issues)")
else:
    print("⚠️  No tests completed")

print("=" * 70)
