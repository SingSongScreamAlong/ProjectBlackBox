"""
VOICE-DRIVEN RACE TEAM INTERFACE
Natural language communication with your digital race team

Driver talks to team via voice, team responds with voice
Team has access to ALL telemetry and data
Minimalist UI, Maximalist conversation

Like talking to a real race team over radio.
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class VoiceCommand:
    """Driver voice command"""
    raw_text: str
    timestamp: float
    intent: str  # 'question', 'request', 'feedback', 'emergency'
    target_team_member: str  # 'engineer', 'strategist', 'coach', 'intel', 'any'
    extracted_entities: Dict  # Key info from command
    urgency: str  # 'low', 'medium', 'high', 'critical'


@dataclass
class TeamResponse:
    """Team voice response"""
    team_member: str  # Who's responding
    response_text: str  # What they say
    response_audio: Optional[bytes]  # TTS audio
    priority: str  # 'info', 'important', 'critical'
    requires_acknowledgment: bool
    related_data: Dict  # Data to show on minimal UI


class VoiceRaceTeamInterface:
    """
    Natural language voice interface for race team
    
    Driver can say things like:
    - "How are my tires?"
    - "When should I pit?"
    - "Can I catch the guy ahead?"
    - "What's my gap to P3?"
    - "Setup feels understeery in Turn 3"
    - "Who's fast in Turn 7?"
    
    Team responds naturally with voice and minimal UI updates
    """
    
    def __init__(self, 
                 engineer,
                 strategist, 
                 coach,
                 intelligence_analyst):
        self.engineer = engineer
        self.strategist = strategist
        self.coach = coach
        self.intel = intelligence_analyst
        
        # Team has access to ALL data
        self.live_telemetry = []
        self.session_data = {}
        self.competitor_data = {}
        
        # Conversation history
        self.conversation_history = []
        
        # Voice settings
        self.voice_enabled = True
        self.auto_updates_enabled = True  # Team proactively gives updates
        
    def process_driver_voice_input(self, 
                                   voice_text: str,
                                   current_context: Dict) -> TeamResponse:
        """
        Process driver's voice input and generate team response
        
        Args:
            voice_text: What the driver said
            current_context: Current race state (lap, position, etc.)
            
        Returns:
            Team response with voice and minimal UI data
        """
        
        # Parse driver intent
        command = self._parse_voice_command(voice_text, current_context)
        
        # Route to appropriate team member
        if command.target_team_member == 'engineer' or self._is_technical_question(command):
            response = self._engineer_response(command, current_context)
        elif command.target_team_member == 'strategist' or self._is_strategy_question(command):
            response = self._strategist_response(command, current_context)
        elif command.target_team_member == 'coach' or self._is_coaching_question(command):
            response = self._coach_response(command, current_context)
        elif command.target_team_member == 'intel' or self._is_intel_question(command):
            response = self._intel_response(command, current_context)
        else:
            # General question - route to most appropriate
            response = self._general_response(command, current_context)
        
        # Log conversation
        self.conversation_history.append({
            'driver': voice_text,
            'team': response.response_text,
            'timestamp': datetime.now().timestamp()
        })
        
        return response
    
    def _parse_voice_command(self, text: str, context: Dict) -> VoiceCommand:
        """Parse driver's voice command into structured data"""
        
        text_lower = text.lower()
        
        # Determine intent
        if any(word in text_lower for word in ['?', 'how', 'what', 'when', 'where', 'who']):
            intent = 'question'
        elif any(word in text_lower for word in ['help', 'emergency', 'problem', 'issue']):
            intent = 'emergency'
        elif any(word in text_lower for word in ['feels', 'think', 'seems']):
            intent = 'feedback'
        else:
            intent = 'request'
        
        # Determine target team member
        if any(word in text_lower for word in ['tire', 'setup', 'fuel', 'brake', 'temperature']):
            target = 'engineer'
        elif any(word in text_lower for word in ['pit', 'strategy', 'overtake', 'position', 'gap']):
            target = 'strategist'
        elif any(word in text_lower for word in ['focus', 'technique', 'improve', 'practice']):
            target = 'coach'
        elif any(word in text_lower for word in ['who', 'driver', 'competitor', 'fast', 'slow']):
            target = 'intel'
        else:
            target = 'any'
        
        # Determine urgency
        if intent == 'emergency' or any(word in text_lower for word in ['now', 'urgent', 'critical']):
            urgency = 'critical'
        elif any(word in text_lower for word in ['soon', 'next lap', 'quickly']):
            urgency = 'high'
        else:
            urgency = 'medium'
        
        # Extract entities (simplified - would use NLP)
        entities = {}
        if 'turn' in text_lower or 'corner' in text_lower:
            # Extract corner number
            for i in range(1, 20):
                if str(i) in text or f"turn {i}" in text_lower:
                    entities['corner'] = i
                    break
        
        return VoiceCommand(
            raw_text=text,
            timestamp=datetime.now().timestamp(),
            intent=intent,
            target_team_member=target,
            extracted_entities=entities,
            urgency=urgency
        )
    
    def _engineer_response(self, command: VoiceCommand, context: Dict) -> TeamResponse:
        """Engineer responds to technical questions"""
        
        text = command.raw_text.lower()
        
        # Tire questions
        if 'tire' in text or 'tyre' in text:
            tire_age = context.get('tire_age', 10)
            tire_temp = context.get('tire_temp_avg', 90)
            
            if 'how' in text:
                response_text = (
                    f"Tires are {tire_age} laps old. "
                    f"Temps are good at {tire_temp:.0f} degrees. "
                    f"You've got about {20 - tire_age} laps left in them."
                )
            elif 'temperature' in text or 'temp' in text:
                response_text = f"Tire temps: {tire_temp:.0f} degrees. Right in the window."
            else:
                response_text = f"Tires good. {tire_age} laps old."
            
            ui_data = {
                'tire_age': tire_age,
                'tire_temp': tire_temp,
                'laps_remaining': 20 - tire_age
            }
        
        # Fuel questions
        elif 'fuel' in text:
            fuel_remaining = context.get('fuel_remaining', 25.0)
            fuel_per_lap = context.get('fuel_per_lap', 2.5)
            laps_remaining = fuel_remaining / fuel_per_lap
            
            response_text = (
                f"Fuel is good. {fuel_remaining:.1f} liters, "
                f"that's {laps_remaining:.0f} laps at current consumption."
            )
            
            ui_data = {
                'fuel_remaining': fuel_remaining,
                'laps_of_fuel': laps_remaining
            }
        
        # Setup feedback
        elif 'understeer' in text or 'oversteer' in text:
            corner = command.extracted_entities.get('corner', 'that corner')
            
            if 'understeer' in text:
                response_text = (
                    f"Copy understeer in Turn {corner}. "
                    f"Try front wing minus one, or front ARB plus one. "
                    f"We can adjust at the pit stop."
                )
            else:
                response_text = (
                    f"Copy oversteer in Turn {corner}. "
                    f"Try rear wing plus one, or rear ARB minus one. "
                    f"We can adjust at the pit stop."
                )
            
            ui_data = {'setup_feedback': text}
        
        # Temperature questions
        elif 'temperature' in text or 'temp' in text:
            track_temp = context.get('track_temp', 28)
            response_text = f"Track temp is {track_temp} degrees. Conditions are stable."
            ui_data = {'track_temp': track_temp}
        
        else:
            response_text = "Copy that. Everything looking good from here."
            ui_data = {}
        
        return TeamResponse(
            team_member='Engineer',
            response_text=response_text,
            response_audio=None,  # Would generate TTS
            priority='info',
            requires_acknowledgment=False,
            related_data=ui_data
        )
    
    def _strategist_response(self, command: VoiceCommand, context: Dict) -> TeamResponse:
        """Strategist responds to strategy questions"""
        
        text = command.raw_text.lower()
        
        # Pit strategy
        if 'pit' in text or 'box' in text:
            current_lap = context.get('current_lap', 10)
            tire_age = context.get('tire_age', 10)
            
            if 'when' in text:
                optimal_pit_lap = current_lap + (20 - tire_age)
                response_text = (
                    f"Optimal pit window is laps {optimal_pit_lap - 2} to {optimal_pit_lap + 2}. "
                    f"We're thinking lap {optimal_pit_lap}. I'll confirm closer to the window."
                )
            elif 'now' in text or 'this lap' in text:
                response_text = "Negative, stay out. Tires still have life. I'll call it when it's time."
            else:
                response_text = f"Pit strategy looking good. We'll box around lap {current_lap + 10}."
            
            ui_data = {'pit_window': (optimal_pit_lap - 2, optimal_pit_lap + 2)}
        
        # Gap questions
        elif 'gap' in text:
            if 'ahead' in text or 'front' in text:
                gap = context.get('gap_ahead', 2.5)
                response_text = f"Gap to car ahead is {gap:.1f} seconds. You're closing."
            elif 'behind' in text:
                gap = context.get('gap_behind', 3.2)
                response_text = f"Gap to car behind is {gap:.1f} seconds. You're safe."
            else:
                gap_ahead = context.get('gap_ahead', 2.5)
                response_text = f"Gap ahead: {gap_ahead:.1f} seconds."
            
            ui_data = {'gaps': context.get('gaps', {})}
        
        # Overtaking
        elif 'overtake' in text or 'pass' in text or 'catch' in text:
            response_text = (
                "You're faster in Turn 3 and Turn 7. "
                "Look for the move into Turn 3. Outbraking opportunity. "
                "DRS available on the main straight."
            )
            ui_data = {'overtake_corners': [3, 7]}
        
        # Position
        elif 'position' in text or 'where am i' in text:
            position = context.get('position', 5)
            response_text = f"You're P{position}. Running well."
            ui_data = {'position': position}
        
        else:
            response_text = "Strategy is on track. Keep doing what you're doing."
            ui_data = {}
        
        return TeamResponse(
            team_member='Strategist',
            response_text=response_text,
            response_audio=None,
            priority='important',
            requires_acknowledgment=False,
            related_data=ui_data
        )
    
    def _coach_response(self, command: VoiceCommand, context: Dict) -> TeamResponse:
        """Coach responds to technique/mental questions"""
        
        text = command.raw_text.lower()
        
        if 'focus' in text or 'concentrate' in text:
            response_text = (
                "Stay focused. One corner at a time. "
                "Breathe. You've got this."
            )
        elif 'mistake' in text or 'error' in text:
            response_text = (
                "Forget it. Next corner. "
                "Reset. You're still in this."
            )
        elif 'improve' in text or 'faster' in text:
            corner = command.extracted_entities.get('corner', 3)
            response_text = (
                f"Turn {corner}: Brake 5 meters later, carry more speed. "
                f"You can do it. Trust the car."
            )
        else:
            response_text = "You're doing great. Keep it smooth."
        
        return TeamResponse(
            team_member='Coach',
            response_text=response_text,
            response_audio=None,
            priority='info',
            requires_acknowledgment=False,
            related_data={}
        )
    
    def _intel_response(self, command: VoiceCommand, context: Dict) -> TeamResponse:
        """Intel analyst responds to competitor questions"""
        
        text = command.raw_text.lower()
        
        # Who's fast where
        if 'fast' in text and ('turn' in text or 'corner' in text):
            corner = command.extracted_entities.get('corner', 3)
            response_text = (
                f"Car ahead is strong in Turn {corner}. "
                f"But they're weak in Turn {corner + 2}. "
                f"That's your opportunity."
            )
            ui_data = {'intel_corners': {corner: 'their_strength', corner + 2: 'their_weakness'}}
        
        # Driver info
        elif 'who' in text:
            response_text = (
                "Car ahead is Driver 'FastGuy'. "
                "Aggressive, tends to pit early. "
                "Weak in Turn 5 and Turn 9. Attack there."
            )
            ui_data = {'competitor': 'FastGuy', 'weak_corners': [5, 9]}
        
        # Pit predictions
        elif 'pit' in text and ('they' in text or 'them' in text):
            response_text = (
                "Intel says they'll pit in 2-3 laps. "
                "We can undercut or overcut. Your call."
            )
            ui_data = {'predicted_pit': 'lap 12-13'}
        
        else:
            response_text = "Monitoring competitors. I'll update you if anything changes."
            ui_data = {}
        
        return TeamResponse(
            team_member='Intel',
            response_text=response_text,
            response_audio=None,
            priority='important',
            requires_acknowledgment=False,
            related_data=ui_data
        )
    
    def _general_response(self, command: VoiceCommand, context: Dict) -> TeamResponse:
        """General response when intent is unclear"""
        
        return TeamResponse(
            team_member='Engineer',
            response_text="Copy that. Let me know if you need anything.",
            response_audio=None,
            priority='info',
            requires_acknowledgment=False,
            related_data={}
        )
    
    def generate_proactive_updates(self, context: Dict) -> List[TeamResponse]:
        """
        Team proactively gives updates without driver asking
        
        Like a real race team would do:
        - "Pit window opening in 3 laps"
        - "Car behind is closing, 2 seconds"
        - "Track temp rising, watch tire temps"
        """
        
        updates = []
        current_lap = context.get('current_lap', 10)
        
        # Pit window update
        if current_lap == 15:
            updates.append(TeamResponse(
                team_member='Strategist',
                response_text="Pit window opens in 3 laps. We're thinking lap 18. I'll confirm.",
                response_audio=None,
                priority='important',
                requires_acknowledgment=False,
                related_data={'pit_window': (16, 20)}
            ))
        
        # Threat warning
        gap_behind = context.get('gap_behind', 5.0)
        if gap_behind < 2.0:
            updates.append(TeamResponse(
                team_member='Intel',
                response_text=f"Car behind closing. {gap_behind:.1f} seconds. Defend Turn 3.",
                response_audio=None,
                priority='important',
                requires_acknowledgment=False,
                related_data={'threat': True, 'gap_behind': gap_behind}
            ))
        
        # Track condition change
        track_temp = context.get('track_temp', 25)
        if track_temp > 35:
            updates.append(TeamResponse(
                team_member='Engineer',
                response_text="Track temp rising. Watch tire temps, especially fronts.",
                response_audio=None,
                priority='info',
                requires_acknowledgment=False,
                related_data={'track_temp': track_temp}
            ))
        
        return updates
    
    # Helper methods
    def _is_technical_question(self, command: VoiceCommand) -> bool:
        keywords = ['tire', 'fuel', 'setup', 'temperature', 'brake', 'engine']
        return any(kw in command.raw_text.lower() for kw in keywords)
    
    def _is_strategy_question(self, command: VoiceCommand) -> bool:
        keywords = ['pit', 'gap', 'position', 'overtake', 'strategy', 'box']
        return any(kw in command.raw_text.lower() for kw in keywords)
    
    def _is_coaching_question(self, command: VoiceCommand) -> bool:
        keywords = ['focus', 'improve', 'technique', 'faster', 'mistake']
        return any(kw in command.raw_text.lower() for kw in keywords)
    
    def _is_intel_question(self, command: VoiceCommand) -> bool:
        keywords = ['who', 'driver', 'competitor', 'fast', 'slow', 'they', 'them']
        return any(kw in command.raw_text.lower() for kw in keywords)


# ============================================================================
# MINIMAL UI DATA STRUCTURE
# ============================================================================

@dataclass
class MinimalUIState:
    """
    Minimal UI - only essential info visible
    Everything else is voice conversation
    """
    
    # Essential race info (always visible)
    current_lap: int
    total_laps: int
    position: int
    gap_ahead: float
    gap_behind: float
    
    # Current focus (what team just talked about)
    active_message: Optional[str]
    active_data: Optional[Dict]
    
    # Quick glance info
    tire_age: int
    fuel_laps_remaining: int
    pit_window: Optional[Tuple[int, int]]
    
    # Alerts (only when critical)
    alerts: List[str]


# Example usage
if __name__ == '__main__':
    print("VOICE-DRIVEN RACE TEAM INTERFACE")
    print("=" * 70)
    print("\nDriver talks to team naturally:")
    print("\nDriver: 'How are my tires?'")
    print("Engineer: 'Tires are 10 laps old. Temps are good at 90 degrees. You've got about 10 laps left in them.'")
    print("\nDriver: 'When should I pit?'")
    print("Strategist: 'Optimal pit window is laps 16 to 20. We're thinking lap 18. I'll confirm closer to the window.'")
    print("\nDriver: 'Can I catch the guy ahead?'")
    print("Strategist: 'You're faster in Turn 3 and Turn 7. Look for the move into Turn 3. Outbraking opportunity.'")
    print("\nDriver: 'Who's fast in Turn 7?'")
    print("Intel: 'Car ahead is strong in Turn 7. But they're weak in Turn 9. That's your opportunity.'")
    print("\nDriver: 'Setup feels understeery in Turn 3'")
    print("Engineer: 'Copy understeer in Turn 3. Try front wing minus one. We can adjust at the pit stop.'")
    print("\n[PROACTIVE UPDATE]")
    print("Strategist: 'Pit window opens in 3 laps. We're thinking lap 18.'")
    print("\n" + "=" * 70)
    print("\nMINIMAL UI shows:")
    print("  Lap 15/40 | P5 | +2.3s | -3.1s")
    print("  Tires: 10 laps | Fuel: 15 laps")
    print("  Pit: Laps 16-20")
    print("\nEverything else is VOICE CONVERSATION.")
