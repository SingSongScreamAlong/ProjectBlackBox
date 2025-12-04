"""
Complete Audio Pipeline
Integrates voice recognition and synthesis with race team
"""

import asyncio
import logging
from typing import Optional
import os

from voice_recognition import VoiceRecognition
from voice_synthesis import VoiceSynthesis
from voice_race_team import VoiceRaceTeamInterface
from digital_race_team import EnhancedRaceEngineer
from digital_race_team_part2 import RaceStrategist, PerformanceCoach
from digital_race_team_part3 import IntelligenceAnalyst

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AudioPipeline:
    """
    Complete audio processing pipeline
    Handles voice input/output for race team communication
    """
    
    def __init__(self, 
                 openai_api_key: str,
                 elevenlabs_api_key: str):
        # Voice I/O
        self.recognition = VoiceRecognition(openai_api_key)
        self.synthesis = VoiceSynthesis(elevenlabs_api_key)
        
        # Race team
        self.engineer = EnhancedRaceEngineer()
        self.strategist = RaceStrategist()
        self.coach = PerformanceCoach()
        self.intel = IntelligenceAnalyst()
        
        # Voice interface
        self.team = VoiceRaceTeamInterface(
            engineer=self.engineer,
            strategist=self.strategist,
            coach=self.coach,
            intelligence_analyst=self.intel
        )
        
        self.is_running = False
        self.current_context = {}
    
    async def start(self, ptt_key: str = 'f1'):
        """
        Start audio pipeline with push-to-talk
        
        Args:
            ptt_key: Key to use for PTT (default F1)
        """
        logger.info("🎙️ Starting audio pipeline...")
        self.is_running = True
        
        # Start PTT listener
        self.recognition.start_ptt_listener(self.on_ptt_input)
        
        logger.info(f"✅ Audio pipeline ready - press {ptt_key.upper()} to talk")
    
    async def stop(self):
        """Stop audio pipeline"""
        logger.info("Stopping audio pipeline...")
        self.is_running = False
    
    async def on_ptt_input(self, text: str):
        """
        Called when driver uses push-to-talk
        
        Args:
            text: Transcribed driver input
        """
        logger.info(f"🎤 Driver: {text}")
        await self.process_command(text)
    
    async def process_command(self, text: str):
        """
        Process driver voice command
        
        Args:
            text: Driver's voice command
        """
        logger.info(f"📝 Processing command: {text}")
        
        # Get response from team
        response = self.team.process_driver_voice_input(text, self.current_context)
        
        logger.info(f"💬 {response.team_member}: {response.response_text}")
        
        # Generate and play speech
        await self.synthesis.speak(response.response_text, response.team_member.lower())
    
    async def send_proactive_update(self, message: str, team_member: str = 'engineer'):
        """
        Team sends proactive update to driver
        
        Args:
            message: Update message
            team_member: Who's sending the update
        """
        logger.info(f"📢 Proactive update from {team_member}: {message}")
        await self.synthesis.speak(message, team_member)
    
    def update_context(self, context: dict):
        """
        Update current race context
        
        Args:
            context: Current race state (lap, position, gaps, etc.)
        """
        self.current_context = context
    
    async def run_loop(self):
        """Main audio pipeline loop"""
        await self.start()
        
        try:
            while self.is_running:
                # Check for proactive updates
                updates = self.team.generate_proactive_updates(self.current_context)
                
                for update in updates:
                    await self.send_proactive_update(
                        update.response_text,
                        update.team_member.lower()
                    )
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        finally:
            await self.stop()
            self.recognition.cleanup()
            self.synthesis.cleanup()


# Example usage
if __name__ == '__main__':
    async def main():
        # Get API keys from environment
        openai_key = os.getenv('OPENAI_API_KEY')
        elevenlabs_key = os.getenv('ELEVENLABS_API_KEY')
        
        if not openai_key or not elevenlabs_key:
            print("Error: API keys not set")
            print("Set OPENAI_API_KEY and ELEVENLABS_API_KEY environment variables")
            return
        
        # Create audio pipeline
        pipeline = AudioPipeline(openai_key, elevenlabs_key)
        
        # Simulate race context updates
        async def update_context_loop():
            lap = 1
            while pipeline.is_running:
                pipeline.update_context({
                    'current_lap': lap,
                    'position': 5,
                    'gap_ahead': 2.3,
                    'gap_behind': 3.1,
                    'tire_age': lap,
                    'fuel_remaining': 25.0 - (lap * 2.5)
                })
                lap += 1
                await asyncio.sleep(60)  # Update every "lap"
        
        # Start context updates
        asyncio.create_task(update_context_loop())
        
        # Run pipeline
        await pipeline.run_loop()
    
    asyncio.run(main())
