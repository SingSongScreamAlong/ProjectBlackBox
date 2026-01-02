#!/usr/bin/env python3
"""Minimal Socket.IO connection test"""
import socketio
import time

print("Testing Socket.IO connection to DigitalOcean...")
print("=" * 50)

sio = socketio.Client(logger=True, engineio_logger=True)

@sio.event
def connect():
    print("SUCCESS! Connected to server")
    
@sio.event  
def connect_error(data):
    print(f"Connection error: {data}")

@sio.event
def disconnect():
    print("Disconnected")

try:
    print("Attempting connection...")
    sio.connect(
        'https://octopus-app-qsi3i.ondigitalocean.app',
        transports=['polling', 'websocket'],
        wait_timeout=30
    )
    print("Connection established, waiting 5 seconds...")
    time.sleep(5)
    sio.disconnect()
    print("Test complete - SUCCESS")
except Exception as e:
    print(f"Connection failed: {type(e).__name__}: {e}")
