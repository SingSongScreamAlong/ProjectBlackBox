"""
Centralized Configuration for Relay Agent

All environment variables should be accessed through this module.
Provides type-safe configuration with sensible defaults for development.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from root .env file first, then local
root_env = Path(__file__).parent.parent / '.env'
local_env = Path(__file__).parent / '.env'

if root_env.exists():
    load_dotenv(root_env)
if local_env.exists():
    load_dotenv(local_env, override=True)  # Local overrides root


class Config:
    """Centralized configuration class"""
    
    def __init__(self):
        self._validate_production()
    
    # Server Configuration
    @property
    def NODE_ENV(self) -> str:
        return os.getenv('NODE_ENV', 'development')
    
    @property
    def is_production(self) -> bool:
        return self.NODE_ENV == 'production'
    
    @property
    def is_development(self) -> bool:
        return self.NODE_ENV == 'development'
    
    # Backend Services
    @property
    def BACKEND_URL(self) -> str:
        return os.getenv('BACKEND_URL', 'http://localhost:3000')
    
    @property
    def SERVER_URL(self) -> str:
        return os.getenv('SERVER_URL', 'http://localhost:3000')
    
    @property
    def RELAY_AGENT_PORT(self) -> int:
        return int(os.getenv('RELAY_AGENT_PORT', '8765'))
    
    @property
    def RELAY_AGENT_HOST(self) -> str:
        return os.getenv('RELAY_AGENT_HOST', '0.0.0.0')
    
    # API Keys
    @property
    def API_KEY(self) -> Optional[str]:
        return os.getenv('API_KEY')
    
    @property
    def SERVICE_TOKEN(self) -> Optional[str]:
        return os.getenv('SERVICE_TOKEN')
    
    @property
    def OPENAI_API_KEY(self) -> Optional[str]:
        return os.getenv('OPENAI_API_KEY')
    
    @property
    def ELEVENLABS_API_KEY(self) -> Optional[str]:
        return os.getenv('ELEVENLABS_API_KEY')
    
    # Video Configuration
    @property
    def VIDEO_BITRATE(self) -> int:
        return int(os.getenv('VIDEO_BITRATE', '2500'))  # kbps
    
    @property
    def VIDEO_FPS(self) -> int:
        return int(os.getenv('VIDEO_FPS', '30'))
    
    @property
    def VIDEO_RESOLUTION(self) -> tuple:
        width = int(os.getenv('VIDEO_WIDTH', '1280'))
        height = int(os.getenv('VIDEO_HEIGHT', '720'))
        return (width, height)
    
    # Telemetry Configuration
    @property
    def TELEMETRY_BATCH_SIZE(self) -> int:
        return int(os.getenv('TELEMETRY_BATCH_SIZE', '10'))
    
    @property
    def TELEMETRY_SEND_INTERVAL(self) -> float:
        return float(os.getenv('TELEMETRY_SEND_INTERVAL', '1.0'))  # seconds
    
    # Feature Flags
    @property
    def ENABLE_VIDEO_STREAMING(self) -> bool:
        return os.getenv('ENABLE_VIDEO_STREAMING', 'true').lower() != 'false'
    
    @property
    def ENABLE_TELEMETRY_RELAY(self) -> bool:
        return os.getenv('ENABLE_TELEMETRY_RELAY', 'true').lower() != 'false'
    
    # Logging
    @property
    def LOG_LEVEL(self) -> str:
        default = 'INFO' if self.is_production else 'DEBUG'
        return os.getenv('LOG_LEVEL', default).upper()
    
    def _validate_production(self):
        """Validate required environment variables in production"""
        if not self.is_production:
            return
        
        required = ['BACKEND_URL', 'API_KEY']
        missing = [key for key in required if not os.getenv(key)]
        
        if missing:
            raise ValueError(f"Missing required environment variables in production: {', '.join(missing)}")


# Export singleton instance
config = Config()


# Helper functions
def get_backend_url() -> str:
    """Get backend URL"""
    return config.BACKEND_URL


def get_api_key() -> Optional[str]:
    """Get API key for backend authentication"""
    return config.API_KEY


def is_production() -> bool:
    """Check if running in production"""
    return config.is_production
