#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
BlackBox Relay Agent - Video Encoder Module

This module is responsible for:
1. Receiving video frames from the driver app
2. Encoding video frames using hardware acceleration when available
3. Transmitting encoded video to the backend server
4. Managing video quality and bitrate based on network conditions
"""

import os
import time
import json
import queue
import logging
import threading
import subprocess
from typing import Dict, List, Optional, Tuple, Union, Any
from datetime import datetime

import cv2
import numpy as np
import websocket
import requests
from PIL import Image
import io

# Configure logging
logger = logging.getLogger("video_encoder")

class VideoEncoder:
    """Video encoder for BlackBox Relay Agent"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the video encoder
        
        Args:
            config: Configuration dictionary with the following keys:
                - backend_url: URL of the backend server
                - api_key: API key for authentication
                - video_quality: Quality setting (low, medium, high)
                - max_bitrate: Maximum bitrate in kbps
                - frame_rate: Target frame rate
                - resolution: Output resolution (width x height)
                - encoder: Preferred encoder (h264, h265, vp9)
                - use_hardware_accel: Whether to use hardware acceleration
        """
        self.config = config
        self.backend_url = config.get("backend_url", "ws://localhost:3000/video")
        self.api_key = config.get("api_key", "")
        self.video_quality = config.get("video_quality", "medium")
        self.max_bitrate = config.get("max_bitrate", 2000)  # kbps
        self.frame_rate = config.get("frame_rate", 30)
        self.resolution = config.get("resolution", "1280x720")
        self.encoder = config.get("encoder", "h264")
        self.use_hardware_accel = config.get("use_hardware_accel", True)
        
        # Parse resolution
        width, height = self.resolution.split("x")
        self.width = int(width)
        self.height = int(height)
        
        # Initialize state
        self.running = False
        self.connected = False
        self.session_id = ""
        self.frame_queue = queue.Queue(maxsize=100)  # Max 100 frames in queue
        self.encoded_frame_queue = queue.Queue(maxsize=50)  # Queue for encoded frames ready to transmit
        self.ws = None
        self.encode_thread = None
        self.transmit_thread = None
        self.current_quality = 85  # JPEG quality (0-100)
        self.stats = {
            "frames_received": 0,
            "frames_encoded": 0,
            "frames_transmitted": 0,
            "encoding_fps": 0,
            "transmission_fps": 0,
            "current_bitrate": 0,
            "dropped_frames": 0,
            "encoding_latency_ms": 0,
            "transmission_latency_ms": 0
        }
        
        # Select encoder based on hardware availability
        self.select_encoder()
        
        logger.info(f"VideoEncoder initialized with {self.width}x{self.height} at {self.frame_rate}fps")
        logger.info(f"Using encoder: {self.encoder_name}")
    
    def select_encoder(self):
        """Select the best available encoder based on hardware and preferences"""
        # Default to software encoding
        self.encoder_name = "libx264"  # Default software H.264 encoder
        self.encoding_params = {
            "preset": "veryfast",
            "tune": "zerolatency"
        }
        
        if not self.use_hardware_accel:
            logger.info("Hardware acceleration disabled, using software encoding")
            return
        
        # Check for NVIDIA GPU (NVENC)
        try:
            gpu_info = subprocess.check_output("nvidia-smi", shell=True)
            if b"NVIDIA" in gpu_info:
                if self.encoder == "h264":
                    self.encoder_name = "h264_nvenc"
                elif self.encoder == "h265":
                    self.encoder_name = "hevc_nvenc"
                logger.info(f"NVIDIA GPU detected, using {self.encoder_name}")
                self.encoding_params = {
                    "preset": "p1",  # Low latency preset
                    "zerolatency": "1"
                }
                return
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        
        # Check for Intel QuickSync
        try:
            cpu_info = subprocess.check_output("lscpu", shell=True)
            if b"Intel" in cpu_info:
                if self.encoder == "h264":
                    self.encoder_name = "h264_qsv"
                elif self.encoder == "h265":
                    self.encoder_name = "hevc_qsv"
                logger.info(f"Intel CPU detected, using {self.encoder_name}")
                self.encoding_params = {
                    "preset": "veryfast"
                }
                return
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        
        # Check for AMD GPU (AMF)
        try:
            gpu_info = subprocess.check_output("lspci | grep -i amd", shell=True)
            if b"AMD" in gpu_info or b"Radeon" in gpu_info:
                if self.encoder == "h264":
                    self.encoder_name = "h264_amf"
                elif self.encoder == "h265":
                    self.encoder_name = "hevc_amf"
                logger.info(f"AMD GPU detected, using {self.encoder_name}")
                self.encoding_params = {
                    "usage": "lowlatency"
                }
                return
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        
        # Fallback to software encoding
        logger.info("No hardware encoder detected, using software encoding")
    
    def start(self, session_id: str) -> bool:
        """
        Start the video encoder
        
        Args:
            session_id: Session ID for the current recording
            
        Returns:
            bool: True if started successfully, False otherwise
        """
        if self.running:
            logger.warning("VideoEncoder is already running")
            return True
        
        self.session_id = session_id
        self.running = True
        
        # Initialize video writer
        self.init_video_writer()
        
        # Start encoding thread
        self.encode_thread = threading.Thread(target=self._encoding_loop)
        self.encode_thread.daemon = True
        self.encode_thread.start()
        
        # Start transmission thread
        self.transmit_thread = threading.Thread(target=self._transmission_loop)
        self.transmit_thread.daemon = True
        self.transmit_thread.start()
        
        logger.info(f"VideoEncoder started for session {session_id}")
        return True
    
    def stop(self):
        """Stop the video encoder"""
        if not self.running:
            return
        
        self.running = False
        
        # Wait for threads to finish
        if self.encode_thread:
            self.encode_thread.join(timeout=2.0)
        
        if self.transmit_thread:
            self.transmit_thread.join(timeout=2.0)
        
        # Close WebSocket connection
        if self.ws and self.connected:
            self.ws.close()
            self.connected = False
        
        # Release video writer
        if hasattr(self, 'video_writer') and self.video_writer:
            self.video_writer.release()
        
        logger.info("VideoEncoder stopped")
    
    def init_video_writer(self):
        """Initialize the video writer based on selected encoder"""
        # Set codec based on encoder
        if "264" in self.encoder_name:
            fourcc = cv2.VideoWriter_fourcc(*'H264')
        elif "265" in self.encoder_name or "hevc" in self.encoder_name:
            fourcc = cv2.VideoWriter_fourcc(*'HEVC')
        elif "vp9" in self.encoder_name:
            fourcc = cv2.VideoWriter_fourcc(*'VP90')
        else:
            fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Fallback
        
        # Quality settings
        bitrate_map = {
            "low": int(self.max_bitrate * 0.5),
            "medium": int(self.max_bitrate * 0.75),
            "high": self.max_bitrate
        }
        bitrate = bitrate_map.get(self.video_quality, bitrate_map["medium"])
        
        # Create temp file path for encoded video
        temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp")
        os.makedirs(temp_dir, exist_ok=True)
        temp_file = os.path.join(temp_dir, f"{self.session_id}.mp4")
        
        # Initialize video writer
        self.video_writer = cv2.VideoWriter()
        self.video_writer.open(
            temp_file,
            fourcc,
            self.frame_rate,
            (self.width, self.height),
            True  # isColor
        )
        
        # Set bitrate
        self.video_writer.set(cv2.VIDEOWRITER_PROP_QUALITY, 100)  # Quality percentage
        if hasattr(cv2, 'VIDEOWRITER_PROP_BITRATE'):
            self.video_writer.set(cv2.VIDEOWRITER_PROP_BITRATE, bitrate * 1000)  # Convert to bps
        
        logger.info(f"Video writer initialized with {self.width}x{self.height} at {self.frame_rate}fps, {bitrate}kbps")
    
    def add_frame(self, frame_data: Dict[str, Any]):
        """
        Add a frame to the encoding queue
        
        Args:
            frame_data: Dictionary containing frame information:
                - image: PIL Image or numpy array
                - timestamp: Frame timestamp
                - frame_number: Frame number in sequence
                - metadata: Additional metadata
        """
        if not self.running:
            return
        
        try:
            # Add to queue, drop if queue is full
            try:
                self.frame_queue.put(frame_data, block=False)
                self.stats["frames_received"] += 1
            except queue.Full:
                self.stats["dropped_frames"] += 1
                logger.warning("Frame queue full, dropping frame")
        except Exception as e:
            logger.error(f"Error adding frame: {e}")
    
    def _encoding_loop(self):
        """Main encoding loop"""
        last_fps_time = time.time()
        frames_encoded = 0
        
        while self.running:
            try:
                # Get frame from queue
                try:
                    frame_data = self.frame_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                
                # Measure encoding time
                start_time = time.time()
                
                # Process frame
                frame = frame_data.get("image")
                if isinstance(frame, Image.Image):
                    # Convert PIL image to numpy array
                    frame = np.array(frame)
                    # Convert RGB to BGR (OpenCV format)
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                # Resize if needed
                if frame.shape[1] != self.width or frame.shape[0] != self.height:
                    frame = cv2.resize(frame, (self.width, self.height))
                
                # Write frame to video writer for recording
                if hasattr(self, 'video_writer') and self.video_writer:
                    self.video_writer.write(frame)

                # Encode frame to JPEG for transmission
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.current_quality]
                success, buffer = cv2.imencode('.jpg', frame, encode_param)

                if success:
                    # Create frame packet
                    frame_packet = {
                        "session_id": self.session_id,
                        "frame_number": frame_data.get("frame_number", 0),
                        "timestamp": frame_data.get("timestamp", time.time()),
                        "data": buffer.tobytes(),
                        "metadata": frame_data.get("metadata", {})
                    }

                    # Add to transmission queue
                    try:
                        self.encoded_frame_queue.put(frame_packet, block=False)
                    except queue.Full:
                        # Drop oldest frame and add new one
                        try:
                            self.encoded_frame_queue.get_nowait()
                            self.encoded_frame_queue.put(frame_packet, block=False)
                        except:
                            pass

                # Update stats
                frames_encoded += 1
                self.stats["frames_encoded"] += 1
                self.stats["encoding_latency_ms"] = (time.time() - start_time) * 1000

                # Calculate FPS
                if time.time() - last_fps_time >= 1.0:
                    self.stats["encoding_fps"] = frames_encoded
                    frames_encoded = 0
                    last_fps_time = time.time()

                # Mark as done
                self.frame_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in encoding loop: {e}")
                time.sleep(0.1)
    
    def _transmission_loop(self):
        """Main transmission loop"""
        last_fps_time = time.time()
        frames_transmitted = 0
        
        # Connect to backend
        self._connect_to_backend()
        
        while self.running:
            try:
                # If not connected, try to reconnect
                if not self.connected:
                    if not self._connect_to_backend():
                        time.sleep(2.0)  # Wait before retry
                        continue

                # Get encoded frame from queue
                try:
                    frame_packet = self.encoded_frame_queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                # Measure transmission time
                start_time = time.time()

                try:
                    # Send frame via WebSocket
                    if self.ws and self.connected:
                        # Create message with frame data
                        message = {
                            "type": "video_frame",
                            "session_id": frame_packet["session_id"],
                            "frame_number": frame_packet["frame_number"],
                            "timestamp": frame_packet["timestamp"],
                            "metadata": frame_packet["metadata"]
                        }

                        # Send metadata first
                        self.ws.send(json.dumps(message))

                        # Send binary frame data
                        self.ws.send(frame_packet["data"], opcode=websocket.ABNF.OPCODE_BINARY)

                        # Update stats
                        frames_transmitted += 1
                        self.stats["frames_transmitted"] += 1
                        self.stats["transmission_latency_ms"] = (time.time() - start_time) * 1000

                        # Calculate FPS
                        if time.time() - last_fps_time >= 1.0:
                            self.stats["transmission_fps"] = frames_transmitted
                            frames_transmitted = 0
                            last_fps_time = time.time()
                    else:
                        # Not connected, discard frame
                        logger.warning("WebSocket not connected, discarding frame")
                        self.connected = False

                except Exception as e:
                    logger.error(f"Error transmitting frame: {e}")
                    self.connected = False
                
            except Exception as e:
                logger.error(f"Error in transmission loop: {e}")
                self.connected = False
                time.sleep(0.1)
    
    def _connect_to_backend(self) -> bool:
        """
        Connect to the backend server
        
        Returns:
            bool: True if connected successfully, False otherwise
        """
        try:
            # Close existing connection if any
            if self.ws:
                try:
                    self.ws.close()
                except:
                    pass
                self.ws = None
            
            # Create new WebSocket connection
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "X-Session-ID": self.session_id
            }
            
            self.ws = websocket.WebSocketApp(
                self.backend_url,
                header=headers,
                on_open=self._on_ws_open,
                on_message=self._on_ws_message,
                on_error=self._on_ws_error,
                on_close=self._on_ws_close
            )
            
            # Start WebSocket in a separate thread
            ws_thread = threading.Thread(target=self.ws.run_forever)
            ws_thread.daemon = True
            ws_thread.start()
            
            # Wait for connection to establish
            for _ in range(10):  # Wait up to 1 second
                if self.connected:
                    return True
                time.sleep(0.1)
            
            return self.connected
            
        except Exception as e:
            logger.error(f"Error connecting to backend: {e}")
            self.connected = False
            return False
    
    def _on_ws_open(self, ws):
        """WebSocket open handler"""
        logger.info("Connected to backend server")
        self.connected = True
        
        # Send initial configuration
        config_msg = {
            "type": "config",
            "session_id": self.session_id,
            "frame_rate": self.frame_rate,
            "resolution": f"{self.width}x{self.height}",
            "encoder": self.encoder,
            "timestamp": datetime.now().isoformat()
        }
        ws.send(json.dumps(config_msg))
    
    def _on_ws_message(self, ws, message):
        """WebSocket message handler"""
        try:
            data = json.loads(message)
            msg_type = data.get("type", "")
            
            if msg_type == "config_ack":
                logger.info("Configuration acknowledged by server")
            elif msg_type == "bitrate_update":
                # Adjust bitrate based on network conditions
                new_bitrate = data.get("bitrate", self.max_bitrate)
                logger.info(f"Adjusting bitrate to {new_bitrate}kbps")
                self.stats["current_bitrate"] = new_bitrate

                # Update encoder quality based on bitrate
                # Map bitrate to JPEG quality (higher bitrate = higher quality)
                # Assuming max_bitrate corresponds to quality 95
                quality_ratio = min(new_bitrate / self.max_bitrate, 1.0)
                self.current_quality = int(50 + (quality_ratio * 45))  # Range: 50-95
                logger.info(f"Adjusted JPEG quality to {self.current_quality}")
            elif msg_type == "ping":
                # Respond to ping
                ws.send(json.dumps({"type": "pong", "timestamp": datetime.now().isoformat()}))
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}")
    
    def _on_ws_error(self, ws, error):
        """WebSocket error handler"""
        logger.error(f"WebSocket error: {error}")
        self.connected = False
    
    def _on_ws_close(self, ws, close_status_code, close_msg):
        """WebSocket close handler"""
        logger.info(f"WebSocket connection closed: {close_status_code} - {close_msg}")
        self.connected = False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get encoder statistics
        
        Returns:
            Dict: Statistics dictionary
        """
        return self.stats.copy()
    
    def update_settings(self, settings: Dict[str, Any]):
        """
        Update encoder settings
        
        Args:
            settings: New settings dictionary
        """
        # Store old settings
        old_settings = {
            "resolution": self.resolution,
            "frame_rate": self.frame_rate,
            "encoder": self.encoder,
            "video_quality": self.video_quality,
            "max_bitrate": self.max_bitrate,
            "use_hardware_accel": self.use_hardware_accel
        }
        
        # Update settings
        if "resolution" in settings:
            self.resolution = settings["resolution"]
            width, height = self.resolution.split("x")
            self.width = int(width)
            self.height = int(height)
        
        if "frame_rate" in settings:
            self.frame_rate = settings["frame_rate"]
        
        if "encoder" in settings:
            self.encoder = settings["encoder"]
        
        if "video_quality" in settings:
            self.video_quality = settings["video_quality"]
        
        if "max_bitrate" in settings:
            self.max_bitrate = settings["max_bitrate"]
        
        if "use_hardware_accel" in settings:
            self.use_hardware_accel = settings["use_hardware_accel"]
        
        # Check if we need to restart
        need_restart = (
            old_settings["resolution"] != self.resolution or
            old_settings["frame_rate"] != self.frame_rate or
            old_settings["encoder"] != self.encoder or
            old_settings["use_hardware_accel"] != self.use_hardware_accel
        )
        
        if need_restart and self.running:
            logger.info("Settings changed, restarting encoder")
            session_id = self.session_id
            self.stop()
            # Re-select encoder with new settings
            self.select_encoder()
            self.start(session_id)
        else:
            # Just update encoder settings
            self.select_encoder()
