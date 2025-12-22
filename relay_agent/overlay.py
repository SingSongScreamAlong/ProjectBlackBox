"""
PitBox Driver HUD Overlay
A comprehensive in-car HUD showing telemetry data and voice engineer responses.
Always-on-top, transparent overlay for use while racing.
"""
import threading
import time
import tkinter as tk
from tkinter import font as tkfont
from typing import Optional, Dict, Any
import logging

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
        """Start dragging the window"""
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
        
        # Speed (large)
        speed = int(self.telemetry['speed'])
        self.canvas.create_text(self.width // 2 - 30, y, text=str(speed), fill=text_primary,
                               font=("Arial", 28, "bold"), anchor="e")
        self.canvas.create_text(self.width // 2 - 25, y + 5, text="km/h", fill=text_secondary,
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
