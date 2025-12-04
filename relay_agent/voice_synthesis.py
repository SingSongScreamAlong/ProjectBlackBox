"""
Voice Synthesis
Text-to-speech using ElevenLabs API
"""

import asyncio
import logging
from typing import Optional
import pyaudio
from elevenlabs import ElevenLabs, Voice, VoiceSettings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VoiceSynthesis:
    """
    Convert team responses to speech using ElevenLabs
    """
    
    def __init__(self, api_key: str):
        self.client = ElevenLabs(api_key=api_key)
        
        # Different voices for team members
        # These are example voice IDs - replace with actual ElevenLabs voice IDs
        self.voices = {
            'engineer': 'EXAVITQu4vr4xnSDxMaL',  # Professional, technical
            'strategist': '21m00Tcm4TlvDq8ikWAM',  # Calm, analytical
            'coach': 'AZnzlk1XvdvUeBnXmlld',  # Encouraging, supportive
            'intel': 'pNInz6obpgDQGcFmaJgB'  # Quick, informative
        }
        
        # Audio playback
        self.audio = pyaudio.PyAudio()
        self.sample_rate = 44100
    
    async def generate_speech(self, text: str, team_member: str = 'engineer') -> bytes:
        """
        Generate speech audio from text
        
        Args:
            text: Text to convert to speech
            team_member: Which team member is speaking
            
        Returns:
            Audio data as bytes
        """
        try:
            voice_id = self.voices.get(team_member, self.voices['engineer'])
            
            logger.info(f"🔊 Generating speech for {team_member}: {text[:50]}...")
            
            # Generate audio
            audio = self.client.generate(
                text=text,
                voice=Voice(
                    voice_id=voice_id,
                    settings=VoiceSettings(
                        stability=0.5,
                        similarity_boost=0.75,
                        style=0.0,
                        use_speaker_boost=True
                    )
                ),
                model="eleven_monolingual_v1"
            )
            
            # Convert generator to bytes
            audio_bytes = b''.join(audio)
            
            logger.info("✅ Speech generated")
            return audio_bytes
            
        except Exception as e:
            logger.error(f"Error generating speech: {e}")
            return b''
    
    async def play_audio(self, audio_bytes: bytes):
        """
        Play audio through speakers
        
        Args:
            audio_bytes: Audio data to play
        """
        try:
            logger.info("🔊 Playing audio...")
            
            # Open audio stream
            stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                output=True
            )
            
            # Play audio
            stream.write(audio_bytes)
            
            # Cleanup
            stream.stop_stream()
            stream.close()
            
            logger.info("✅ Audio playback complete")
            
        except Exception as e:
            logger.error(f"Error playing audio: {e}")
    
    async def speak(self, text: str, team_member: str = 'engineer'):
        """
        Generate and play speech
        
        Args:
            text: Text to speak
            team_member: Which team member is speaking
        """
        audio = await self.generate_speech(text, team_member)
        if audio:
            await self.play_audio(audio)
    
    def cleanup(self):
        """Cleanup audio resources"""
        self.audio.terminate()


# Example usage
if __name__ == '__main__':
    import os
    
    async def main():
        # Get API key from environment
        api_key = os.getenv('ELEVENLABS_API_KEY')
        if not api_key:
            print("Error: ELEVENLABS_API_KEY not set")
            return
        
        # Create voice synthesis
        vs = VoiceSynthesis(api_key)
        
        # Test different team members
        await vs.speak("Tires are 10 laps old. Temps are good at 90 degrees.", 'engineer')
        await asyncio.sleep(1)
        
        await vs.speak("Pit window opens in 3 laps. We're thinking lap 18.", 'strategist')
        await asyncio.sleep(1)
        
        await vs.speak("Stay focused. One corner at a time.", 'coach')
        await asyncio.sleep(1)
        
        await vs.speak("Car ahead is strong in Turn 7. Attack Turn 9.", 'intel')
        
        vs.cleanup()
    
    asyncio.run(main())
