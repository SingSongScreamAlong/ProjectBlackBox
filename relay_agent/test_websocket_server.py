#!/usr/bin/env python3
"""
Test script to verify WebSocket server startup
"""

import asyncio
import logging
import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.telemetry_server import TelemetryServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("WebSocketTest")

async def test_websocket_server():
    """Test the WebSocket server startup"""
    try:
        logger.info("Creating TelemetryServer instance")
        server = TelemetryServer()
        
        logger.info("Starting WebSocket server only")
        # Start just the WebSocket server
        await server.start_websocket_server()
        
    except Exception as e:
        logger.error(f"Error starting WebSocket server: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    logger.info("Testing WebSocket server startup")
    asyncio.run(test_websocket_server())
