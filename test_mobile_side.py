"""
Mobile/iPad Side Component Tests
Tests dashboard, WebSocket services, and mobile integration
"""

import sys
import os
import json

# Test results
test_results = {
    'passed': [],
    'failed': [],
    'warnings': [],
    'info': []
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

def test_info(name, message):
    """Record info"""
    test_results['info'].append(name)
    print(f"ℹ️  {name}")
    print(f"   {message}")

print("=" * 70)
print("MOBILE/iPAD SIDE COMPONENT TESTS")
print("=" * 70)

# Test 1: Dashboard Directory Structure
print("\n1️⃣  Testing Dashboard Structure...")
dashboard_dirs = [
    'dashboard',
    'dashboard/src',
    'dashboard/src/components',
    'dashboard/src/services',
    'dashboard/public'
]

missing_dirs = []
for dir_path in dashboard_dirs:
    if not os.path.exists(dir_path):
        missing_dirs.append(dir_path)

if not missing_dirs:
    test_result("Dashboard Structure", True, "All directories present")
else:
    test_result("Dashboard Structure", False, f"Missing: {', '.join(missing_dirs)}")

# Test 2: Dashboard Package Configuration
print("\n2️⃣  Testing Dashboard Package Configuration...")
try:
    with open('dashboard/package.json', 'r') as f:
        package = json.load(f)

    # Check key dependencies
    deps = package.get('dependencies', {})
    required = ['react', 'socket.io-client', '@mui/material']

    missing_deps = [dep for dep in required if dep not in deps]

    if not missing_deps:
        test_result("Dashboard Dependencies", True,
                   f"React {deps.get('react', 'N/A')}, Socket.IO {deps.get('socket.io-client', 'N/A')}")
    else:
        test_result("Dashboard Dependencies", False, f"Missing: {', '.join(missing_deps)}")

except FileNotFoundError:
    test_result("Dashboard Dependencies", False, "package.json not found")
except Exception as e:
    test_result("Dashboard Dependencies", False, f"Error: {str(e)}")

# Test 3: WebSocket Service
print("\n3️⃣  Testing WebSocket Service...")
ws_service_files = [
    'dashboard/src/services/WebSocketService.ts',
    'dashboard/src/services/RelayAgentService.ts'
]

found_services = [f for f in ws_service_files if os.path.exists(f)]

if found_services:
    test_result("WebSocket Service", True,
               f"Found {len(found_services)} WebSocket service(s)")

    # Check for key features in WebSocketService
    if os.path.exists('dashboard/src/services/WebSocketService.ts'):
        with open('dashboard/src/services/WebSocketService.ts', 'r') as f:
            content = f.read()

        features = {
            'throttling': 'throttle' in content.lower(),
            'reconnect': 'reconnect' in content.lower(),
            'error_handling': 'error' in content.lower(),
            'telemetry': 'telemetry' in content.lower()
        }

        feature_status = [f"{k}: {'✓' if v else '✗'}" for k, v in features.items()]
        test_info("WebSocket Features", ", ".join(feature_status))
else:
    test_result("WebSocket Service", False, "No WebSocket services found")

# Test 4: Multi-Driver Support
print("\n4️⃣  Testing Multi-Driver Support...")
multi_driver_files = [
    'dashboard/src/services/MultiDriverService.ts',
    'dashboard/src/components/MultiDriverPanel.tsx'
]

found_multi = [f for f in multi_driver_files if os.path.exists(f)]

if len(found_multi) >= 1:
    test_result("Multi-Driver Support", True,
               f"Found {len(found_multi)} multi-driver component(s)")
else:
    test_warning("Multi-Driver Support", "Multi-driver components not found")

# Test 5: Mobile-Responsive Components
print("\n5️⃣  Testing Mobile-Responsive Components...")
try:
    # Check for Material-UI (responsive by default)
    with open('dashboard/package.json', 'r') as f:
        package = json.load(f)

    has_mui = '@mui/material' in package.get('dependencies', {})

    # Check for viewport meta tag in HTML
    html_files = ['dashboard/public/index.html']
    has_viewport = False

    for html_file in html_files:
        if os.path.exists(html_file):
            with open(html_file, 'r') as f:
                content = f.read()
                if 'viewport' in content:
                    has_viewport = True

    if has_mui and has_viewport:
        test_result("Mobile Responsiveness", True,
                   "Material-UI + viewport meta tag present")
    elif has_mui:
        test_warning("Mobile Responsiveness",
                    "Material-UI present, but check viewport configuration")
    else:
        test_warning("Mobile Responsiveness",
                    "Material-UI not found - may need responsive design work")

except Exception as e:
    test_warning("Mobile Responsiveness", f"Could not verify: {str(e)}")

# Test 6: Real-time Telemetry Display
print("\n6️⃣  Testing Real-time Telemetry Display...")
telemetry_components = [
    'dashboard/src/components/TelemetryDisplay',
    'dashboard/src/components/Telemetry',
    'dashboard/src/components/LiveTelemetry'
]

found_telemetry = []
for comp_base in telemetry_components:
    # Check for .tsx or .jsx
    if os.path.exists(f"{comp_base}.tsx") or os.path.exists(f"{comp_base}.jsx"):
        found_telemetry.append(comp_base)

if found_telemetry:
    test_result("Telemetry Display", True,
               f"Found {len(found_telemetry)} telemetry component(s)")
else:
    test_warning("Telemetry Display", "No dedicated telemetry components found")

# Test 7: Track Map Visualization
print("\n7️⃣  Testing Track Map Visualization...")
map_components = [
    'dashboard/src/components/TrackMap',
    'dashboard/src/components/MiniMap',
    'dashboard/src/components/TrackVisualization'
]

found_maps = []
for comp_base in map_components:
    if os.path.exists(f"{comp_base}.tsx") or os.path.exists(f"{comp_base}.jsx"):
        found_maps.append(comp_base)

if found_maps:
    test_result("Track Map", True, f"Found {len(found_maps)} map component(s)")
else:
    test_warning("Track Map", "No track map components found")

# Test 8: API Client for Backend
print("\n8️⃣  Testing Backend API Client...")
api_files = [
    'dashboard/src/services/BackendClient.ts',
    'dashboard/src/services/ApiClient.ts',
    'dashboard/src/api/client.ts'
]

found_api = [f for f in api_files if os.path.exists(f)]

if found_api:
    test_result("Backend API Client", True, f"Found API client: {found_api[0]}")
else:
    test_warning("Backend API Client", "No API client found")

# Test 9: Redux/State Management
print("\n9️⃣  Testing State Management...")
try:
    with open('dashboard/package.json', 'r') as f:
        package = json.load(f)

    deps = package.get('dependencies', {})

    has_redux = '@reduxjs/toolkit' in deps or 'redux' in deps
    has_context = True  # React Context API is built-in

    if has_redux:
        test_result("State Management", True, "Redux configured")
    elif has_context:
        test_info("State Management", "Using React Context API (built-in)")
    else:
        test_warning("State Management", "No state management detected")

except Exception as e:
    test_warning("State Management", f"Could not verify: {str(e)}")

# Test 10: iPad-Specific Features
print("\n🔟 Testing iPad-Specific Features...")

ipad_features = {
    'touch_optimization': False,
    'landscape_mode': False,
    'split_screen': False,
    'responsive_grid': False
}

# Check for touch event handlers
dashboard_components = []
if os.path.exists('dashboard/src/components'):
    for root, dirs, files in os.walk('dashboard/src/components'):
        for file in files:
            if file.endswith('.tsx') or file.endswith('.jsx'):
                dashboard_components.append(os.path.join(root, file))

# Sample check in a few files
for comp_file in dashboard_components[:5]:  # Check first 5 components
    try:
        with open(comp_file, 'r') as f:
            content = f.read()

        if 'onTouch' in content or 'touch' in content.lower():
            ipad_features['touch_optimization'] = True
        if 'landscape' in content.lower():
            ipad_features['landscape_mode'] = True
        if 'Grid' in content:
            ipad_features['responsive_grid'] = True
    except:
        pass

detected_features = [k for k, v in ipad_features.items() if v]

if len(detected_features) >= 2:
    test_result("iPad Features", True, f"Detected: {', '.join(detected_features)}")
elif len(detected_features) >= 1:
    test_warning("iPad Features", f"Partial support: {', '.join(detected_features)}")
else:
    test_info("iPad Features",
             "Standard React app - iPad compatible via responsive design")

# Test 11: Build Configuration
print("\n1️⃣1️⃣  Testing Build Configuration...")
try:
    with open('dashboard/package.json', 'r') as f:
        package = json.load(f)

    scripts = package.get('scripts', {})

    has_build = 'build' in scripts
    has_start = 'start' in scripts or 'dev' in scripts
    has_test = 'test' in scripts

    if has_build and has_start:
        test_result("Build Configuration", True,
                   "Build and start scripts configured")
    else:
        test_warning("Build Configuration",
                    f"Build: {has_build}, Start: {has_start}")

except Exception as e:
    test_result("Build Configuration", False, f"Error: {str(e)}")

# Test 12: WebSocket Connection Configuration
print("\n1️⃣2️⃣  Testing WebSocket Connection Configuration...")

# Check for WebSocket URLs in service files
ws_configs = []

for service_file in found_services:
    try:
        with open(service_file, 'r') as f:
            content = f.read()

        if 'localhost:8765' in content:
            ws_configs.append('Relay Agent (port 8765)')
        if 'ws://' in content or 'wss://' in content:
            ws_configs.append(f'{service_file.split("/")[-1]}')
    except:
        pass

if ws_configs:
    test_result("WebSocket Configuration", True,
               f"Found configurations: {', '.join(set(ws_configs))}")
else:
    test_warning("WebSocket Configuration",
                "No WebSocket URLs found in services")

# Results Summary
print("\n" + "=" * 70)
print("MOBILE/iPAD SIDE TEST RESULTS")
print("=" * 70)
print(f"✅ Passed: {len(test_results['passed'])}")
print(f"❌ Failed: {len(test_results['failed'])}")
print(f"⚠️  Warnings: {len(test_results['warnings'])}")
print(f"ℹ️  Info: {len(test_results['info'])}")

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
        print("✅ Mobile/iPad side: READY")
    elif pass_rate >= 60:
        print("⚠️  Mobile/iPad side: MOSTLY READY (minor issues)")
    else:
        print("❌ Mobile/iPad side: NOT READY (major issues)")
else:
    print("⚠️  No tests completed")

# iPad Deployment Notes
print("\n" + "=" * 70)
print("iPAD DEPLOYMENT NOTES")
print("=" * 70)
print("""
📱 For iPad deployment:

1. LOCAL NETWORK ACCESS:
   - Dashboard runs on local network (e.g., http://192.168.1.X:3000)
   - iPad connects via Safari or Chrome
   - No app store submission needed for testing

2. PRODUCTION DEPLOYMENT:
   - Deploy dashboard to DigitalOcean
   - Access via https://your-domain.com
   - Works on any iPad with modern browser

3. PROGRESSIVE WEB APP (PWA):
   - Dashboard can be "Add to Home Screen" on iPad
   - Runs like native app
   - Requires manifest.json and service worker

4. NATIVE APP (Optional):
   - React Native wrapper for App Store
   - Not required - web app works great on iPad

5. RECOMMENDED SETUP:
   - iPad mounted on rig/stand
   - Connected to same WiFi as racing PC
   - Full-screen mode for immersive experience
   - Landscape orientation recommended
""")

print("=" * 70)
