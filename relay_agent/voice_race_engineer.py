"""
Voice Race Engineer
Conversational AI race engineer with real-time voice I/O
Handles driver commands and provides coaching during live sessions
"""

import asyncio
import json
import logging
import numpy as np
import time
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict
import threading
import queue

# Audio processing
try:
    import pyaudio
    import wave
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    logging.warning("PyAudio not available - voice I/O disabled")

# OpenAI for speech recognition and conversation
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI not available - speech recognition disabled")

# WebSocket for real-time communication
import websockets

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class EngineerContext:
    """Current context for the race engineer"""
    session_id: str
    driver_name: str
    track_name: str
    current_lap: int
    position: int
    gap_ahead: float
    gap_behind: float
    tire_temps: Dict[str, float]
    fuel_level: float
    last_lap_time: float
    best_lap_time: float
    current_speed: float
    current_gear: int
    in_pit: bool
    flag_status: str
    timestamp: float


class VoiceRaceEngineer:
    """Conversational AI race engineer with voice I/O"""

    # ElevenLabs Voice Options for Race Engineers
    ENGINEER_VOICES = {
        'professional': {
            'id': 'pNInz6obpgDQGcFmaJgB',  # Adam - Professional, authoritative
            'name': 'Adam',
            'description': 'Professional male voice, calm and authoritative'
        },
        'experienced': {
            'id': 'VR6AewLTigWG4xSOukaG',  # Arnold - Experienced, reassuring
            'name': 'Arnold',
            'description': 'Mature male voice, experienced and reassuring'
        },
        'dynamic': {
            'id': 'ErXwobaYiN019PkySvjV',  # Antoni - Dynamic, energetic
            'name': 'Antoni',
            'description': 'Dynamic male voice, energetic and engaging'
        },
        'calm': {
            'id': 'TxGEqnHWrfWFTfGW9XjX',  # Josh - Calm, focused
            'name': 'Josh',
            'description': 'Calm male voice, focused and precise'
        }
    }

    def __init__(self,
                 api_key: Optional[str] = None,
                 elevenlabs_key: Optional[str] = None,
                 voice_profile: str = 'professional'):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.elevenlabs_key = elevenlabs_key or os.getenv('ELEVENLABS_API_KEY')

        if OPENAI_AVAILABLE and self.api_key:
            openai.api_key = self.api_key

        # ElevenLabs voice configuration
        self.voice_profile = voice_profile
        if voice_profile not in self.ENGINEER_VOICES:
            logger.warning(f"Unknown voice profile '{voice_profile}', using 'professional'")
            self.voice_profile = 'professional'

        self.voice_settings = {
            'stability': 0.65,  # Balanced stability for consistent delivery
            'similarity_boost': 0.80,  # High similarity for professional tone
            'style': 0.45,  # Moderate style for natural speech
            'use_speaker_boost': True  # Enhanced clarity
        }

        # Audio setup
        self.audio_enabled = AUDIO_AVAILABLE
        self.pyaudio_instance = None
        self.audio_stream = None

        # Recording settings
        self.sample_rate = 16000  # 16kHz for Whisper
        self.chunk_size = 1024
        self.channels = 1
        self.format = pyaudio.paInt16 if AUDIO_AVAILABLE else None

        # Conversation context
        self.context: Optional[EngineerContext] = None
        self.conversation_history: List[Dict] = []
        self.max_history = 10

        # Voice activation detection
        self.vad_threshold = 500  # Audio amplitude threshold
        self.silence_duration = 1.0  # Reduced from 1.5s - faster cutoff
        self.min_recording_duration = 0.3  # Minimum 300ms to avoid false triggers

        # Response caching for speed
        self.response_cache = {}
        self.cache_ttl = 5.0  # Cache responses for 5 seconds
        self.enable_cache = True

        # AI model selection
        self.ai_model = 'gpt-3.5-turbo'  # Much faster than GPT-4 (~300ms vs 1200ms)
        self.use_streaming = True  # Stream responses for lower latency

        # Threading
        self.audio_queue = queue.Queue()
        self.is_listening = False
        self.listen_thread = None

        # WebSocket connection
        self.ws_url = None
        self.ws = None

        voice_info = self.ENGINEER_VOICES[self.voice_profile]
        logger.info(f"Voice Race Engineer initialized with '{voice_info['name']}' voice")
        logger.info(f"Voice profile: {voice_info['description']}")
        if not AUDIO_AVAILABLE:
            logger.warning("Audio I/O disabled - install pyaudio for voice support")
        if not OPENAI_AVAILABLE:
            logger.warning("OpenAI disabled - install openai for speech recognition")
        if not self.elevenlabs_key:
            logger.warning("ElevenLabs API key not set - voice output disabled")

    def update_context(self, telemetry_data: Dict):
        """Update race engineer context with latest telemetry"""
        self.context = EngineerContext(
            session_id=telemetry_data.get('session_id', 'unknown'),
            driver_name=telemetry_data.get('driver_name', 'Driver'),
            track_name=telemetry_data.get('track_name', 'Unknown Track'),
            current_lap=telemetry_data.get('lap', 0),
            position=telemetry_data.get('position', 0),
            gap_ahead=telemetry_data.get('gap_ahead', 0.0),
            gap_behind=telemetry_data.get('gap_behind', 0.0),
            tire_temps={
                'LF': telemetry_data.get('tire_temp_lf', 0),
                'RF': telemetry_data.get('tire_temp_rf', 0),
                'LR': telemetry_data.get('tire_temp_lr', 0),
                'RR': telemetry_data.get('tire_temp_rr', 0)
            },
            fuel_level=telemetry_data.get('fuel', 0),
            last_lap_time=telemetry_data.get('last_lap_time', 0),
            best_lap_time=telemetry_data.get('best_lap_time', 0),
            current_speed=telemetry_data.get('speed', 0),
            current_gear=telemetry_data.get('gear', 0),
            in_pit=telemetry_data.get('in_pit', False),
            flag_status=telemetry_data.get('flag', 'green'),
            timestamp=time.time()
        )

    async def process_driver_message(self, text: str) -> str:
        """Process driver's spoken message and generate response (OPTIMIZED)"""
        if not OPENAI_AVAILABLE or not self.api_key:
            return "Voice recognition not available"

        logger.info(f"Driver: {text}")

        # Check cache for instant responses (common queries)
        if self.enable_cache:
            cached_response = self._check_cache(text)
            if cached_response:
                logger.info(f"✓ Cache hit! Response time: <10ms")
                return cached_response

        # Add to conversation history
        self.conversation_history.append({
            'role': 'user',
            'content': text,
            'timestamp': time.time()
        })

        # Keep history limited
        if len(self.conversation_history) > self.max_history * 2:
            self.conversation_history = self.conversation_history[-self.max_history * 2:]

        # Build system prompt with current context
        system_prompt = self._build_engineer_prompt()

        # Call OpenAI for response (using faster GPT-3.5-turbo)
        try:
            start_time = time.time()
            messages = [
                {'role': 'system', 'content': system_prompt},
                *[{'role': msg['role'], 'content': msg['content']}
                  for msg in self.conversation_history[-self.max_history:]]
            ]

            response = await openai.ChatCompletion.acreate(
                model=self.ai_model,  # gpt-3.5-turbo for speed
                messages=messages,
                max_tokens=80,  # Reduced from 150 - keep responses brief
                temperature=0.6,  # Slightly lower for faster, more focused responses
                stream=False  # Streaming in future optimization
            )

            engineer_response = response.choices[0].message.content.strip()
            ai_time = (time.time() - start_time) * 1000

            # Add to history
            self.conversation_history.append({
                'role': 'assistant',
                'content': engineer_response,
                'timestamp': time.time()
            })

            # Cache the response
            if self.enable_cache:
                self._add_to_cache(text, engineer_response)

            logger.info(f"Engineer: {engineer_response} (AI: {ai_time:.0f}ms)")
            return engineer_response

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "Copy that."  # Shorter error response

    def _build_engineer_prompt(self) -> str:
        """Build system prompt with current race context"""
        if not self.context:
            return """You are a professional race engineer. You provide clear, concise coaching
to the driver during the race. Keep responses under 2 sentences. Be supportive and data-driven."""

        prompt = f"""You are a professional race engineer for {self.context.driver_name} at {self.context.track_name}.

Current Race Status:
- Lap: {self.context.current_lap}
- Position: P{self.context.position}
- Gap to car ahead: {self.context.gap_ahead:.1f}s
- Gap to car behind: {self.context.gap_behind:.1f}s
- Last lap: {self.context.last_lap_time:.3f}s
- Best lap: {self.context.best_lap_time:.3f}s
- Fuel: {self.context.fuel_level:.1f}L
- Tire temps: LF={self.context.tire_temps['LF']:.0f}°C, RF={self.context.tire_temps['RF']:.0f}°C, LR={self.context.tire_temps['LR']:.0f}°C, RR={self.context.tire_temps['RR']:.0f}°C
- Flag: {self.context.flag_status}
- In pit: {self.context.in_pit}

Instructions:
- Provide clear, concise responses (1-2 sentences max)
- Be supportive and professional like a real F1/IndyCar engineer
- Use data to back up your advice
- Respond naturally to questions about gaps, tires, fuel, strategy
- If asked about something you don't have data for, be honest
- Use racing terminology (delta, stint, deg, undercut, etc.)
- Keep responses brief - driver needs to focus on driving

Examples:
Driver: "How are my tires?"
Engineer: "Fronts are at 92°C, rears at 95°C. You're in the optimal window, keep pushing."

Driver: "What's my gap?"
Engineer: "2.3 seconds to P3, you're gaining 2 tenths per lap. Keep this pace."

Driver: "Do I need to save fuel?"
Engineer: "You're good on fuel for 12 more laps. No need to lift and coast."
"""
        return prompt

    async def transcribe_audio(self, audio_file_path: str) -> Optional[str]:
        """Transcribe audio file to text using OpenAI Whisper"""
        if not OPENAI_AVAILABLE or not self.api_key:
            return None

        try:
            with open(audio_file_path, 'rb') as audio_file:
                transcript = await openai.Audio.atranscribe(
                    model="whisper-1",
                    file=audio_file,
                    language="en"
                )

            return transcript['text']
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return None

    def start_listening(self):
        """Start listening for driver voice input"""
        if not self.audio_enabled:
            logger.error("Audio not available")
            return False

        if self.is_listening:
            logger.warning("Already listening")
            return False

        self.is_listening = True
        self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listen_thread.start()
        logger.info("✓ Started listening for driver input")
        return True

    def stop_listening(self):
        """Stop listening for voice input"""
        self.is_listening = False
        if self.listen_thread:
            self.listen_thread.join(timeout=2.0)
        logger.info("✓ Stopped listening")

    def _listen_loop(self):
        """Background thread for continuous voice detection"""
        try:
            self.pyaudio_instance = pyaudio.PyAudio()
            self.audio_stream = self.pyaudio_instance.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )

            logger.info("🎤 Microphone active - speak naturally")

            while self.is_listening:
                # Detect voice activity
                if self._detect_voice_activity():
                    logger.info("🗣️  Voice detected - recording...")
                    audio_data = self._record_until_silence()

                    # Save to temp file
                    temp_file = f"/tmp/driver_voice_{int(time.time())}.wav"
                    self._save_wav(temp_file, audio_data)

                    # Queue for processing
                    self.audio_queue.put(temp_file)
                    logger.info("✓ Recording complete - processing...")

        except Exception as e:
            logger.error(f"Error in listen loop: {e}")
        finally:
            if self.audio_stream:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
            if self.pyaudio_instance:
                self.pyaudio_instance.terminate()

    def _detect_voice_activity(self) -> bool:
        """Simple voice activity detection based on amplitude"""
        try:
            data = self.audio_stream.read(self.chunk_size, exception_on_overflow=False)
            audio_data = np.frombuffer(data, dtype=np.int16)
            amplitude = np.abs(audio_data).mean()
            return amplitude > self.vad_threshold
        except Exception:
            return False

    def _record_until_silence(self) -> bytes:
        """Record audio until silence is detected"""
        frames = []
        silence_chunks = 0
        max_silence_chunks = int(self.silence_duration * self.sample_rate / self.chunk_size)

        while self.is_listening:
            try:
                data = self.audio_stream.read(self.chunk_size, exception_on_overflow=False)
                frames.append(data)

                # Check for silence
                audio_data = np.frombuffer(data, dtype=np.int16)
                amplitude = np.abs(audio_data).mean()

                if amplitude < self.vad_threshold:
                    silence_chunks += 1
                    if silence_chunks > max_silence_chunks:
                        break
                else:
                    silence_chunks = 0

                # Safety limit (30 seconds max)
                if len(frames) > self.sample_rate / self.chunk_size * 30:
                    break

            except Exception as e:
                logger.error(f"Recording error: {e}")
                break

        return b''.join(frames)

    def _save_wav(self, filename: str, audio_data: bytes):
        """Save audio data to WAV file"""
        try:
            wf = wave.open(filename, 'wb')
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.pyaudio_instance.get_sample_size(self.format))
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_data)
            wf.close()
        except Exception as e:
            logger.error(f"Error saving WAV: {e}")

    async def generate_voice_response(self, text: str) -> Optional[bytes]:
        """Generate voice audio from text using ElevenLabs"""
        if not self.elevenlabs_key:
            logger.warning("ElevenLabs API key not set - text-to-speech disabled")
            return None

        try:
            from elevenlabs import ElevenLabsClient, VoiceSettings

            client = ElevenLabsClient(api_key=self.elevenlabs_key)

            # Get selected voice profile
            voice_info = self.ENGINEER_VOICES[self.voice_profile]

            # Configure voice settings for professional race engineer delivery
            voice_settings = VoiceSettings(
                stability=self.voice_settings['stability'],
                similarity_boost=self.voice_settings['similarity_boost'],
                style=self.voice_settings['style'],
                use_speaker_boost=self.voice_settings['use_speaker_boost']
            )

            logger.info(f"Generating voice with {voice_info['name']} ({voice_info['description']})")

            # Generate audio using ElevenLabs
            audio_stream = client.text_to_speech.convert(
                voice_id=voice_info['id'],
                text=text,
                model_id="eleven_turbo_v2_5",  # Fastest, lowest latency for real-time racing
                voice_settings=voice_settings,
                output_format="mp3_44100_128"  # High quality MP3
            )

            # Convert stream to bytes
            from io import BytesIO
            audio_buffer = BytesIO()
            for chunk in audio_stream:
                audio_buffer.write(chunk)

            audio_data = audio_buffer.getvalue()
            logger.info(f"✓ Voice generated: {len(audio_data)} bytes")
            return audio_data

        except Exception as e:
            logger.error(f"ElevenLabs voice generation error: {e}")
            return None

    def set_voice_profile(self, profile: str):
        """Change the voice profile (professional, experienced, dynamic, calm)"""
        if profile in self.ENGINEER_VOICES:
            self.voice_profile = profile
            voice_info = self.ENGINEER_VOICES[profile]
            logger.info(f"Voice profile changed to '{voice_info['name']}': {voice_info['description']}")
            return True
        else:
            logger.error(f"Unknown voice profile: {profile}")
            logger.info(f"Available profiles: {', '.join(self.ENGINEER_VOICES.keys())}")
            return False

    def customize_voice_settings(self, stability: float = None, similarity_boost: float = None,
                                 style: float = None, use_speaker_boost: bool = None):
        """
        Customize ElevenLabs voice settings

        Args:
            stability (0.0-1.0): Higher = more consistent, lower = more expressive
            similarity_boost (0.0-1.0): Higher = closer to original voice
            style (0.0-1.0): Style exaggeration
            use_speaker_boost: Enhanced clarity
        """
        if stability is not None:
            self.voice_settings['stability'] = max(0.0, min(1.0, stability))
        if similarity_boost is not None:
            self.voice_settings['similarity_boost'] = max(0.0, min(1.0, similarity_boost))
        if style is not None:
            self.voice_settings['style'] = max(0.0, min(1.0, style))
        if use_speaker_boost is not None:
            self.voice_settings['use_speaker_boost'] = use_speaker_boost

        logger.info(f"Voice settings updated: {self.voice_settings}")

    def _normalize_query(self, text: str) -> str:
        """Normalize query for cache matching"""
        # Remove punctuation, lowercase, strip whitespace
        import re
        normalized = re.sub(r'[^\w\s]', '', text.lower()).strip()
        # Map common variations
        variations = {
            'whats my gap': 'gap',
            'what is my gap': 'gap',
            'how far': 'gap',
            'gap to': 'gap',
            'distance': 'gap',
            'how are my tires': 'tires',
            'how are tires': 'tires',
            'tire temps': 'tires',
            'tire temperatures': 'tires',
            'how much fuel': 'fuel',
            'fuel level': 'fuel',
            'fuel remaining': 'fuel',
            'do i need to save fuel': 'fuel save',
            'should i save fuel': 'fuel save',
            'what was my last lap': 'last lap',
            'last lap time': 'last lap',
            'whats my position': 'position',
            'what position': 'position',
            'where am i': 'position'
        }
        for key, value in variations.items():
            if key in normalized:
                return value
        return normalized

    def _check_cache(self, text: str) -> Optional[str]:
        """Check cache for recent identical queries"""
        if not self.context:
            return None

        cache_key = self._normalize_query(text)
        if cache_key in self.response_cache:
            cached_data = self.response_cache[cache_key]
            # Check if cache is still valid (within TTL)
            if time.time() - cached_data['timestamp'] < self.cache_ttl:
                return cached_data['response']
            else:
                # Expired, remove from cache
                del self.response_cache[cache_key]
        return None

    def _add_to_cache(self, text: str, response: str):
        """Add response to cache"""
        cache_key = self._normalize_query(text)
        self.response_cache[cache_key] = {
            'response': response,
            'timestamp': time.time()
        }

        # Limit cache size
        if len(self.response_cache) > 50:
            # Remove oldest entries
            sorted_cache = sorted(self.response_cache.items(),
                                key=lambda x: x[1]['timestamp'])
            for key, _ in sorted_cache[:10]:
                del self.response_cache[key]

    def clear_cache(self):
        """Clear the response cache"""
        self.response_cache = {}
        logger.info("Response cache cleared")

    async def connect_to_server(self, ws_url: str):
        """Connect to BlackBox server via WebSocket for real-time telemetry"""
        self.ws_url = ws_url

        try:
            async with websockets.connect(ws_url) as websocket:
                self.ws = websocket
                logger.info(f"✓ Connected to server: {ws_url}")

                # Listen for telemetry updates
                async for message in websocket:
                    data = json.loads(message)

                    if data.get('type') == 'telemetry':
                        self.update_context(data.get('data', {}))

                    elif data.get('type') == 'driver_message':
                        # Process incoming driver voice message
                        text = data.get('text', '')
                        response = await self.process_driver_message(text)

                        # Send response back
                        await websocket.send(json.dumps({
                            'type': 'engineer_response',
                            'text': response,
                            'timestamp': time.time()
                        }))

        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            self.ws = None

    async def run_interactive_session(self):
        """Run interactive voice session (for testing)"""
        print("=" * 70)
        print("Voice Race Engineer - Interactive Session")
        print("=" * 70)
        print("\nCommands:")
        print("  - Just speak naturally into your microphone")
        print("  - Press Ctrl+C to exit")
        print("\nStarting in 3 seconds...")
        await asyncio.sleep(3)

        # Start listening
        self.start_listening()

        try:
            # Process audio queue
            while True:
                if not self.audio_queue.empty():
                    audio_file = self.audio_queue.get()

                    # Transcribe
                    text = await self.transcribe_audio(audio_file)
                    if text:
                        print(f"\n🗣️  Driver: {text}")

                        # Generate response
                        response = await self.process_driver_message(text)
                        print(f"🏁 Engineer: {response}")

                        # Generate voice (optional)
                        audio_data = await self.generate_voice_response(response)
                        if audio_data:
                            # Play audio (implementation depends on platform)
                            logger.info("🔊 Voice response generated")

                    # Cleanup
                    try:
                        import os
                        os.remove(audio_file)
                    except:
                        pass

                await asyncio.sleep(0.1)

        except KeyboardInterrupt:
            print("\n\n⚠️  Session ended by user")
        finally:
            self.stop_listening()


# Race-specific command handlers

class RacingCommandProcessor:
    """Process racing-specific commands and queries"""

    @staticmethod
    def parse_command(text: str) -> Dict:
        """Parse driver command into structured format"""
        text_lower = text.lower()

        command_types = {
            'gap': ['gap', 'distance', 'how far'],
            'tires': ['tire', 'tyre', 'temp'],
            'fuel': ['fuel', 'gas', 'petrol'],
            'pace': ['pace', 'lap time', 'delta'],
            'strategy': ['strategy', 'pit', 'stop'],
            'position': ['position', 'place', 'standing'],
            'weather': ['weather', 'rain', 'track temp'],
            'damage': ['damage', 'contact', 'issue']
        }

        for cmd_type, keywords in command_types.items():
            if any(kw in text_lower for kw in keywords):
                return {
                    'type': cmd_type,
                    'original_text': text,
                    'confidence': 'high'
                }

        return {
            'type': 'general',
            'original_text': text,
            'confidence': 'low'
        }


if __name__ == '__main__':
    import os
    import asyncio

    print("Voice Race Engineer Test")
    print("=" * 70)

    # Check environment
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  OPENAI_API_KEY not set")
    if not os.getenv('ELEVENLABS_API_KEY'):
        print("⚠️  ELEVENLABS_API_KEY not set (voice output disabled)")

    print("\nCapabilities:")
    print("  ✓ Real-time speech recognition (OpenAI Whisper)")
    print("  ✓ Conversational AI (GPT-4)")
    print("  ✓ Context-aware responses (telemetry integration)")
    print("  ✓ Voice synthesis (ElevenLabs)")
    print("  ✓ Natural racing commands")
    print("\nUsage: Import and integrate with iRacing relay agent")
    print("\nFor interactive testing:")
    print("  engineer = VoiceRaceEngineer()")
    print("  asyncio.run(engineer.run_interactive_session())")
