#!/usr/bin/env python3
"""
BlackBox Relay Agent - Core Agent Module

This module serves as the main controller for the BlackBox Relay Agent,
coordinating between telemetry collection, video encoding, and backend communication.
"""

import os
import sys
import time
import json
import logging
import threading
import signal
import platform
import subprocess
import requests
import psutil
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union, Any

# Import local modules
from video_encoder import VideoEncoder

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.expanduser("~"), "BlackBoxRelay", "logs", "relay_agent.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("BlackBoxRelayAgent")

# Constants
VERSION = "0.1.0"
CONFIG_DIR = os.path.join(os.path.expanduser("~"), "BlackBoxRelay", "config")
DATA_DIR = os.path.join(os.path.expanduser("~"), "BlackBoxRelay", "data")
DEFAULT_CONFIG = {
    "backend_url": "https://api.blackbox.racing",
    "telemetry_mode": "enabled",
    "video_mode": "auto",  # auto, enabled, disabled
    "video_quality": "medium",  # low, medium, high
    "video_resolution": "1280x720",
    "video_frame_rate": 30,
    "video_encoder": "h264",
    "video_max_bitrate": 2000,  # kbps
    "video_use_hardware_accel": True,
    "auto_update": True,
    "start_with_iracing": True,
    "resource_limits": {
        "max_cpu_percent": 5.0,
        "max_memory_mb": 200,
        "max_gpu_percent": 10.0
    },
    "api_key": "",
    "user_id": "",
    "team_id": ""
}


class CoreAgent:
    """
    Core Agent class that manages the BlackBox Relay Agent's operation.
    """
    
    def __init__(self):
        """Initialize the Core Agent."""
        self.running = False
        self.config = {}
        self.telemetry_thread = None
        self.video_thread = None
        self.monitor_thread = None
        self.update_thread = None
        self.iracing_running = False
        self.backend_connected = False
        self.last_telemetry_time = 0
        self.last_video_frame_time = 0
        self.resource_usage = {
            "cpu_percent": 0.0,
            "memory_mb": 0.0,
            "gpu_percent": 0.0
        }
        self.session_id = str(uuid.uuid4())
        self.video_encoder = None
        self.video_enabled = False
        
        # Ensure directories exist
        os.makedirs(CONFIG_DIR, exist_ok=True)
        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(os.path.join(os.path.expanduser("~"), "BlackBoxRelay", "logs"), exist_ok=True)
        
        # Load configuration
        self.load_config()
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self.handle_exit)
        signal.signal(signal.SIGTERM, self.handle_exit)
        
        logger.info(f"BlackBox Relay Agent v{VERSION} initialized")
    
    def load_config(self) -> None:
        """Load configuration from file or create default if not exists."""
        config_file = os.path.join(CONFIG_DIR, "config.json")
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    loaded_config = json.load(f)
                    # Update default config with loaded values
                    for key, value in loaded_config.items():
                        if key in DEFAULT_CONFIG:
                            if isinstance(DEFAULT_CONFIG[key], dict) and isinstance(value, dict):
                                DEFAULT_CONFIG[key].update(value)
                            else:
                                DEFAULT_CONFIG[key] = value
                    
                    self.config = DEFAULT_CONFIG
                    logger.info("Configuration loaded successfully")
            except Exception as e:
                logger.error(f"Error loading configuration: {e}")
                self.config = DEFAULT_CONFIG
                self.save_config()  # Save default config
        else:
            logger.info("No configuration file found, creating default")
            self.config = DEFAULT_CONFIG
            self.save_config()
    
    def save_config(self) -> None:
        """Save current configuration to file."""
        config_file = os.path.join(CONFIG_DIR, "config.json")
        try:
            with open(config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            logger.info("Configuration saved successfully")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
    
    def start(self) -> None:
        """Start the Core Agent and its components."""
        if self.running:
            logger.warning("Agent is already running")
            return
        
        self.running = True
        logger.info("Starting BlackBox Relay Agent")
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self.monitor_resources, daemon=True)
        self.monitor_thread.start()
        
        # Start update check thread
        if self.config["auto_update"]:
            self.update_thread = threading.Thread(target=self.check_for_updates, daemon=True)
            self.update_thread.start()
        
        # Main loop - will start telemetry and video when iRacing is detected
        self.main_loop()
    
    def stop(self) -> None:
        """Stop the Core Agent and all its components."""
        if not self.running:
            return
        
        logger.info("Stopping BlackBox Relay Agent")
        self.running = False
        
        # Stop telemetry collection if running
        if self.telemetry_thread and self.telemetry_thread.is_alive():
            # We'll implement a stop mechanism in the telemetry module
            logger.info("Stopping telemetry collection")
            # self.telemetry_module.stop()
            self.telemetry_thread.join(timeout=5.0)
        
        # Stop video encoding if running
        if self.video_thread and self.video_thread.is_alive():
            # We'll implement a stop mechanism in the video module
            logger.info("Stopping video encoding")
            # self.video_module.stop()
            self.video_thread.join(timeout=5.0)
        
        # Wait for monitor thread to finish
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2.0)
        
        # Wait for update thread to finish
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=2.0)
        
        logger.info("BlackBox Relay Agent stopped")
    
    def main_loop(self) -> None:
        """Main operational loop for the agent."""
        try:
            while self.running:
                # Check if iRacing is running
                iracing_status = self.check_iracing_status()
                
                if iracing_status and not self.iracing_running:
                    # iRacing just started
                    logger.info("iRacing detected, starting data collection")
                    self.iracing_running = True
                    self.start_telemetry_collection()
                    
                    # Start video collection if enabled
                    if self.config["video_mode"] in ["enabled", "auto"]:
                        self.start_video_encoding()
                
                elif not iracing_status and self.iracing_running:
                    # iRacing just stopped
                    logger.info("iRacing no longer detected, stopping data collection")
                    self.iracing_running = False
                    self.stop_telemetry_collection()
                    self.stop_video_encoding()
                
                # Check backend connection periodically
                self.check_backend_connection()
                
                # Sleep to prevent CPU hogging
                time.sleep(2.0)
                
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            self.running = False
    
    def check_iracing_status(self) -> bool:
        """Check if iRacing is currently running."""
        for proc in psutil.process_iter(['name']):
            try:
                if 'iRacing' in proc.info['name']:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False
    
    def check_backend_connection(self) -> bool:
        """Check connection to the backend server."""
        if not self.config["api_key"]:
            logger.warning("No API key configured, skipping backend connection check")
            self.backend_connected = False
            return False
        
        try:
            response = requests.get(
                f"{self.config['backend_url']}/api/v1/health",
                headers={"Authorization": f"Bearer {self.config['api_key']}"},
                timeout=5.0
            )
            
            if response.status_code == 200:
                if not self.backend_connected:
                    logger.info("Successfully connected to backend")
                self.backend_connected = True
                return True
            else:
                if self.backend_connected:
                    logger.warning(f"Backend connection failed: HTTP {response.status_code}")
                self.backend_connected = False
                return False
                
        except requests.exceptions.RequestException as e:
            if self.backend_connected:
                logger.warning(f"Backend connection error: {e}")
            self.backend_connected = False
            return False
    
    def start_telemetry_collection(self) -> None:
        """Start the telemetry collection thread."""
        if self.telemetry_thread and self.telemetry_thread.is_alive():
            logger.warning("Telemetry collection already running")
            return
        
        logger.info("Starting telemetry collection")
        
        # In a real implementation, we would import and initialize the telemetry module here
        # For now, we'll just create a placeholder thread
        self.telemetry_thread = threading.Thread(
            target=self.telemetry_placeholder,
            daemon=True
        )
        self.telemetry_thread.start()
    
    def stop_telemetry_collection(self) -> None:
        """Stop the telemetry collection thread."""
        if not self.telemetry_thread or not self.telemetry_thread.is_alive():
            return
        
        logger.info("Stopping telemetry collection")
        # In a real implementation, we would call stop() on the telemetry module
        # For now, we'll just wait for the thread to finish
        self.telemetry_thread.join(timeout=5.0)
        self.telemetry_thread = None
    
    def start_video_encoding(self) -> None:
        """Start the video encoding thread if conditions are met."""
        # Check if video is already running
        if self.video_thread and self.video_thread.is_alive():
            logger.info("Video encoding already running")
            return
        
        # Check if video mode is disabled
        if self.config["video_mode"] == "disabled":
            logger.info("Video encoding disabled in configuration")
            return
        
        # Check if iRacing is running (required for video)
        if not self.iracing_running and self.config["video_mode"] != "enabled":
            logger.info("iRacing not running, video encoding not started")
            return
        
        # Check system resources
        if (self.resource_usage["cpu_percent"] > self.config["resource_limits"]["max_cpu_percent"] or
            self.resource_usage["memory_mb"] > self.config["resource_limits"]["max_memory_mb"] or
            self.resource_usage["gpu_percent"] > self.config["resource_limits"]["max_gpu_percent"]):
            logger.warning("System resources too high, not starting video encoding")
            return
        
        # Initialize video encoder if not already done
        if not self.video_encoder:
            video_config = {
                "backend_url": f"{self.config['backend_url']}/video",
                "api_key": self.config["api_key"],
                "video_quality": self.config["video_quality"],
                "max_bitrate": self.config["video_max_bitrate"],
                "frame_rate": self.config["video_frame_rate"],
                "resolution": self.config["video_resolution"],
                "encoder": self.config["video_encoder"],
                "use_hardware_accel": self.config["video_use_hardware_accel"]
            }
            self.video_encoder = VideoEncoder(video_config)
        
        # Start video encoding thread
        logger.info("Starting video encoding")
        self.video_enabled = True
        self.video_encoder.start(self.session_id)
        self.video_thread = threading.Thread(target=self.video_encoding_loop)
        self.video_thread.daemon = True
        self.video_thread.start()
    
    def stop_video_encoding(self) -> None:
        """Stop the video encoding thread."""
        if not self.video_enabled:
            return
        
        logger.info("Stopping video encoding")
        
        # Stop the video encoder
        if self.video_encoder:
            self.video_encoder.stop()
        
        # Set flag to stop the thread
        self.video_enabled = False
        if self.video_thread and self.video_thread.is_alive():
            self.video_thread.join(timeout=5.0)
        self.video_thread = None
    
    def monitor_resources(self) -> None:
        """Monitor system resources and adjust behavior accordingly."""
        while self.running:
            try:
                # Get CPU usage
                self.resource_usage["cpu_percent"] = psutil.cpu_percent(interval=1.0)
                
                # Get memory usage
                process = psutil.Process(os.getpid())
                self.resource_usage["memory_mb"] = process.memory_info().rss / (1024 * 1024)
                
                # Get GPU usage (placeholder - would need a GPU monitoring library)
                # In a real implementation, we would use nvidia-smi, AMD equivalent, or a library
                self.resource_usage["gpu_percent"] = 0.0
                
                # Log resource usage periodically
                logger.debug(f"Resource usage: CPU {self.resource_usage['cpu_percent']}%, "
                           f"Memory {self.resource_usage['memory_mb']:.2f} MB, "
                           f"GPU {self.resource_usage['gpu_percent']}%")
                
                # Check if we need to adjust video encoding based on resource usage
                if (self.video_thread and self.video_thread.is_alive() and
                    self.config["video_mode"] == "auto"):
                    
                    if (self.resource_usage["cpu_percent"] > self.config["resource_limits"]["max_cpu_percent"] or
                        self.resource_usage["gpu_percent"] > self.config["resource_limits"]["max_gpu_percent"]):
                        logger.info("System resources too high, stopping video encoding")
                        self.stop_video_encoding()
                
                # Sleep before next check
                time.sleep(5.0)
                
            except Exception as e:
                logger.error(f"Error monitoring resources: {e}")
                time.sleep(10.0)  # Longer sleep on error
    
    def check_for_updates(self) -> None:
        """Check for agent updates periodically."""
        while self.running:
            try:
                logger.info("Checking for updates")
                
                # In a real implementation, we would check a server endpoint for updates
                # For now, we'll just simulate no updates available
                
                # Simulated update check
                # response = requests.get(
                #     f"{self.config['backend_url']}/api/v1/agent/version",
                #     headers={"Authorization": f"Bearer {self.config['api_key']}"},
                #     timeout=10.0
                # )
                # 
                # if response.status_code == 200:
                #     latest_version = response.json().get("version")
                #     if latest_version and latest_version != VERSION:
                #         logger.info(f"Update available: v{latest_version}")
                #         self.download_and_apply_update(latest_version)
                #     else:
                #         logger.info("No updates available")
                # else:
                #     logger.warning(f"Failed to check for updates: HTTP {response.status_code}")
                
                logger.info("No updates available")
                
                # Sleep for a longer period before checking again
                time.sleep(3600.0)  # Check once per hour
                
            except Exception as e:
                logger.error(f"Error checking for updates: {e}")
                time.sleep(7200.0)  # Retry after 2 hours on error
    
    def download_and_apply_update(self, version: str) -> None:
        """
        Download and apply an agent update.
        
        Args:
            version: The version to update to
        """
        logger.info(f"Downloading update v{version}")
        
        # In a real implementation, we would:
        # 1. Download the update package
        # 2. Verify its integrity
        # 3. Stop all agent components
        # 4. Apply the update
        # 5. Restart the agent
        
        logger.info(f"Update to v{version} would be applied here")
    
    def telemetry_placeholder(self) -> None:
        """Placeholder for telemetry collection functionality."""
        logger.info("Telemetry collection started (placeholder)")
        while self.running and self.iracing_running:
            # Simulate telemetry collection
            self.last_telemetry_time = time.time()
            time.sleep(0.1)  # Simulate 10Hz telemetry
    
    def video_encoding_loop(self) -> None:
        """Main video encoding loop."""
        logger.info("Video encoding started")
        frame_interval = 1.0 / self.config["video_frame_rate"]
        last_frame_time = time.time()
        
        while self.running and self.video_enabled:
            try:
                current_time = time.time()
                elapsed = current_time - last_frame_time
                
                # Capture frame at the specified frame rate
                if elapsed >= frame_interval:
                    # In a real implementation, we would capture the frame from the game
                    # For now, we'll simulate frame capture with mock data
                    self.capture_and_encode_frame()
                    last_frame_time = current_time
                    self.last_video_frame_time = current_time
                else:
                    # Sleep for a bit to avoid consuming too much CPU
                    sleep_time = max(0.001, frame_interval - elapsed)
                    time.sleep(sleep_time)
            except Exception as e:
                logger.error(f"Error in video encoding loop: {e}")
                time.sleep(0.1)  # Sleep on error to avoid tight loop
        
        logger.info("Video encoding stopped")
    
    def capture_and_encode_frame(self) -> None:
        """Capture a frame from the game and send it to the encoder."""
        try:
            # In a real implementation, we would:
            # 1. Capture the frame from the game window
            # 2. Process the frame if needed (resize, crop, etc.)
            # 3. Send it to the encoder
            
            # For now, we'll simulate with mock data
            import numpy as np
            from PIL import Image
            
            # Create a mock frame (black with a timestamp)
            width, height = map(int, self.config["video_resolution"].split("x"))
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Add timestamp text to the frame
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            
            # Convert to PIL Image for easier text rendering
            pil_image = Image.fromarray(frame)
            
            # Send to encoder
            if self.video_encoder:
                self.video_encoder.add_frame({
                    "image": pil_image,
                    "timestamp": time.time(),
                    "frame_number": self.video_encoder.stats["frames_received"] + 1,
                    "metadata": {
                        "session_id": self.session_id,
                        "timestamp": timestamp
                    }
                })
        except Exception as e:
            logger.error(f"Error capturing frame: {e}")
    
    def handle_exit(self, signum, frame) -> None:
        """Handle exit signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down")
        self.stop()
        sys.exit(0)


def main():
    """Main entry point for the BlackBox Relay Agent."""
    agent = CoreAgent()
    try:
        agent.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down")
        agent.stop()
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        agent.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()
