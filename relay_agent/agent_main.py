#!/usr/bin/env python3
"""
BlackBox Relay Agent - Main Entry Point

This module serves as the main entry point for the BlackBox Relay Agent,
integrating the core agent and telemetry collector components.
"""

import os
import sys
import time
import logging
import argparse
import signal
import threading
import asyncio
from typing import Dict, Any, Optional

# Import local modules
from core_agent import CoreAgent
from telemetry_collector import create_telemetry_collector
from backend.telemetry_server import TelemetryServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.expanduser("~"), "BlackBoxRelay", "logs", "agent.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("BlackBoxRelayAgent")


class BlackBoxRelayAgent:
    """
    Main BlackBox Relay Agent class that integrates all components.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the BlackBox Relay Agent.
        
        Args:
            config_path: Optional path to configuration file
        """
        # Initialize core agent
        self.core_agent = CoreAgent()
        
        # Override config path if provided
        if config_path:
            config_file = os.path.abspath(config_path)
            if os.path.exists(config_file):
                logger.info(f"Loading configuration from {config_file}")
                # In a real implementation, we would load the config here
        
        # Initialize telemetry collector
        self.telemetry_collector = create_telemetry_collector(self.core_agent.config)
        
        # Initialize telemetry server
        self.telemetry_server = TelemetryServer()
        self.telemetry_server_task = None
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.handle_exit)
        signal.signal(signal.SIGTERM, self.handle_exit)
        
        # Running flag
        self.running = False
        
        # Create event loop for async operations if needed
        self.loop = None
        
        logger.info("BlackBox Relay Agent initialized")
    
    def start(self) -> None:
        """Start the BlackBox Relay Agent."""
        if self.running:
            logger.warning("Agent is already running")
            return
        
        self.running = True
        logger.info("Starting BlackBox Relay Agent")
        
        # Start the core agent
        self.core_agent.start()
        
        # Start the telemetry server in a separate thread
        self.start_telemetry_server()
        
        # For now, we'll just keep the main thread alive
        try:
            while self.running:
                time.sleep(1.0)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self) -> None:
        """Stop the BlackBox Relay Agent."""
        if not self.running:
            return
        
        logger.info("Stopping BlackBox Relay Agent")
        self.running = False
        
        # Stop the core agent
        self.core_agent.stop()
        
        # Stop the telemetry server
        self.stop_telemetry_server()
        
        logger.info("BlackBox Relay Agent stopped")
    
    def handle_exit(self, signum, frame) -> None:
        """Handle exit signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down")
        self.stop()
        sys.exit(0)
        
    def start_telemetry_server(self) -> None:
        """Start the telemetry server in a separate thread."""
        def run_telemetry_server():
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self.loop = loop
            
            # Start the telemetry server
            try:
                logger.info("Starting telemetry server")
                
                # Start WebSocket server directly
                websocket_host = self.telemetry_server.config.get("websocket_host", "0.0.0.0")
                websocket_port = self.telemetry_server.config.get("websocket_port", 8765)
                
                # Create and start the WebSocket server
                websocket_server_task = loop.create_task(
                    self.telemetry_server.start_websocket_server()
                )
                
                # Start the main telemetry server
                self.telemetry_server_task = loop.create_task(self.telemetry_server.start())
                
                logger.info(f"WebSocket server starting on {websocket_host}:{websocket_port}")
                
                # Run the event loop
                loop.run_forever()
            except Exception as e:
                logger.error(f"Error running telemetry server: {e}")
                import traceback
                logger.error(traceback.format_exc())
            finally:
                if loop.is_running():
                    loop.close()
        
        # Start the telemetry server in a separate thread
        self.telemetry_server_thread = threading.Thread(target=run_telemetry_server, daemon=True)
        self.telemetry_server_thread.start()
        logger.info("Telemetry server thread started")
        
        # Give the server a moment to start
        time.sleep(1.0)
    
    def stop_telemetry_server(self) -> None:
        """Stop the telemetry server."""
        if self.loop and self.telemetry_server_task:
            try:
                # Create a task to stop the server
                async def stop_server():
                    await self.telemetry_server.stop()
                
                # Run the stop task in the event loop
                future = asyncio.run_coroutine_threadsafe(stop_server(), self.loop)
                future.result(timeout=5.0)  # Wait up to 5 seconds for server to stop
                
                logger.info("Telemetry server stopped")
            except Exception as e:
                logger.error(f"Error stopping telemetry server: {e}")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="BlackBox Relay Agent")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--no-gui", action="store_true", help="Run without GUI (no system tray)")
    return parser.parse_args()


def main():
    """Main entry point for the BlackBox Relay Agent."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Set logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    # Create and start agent
    agent = BlackBoxRelayAgent(config_path=args.config)
    
    try:
        agent.start()
    except Exception as e:
        logger.error(f"Error starting agent: {e}")
        agent.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()
