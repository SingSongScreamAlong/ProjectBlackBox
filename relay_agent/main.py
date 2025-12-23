#!/usr/bin/env python3
"""
PitBox Relay Agent - Main Entry Point
Connects iRacing to PitBox Server for real-time telemetry and AI coaching

Usage:
    python main.py [--url SERVER_URL]

Environment Variables:
    BLACKBOX_SERVER_URL - PitBox Server WebSocket URL (default: http://localhost:3000)
    POLL_RATE_HZ - Telemetry polling rate (default: 10)
    LOG_LEVEL - Logging level (default: INFO)
"""
import argparse
import logging
import signal
import sys
import time
from typing import Optional

import config
from iracing_reader import IRacingReader
from pitbox_client import PitBoxClient
from video_encoder import VideoEncoder
from data_mapper import (
    map_session_metadata,
    map_telemetry_snapshot,
    map_race_event,
    map_incident
)
from voice_recognition import VoiceRecognition
from overlay import PTTOverlay
from audio_recorder import AudioRecorder

# ========================
# Logging Setup
# ========================

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


# ========================
# Main Relay Agent
# ========================

import os
from exporters.motec_exporter import MoTeCLDExporter
import json

def load_ptt_config():
    """Load PTT configuration from ptt_config.json, falling back to config.py defaults"""
    config_path = os.path.join(os.path.dirname(__file__), 'ptt_config.json')
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                ptt_config = json.load(f)
                logger.info(f"📋 Loaded PTT config: {ptt_config}")
                return ptt_config
    except Exception as e:
        logger.warning(f"Could not load ptt_config.json: {e}")
    
    # Fall back to config.py defaults
    return {
        'ptt_type': config.PTT_TYPE,
        'ptt_key': config.PTT_KEY,
        'joystick_id': config.JOYSTICK_ID,
        'joystick_button': config.JOYSTICK_BUTTON
    }

class RelayAgent:
    """
    Main Relay Agent Class
    Orchestrates reading from iRacing and sending to PitBox Cloud
    """
    
    def __init__(self, cloud_url: str = None, monitor_index: int = 1):
        self.ir_reader = IRacingReader()
        self.cloud_client = PitBoxClient(cloud_url)
        self.video_encoder = VideoEncoder(self.cloud_client, monitor_index)
        
        # Load PTT config from ptt_config.json
        ptt_config = load_ptt_config()
        self.vr = VoiceRecognition(
            ptt_type=ptt_config.get('ptt_type', 'keyboard'),
            ptt_key=ptt_config.get('ptt_key', 'space'),
            joystick_id=ptt_config.get('joystick_id', 0),
            joystick_button=ptt_config.get('joystick_button', 0)
        )
        self.overlay = PTTOverlay()
        
        # Set up callback for when PTT binding changes via HUD
        if hasattr(self.overlay, 'hud'):
            self.overlay.hud.set_ptt_callback(self._on_ptt_binding_changed)
        
        # Audio recorder for voice commands
        self.audio_recorder = AudioRecorder()
        self._setup_voice_callbacks()
        
        # MoTeC Exporter
        self.motec_exporter = MoTeCLDExporter()
        self._setup_motec_channels()
        
        self.running = False
        self.session_id: Optional[str] = None
        self.last_flag_state: str = 'green'
        self.discipline_category: str = 'road'
        
        # Voice state
        self.ptt_was_pressed = False
        self.current_context: dict = {}
        
        # Stats
        self.start_time = 0
        self.telemetry_count = 0
        self.incident_count = 0
    
    def _setup_voice_callbacks(self):
        """Set up callbacks for voice responses from server"""
        def on_voice_audio(audio_bytes):
            """Play TTS audio response"""
            self.audio_recorder.play_audio(audio_bytes, 'mp3')
        
        def on_engineer_text(text):
            """Display engineer response in HUD"""
            if hasattr(self.overlay, 'set_engineer_response'):
                self.overlay.set_engineer_response(text)
            elif hasattr(self.overlay, 'hud'):
                self.overlay.hud.set_engineer_response(text)
        
        self.cloud_client.on_voice_response = on_voice_audio
        self.cloud_client.on_engineer_text = on_engineer_text
    
    def _on_ptt_binding_changed(self, ptt_type: str, ptt_key: str, joystick_id: int, joystick_button: int):
        """Callback when PTT binding is changed via HUD settings"""
        logger.info(f"🎯 PTT binding changed: type={ptt_type}, key={ptt_key}, joy_id={joystick_id}, button={joystick_button}")
        
        # Update VoiceRecognition with new binding and re-initialize devices
        self.vr.reconfigure(
            ptt_type=ptt_type,
            ptt_key=ptt_key,
            joystick_id=joystick_id,
            joystick_button=joystick_button
        )
        
        logger.info(f"✅ VoiceRecognition reconfigured with new PTT binding")

    def _setup_motec_channels(self):
        """Configure MoTeC channels"""
        self.motec_exporter.add_channel("Speed", "km/h")
        self.motec_exporter.add_channel("RPM", "rpm")
        self.motec_exporter.add_channel("Gear", "")
        self.motec_exporter.add_channel("Throttle", "%")
        self.motec_exporter.add_channel("Brake", "%")
        self.motec_exporter.add_channel("Steering", "%") # Or degrees
        self.motec_exporter.add_channel("Lap", "")
        
    def start(self):
        """Start the relay agent"""
        self.running = True
        self.start_time = time.time()
        
        # Video encoder flag - starts after session is established
        self.video_started = False
        
        # Start Overlay
        self.overlay.start()
        
        print("╔════════════════════════════════════════════════════════════╗")
        print("║         PitBox Relay Agent v1.0.0                        ║")
        print("║         iRacing → PitBox AI Coaching Bridge              ║")
        print("╚════════════════════════════════════════════════════════════╝")
        print(f"Connecting to: {self.cloud_client.url}")
        
        self.cloud_client.connect()
        self._main_loop()
    
    def stop(self):
        """Stop the relay agent"""
        self.running = False
        self.video_encoder.stop()
        self.overlay.stop()
        self.ir_reader.disconnect()
        self.cloud_client.disconnect()
        
        # Export MoTeC Data
        if self.session_id:
            filename = f"pitbox_session_{self.session_id}_{int(time.time())}.ld"
            self.motec_exporter.export(filename)
            print(f"💾 Saved MoTeC telemetry to: {filename}")
        
        # Print stats
        elapsed = time.time() - self.start_time
        print()
        print("═" * 50)
        print(f"Session Stats:")
        print(f"  Runtime: {elapsed:.1f}s")
        print(f"  Telemetry frames sent: {self.telemetry_count}")
        print(f"  Video frames sent: {self.video_encoder.frames_sent}")
        print(f"  Incidents detected: {self.incident_count}")
        print("═" * 50)
    
    def _main_loop(self):
        """Main polling loop"""
        logger.info("Waiting for iRacing...")
        
        session_sent = False
        
        while self.running:
            # Check PTT for voice recording
            ptt_pressed = self.vr.is_pressed() if hasattr(self, 'vr') else False
            
            # Update overlay PTT state
            if hasattr(self, 'overlay'):
                self.overlay.set_talking(ptt_pressed)
            
            # Handle PTT press/release for voice recording
            if ptt_pressed and not self.ptt_was_pressed:
                # PTT just pressed - start recording
                self.audio_recorder.start_recording()
            elif not ptt_pressed and self.ptt_was_pressed:
                # PTT just released - stop recording and send
                audio_data = self.audio_recorder.stop_recording()
                if audio_data:
                    self.cloud_client.send_voice_command(audio_data, self.current_context)
            
            self.ptt_was_pressed = ptt_pressed
                
            # Try to connect to iRacing
            if not self.ir_reader.is_connected():
                if self.ir_reader.connect():
                    session_sent = False  # Reset for new connection
                else:
                    # Not connected, wait and retry
                    self.cloud_client.wait(1.0)
                    continue
            
            # Freeze telemetry frame for consistent reads
            self.ir_reader.freeze_frame()
            
            try:
                # Send session metadata on first connect
                if not session_sent:
                    self._send_session_metadata()
                    session_sent = True
                
                # Check flag state changes
                self._check_flag_state()
                
                # Detect and report incidents
                self._check_incidents()
                
                # Send telemetry
                self._send_telemetry()
                
            finally:
                self.ir_reader.unfreeze_frame()
            
            # Wait for next poll interval
            self.cloud_client.wait(config.POLL_INTERVAL)
    
    def _send_session_metadata(self):
        """Send session metadata to cloud"""
        session = self.ir_reader.get_session_data()
        if not session:
            logger.warning("Could not read session data")
            return
        
        self.session_id = session.session_id
        metadata = map_session_metadata(session, config.RELAY_ID)
        self.discipline_category = metadata['category']
        
        logger.info(f"📋 Session: {session.track_name} [{session.session_type}]")
        logger.info(f"   Category: {self.discipline_category}")
        logger.info(f"   Multi-class: {session.is_multiclass}")
        
        self.cloud_client.send_session_metadata(metadata)
        
        # NOW start video encoder (client has session ID)
        if not self.video_encoder.running:
            logger.info("🎥 Starting video encoder...")
            self.video_encoder.start()
    
    def _check_flag_state(self):
        """Check for flag state changes and send race events"""
        flag_state = self.ir_reader.get_flag_state()
        
        if flag_state != self.last_flag_state:
            logger.info(f"🏁 Flag: {self.last_flag_state} → {flag_state}")
            
            event = map_race_event(
                self.session_id,
                flag_state,
                self.ir_reader.get_leader_lap(),
                self.ir_reader.get_session_time()
            )
            self.cloud_client.send_race_event(event)
            self.last_flag_state = flag_state
    
    def _check_incidents(self):
        """Check for and report incidents"""
        incidents = self.ir_reader.detect_incidents()
        
        for incident_data in incidents:
            logger.warning(f"⚠️ Incident detected: {incident_data['driver_names']}")
            
            incident = map_incident(
                self.session_id,
                incident_data,
                self.discipline_category
            )
            self.cloud_client.send_incident(incident)
            self.incident_count += 1
    
    def _send_telemetry(self):
        """Send telemetry snapshot"""
        cars = self.ir_reader.get_all_cars()
        
        if not cars:
            return
        
        # Filter for player car to log to MoTeC
        for car in cars:
            if car.is_player:
                self.motec_exporter.add_sample({
                    "Speed": car.speed * 3.6, # m/s to km/h
                    "RPM": car.rpm,
                    "Gear": float(car.gear),
                    "Throttle": car.throttle * 100,
                    "Brake": car.brake * 100,
                    "Steering": car.steering * 100, # Approx %
                    "Lap": float(car.lap)
                })
                break
        
        telemetry = map_telemetry_snapshot(self.session_id, cars)
        self.cloud_client.send_telemetry(telemetry)
        self.telemetry_count += 1
        
        # Update HUD with player telemetry
        for car in cars:
            if car.is_player:
                hud_data = {
                    'speed': car.speed * 3.6,  # m/s to km/h
                    'gear': car.gear,
                    'rpm': car.rpm,
                    'max_rpm': 8000,  # TODO: Get from car data
                    'lap': car.lap,
                    'total_laps': 0,  # TODO: Get from session
                    'position': car.position,
                    'gap_ahead': car.gap_to_leader if hasattr(car, 'gap_to_leader') else 0,
                    'fuel_remaining': car.fuel_level if hasattr(car, 'fuel_level') else 0,
                    'fuel_laps': 0,  # TODO: Calculate
                    'flag': self.last_flag_state,
                }
                
                # Update current context for voice commands
                self.current_context = {
                    'lap': car.lap,
                    'position': car.position,
                    'speed': car.speed * 3.6,
                }
                
                # Update HUD
                if hasattr(self.overlay, 'update_telemetry'):
                    self.overlay.update_telemetry(hud_data)
                elif hasattr(self.overlay, 'hud'):
                    self.overlay.hud.update_telemetry(hud_data)
                break
        
        if config.LOG_TELEMETRY:
            logger.debug(f"📊 Telemetry: {len(cars)} cars")


# ========================
# Entry Point
# ========================

def main():
    parser = argparse.ArgumentParser(
        description='PitBox Relay Agent - Bridge iRacing to PitBox Server'
    )
    parser.add_argument(
        '--url',
        default=config.CLOUD_URL,
        help=f'PitBox Server URL (default: {config.CLOUD_URL})'
    )
    parser.add_argument(
        '--rate',
        type=int,
        default=config.POLL_RATE_HZ,
        help=f'Telemetry poll rate in Hz (default: {config.POLL_RATE_HZ})'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--monitor',
        type=int,
        default=1,
        help='Monitor index to capture (default: 1)'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.rate:
        config.POLL_RATE_HZ = args.rate
        config.POLL_INTERVAL = 1.0 / args.rate
    
    # Create and start agent
    agent = RelayAgent(args.url, monitor_index=args.monitor)
    
    # Handle signals
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal")
        agent.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start
    agent.start()


if __name__ == '__main__':
    main()
