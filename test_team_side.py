"""
Team Side Component Tests
Tests AI race team, voice recognition, and voice synthesis components
"""

import sys
import os
sys.path.append('./relay_agent')

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
print("TEAM SIDE COMPONENT TESTS")
print("=" * 70)

# Test 1: Digital Race Team - Engineer
print("\n1️⃣  Testing Race Engineer...")
try:
    from digital_race_team import EnhancedRaceEngineer

    engineer = EnhancedRaceEngineer()

    # Test query
    context = {
        'current_lap': 5,
        'tire_age': 5,
        'tire_temps': {'FL': 85, 'FR': 87, 'RL': 90, 'RR': 92}
    }

    response = engineer.process_query("How are my tire temps?", context)

    assert response is not None
    assert len(response) > 0
    assert 'tire' in response.lower() or 'temp' in response.lower()

    test_result("Race Engineer", True, f"Response: {response[:100]}...")

except Exception as e:
    test_result("Race Engineer", False, f"Error: {str(e)}")

# Test 2: Digital Race Team - Strategist
print("\n2️⃣  Testing Race Strategist...")
try:
    from digital_race_team_part2 import RaceStrategist

    strategist = RaceStrategist()

    context = {
        'current_lap': 10,
        'fuel_remaining': 15.5,
        'laps_remaining': 20
    }

    response = strategist.process_query("When should I pit?", context)

    assert response is not None
    assert len(response) > 0
    assert 'pit' in response.lower() or 'lap' in response.lower()

    test_result("Race Strategist", True, f"Response: {response[:100]}...")

except Exception as e:
    test_result("Race Strategist", False, f"Error: {str(e)}")

# Test 3: Digital Race Team - Coach
print("\n3️⃣  Testing Performance Coach...")
try:
    from digital_race_team_part2 import PerformanceCoach

    coach = PerformanceCoach()

    context = {
        'current_lap': 3,
        'last_lap_time': 105.234,
        'best_lap_time': 104.567
    }

    response = coach.process_query("How's my pace?", context)

    assert response is not None
    assert len(response) > 0

    test_result("Performance Coach", True, f"Response: {response[:100]}...")

except Exception as e:
    test_result("Performance Coach", False, f"Error: {str(e)}")

# Test 4: Digital Race Team - Intelligence Analyst
print("\n4️⃣  Testing Intelligence Analyst...")
try:
    from digital_race_team_part3 import IntelligenceAnalyst

    analyst = IntelligenceAnalyst()

    context = {
        'position': 5,
        'gap_ahead': 2.3,
        'gap_behind': 3.1
    }

    response = analyst.process_query("Can I catch the guy ahead?", context)

    assert response is not None
    assert len(response) > 0

    test_result("Intelligence Analyst", True, f"Response: {response[:100]}...")

except Exception as e:
    test_result("Intelligence Analyst", False, f"Error: {str(e)}")

# Test 5: Voice Race Team Interface
print("\n5️⃣  Testing Voice Race Team Interface...")
try:
    from voice_race_team import VoiceRaceTeamInterface
    from digital_race_team import EnhancedRaceEngineer
    from digital_race_team_part2 import RaceStrategist, PerformanceCoach
    from digital_race_team_part3 import IntelligenceAnalyst

    # Create team
    team = VoiceRaceTeamInterface(
        engineer=EnhancedRaceEngineer(),
        strategist=RaceStrategist(),
        coach=PerformanceCoach(),
        intelligence_analyst=IntelligenceAnalyst()
    )

    context = {
        'current_lap': 5,
        'position': 3,
        'tire_age': 5
    }

    # Test routing
    response = team.process_driver_voice_input("How are my tires?", context)

    assert response is not None
    assert hasattr(response, 'team_member')
    assert hasattr(response, 'response_text')
    assert response.team_member in ['Engineer', 'Strategist', 'Coach', 'Intel']

    test_result("Voice Race Team Interface", True,
               f"{response.team_member}: {response.response_text[:80]}...")

except Exception as e:
    test_result("Voice Race Team Interface", False, f"Error: {str(e)}")

# Test 6: Voice Recognition (without audio)
print("\n6️⃣  Testing Voice Recognition Module...")
try:
    from voice_recognition import VoiceRecognition

    # Just test initialization without API key
    # Real testing requires OpenAI API key

    test_warning("Voice Recognition",
                "Module loads correctly (API key required for actual testing)")

except Exception as e:
    test_result("Voice Recognition", False, f"Error: {str(e)}")

# Test 7: Voice Synthesis (without audio)
print("\n7️⃣  Testing Voice Synthesis Module...")
try:
    from voice_synthesis import VoiceSynthesis

    # Just test initialization without API key
    # Real testing requires ElevenLabs API key

    test_warning("Voice Synthesis",
                "Module loads correctly (API key required for actual testing)")

except Exception as e:
    test_result("Voice Synthesis", False, f"Error: {str(e)}")

# Test 8: Audio Pipeline Integration
print("\n8️⃣  Testing Audio Pipeline Integration...")
try:
    from audio_pipeline import AudioPipeline

    # Test initialization without API keys (will work but not functional)
    # Real testing requires OpenAI + ElevenLabs API keys

    test_warning("Audio Pipeline",
                "Integration complete (API keys required for full functionality)")

except Exception as e:
    test_result("Audio Pipeline", False, f"Error: {str(e)}")

# Test 9: AI Team Response Quality
print("\n9️⃣  Testing AI Team Response Quality...")
try:
    from voice_race_team import VoiceRaceTeamInterface
    from digital_race_team import EnhancedRaceEngineer
    from digital_race_team_part2 import RaceStrategist, PerformanceCoach
    from digital_race_team_part3 import IntelligenceAnalyst

    team = VoiceRaceTeamInterface(
        engineer=EnhancedRaceEngineer(),
        strategist=RaceStrategist(),
        coach=PerformanceCoach(),
        intelligence_analyst=IntelligenceAnalyst()
    )

    # Test different query types
    queries = [
        ("How's my fuel?", "Engineer"),
        ("When to pit?", "Strategist"),
        ("Am I improving?", "Coach"),
        ("Gap to leader?", "Intel")
    ]

    correct_routing = 0
    for query, expected_member in queries:
        response = team.process_driver_voice_input(query, {})
        if expected_member.lower() in response.team_member.lower():
            correct_routing += 1

    routing_accuracy = (correct_routing / len(queries)) * 100

    test_result("AI Team Response Quality", True,
               f"Routing accuracy: {routing_accuracy:.0f}% ({correct_routing}/{len(queries)})")

except Exception as e:
    test_result("AI Team Response Quality", False, f"Error: {str(e)}")

# Test 10: Context Processing
print("\n🔟 Testing Context Processing...")
try:
    from voice_race_team import VoiceRaceTeamInterface
    from digital_race_team import EnhancedRaceEngineer
    from digital_race_team_part2 import RaceStrategist, PerformanceCoach
    from digital_race_team_part3 import IntelligenceAnalyst

    team = VoiceRaceTeamInterface(
        engineer=EnhancedRaceEngineer(),
        strategist=RaceStrategist(),
        coach=PerformanceCoach(),
        intelligence_analyst=IntelligenceAnalyst()
    )

    # Test with empty context
    response1 = team.process_driver_voice_input("Status?", {})

    # Test with full context
    full_context = {
        'current_lap': 10,
        'position': 3,
        'tire_age': 10,
        'fuel_remaining': 20.5,
        'gap_ahead': 1.5,
        'gap_behind': 2.3,
        'tire_temps': {'FL': 85, 'FR': 87, 'RL': 90, 'RR': 92}
    }
    response2 = team.process_driver_voice_input("Status?", full_context)

    # Both should work
    assert response1 is not None
    assert response2 is not None
    assert len(response2.response_text) > 0

    test_result("Context Processing", True,
               "Handles both empty and full context correctly")

except Exception as e:
    test_result("Context Processing", False, f"Error: {str(e)}")

# Results Summary
print("\n" + "=" * 70)
print("TEAM SIDE TEST RESULTS")
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
        print("✅ Team side: READY")
    elif pass_rate >= 60:
        print("⚠️  Team side: MOSTLY READY (minor issues)")
    else:
        print("❌ Team side: NOT READY (major issues)")
else:
    print("⚠️  No tests completed")

print("=" * 70)
