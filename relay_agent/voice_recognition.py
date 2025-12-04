"""
Voice Recognition - Push-to-Talk
Speech-to-text using OpenAI Whisper API
Supports keyboard keys AND wheel/joystick buttons
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
import pygame

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VoiceRecognition:
    """
    Push-to-talk voice recognition
    Supports keyboard keys OR wheel/joystick buttons
    """
    
    def __init__(self, api_key: str, ptt_type: str = 'keyboard', ptt_key: str = 'f1', 
                 joystick_id: int = 0, joystick_button: int = 0):
        """
        Args:
            api_key: OpenAI API key
            ptt_type: 'keyboard' or 'joystick' (for wheel buttons)
            ptt_key: Keyboard key if using keyboard (default F1)
            joystick_id: Joystick/wheel device ID (default 0)
            joystick_button: Button number on wheel (default 0)
        """
        self.client = OpenAI(api_key=api_key)
        self.ptt_type = ptt_type
        self.ptt_key = ptt_key
        self.joystick_id = joystick_id
        self.joystick_button = joystick_button
        self.is_ptt_pressed = False
        self.ptt_callback = None
        
        # Audio settings
        self.sample_rate = 16000
        self.chunk_size = 1024
        self.channels = 1
        self.format = pyaudio.paInt16
        
        self.audio = pyaudio.PyAudio()
        self.is_listening = False
        
        # Joystick support
        if self.ptt_type == 'joystick':
            pygame.init()
            pygame.joystick.init()
            if pygame.joystick.get_count() > 0:
                self.joystick = pygame.joystick.Joystick(joystick_id)
                self.joystick.init()
                logger.info(f"✅ Wheel detected: {self.joystick.get_name()}")
                logger.info(f"   Buttons available: {self.joystick.get_numbuttons()}")
            else:
                logger.warning("⚠️ No wheel/joystick detected, falling back to keyboard")
                self.ptt_type = 'keyboard'
    
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
        
        if self.ptt_type == 'keyboard':
            self._start_keyboard_listener()
        else:
            self._start_joystick_listener()
    
    def _start_keyboard_listener(self):
        """Start keyboard PTT listener"""
        def on_press(key):
            """Handle key press"""
            try:
                if hasattr(key, 'name') and key.name == self.ptt_key:
                    if not self.is_ptt_pressed:
                        self.is_ptt_pressed = True
                        logger.info(f"🎤 PTT pressed ({self.ptt_key})")
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
        
        self.keyboard_listener = keyboard.Listener(
            on_press=on_press,
            on_release=on_release
        )
        self.keyboard_listener.start()
        
        logger.info(f"✅ Push-to-talk ready (keyboard: {self.ptt_key.upper()})")
    
    def _start_joystick_listener(self):
        """Start wheel/joystick PTT listener"""
        async def poll_joystick():
            """Poll joystick for button presses"""
            logger.info(f"✅ Push-to-talk ready (wheel button {self.joystick_button})")
            
            while self.is_listening:
                pygame.event.pump()  # Process events
                
                # Check button state
                button_pressed = self.joystick.get_button(self.joystick_button)
                
                if button_pressed and not self.is_ptt_pressed:
                    # Button just pressed
                    self.is_ptt_pressed = True
                    logger.info(f"🎤 PTT pressed (wheel button {self.joystick_button})")
                    asyncio.create_task(self._handle_ptt_press())
                    
                elif not button_pressed and self.is_ptt_pressed:
                    # Button just released
                    self.is_ptt_pressed = False
                    logger.info(f"🎤 PTT released (wheel button {self.joystick_button})")
                
                await asyncio.sleep(0.01)  # Poll at 100Hz
        
        # Start polling task
        asyncio.create_task(poll_joystick())
    
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
                await asyncio.sleep(0.001)
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
        if hasattr(self, 'joystick'):
            self.joystick.quit()
        if hasattr(self, 'audio'):
            self.audio.terminate()
    
    @staticmethod
    def list_available_wheels():
        """List all available wheels/joysticks"""
        pygame.init()
        pygame.joystick.init()
        
        count = pygame.joystick.get_count()
        print(f"\n🎮 Found {count} device(s):")
        
        for i in range(count):
            joystick = pygame.joystick.Joystick(i)
            joystick.init()
            print(f"\n  Device {i}:")
            print(f"    Name: {joystick.get_name()}")
            print(f"    Buttons: {joystick.get_numbuttons()}")
            print(f"    Axes: {joystick.get_numaxes()}")
            joystick.quit()
        
        pygame.quit()


# Example usage
if __name__ == '__main__':
    import os
    import sys
    
    async def main():
        # List available wheels
        if len(sys.argv) > 1 and sys.argv[1] == '--list':
            VoiceRecognition.list_available_wheels()
            return
        
        # Get API key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("Error: OPENAI_API_KEY not set")
            return
        
        # Create voice recognition
        print("\nPush-to-Talk Configuration:")
        print("1. Keyboard (F1 key)")
        print("2. Wheel/Joystick button")
        choice = input("Select (1 or 2): ").strip()
        
        if choice == '2':
            # List available devices
            VoiceRecognition.list_available_wheels()
            
            device_id = int(input("\nEnter device ID: "))
            button_num = int(input("Enter button number: "))
            
            vr = VoiceRecognition(
                api_key, 
                ptt_type='joystick',
                joystick_id=device_id,
                joystick_button=button_num
            )
        else:
            vr = VoiceRecognition(api_key, ptt_type='keyboard', ptt_key='f1')
        
        # Callback
        async def on_driver_input(text):
            print(f"\n🎤 Driver said: {text}\n")
        
        # Start PTT
        vr.start_listening()
        vr.start_ptt_listener(on_driver_input)
        
        print("\n✅ Push-to-talk ready!")
        print("Press your configured button to talk, release to send.")
        print("Press Ctrl+C to exit\n")
        
        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\nExiting...")
        
        vr.cleanup()
    
    asyncio.run(main())
