"""
PitBox Driver HUD Overlay
A comprehensive in-car HUD showing telemetry data and voice engineer responses.
Always-on-top, transparent overlay for use while racing.
"""
import threading
import time
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk
from typing import Optional, Dict, Any, Callable
import logging
import os
import json

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

logger = logging.getLogger(__name__)


class DriverHUD:
    """
    Comprehensive driver HUD overlay showing:
    - Lap / Position / Gap
    - Speed / Gear
    - RPM bar
    - Fuel remaining
    - Flag status
    - PTT status and AI response text
    """
    
    def __init__(self, width: int = 300, height: int = 180, x_offset: int = 50, y_offset: int = 50):
        self.width = width
        self.height = height
        self.x_offset = x_offset
        self.y_offset = y_offset
        
        self.root: Optional[tk.Tk] = None
        self.canvas: Optional[tk.Canvas] = None
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
        # Telemetry state
        self.telemetry: Dict[str, Any] = {
            'speed': 0,
            'gear': 'N',
            'rpm': 0,
            'max_rpm': 8000,
            'lap': 0,
            'total_laps': 0,
            'position': 0,
            'total_cars': 0,
            'gap_ahead': 0.0,
            'gap_behind': 0.0,
            'fuel_remaining': 0.0,
            'fuel_laps': 0.0,
            'flag': 'green',
        }
        
        # Voice state
        self.ptt_active = False
        self.engineer_response = ""
        self.response_timestamp = 0
        self.response_display_duration = 8  # seconds
        
        # Drag state
        self._drag_start_x = 0
        self._drag_start_y = 0
        self._is_dragging = False
        
        # Settings dialog state
        self._settings_dialog: Optional[tk.Toplevel] = None
        self._settings_icon_bbox = None  # Bounding box for click detection
        self._ptt_binding_callback: Optional[Callable[[str, str, int], None]] = None
        self._current_ptt_config = self._load_ptt_config()
        
    def start(self):
        """Start the HUD in a separate thread"""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run_gui, daemon=True)
        self.thread.start()
        logger.info("🖥️ Driver HUD started")
        
    def stop(self):
        """Stop the HUD"""
        self.running = False
        if self.root:
            try:
                self.root.quit()
            except:
                pass
        logger.info("🖥️ Driver HUD stopped")
    
    def set_ptt_callback(self, callback: Callable[[str, str, int], None]):
        """Set callback to be called when PTT binding changes
        
        Callback signature: callback(ptt_type, ptt_key, joystick_button)
        - ptt_type: 'keyboard' or 'joystick'  
        - ptt_key: key name for keyboard (e.g., 'v') or ''
        - joystick_button: button index for joystick or -1
        """
        self._ptt_binding_callback = callback
    
    def _load_ptt_config(self) -> Dict[str, Any]:
        """Load PTT configuration from ptt_config.json"""
        config_path = os.path.join(os.path.dirname(__file__), 'ptt_config.json')
        default_config = {
            'ptt_type': 'keyboard',
            'ptt_key': 'v',
            'joystick_id': 0,
            'joystick_button': 0
        }
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults
                    return {**default_config, **config}
        except Exception as e:
            logger.warning(f"Could not load PTT config: {e}")
        return default_config
    
    def _save_ptt_config(self, config: Dict[str, Any]):
        """Save PTT configuration to ptt_config.json"""
        config_path = os.path.join(os.path.dirname(__file__), 'ptt_config.json')
        try:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"💾 Saved PTT config: {config}")
            self._current_ptt_config = config
        except Exception as e:
            logger.error(f"Could not save PTT config: {e}")
    
    def _open_settings_dialog(self, event=None):
        """Open the PTT settings dialog"""
        if self._settings_dialog is not None:
            return  # Already open
        
        dialog = tk.Toplevel(self.root)
        dialog.title("PitBox Settings")
        dialog.geometry("320x280")
        dialog.resizable(False, False)
        dialog.configure(bg="#1a1a1a")
        
        # Make dialog modal and on top
        dialog.transient(self.root)
        dialog.wm_attributes("-topmost", True)
        dialog.grab_set()
        
        self._settings_dialog = dialog
        
        # Title
        tk.Label(dialog, text="🎙️ Push-to-Talk Binding", font=("Arial", 12, "bold"),
                fg="#ffffff", bg="#1a1a1a").pack(pady=(15, 10))
        
        # Current binding display
        current = self._current_ptt_config
        if current['ptt_type'] == 'keyboard':
            binding_text = f"Current: Keyboard [{current['ptt_key'].upper()}]"
        else:
            binding_text = f"Current: Joystick {current['joystick_id']} Button {current['joystick_button']}"
        
        current_label = tk.Label(dialog, text=binding_text, font=("Arial", 10),
                                fg="#888888", bg="#1a1a1a")
        current_label.pack(pady=5)
        
        # Separator
        ttk.Separator(dialog, orient='horizontal').pack(fill='x', padx=20, pady=10)
        
        # Instructions
        self._binding_label = tk.Label(dialog, text="Click below, then press a key\nor wheel button to bind",
                                        font=("Arial", 10), fg="#cccccc", bg="#1a1a1a")
        self._binding_label.pack(pady=5)
        
        # Bind button
        self._listen_button = tk.Button(dialog, text="🎯 Press to Bind", 
                                        font=("Arial", 11, "bold"),
                                        bg="#2a5a8a", fg="#ffffff",
                                        activebackground="#3a7aba",
                                        width=20, height=2,
                                        command=self._start_binding_listener)
        self._listen_button.pack(pady=10)
        
        # Status label (for feedback)
        self._status_label = tk.Label(dialog, text="", font=("Arial", 9),
                                      fg="#00ff88", bg="#1a1a1a")
        self._status_label.pack(pady=5)
        
        # Close button
        tk.Button(dialog, text="Close", font=("Arial", 10),
                 bg="#333333", fg="#ffffff",
                 activebackground="#444444",
                 width=10,
                 command=self._close_settings_dialog).pack(pady=15)
        
        # Handle window close
        dialog.protocol("WM_DELETE_WINDOW", self._close_settings_dialog)
    
    def _close_settings_dialog(self):
        """Close the settings dialog"""
        if self._settings_dialog:
            self._settings_dialog.destroy()
            self._settings_dialog = None
            self._binding_active = False
    
    def _start_binding_listener(self):
        """Start listening for key/button input"""
        self._binding_active = True
        self._binding_label.config(text="Listening... Press any key or button", fg="#ffaa00")
        self._listen_button.config(state='disabled', text="⏳ Waiting...")
        
        # Start keyboard listener - bind to dialog and force focus
        if self._settings_dialog:
            # Bind to the dialog itself
            self._settings_dialog.bind('<Key>', self._on_keyboard_bind)
            self._settings_dialog.bind('<KeyPress>', self._on_keyboard_bind)
            # Force focus to the dialog
            self._settings_dialog.focus_force()
            self._settings_dialog.grab_set()
            # Also try using a global keyboard hook via after()
            self._poll_keyboard()
            logger.info("🎹 Keyboard listener started, dialog focused")
        
        # Start joystick polling in a thread
        if PYGAME_AVAILABLE:
            threading.Thread(target=self._poll_joystick_for_binding, daemon=True).start()
    
    def _poll_keyboard(self):
        """Poll for keyboard input as fallback (using keyboard library if available)"""
        if not getattr(self, '_binding_active', False):
            return
        
        try:
            import keyboard
            # Check if any key is pressed
            for key in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
                       'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
                       '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
                       'space', 'tab', 'shift', 'ctrl', 'alt']:
                if keyboard.is_pressed(key):
                    self._binding_active = False
                    self._complete_keyboard_binding(key)
                    return
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"Keyboard poll error: {e}")
        
        # Continue polling
        if self._settings_dialog and getattr(self, '_binding_active', False):
            self._settings_dialog.after(50, self._poll_keyboard)
    
    def _complete_keyboard_binding(self, key: str):
        """Complete keyboard binding (can be called from polling or event)"""
        # Save the binding
        new_config = {
            'ptt_type': 'keyboard',
            'ptt_key': key,
            'joystick_id': self._current_ptt_config.get('joystick_id', 0),
            'joystick_button': self._current_ptt_config.get('joystick_button', 0)
        }
        self._save_ptt_config(new_config)
        
        # Update UI
        if hasattr(self, '_status_label') and self._status_label.winfo_exists():
            self._status_label.config(text=f"✓ Bound to keyboard [{key.upper()}]", fg="#00ff88")
        if hasattr(self, '_binding_label') and self._binding_label.winfo_exists():
            self._binding_label.config(text="Click below, then press a key\nor wheel button to bind", fg="#cccccc")
        if hasattr(self, '_listen_button') and self._listen_button.winfo_exists():
            self._listen_button.config(state='normal', text="🎯 Press to Bind")
        
        # Notify callback
        if self._ptt_binding_callback:
            self._ptt_binding_callback('keyboard', key, 0, -1)
        
        logger.info(f"✅ PTT bound to keyboard key: {key}")
    
    def _on_keyboard_bind(self, event):
        """Handle keyboard key press for binding"""
        if not getattr(self, '_binding_active', False):
            return
        
        key = event.keysym.lower()
        if key in ('escape', 'return', 'tab'):
            # Cancel on escape
            if key == 'escape':
                self._cancel_binding()
            return
        
        self._binding_active = False
        
        # Save the binding
        new_config = {
            'ptt_type': 'keyboard',
            'ptt_key': key,
            'joystick_id': self._current_ptt_config.get('joystick_id', 0),
            'joystick_button': self._current_ptt_config.get('joystick_button', 0)
        }
        self._save_ptt_config(new_config)
        
        # Update UI
        self._status_label.config(text=f"✓ Bound to keyboard [{key.upper()}]", fg="#00ff88")
        self._binding_label.config(text="Click below, then press a key\nor wheel button to bind", fg="#cccccc")
        self._listen_button.config(state='normal', text="🎯 Press to Bind")
        
        # Notify callback
        if self._ptt_binding_callback:
            self._ptt_binding_callback('keyboard', key, -1)
    
    def _poll_joystick_for_binding(self):
        """Poll joysticks for button press (runs in separate thread)"""
        if not PYGAME_AVAILABLE:
            return
        
        try:
            pygame.init()
            pygame.joystick.init()
            
            joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
            for js in joysticks:
                js.init()
            
            if not joysticks:
                return
            
            # Poll for button presses
            timeout = time.time() + 10  # 10 second timeout
            while getattr(self, '_binding_active', False) and time.time() < timeout:
                pygame.event.pump()
                
                for js_idx, js in enumerate(joysticks):
                    for btn in range(js.get_numbuttons()):
                        if js.get_button(btn):
                            # Button pressed!
                            self._binding_active = False
                            
                            # Save the binding
                            new_config = {
                                'ptt_type': 'joystick',
                                'ptt_key': self._current_ptt_config.get('ptt_key', 'v'),
                                'joystick_id': js_idx,
                                'joystick_button': btn
                            }
                            
                            # Update UI from main thread
                            if self.root:
                                self.root.after(0, lambda c=new_config, j=js_idx, b=btn: 
                                               self._complete_joystick_binding(c, j, b))
                            return
                
                time.sleep(0.05)
            
            # Timeout - reset UI
            if self.root and not getattr(self, '_binding_active', False):
                return  # Already handled
            if self.root:
                self.root.after(0, self._cancel_binding)
                
        except Exception as e:
            logger.warning(f"Joystick polling error: {e}")
    
    def _complete_joystick_binding(self, config: Dict[str, Any], js_idx: int, btn: int):
        """Complete joystick binding (called from main thread)"""
        self._save_ptt_config(config)
        
        if hasattr(self, '_status_label') and self._status_label.winfo_exists():
            self._status_label.config(text=f"✓ Bound to Joystick {js_idx} Button {btn}", fg="#00ff88")
        if hasattr(self, '_binding_label') and self._binding_label.winfo_exists():
            self._binding_label.config(text="Click below, then press a key\nor wheel button to bind", fg="#cccccc")
        if hasattr(self, '_listen_button') and self._listen_button.winfo_exists():
            self._listen_button.config(state='normal', text="🎯 Press to Bind")
        
        # Notify callback
        if self._ptt_binding_callback:
            self._ptt_binding_callback('joystick', '', js_idx, btn)
    
    def _cancel_binding(self):
        """Cancel the binding process"""
        self._binding_active = False
        if hasattr(self, '_binding_label') and self._binding_label.winfo_exists():
            self._binding_label.config(text="Binding cancelled", fg="#ff6666")
        if hasattr(self, '_listen_button') and self._listen_button.winfo_exists():
            self._listen_button.config(state='normal', text="🎯 Press to Bind")
        # Reset label after a moment
        if self.root:
            self.root.after(2000, lambda: self._binding_label.config(
                text="Click below, then press a key\nor wheel button to bind", fg="#cccccc") 
                if hasattr(self, '_binding_label') and self._binding_label.winfo_exists() else None)
    
    def update_telemetry(self, data: Dict[str, Any]):
        """Update telemetry data from iRacing"""
        for key in self.telemetry:
            if key in data:
                self.telemetry[key] = data[key]
        
        if self.root:
            self.root.after(0, self._redraw)
    
    def set_ptt_active(self, active: bool):
        """Update PTT state"""
        self.ptt_active = active
        if self.root:
            self.root.after(0, self._redraw)
    
    def set_engineer_response(self, text: str):
        """Display engineer response text"""
        self.engineer_response = text
        self.response_timestamp = time.time()
        if self.root:
            self.root.after(0, self._redraw)
    
    def _run_gui(self):
        """Main GUI loop"""
        self.root = tk.Tk()
        self.root.title("PitBox HUD")
        
        # Window setup - frameless, always on top
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        
        # Transparency
        try:
            self.root.wait_visibility(self.root)
            self.root.wm_attributes("-alpha", 0.85)
        except:
            pass
        
        # Position (top-left by default)
        self.root.geometry(f"{self.width}x{self.height}+{self.x_offset}+{self.y_offset}")
        
        # Background color for transparency key (if needed)
        bg_color = "#0a0a0a"
        self.root.configure(bg=bg_color)
        
        # Canvas for drawing
        self.canvas = tk.Canvas(
            self.root,
            width=self.width,
            height=self.height,
            bg=bg_color,
            highlightthickness=0
        )
        self.canvas.pack(fill='both', expand=True)
        
        # Enable drag functionality
        self.canvas.bind("<Button-1>", self._on_drag_start)
        self.canvas.bind("<B1-Motion>", self._on_drag_motion)
        self.canvas.bind("<ButtonRelease-1>", self._on_drag_end)
        
        # Initial draw
        self._redraw()
        
        # Periodic redraw for response timeout
        self._periodic_update()
        
        self.root.mainloop()
    
    def _on_drag_start(self, event):
        """Start dragging the window, or open settings if clicking gear icon"""
        # Check if clicking on settings icon
        if self._settings_icon_bbox:
            x1, y1, x2, y2 = self._settings_icon_bbox
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                self._open_settings_dialog(event)
                return
        
        self._is_dragging = True
        self._drag_start_x = event.x
        self._drag_start_y = event.y
    
    def _on_drag_motion(self, event):
        """Handle drag motion"""
        if self._is_dragging and self.root:
            # Calculate new position
            x = self.root.winfo_x() + (event.x - self._drag_start_x)
            y = self.root.winfo_y() + (event.y - self._drag_start_y)
            self.root.geometry(f"+{x}+{y}")
            # Update internal offset for reference
            self.x_offset = x
            self.y_offset = y
    
    def _on_drag_end(self, event):
        """End dragging"""
        self._is_dragging = False
        if self.root:
            logger.debug(f"HUD moved to position ({self.x_offset}, {self.y_offset})")
    
    def _periodic_update(self):
        """Periodic update for time-based elements"""
        if not self.running:
            return
        
        # Clear expired engineer response
        if self.engineer_response and time.time() - self.response_timestamp > self.response_display_duration:
            self.engineer_response = ""
            self._redraw()
        
        if self.root:
            self.root.after(1000, self._periodic_update)
    
    def _redraw(self):
        """Redraw the entire HUD"""
        if not self.canvas:
            return
            
        self.canvas.delete("all")
        
        # Colors
        bg = "#0a0a0a"
        border = "#333333"
        text_primary = "#ffffff"
        text_secondary = "#888888"
        accent = "#00ff9d"  # PitBox green
        warning = "#ffcc00"
        danger = "#ff4444"
        
        # Background with border
        self.canvas.create_rectangle(
            2, 2, self.width - 2, self.height - 2,
            fill=bg, outline=border, width=2
        )
        
        # === Settings Icon (top-right corner) ===
        icon_x = self.width - 18
        icon_y = 12
        icon_size = 12
        self.canvas.create_text(icon_x, icon_y, text="⚙️", fill="#666666",
                               font=("Arial", 10), anchor="center")
        # Store bounding box for click detection
        self._settings_icon_bbox = (icon_x - icon_size, icon_y - icon_size, 
                                    icon_x + icon_size, icon_y + icon_size)
        
        # === Row 1: Lap / Position / Gap ===
        y = 20
        
        # Lap
        lap_text = f"LAP {self.telemetry['lap']}"
        if self.telemetry['total_laps'] > 0:
            lap_text += f"/{self.telemetry['total_laps']}"
        self.canvas.create_text(15, y, text=lap_text, fill=text_primary, 
                               font=("Arial", 11, "bold"), anchor="w")
        
        # Position
        pos = self.telemetry['position']
        pos_text = f"P{pos}" if pos > 0 else "P--"
        pos_color = accent if pos <= 3 else text_primary
        self.canvas.create_text(self.width // 2, y, text=pos_text, fill=pos_color,
                               font=("Arial", 14, "bold"), anchor="center")
        
        # Gap ahead
        gap = self.telemetry['gap_ahead']
        gap_text = f"+{gap:.1f}s" if gap > 0 else "LEADER"
        gap_color = warning if gap < 1.0 and gap > 0 else text_secondary
        self.canvas.create_text(self.width - 15, y, text=gap_text, fill=gap_color,
                               font=("Arial", 10), anchor="e")
        
        # Separator
        self.canvas.create_line(10, 35, self.width - 10, 35, fill=border)
        
        # === Row 2: Speed / Gear ===
        y = 60
        
        # Speed (large) - Default to MPH
        # iracing_reader provides m/s. 1 m/s = 2.23694 mph
        speed_mph = int(self.telemetry['speed'] * 2.23694)
        self.canvas.create_text(self.width // 2 - 30, y, text=str(speed_mph), fill=text_primary,
                               font=("Arial", 28, "bold"), anchor="e")
        self.canvas.create_text(self.width // 2 - 25, y + 5, text="MPH", fill=text_secondary,
                               font=("Arial", 9), anchor="w")
        
        # Gear (right side)
        gear = self.telemetry['gear']
        gear_text = str(gear) if gear not in ['N', 'R', 0] else 'N'
        if gear == -1 or gear == 'R':
            gear_text = 'R'
        self.canvas.create_text(self.width - 40, y, text=gear_text, fill=accent,
                               font=("Arial", 24, "bold"), anchor="center")
        
        # === Row 3: RPM Bar ===
        y = 90
        rpm = self.telemetry['rpm']
        max_rpm = self.telemetry['max_rpm'] or 8000
        rpm_pct = min(rpm / max_rpm, 1.0)
        
        bar_width = self.width - 30
        bar_height = 12
        bar_x = 15
        
        # RPM bar background
        self.canvas.create_rectangle(bar_x, y, bar_x + bar_width, y + bar_height,
                                    fill="#222222", outline=border)
        
        # RPM bar fill with color gradient
        if rpm_pct > 0:
            fill_width = bar_width * rpm_pct
            rpm_color = accent if rpm_pct < 0.85 else (warning if rpm_pct < 0.95 else danger)
            self.canvas.create_rectangle(bar_x, y, bar_x + fill_width, y + bar_height,
                                        fill=rpm_color, outline="")
        
        # === Row 4: Fuel ===
        y = 115
        fuel = self.telemetry['fuel_remaining']
        fuel_laps = self.telemetry['fuel_laps']
        
        fuel_text = f"⛽ {fuel:.1f}L"
        fuel_laps_text = f"({fuel_laps:.1f} laps)" if fuel_laps > 0 else ""
        fuel_color = text_secondary if fuel_laps > 3 else (warning if fuel_laps > 1 else danger)
        
        self.canvas.create_text(15, y, text=fuel_text, fill=fuel_color,
                               font=("Arial", 10), anchor="w")
        self.canvas.create_text(90, y, text=fuel_laps_text, fill=text_secondary,
                               font=("Arial", 9), anchor="w")
        
        # Flag indicator (right side)
        flag = self.telemetry['flag']
        flag_colors = {
            'green': '#00ff00',
            'yellow': '#ffff00',
            'red': '#ff0000',
            'white': '#ffffff',
            'checkered': '#ffffff',
            'blue': '#0088ff',
        }
        if flag and flag != 'green':
            self.canvas.create_oval(self.width - 30, y - 6, self.width - 18, y + 6,
                                   fill=flag_colors.get(flag, '#888888'), outline="")
        
        # === Row 5: Voice / PTT ===
        y = 140
        self.canvas.create_line(10, y - 10, self.width - 10, y - 10, fill=border)
        
        if self.ptt_active:
            # PTT Active indicator
            self.canvas.create_text(self.width // 2, y + 10, text="🎙️ LISTENING...",
                                   fill=accent, font=("Arial", 11, "bold"), anchor="center")
        elif self.engineer_response:
            # Engineer response (truncate if too long)
            response = self.engineer_response
            if len(response) > 40:
                response = response[:37] + "..."
            self.canvas.create_text(15, y + 5, text=f"🎙️ \"{response}\"",
                                   fill=text_secondary, font=("Arial", 9), anchor="w")
        else:
            # Ready state
            self.canvas.create_text(self.width // 2, y + 10, text="Press PTT to talk",
                                   fill="#555555", font=("Arial", 9), anchor="center")


# Backwards compatibility wrapper
    def set_listening(self, active: bool):
        """Set PTT active state"""
        self.ptt_active = active
        if active:
            # Clear previous response when starting to listen
            self.engineer_response = None
        self._update_canvas()
        
    def set_engineer_response(self, text: str):
        """Set engineer response text"""
        self.engineer_response = text
        self.ptt_active = False # Ensure PTT is off
        self._update_canvas()
        
        # Clear response after 8 seconds
        self.root.after(8000, lambda: self._clear_response(text))
        
    def _clear_response(self, text):
        """Clear response if it matches current (expired)"""
        if self.engineer_response == text:
            self.engineer_response = None
            self._update_canvas()

class PTTOverlay:
    """
    Wrapper for backwards compatibility with old PTTOverlay interface.
    Now delegates to DriverHUD.
    """
    def __init__(self):
        self.hud = DriverHUD()
        
    def start(self):
        self.hud.start()
        
    def stop(self):
        self.hud.stop()
        
    def set_talking(self, talking: bool):
        self.hud.set_ptt_active(talking)
    
    def update_telemetry(self, data: Dict[str, Any]):
        self.hud.update_telemetry(data)
    
    def set_engineer_response(self, text: str):
        self.hud.set_engineer_response(text)


if __name__ == "__main__":
    # Test the HUD
    hud = DriverHUD()
    hud.start()
    
    print("HUD started. Testing...")
    time.sleep(1)
    
    # Simulate telemetry updates
    test_data = {
        'speed': 0,
        'gear': 'N',
        'rpm': 0,
        'max_rpm': 8500,
        'lap': 5,
        'total_laps': 30,
        'position': 3,
        'gap_ahead': 1.5,
        'fuel_remaining': 45.2,
        'fuel_laps': 12.3,
        'flag': 'green',
    }
    
    try:
        for i in range(50):
            # Simulate driving
            test_data['speed'] = min(280, i * 6)
            test_data['rpm'] = min(8500, 1000 + i * 150)
            test_data['gear'] = min(6, 1 + i // 8)
            
            hud.update_telemetry(test_data)
            time.sleep(0.1)
        
        # Test PTT
        print("Testing PTT...")
        hud.set_ptt_active(True)
        time.sleep(2)
        hud.set_ptt_active(False)
        
        # Test engineer response
        print("Testing engineer response...")
        hud.set_engineer_response("Box this lap, we're going to Softs. Fuel to the end.")
        time.sleep(10)
        
    except KeyboardInterrupt:
        pass
    finally:
        hud.stop()
