"""
PitBox Relay Agent - Video Encoder
Captures and streams video frames to PitBox Server.
Uses dxcam for DirectX game capture (like Discord).
Falls back to mss for regular screen capture.
"""
import base64
import logging
import time
import threading
import cv2
import numpy as np

try:
    import dxcam
    DXCAM_AVAILABLE = True
except ImportError:
    DXCAM_AVAILABLE = False

try:
    import mss
    MSS_AVAILABLE = True
except ImportError:
    MSS_AVAILABLE = False

# Windows-specific imports for window detection
try:
    import win32gui
    import win32con
    PYWIN32_AVAILABLE = True
except ImportError:
    PYWIN32_AVAILABLE = False

import config

logger = logging.getLogger(__name__)


def find_window_by_title(title_substring: str):
    """
    Find a window handle and its screen coordinates by partial title match.
    Returns (hwnd, full_title, region) or (None, None, None) if not found.
    Region is (left, top, right, bottom) in screen coordinates.
    """
    result = [None, None, None]
    
    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            window_title = win32gui.GetWindowText(hwnd)
            if title_substring.lower() in window_title.lower():
                try:
                    # Get window rectangle in screen coordinates
                    rect = win32gui.GetWindowRect(hwnd)
                    result[0] = hwnd
                    result[1] = window_title
                    result[2] = rect  # (left, top, right, bottom)
                    return False  # Stop enumeration
                except Exception:
                    pass
        return True
    
    try:
        win32gui.EnumWindows(callback, None)
    except Exception:
        pass  # Enumeration stopped early (window found)
    
    return result[0], result[1], result[2]


class VideoEncoder:
    """
    Captures video using dxcam (DirectX capture) or mss (fallback).
    Targets iRacing window by title, similar to Discord's game streaming.
    """
    
    def __init__(self, client, monitor_index=0, window_title="iRacing.com Simulator"):
        self.client = client
        self.running = False
        self.thread = None
        
        # Capture settings
        self.window_title = window_title
        self.monitor_index = monitor_index
        self.use_dxcam = DXCAM_AVAILABLE
        
        # Stats
        self.frames_sent = 0
        self.start_time = 0
        self.window_region = None  # Cached window region
        self.last_window_check = 0
        
        # Output settings - optimized for LOW LATENCY
        self.width = 960    # 540p - good balance of quality vs speed
        self.height = 540
        self.quality = 45   # Lower quality = smaller files = faster transmission
        self.fps = 90       # 90fps for extra smoothness
        
        # DXCam camera instance
        self.camera = None
        
    def start(self):
        """Start capture thread"""
        if self.running:
            return
        
        if not DXCAM_AVAILABLE and not MSS_AVAILABLE:
            logger.error("❌ No capture method available. Install 'dxcam' or 'mss'")
            return
        
        # Detailed startup logging
        logger.info("=" * 50)
        logger.info("🎥 VIDEO ENCODER STARTUP")
        logger.info("=" * 50)
        logger.info(f"   Capture Libraries:")
        logger.info(f"      - dxcam (DirectX): {'✅ Available' if DXCAM_AVAILABLE else '❌ Not installed'}")
        logger.info(f"      - mss (Screen):    {'✅ Available' if MSS_AVAILABLE else '❌ Not installed'}")
        logger.info(f"      - pywin32 (Window): {'✅ Available' if PYWIN32_AVAILABLE else '❌ Not installed'}")
        logger.info(f"   Target Window: '{self.window_title}'")
        logger.info(f"   Fallback Monitor: {self.monitor_index}")
        logger.info(f"   Output: {self.width}x{self.height} @ {self.fps}fps (JPEG q={self.quality})")
        
        if DXCAM_AVAILABLE:
            logger.info("   Mode: DirectX Game Capture (like Discord)")
        else:
            logger.info("   Mode: Standard Screen Capture")
        logger.info("=" * 50)
            
        self.running = True
        self.start_time = time.time()
        
        # Start capture thread
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        
    def stop(self):
        """Stop capture"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        
        # Cleanup dxcam
        if self.camera:
            try:
                self.camera.stop()
            except Exception:
                pass
            self.camera = None
            
        logger.info(f"Video Capture stopped. Frames sent: {self.frames_sent}")

    def _find_iracing_window(self) -> tuple:
        """Find the iRacing window and return its screen region."""
        if not PYWIN32_AVAILABLE:
            return None
        
        hwnd, title, rect = find_window_by_title(self.window_title)
        if hwnd and rect:
            # rect is (left, top, right, bottom)
            # Clamp to non-negative values (window may be partially off-screen)
            left, top, right, bottom = rect
            left = max(0, left)
            top = max(0, top)
            # Ensure we have a valid region (min 100x100)
            if right - left < 100 or bottom - top < 100:
                logger.warning(f"⚠️ Window too small or invalid: {rect}")
                return None
            clamped_rect = (left, top, right, bottom)
            logger.info(f"🎮 Found window: '{title}' at {clamped_rect}")
            return clamped_rect
        return None

    def _capture_loop(self):
        """Main capture loop using dxcam or mss"""
        frame_interval = 1.0 / self.fps
        last_frame_time = 0
        window_check_interval = 5.0  # Re-check window position every 5 seconds
        
        # Try to find iRacing window first
        if PYWIN32_AVAILABLE and self.window_title:
            self.window_region = self._find_iracing_window()
        
        # Initialize dxcam
        if self.use_dxcam:
            try:
                # Create camera for the appropriate monitor
                # dxcam auto-detects the best device
                self.camera = dxcam.create(output_idx=self.monitor_index, output_color="BGR")
                
                if self.window_region:
                    logger.info(f"🎥 dxcam targeting window region: {self.window_region}")
                else:
                    logger.info(f"📺 dxcam capturing full screen (monitor {self.monitor_index})")
                    
            except Exception as e:
                logger.error(f"Failed to initialize dxcam: {e}")
                self.use_dxcam = False
        
        # Fallback to mss
        sct = None
        if not self.use_dxcam:
            if MSS_AVAILABLE:
                sct = mss.mss()
                logger.info("📺 Using mss screen capture")
            else:
                logger.error("No capture method available!")
                return
        
        while self.running:
            # Rate limiting
            now = time.time()
            if now - last_frame_time < frame_interval:
                time.sleep(0.005)
                continue
            
            last_frame_time = now
            frame = None
            
            try:
                # Periodically re-check window position (in case it moved)
                if now - self.last_window_check > window_check_interval:
                    self.last_window_check = now
                    if PYWIN32_AVAILABLE and self.window_title:
                        new_region = self._find_iracing_window()
                        if new_region and new_region != self.window_region:
                            self.window_region = new_region
                            logger.info(f"🎮 Window moved to: {self.window_region}")
                
                # Capture frame
                if self.use_dxcam and self.camera:
                    # dxcam capture with optional region
                    if self.window_region:
                        frame = self.camera.grab(region=self.window_region)
                    else:
                        frame = self.camera.grab()
                        
                elif sct:
                    # mss fallback
                    if self.window_region:
                        left, top, right, bottom = self.window_region
                        monitor = {
                            "left": left,
                            "top": top,
                            "width": right - left,
                            "height": bottom - top
                        }
                    else:
                        monitor = sct.monitors[self.monitor_index + 1]  # mss is 1-indexed
                    
                    screenshot = sct.grab(monitor)
                    frame = np.array(screenshot)
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                
                if frame is None:
                    # Log periodically when frames are failing
                    if self.frames_sent == 0 and int(now) % 5 == 0:
                        logger.warning(f"⚠️ Capture returned None (region: {self.window_region})")
                    continue
                
                # Resize for bandwidth efficiency
                frame = cv2.resize(frame, (self.width, self.height))
                
                # Encode to JPEG
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.quality]
                _, buffer = cv2.imencode('.jpg', frame, encode_param)
                
                # Convert to base64 string
                jpg_as_text = base64.b64encode(buffer).decode('utf-8')
                
                # Send via client
                if self.client.send_video_frame(jpg_as_text):
                    self.frames_sent += 1
                    # Log progress periodically
                    if self.frames_sent == 1:
                        logger.info(f"📹 First video frame sent!")
                    elif self.frames_sent % 100 == 0:
                        logger.info(f"📹 Video frames sent: {self.frames_sent}")
                    
            except Exception as e:
                logger.error(f"Capture error: {e}")
                time.sleep(0.5)
        
        # Cleanup
        if sct:
            sct.close()
        if self.camera:
            try:
                self.camera.stop()
            except Exception:
                pass
