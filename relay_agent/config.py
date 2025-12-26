"""
PitBox Relay Agent - Configuration
(Based on ControlBox Relay)
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from root .env
root_env = Path(__file__).parent.parent / '.env'
local_env = Path(__file__).parent / '.env'

if root_env.exists():
    load_dotenv(root_env)
if local_env.exists():
    load_dotenv(local_env, override=True)

# PitBox Server Connection (local or cloud)
CLOUD_URL = os.getenv('BLACKBOX_SERVER_URL', 'http://localhost:3000')
AI_AGENT_URL = os.getenv('AI_AGENT_URL', 'http://localhost:3001')

# Relay Identification
RELAY_ID = os.getenv('RELAY_ID', 'pitbox-relay-1')
RELAY_VERSION = '1.0.0'

# Telemetry
TELEMETRY_RATE_HZ = int(os.getenv('TELEMETRY_RATE_HZ', '10'))

# PTT Defaults (used by main.py if not using settings_manager directly)
PTT_TYPE = 'keyboard'
PTT_KEY = 'space'
JOYSTICK_ID = 0
JOYSTICK_BUTTON = 0

# Polling Configuration
POLL_RATE_HZ = int(os.getenv('POLL_RATE_HZ', '10'))  # Telemetry updates per second
POLL_INTERVAL = 1.0 / POLL_RATE_HZ

# Incident Detection Thresholds
INCIDENT_THRESHOLD = int(os.getenv('INCIDENT_THRESHOLD', '1'))  # Min incident count change to report
POSITION_JUMP_THRESHOLD = float(os.getenv('POSITION_JUMP_THRESHOLD', '0.05'))  # 5% track position jump

# Logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_TELEMETRY = os.getenv('LOG_TELEMETRY', 'false').lower() == 'true'

# Session Types
SESSION_TYPES = {
    'Practice': 'practice',
    'Lone Qualify': 'qualifying',
    'Open Qualify': 'qualifying',
    'Qualify': 'qualifying',
    'Race': 'race',
    'Warmup': 'warmup',
    'Time Trial': 'practice'
}

# Flag State Mapping (iRacing SessionFlags to PitBox)
FLAG_STATES = {
    'green': 'green',
    'checkered': 'checkered',
    'white': 'white',
    'yellow': 'yellow',
    'yellowWaving': 'yellow',
    'caution': 'caution',
    'cautionWaving': 'caution',
    'red': 'red',
    'blue': 'green',  # Blue flag doesn't change race state
    'debris': 'green',
    'crossed': 'green',
    'black': 'green',
    'disqualify': 'green',
    'repair': 'green',
    'startHidden': 'green',
    'startReady': 'green',
    'startSet': 'green',
    'startGo': 'green',
    'oneLapToGreen': 'restart',
    'greenHeld': 'green',
    'randomWaving': 'localYellow',
    'furled': 'green'
}

# =============================================================================
# BroadcastBox Streaming Configuration
# =============================================================================

# Master enable for video streaming
STREAM_ENABLED = os.getenv('STREAM_ENABLED', 'false').lower() == 'true'

# Video quality settings
STREAM_FPS = int(os.getenv('STREAM_FPS', '60'))
STREAM_RESOLUTION = os.getenv('STREAM_RESOLUTION', '720p')  # 480p, 720p, 1080p
STREAM_BITRATE = int(os.getenv('STREAM_BITRATE', '4000'))   # kbps
STREAM_CODEC = os.getenv('STREAM_CODEC', 'H264')

# Transport selection (WebRTC is recommended for lowest latency)
STREAM_TRANSPORT = os.getenv('STREAM_TRANSPORT', 'webrtc')  # webrtc, srt, rtmp

# STUN/TURN servers for NAT traversal
STUN_SERVERS = os.getenv('STUN_SERVERS', 'stun:stun.l.google.com:19302,stun:stun1.l.google.com:19302').split(',')
TURN_SERVER = os.getenv('TURN_SERVER', '')
TURN_USERNAME = os.getenv('TURN_USERNAME', '')
TURN_CREDENTIAL = os.getenv('TURN_CREDENTIAL', '')

# Performance safeguards (ZERO DRIVER IMPACT rule)
FAILSAFE_FPS_MIN = int(os.getenv('FAILSAFE_FPS_MIN', '55'))      # Min iRacing FPS
FAILSAFE_CPU_MAX = int(os.getenv('FAILSAFE_CPU_MAX', '85'))      # Max system CPU %
FAILSAFE_ENCODE_LAG_MS = int(os.getenv('FAILSAFE_ENCODE_LAG_MS', '50'))  # Max encoder lag

# Stream access control
STREAM_ACCESS_LEVEL = os.getenv('STREAM_ACCESS_LEVEL', 'public')  # public, team, league, private

# Audio capture (Phase 2)
STREAM_AUDIO_ENABLED = os.getenv('STREAM_AUDIO_ENABLED', 'false').lower() == 'true'
STREAM_AUDIO_DEVICE = os.getenv('STREAM_AUDIO_DEVICE', '')  # Empty = default device

