"""
Voice Recognition
Speech-to-text using OpenAI Whisper API
"""

import asyncio
import logging
from typing import Optional, Callable
import pyaudio
import wave
import io
from openai import OpenAI
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VoiceRecognition:
    """
    Convert driver speech to text using Whisper API
    """
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.wake_words = ['hey team', 'engineer', 'strategist', 'coach', 'intel']
        
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
    
    async def listen_for_wake_word(self, callback: Callable):
        """
        Listen for wake word continuously
        
        Args:
            callback: Function to call when wake word detected
        """
        logger.info("Listening for wake words...")
        
        stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size
        )
        
        while self.is_listening:
            try:
                # Record 2 seconds of audio
                frames = []
                for _ in range(0, int(self.sample_rate / self.chunk_size * 2)):
                    data = stream.read(self.chunk_size, exception_on_overflow=False)
                    frames.append(data)
                
                # Convert to audio file
                audio_data = b''.join(frames)
                
                # Quick transcription (using faster model)
                text = await self.transcribe_audio(audio_data, quick=True)
                
                if text:
                    text_lower = text.lower()
                    # Check for wake words
                    if any(wake_word in text_lower for wake_word in self.wake_words):
                        logger.info(f"🎤 Wake word detected: {text}")
                        await callback(text)
                
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in wake word detection: {e}")
        
        stream.stop_stream()
        stream.close()
    
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
        
        # Create voice recognition
        vr = VoiceRecognition(api_key)
        
        # Test recording and transcription
        print("Recording in 3 seconds...")
        await asyncio.sleep(3)
        
        audio = await vr.record_command(duration=3.0)
        text = await vr.transcribe_audio(audio)
        
        print(f"You said: {text}")
        
        vr.cleanup()
    
    asyncio.run(main())
