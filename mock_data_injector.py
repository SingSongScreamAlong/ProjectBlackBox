import requests
import time
import math
import random
import json
import sys

# URL for local_backend
URL = "http://localhost:3000/telemetry"

def generate_telemetry(t):
    """Generate fake telemetry data based on time t"""
    
    # Simple physics simulation
    speed = 150 + 50 * math.sin(t * 0.5)
    rpm = 5000 + 2000 * math.sin(t * 0.5)
    gear = 4 if speed > 100 else 2
    
    # Circle path
    radius = 500
    angle = t * 0.1
    pos_x = radius * math.cos(angle)
    pos_z = radius * math.sin(angle)
    
    data = {
        "timestamp": int(time.time() * 1000),
        "speed": speed,
        "rpm": rpm,
        "gear": gear,
        "throttle": 0.8 if math.sin(t) > 0 else 0,
        "brake": 0.5 if math.sin(t) <= 0 else 0,
        "clutch": 0,
        "steering": math.cos(t) * 90,
        "fuel": {
            "level": 45.5,
            "usagePerHour": 2.5
        },
        "tires": {
            "frontLeft": {"temp": 85, "wear": 98, "pressure": 26},
            "frontRight": {"temp": 88, "wear": 97, "pressure": 26},
            "rearLeft": {"temp": 92, "wear": 95, "pressure": 27},
            "rearRight": {"temp": 90, "wear": 96, "pressure": 27}
        },
        "position": {"x": pos_x, "y": 0, "z": pos_z},
        "lap": int(t / 60) + 1,
        "sector": 1 if (angle % (2*math.pi)) < 2 else 2,
        "lapTime": 90.5,
        "sectorTime": 25.4,
        "bestLapTime": 88.2,
        "deltaToBestLap": 0.5,
        "bestSectorTimes": [24.1, 35.2, 28.9],
        "gForce": {
            "lateral": math.cos(t),
            "longitudinal": math.sin(t) * 0.5,
            "vertical": 0.1
        },
        "trackPosition": (angle % (2*math.pi)) / (2*math.pi),
        "racePosition": 3,
        "gapAhead": 1.2,
        "gapBehind": 0.8,
        
        # Advanced fields (optional but good for completeness)
        "flags": 0,
        "drsStatus": 0,
        "weather": {
            "windSpeed": 5,
            "windDirection": 180
        }
    }
    return data

def main():
    print(f"🚀 Starting mock telemetry injector to {URL}")
    print("Press Ctrl+C to stop")
    
    t = 0
    try:
        while True:
            data = generate_telemetry(t)
            
            try:
                # Local backend might expect just the object
                response = requests.post(URL, json=data, timeout=0.5)
                # print(f"Sent frame {t}: {response.status_code}")
            except Exception as e:
                print(f"Error sending data: {e}", file=sys.stderr)
            
            t += 0.1
            time.sleep(0.5) # 2Hz
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping injector")

if __name__ == "__main__":
    main()
