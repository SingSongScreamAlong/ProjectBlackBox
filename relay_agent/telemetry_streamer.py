
import asyncio
import logging

class TelemetryStreamer:
    """
    Placeholder TelemetryStreamer
    """
    def __init__(self, sdk, url):
        self.sdk = sdk
        self.url = url
        
    async def stream_loop(self, hz=60):
        print("TelemetryStreamer loop (placeholder)")
        while True:
            await asyncio.sleep(1)

    def get_buffered_telemetry(self, lap=0):
        return []

    def stop_streaming(self):
        pass

class SessionMonitor:
    """
    Placeholder SessionMonitor
    """
    def __init__(self, sdk):
        self.sdk = sdk
        
    def register_callback(self, event, callback):
        pass
        
    async def monitor_loop(self):
        print("SessionMonitor loop (placeholder)")
        while True:
            await asyncio.sleep(1)
