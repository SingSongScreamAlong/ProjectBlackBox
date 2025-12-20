import socketio
import time

url = "https://octopus-app-qsi3i.ondigitalocean.app"
print(f"Testing connection to: {url}")

sio = socketio.Client(logger=True, engineio_logger=True)

try:
    sio.connect(url, transports=['websocket'], wait=True, wait_timeout=10)
    print("Connected!")
    sio.disconnect()
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
