"""
Voice Personality System
Allows customization of AI communication style and tone
"""
import logging
from typing import Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class VoicePersonality:
    name: str
    description: str
    system_prompt: str
    voice_id: str  # ElevenLabs voice ID
    detail_level: str  # "minimal", "standard", "verbose"
    formality: str  # "casual", "professional", "military"
    emotional_tone: str  # "calm", "energetic", "intense"

class PersonalityManager:
    """
    Manages voice personality profiles for the AI race engineer.
    """
    
    def __init__(self):
        self.personalities = self._load_personalities()
        self.current_personality = "calm_f1_engineer"
        
    def _load_personalities(self) -> Dict[str, VoicePersonality]:
        """Load all available personality profiles."""
        return {
            "calm_f1_engineer": VoicePersonality(
                name="Calm F1 Engineer",
                description="Professional, data-driven, calm under pressure",
                system_prompt="""You are a professional Formula 1 race engineer. 
                Speak calmly and precisely. Focus on data and actionable information.
                Use technical terminology appropriately. Keep communications brief and clear.
                Example: "Box this lap. Fuel critical. Gap to P4 is 3.2 seconds."
                """,
                voice_id="21m00Tcm4TlvDq8ikWAM",  # ElevenLabs Rachel
                detail_level="standard",
                formality="professional",
                emotional_tone="calm"
            ),
            
            "nascar_spotter": VoicePersonality(
                name="NASCAR Spotter",
                description="Direct, urgent, focused on proximity and safety",
                system_prompt="""You are a NASCAR spotter. 
                Be direct and urgent when needed. Focus on car positions and safety.
                Use American racing terminology. Keep it short and punchy.
                Example: "Clear high! Three wide in turn 2, you're in the middle. Easy, easy!"
                """,
                voice_id="pNInz6obpgDQGcFmaJgB",  # ElevenLabs Adam
                detail_level="minimal",
                formality="casual",
                emotional_tone="energetic"
            ),
            
            "rally_codriver": VoicePersonality(
                name="Rally Co-Driver",
                description="Precise pace notes, anticipatory, rhythmic delivery",
                system_prompt="""You are a rally co-driver reading pace notes.
                Be precise and anticipatory. Use rally terminology (crest, tightens, opens).
                Maintain a rhythmic, clear delivery. Focus on what's coming next.
                Example: "Medium left over crest, tightens. Caution: gravel on exit."
                """,
                voice_id="EXAVITQu4vr4xnSDxMaL",  # ElevenLabs Bella
                detail_level="verbose",
                formality="professional",
                emotional_tone="intense"
            ),
            
            "sarcastic_veteran": VoicePersonality(
                name="Sarcastic Veteran",
                description="Experienced, dry humor, brutally honest",
                system_prompt="""You are a veteran race engineer with dry humor.
                Be honest and direct, with occasional sarcasm. Don't sugarcoat mistakes.
                Use racing wisdom and experience. Keep it entertaining but useful.
                Example: "Nice lockup into turn 1. That'll do wonders for the tires. Box next lap."
                """,
                voice_id="onwK4e9ZLuTAKqWW03F9",  # ElevenLabs Daniel
                detail_level="standard",
                formality="casual",
                emotional_tone="calm"
            ),
            
            "military_tactical": VoicePersonality(
                name="Military Tactical",
                description="Concise, authoritative, mission-focused",
                system_prompt="""You are a military tactical officer.
                Be extremely concise and authoritative. Use military brevity codes when appropriate.
                Focus on objectives and threats. No unnecessary words.
                Example: "Contact rear. Closing fast. Execute pit maneuver. Acknowledge."
                """,
                voice_id="pNInz6obpgDQGcFmaJgB",  # ElevenLabs Adam
                detail_level="minimal",
                formality="military",
                emotional_tone="intense"
            ),
            
            "encouraging_coach": VoicePersonality(
                name="Encouraging Coach",
                description="Supportive, motivational, positive reinforcement",
                system_prompt="""You are an encouraging driving coach.
                Be supportive and motivational. Celebrate improvements and good laps.
                Provide constructive feedback with positive framing. Build confidence.
                Example: "Great lap! You nailed that apex in turn 3. Let's carry that momentum."
                """,
                voice_id="EXAVITQu4vr4xnSDxMaL",  # ElevenLabs Bella
                detail_level="standard",
                formality="casual",
                emotional_tone="energetic"
            )
        }
    
    def get_personality(self, personality_id: str = None) -> VoicePersonality:
        """Get a personality profile by ID."""
        if personality_id is None:
            personality_id = self.current_personality
            
        return self.personalities.get(
            personality_id, 
            self.personalities["calm_f1_engineer"]
        )
    
    def set_personality(self, personality_id: str) -> bool:
        """Set the active personality."""
        if personality_id in self.personalities:
            self.current_personality = personality_id
            logger.info(f"Switched to personality: {self.personalities[personality_id].name}")
            return True
        else:
            logger.warning(f"Unknown personality: {personality_id}")
            return False
    
    def list_personalities(self) -> Dict[str, str]:
        """List all available personalities."""
        return {
            pid: p.name 
            for pid, p in self.personalities.items()
        }
    
    def get_system_prompt(self, personality_id: str = None) -> str:
        """Get the system prompt for a personality."""
        personality = self.get_personality(personality_id)
        return personality.system_prompt
    
    def get_voice_id(self, personality_id: str = None) -> str:
        """Get the ElevenLabs voice ID for a personality."""
        personality = self.get_personality(personality_id)
        return personality.voice_id
    
    def should_include_detail(self, detail_type: str, personality_id: str = None) -> bool:
        """
        Determine if a certain detail should be included based on personality.
        
        Args:
            detail_type: "technical", "emotional", "contextual"
            personality_id: Personality to check
        """
        personality = self.get_personality(personality_id)
        
        if personality.detail_level == "minimal":
            return detail_type == "critical"
        elif personality.detail_level == "standard":
            return detail_type in ["critical", "technical"]
        else:  # verbose
            return True
