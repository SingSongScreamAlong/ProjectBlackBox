"""
PitBox Audio Recorder
Handles voice recording for PTT, sending to server, and playing TTS responses.
"""
import io
import logging
import threading
import time
import wave
from typing import Callable, Optional
import os

logger = logging.getLogger(__name__)

# Audio dependencies - graceful fallback
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    pyaudio = None
    PYAUDIO_AVAILABLE = False
    logger.warning("pyaudio not available - voice recording disabled")

try:
    import pygame.mixer
    PYGAME_AVAILABLE = True
except ImportError:
    pygame = None
    PYGAME_AVAILABLE = False
    logger.warning("pygame not available - audio playback may be limited")


class AudioRecorder:
    """
    Handles:
    - Recording audio while PTT is held
    - Returning audio data as bytes
    - Playing audio responses from server
    """
    
    # Audio settings
    SAMPLE_RATE = 16000  # 16kHz for better compatibility with STT
    CHANNELS = 1  # Mono
    CHUNK_SIZE = 1024
    FORMAT = pyaudio.paInt16 if PYAUDIO_AVAILABLE else None
    
    def __init__(self):
        self.audio: Optional["pyaudio.PyAudio"] = None
        self.stream = None
        self.recording = False
        self.audio_frames: list = []
        self.record_thread: Optional[threading.Thread] = None
        
        # Callbacks
        self.on_recording_complete: Optional[Callable[[bytes], None]] = None
        
        # Initialize audio
        self._init_audio()
        
    def _init_audio(self):
        """Initialize PyAudio"""
        if not PYAUDIO_AVAILABLE:
            logger.error("❌ PyAudio not available - voice disabled")
            return
            
        try:
            self.audio = pyaudio.PyAudio()
            logger.info("✅ Audio system initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize audio: {e}")
            self.audio = None
    
    def start_recording(self):
        """Start recording audio (call when PTT pressed)"""
        if not self.audio:
            logger.warning("Audio not initialized, cannot record")
            return
            
        if self.recording:
            return
            
        self.recording = True
        self.audio_frames = []
        
        try:
            self.stream = self.audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.SAMPLE_RATE,
                input=True,
                frames_per_buffer=self.CHUNK_SIZE
            )
            
            # Start recording in background thread
            self.record_thread = threading.Thread(target=self._record_loop, daemon=True)
            self.record_thread.start()
            
            logger.info("🎤 Recording started")
            
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            self.recording = False
    
    def _record_loop(self):
        """Background recording loop"""
        while self.recording and self.stream:
            try:
                data = self.stream.read(self.CHUNK_SIZE, exception_on_overflow=False)
                self.audio_frames.append(data)
            except Exception as e:
                logger.error(f"Recording error: {e}")
                break
    
    def stop_recording(self) -> Optional[bytes]:
        """Stop recording and return audio data as WAV bytes"""
        if not self.recording:
            return None
            
        self.recording = False
        
        # Wait for record thread to finish
        if self.record_thread:
            self.record_thread.join(timeout=1.0)
        
        # Close stream
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except:
                pass
            self.stream = None
        
        # Convert frames to WAV bytes
        if not self.audio_frames:
            logger.warning("No audio frames recorded")
            return None
            
        try:
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(self.CHANNELS)
                wav_file.setsampwidth(self.audio.get_sample_size(self.FORMAT))
                wav_file.setframerate(self.SAMPLE_RATE)
                wav_file.writeframes(b''.join(self.audio_frames))
            
            wav_data = wav_buffer.getvalue()
            duration = len(self.audio_frames) * self.CHUNK_SIZE / self.SAMPLE_RATE
            logger.info(f"🎤 Recording stopped - {duration:.1f}s captured")
            
            # Trigger callback if set
            if self.on_recording_complete:
                self.on_recording_complete(wav_data)
            
            return wav_data
            
        except Exception as e:
            logger.error(f"Failed to create WAV: {e}")
            return None
    
    def play_audio(self, audio_data: bytes, format: str = 'mp3'):
        """Play audio data (TTS response from server)"""
        if not audio_data:
            return
            
        # Try pygame first (better MP3 support)
        if PYGAME_AVAILABLE:
            try:
                self._play_with_pygame(audio_data)
                return
            except Exception as e:
                logger.warning(f"Pygame playback failed: {e}, trying fallback")
        
        # Fallback: save to temp file and use system player
        try:
            self._play_with_system(audio_data, format)
        except Exception as e:
            logger.error(f"Audio playback failed: {e}")
    
    def _play_with_pygame(self, audio_data: bytes):
        """Play audio using pygame mixer"""
        import pygame.mixer
        
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        
        audio_buffer = io.BytesIO(audio_data)
        pygame.mixer.music.load(audio_buffer)
        pygame.mixer.music.play()
        
        # Wait for playback to complete (non-blocking in separate thread)
        def wait_for_complete():
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
        
        threading.Thread(target=wait_for_complete, daemon=True).start()
        logger.info("🔊 Playing TTS response")
    
    def _play_with_system(self, audio_data: bytes, format: str):
        """Play audio using system default player"""
        import tempfile
        import subprocess
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix=f'.{format}', delete=False) as f:
            f.write(audio_data)
            temp_path = f.name
        
        # Play with system player (Windows)
        try:
            # Use Windows Media Player silently
            subprocess.Popen(
                ['cmd', '/c', 'start', '/min', '', temp_path],
                shell=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            logger.info("🔊 Playing TTS response (system player)")
            
            # Clean up after a delay
            def cleanup():
                time.sleep(30)
                try:
                    os.unlink(temp_path)
                except:
                    pass
            threading.Thread(target=cleanup, daemon=True).start()
            
        except Exception as e:
            logger.error(f"System playback failed: {e}")
    
    def cleanup(self):
        """Clean up audio resources"""
        if self.stream:
            try:
                self.stream.close()
            except:
                pass
        
        if self.audio:
            try:
                self.audio.terminate()
            except:
                pass
        
        logger.info("Audio system cleaned up")


if __name__ == "__main__":
    # Test recording
    logging.basicConfig(level=logging.INFO)
    
    recorder = AudioRecorder()
    
    print("Press Enter to start recording, then Enter again to stop...")
    input()
    
    recorder.start_recording()
    print("Recording... Press Enter to stop")
    input()
    
    wav_data = recorder.stop_recording()
    
    if wav_data:
        print(f"Recorded {len(wav_data)} bytes")
        
        # Save to test file
        with open("test_recording.wav", "wb") as f:
            f.write(wav_data)
        print("Saved to test_recording.wav")
    
    recorder.cleanup()
