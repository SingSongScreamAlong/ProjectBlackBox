"""
PitBox Relay Agent - Voice Recognition / PTT Handler
Handles Push-to-Talk triggers from Keyboard or Joystick/Wheel
"""
import logging
import time

# Optional imports handled gracefully
try:
    import keyboard
except ImportError:
    keyboard = None

try:
    import pygame
except ImportError:
    pygame = None

logger = logging.getLogger(__name__)

class VoiceRecognition:
    """
    Handles PTT state detection
    """
    def __init__(self, ptt_type='keyboard', ptt_key='space', joystick_id=0, joystick_button=0):
        self.ptt_type = ptt_type
        self.ptt_key = ptt_key
        self.joystick_id = joystick_id
        self.joystick_button = joystick_button
        
        self.joystick = None
        self._initialized = False
        
        self.setup()
        
    def reconfigure(self, ptt_type, ptt_key, joystick_id=0, joystick_button=0):
        """Update configuration and re-initialize devices"""
        logger.info(f"🔄 Reconfiguring VoiceRecognition: {ptt_type} (Key: {ptt_type}, JoyID: {joystick_id}, Btn: {joystick_button})")
        
        # Close existing joystick if switching or changing IDs
        if self.joystick and (ptt_type != 'joystick' or joystick_id != self.joystick_id):
            try:
                self.joystick.quit()
            except:
                pass
            self.joystick = None
            
        self.ptt_type = ptt_type
        self.ptt_key = ptt_key
        self.joystick_id = joystick_id
        self.joystick_button = joystick_button
        self._initialized = False
        
        self.setup()

    def setup(self):
        """Initialize input devices"""
        self._initialized = False
        
        if self.ptt_type == 'joystick':
            if not pygame:
                logger.error("pygame not installed. Cannot use joystick PTT.")
                return
            
            try:
                if not pygame.get_init():
                    pygame.init()
                if not pygame.joystick.get_init():
                    pygame.joystick.init()
                
                # Force re-scan of devices
                try:
                    pygame.joystick.quit()
                    pygame.joystick.init()
                except:
                    pass
                
                count = pygame.joystick.get_count()
                logger.info(f"🎮 Found {count} joystick devices")
                
                if count > self.joystick_id:
                    self.joystick = pygame.joystick.Joystick(self.joystick_id)
                    self.joystick.init()
                    logger.info(f"✅ Joystick PTT initialized: {self.joystick.get_name()} (Button {self.joystick_button})")
                    self._initialized = True
                else:
                    logger.error(f"❌ Joystick ID {self.joystick_id} not found. Found {count} devices.")
            except Exception as e:
                logger.error(f"Failed to init joystick: {e}")
                
        elif self.ptt_type == 'keyboard':
            if not keyboard:
                logger.error("keyboard lib not installed. Cannot use keyboard PTT.")
                return
            logger.info(f"✅ Keyboard PTT initialized: Key '{self.ptt_key}'")
            self._initialized = True
            
        self._last_debug_log = 0

    def is_pressed(self) -> bool:
        """Check if PTT button/key is currently pressed"""
        if not self._initialized:
            # Try to setup again if failed previously
            if time.time() - getattr(self, '_last_setup_attempt', 0) > 5:
                self._last_setup_attempt = time.time()
                self.setup()
            if not self._initialized:
                return False
            
        is_active = False
        try:
            if self.ptt_type == 'keyboard' and keyboard:
                try:
                    is_active = keyboard.is_pressed(self.ptt_key)
                except:
                    # Keyboard library error (e.g. no admin)
                    pass
                
            elif self.ptt_type == 'joystick' and self.joystick:
                try:
                    pygame.event.pump() # Process event queue
                    is_active = self.joystick.get_button(self.joystick_button)
                except Exception as e:
                    # Joystick disconnected?
                    if time.time() - self._last_debug_log > 5:
                        logger.error(f"Joystick read error: {e}")
                        self._last_debug_log = time.time()
                    self._initialized = False # Force re-init next time
        except Exception:
            pass
            
        # Debug logging (throttled)
        if is_active and time.time() - self._last_debug_log > 1.0:
            logger.info(f"🎤 PTT ACTIVE ({self.ptt_type})")
            self._last_debug_log = time.time()
            
        return is_active

    def list_devices(self):
        """List available joystick devices"""
        if not pygame:
            print("pygame not installed")
            return
            
        pygame.init()
        pygame.joystick.init()
        count = pygame.joystick.get_count()
        
        print(f"🎮 Found {count} device(s):")
        for i in range(count):
            try:
                j = pygame.joystick.Joystick(i)
                j.init()
                print(f"\n  Device {i}:")
                print(f"    Name: {j.get_name()}")
                print(f"    Buttons: {j.get_numbuttons()}")
            except:
                print(f"  Device {i}: Error reading")

if __name__ == "__main__":
    # Test script usage
    import sys
    
    if "--list" in sys.argv:
        vr = VoiceRecognition()
        vr.list_devices()
    else:
        print("Testing PTT... (Press configured button)")
        # Default test
        vr = VoiceRecognition(ptt_type='keyboard', ptt_key='space') 
        try:
            while True:
                if vr.is_pressed():
                    print("ON", end='\r')
                else:
                    print("OFF", end='\r')
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass
