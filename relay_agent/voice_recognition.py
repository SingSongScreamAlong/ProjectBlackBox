"""
Voice Recognition - Push-to-Talk
Speech-to-text using OpenAI Whisper API
No wake words - just press button, talk, release
"""

import asyncio
import logging
from typing import Optional, Callable
import pyaudio
import wave
import io
from openai import OpenAI
import numpy as np
from pynput import keyboard

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VoiceRecognition:
    """
    Push-to-talk voice recognition
    Driver presses button, talks, releases - like real race radio
    """
    
    def __init__(self, api_key: str, ptt_key: str = 'f1'):
        """
        Args:
            api_key: OpenAI API key
            ptt_key: Push-to-talk key (default F1, configurable)
        """
        self.client = OpenAI(api_key=api_key)
        self.ptt_key = ptt_key
        self.is_ptt_pressed = False
        self.ptt_callback = None
        
        # Audio settings
        self.sample_rate = 16000
        self.chunk_size = 1024
        self.channels = 1
        self.format = pyaudio.paInt16
        
        self.audio = pyaudio.PyAudio()
        self.is_listening = False
    
    def start_listening(self):
        """Start listening for audio"""
        self.is_listening = True
        logger.info("🎤 Voice recognition started")
    
    def stop_listening(self):
        """Stop listening"""
        self.is_listening = False
        logger.info("🎤 Voice recognition stopped")
    
    def start_ptt_listener(self, callback: Callable):
        """
        Start listening for push-to-talk button
        
        Args:
            callback: Function to call when PTT is pressed
        """
        self.ptt_callback = callback
        
        def on_press(key):
            """Handle key press"""
            try:
                # Check if it's our PTT key
                if hasattr(key, 'name') and key.name == self.ptt_key:
                    if not self.is_ptt_pressed:
                        self.is_ptt_pressed = True
                        logger.info(f"🎤 PTT pressed ({self.ptt_key})")
                        # Start recording
                        asyncio.create_task(self._handle_ptt_press())
            except AttributeError:
                pass
        
        def on_release(key):
            """Handle key release"""
            try:
                if hasattr(key, 'name') and key.name == self.ptt_key:
                    if self.is_ptt_pressed:
                        self.is_ptt_pressed = False
                        logger.info(f"🎤 PTT released ({self.ptt_key})")
            except AttributeError:
                pass
        
        # Start keyboard listener
        self.keyboard_listener = keyboard.Listener(
            on_press=on_press,
            on_release=on_release
        )
        self.keyboard_listener.start()
        
        logger.info(f"✅ Push-to-talk ready (press {self.ptt_key.upper()} to talk)")
    
    async def _handle_ptt_press(self):
        """Handle PTT button press - record while held"""
        frames = []
        
        stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size
        )
        
        # Record while button is held (max 10 seconds)
        max_duration = 10.0
        start_time = asyncio.get_event_loop().time()
        
        while self.is_ptt_pressed and (asyncio.get_event_loop().time() - start_time) < max_duration:
            try:
                data = stream.read(self.chunk_size, exception_on_overflow=False)
                frames.append(data)
                await asyncio.sleep(0.001)  # Small delay
            except Exception as e:
                logger.error(f"Error recording: {e}")
                break
        
        stream.stop_stream()
        stream.close()
        
        # Process recorded audio
        if frames:
            audio_data = b''.join(frames)
            duration = len(frames) * self.chunk_size / self.sample_rate
            logger.info(f"📝 Recorded {duration:.1f}s of audio")
            
            # Transcribe
            text = await self.transcribe_audio(audio_data)
            
            if text and self.ptt_callback:
                await self.ptt_callback(text)
    
    async def record_command(self, duration: float = 5.0) -> bytes:
        """
        Record audio command
        
        Args:
            duration: Recording duration in seconds
            
        Returns:
            Audio data as bytes
        """
        logger.info(f"🎤 Recording for {duration} seconds...")
        
        stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size
        )
        
        frames = []
        for _ in range(0, int(self.sample_rate / self.chunk_size * duration)):
            data = stream.read(self.chunk_size)
            frames.append(data)
        
        stream.stop_stream()
        stream.close()
        
        audio_data = b''.join(frames)
        logger.info("✅ Recording complete")
        
        return audio_data
    
    async def transcribe_audio(self, audio_data: bytes, quick: bool = False) -> Optional[str]:
        """
        Transcribe audio using Whisper API
        
        Args:
            audio_data: Raw audio bytes
            quick: Use faster model for wake word detection
            
        Returns:
            Transcribed text or None
        """
        try:
            # Convert to WAV format
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(self.channels)
                wav_file.setsampwidth(self.audio.get_sample_size(self.format))
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(audio_data)
            
            wav_buffer.seek(0)
            wav_buffer.name = "audio.wav"
            
            # Transcribe with Whisper
            response = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=wav_buffer,
                language="en"
            )
            
            text = response.text.strip()
            logger.info(f"📝 Transcribed: {text}")
            
            return text
            
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return None
    
    def cleanup(self):
        """Cleanup audio resources"""
        if hasattr(self, 'keyboard_listener'):
            self.keyboard_listener.stop()
        self.audio.terminate()


# Example usage
if __name__ == '__main__':
    import os
    
    async def main():
        # Get API key from environment
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("Error: OPENAI_API_KEY not set")
            return
        
        # Create voice recognition with PTT
        vr = VoiceRecognition(api_key, ptt_key='f1')
        
        # Callback for when driver talks
        async def on_driver_input(text):
            print(f"Driver said: {text}")
        
        # Start PTT listener
        vr.start_ptt_listener(on_driver_input)
        
        print("Push-to-talk ready! Press F1 to talk, release to send.")
        print("Press Ctrl+C to exit")
        
        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\nExiting...")
        
        vr.cleanup()
    
    asyncio.run(main())
