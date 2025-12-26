"""
BroadcastBox Stream Health Monitor

Monitors system performance and automatically degrades stream quality
to maintain driver performance (zero FPS impact rule).
"""

import logging
import time
import threading
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
import os

logger = logging.getLogger(__name__)

# Try to import psutil for system monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not available - limited system monitoring")


@dataclass
class PerformanceThresholds:
    """Thresholds for performance safeguards"""
    failsafe_fps_min: int = 55      # Min iRacing FPS before degradation
    failsafe_cpu_max: int = 85      # Max CPU % before degradation
    failsafe_encode_lag_ms: int = 50  # Max encoding delay
    
    @classmethod
    def from_env(cls) -> 'PerformanceThresholds':
        return cls(
            failsafe_fps_min=int(os.getenv('FAILSAFE_FPS_MIN', '55')),
            failsafe_cpu_max=int(os.getenv('FAILSAFE_CPU_MAX', '85')),
            failsafe_encode_lag_ms=int(os.getenv('FAILSAFE_ENCODE_LAG_MS', '50')),
        )


@dataclass
class DegradeLevel:
    """Quality level for degradation"""
    bitrate: int
    fps: int
    resolution: str
    
    @property
    def is_disabled(self) -> bool:
        return self.bitrate == 0 or self.fps == 0


# Default degradation levels (from high to low quality)
DEFAULT_DEGRADE_LEVELS = [
    DegradeLevel(4000, 60, '720p'),   # Full quality
    DegradeLevel(2500, 30, '720p'),   # Medium quality
    DegradeLevel(1500, 30, '480p'),   # Low quality
    DegradeLevel(0, 0, 'disabled'),   # Stream disabled
]


class StreamHealthMonitor:
    """
    Monitors system performance and manages stream quality.
    
    The monitor runs in a background thread and checks:
    - iRacing FPS (via callback)
    - System CPU usage
    - Encoder performance
    
    When thresholds are exceeded, it automatically degrades stream quality.
    """
    
    def __init__(
        self,
        thresholds: Optional[PerformanceThresholds] = None,
        degrade_levels: Optional[List[DegradeLevel]] = None,
        on_degrade: Optional[Callable[[DegradeLevel], None]] = None,
        on_warning: Optional[Callable[[str], None]] = None,
    ):
        self.thresholds = thresholds or PerformanceThresholds.from_env()
        self.degrade_levels = degrade_levels or DEFAULT_DEGRADE_LEVELS
        self.on_degrade = on_degrade  # Called when quality changes
        self.on_warning = on_warning  # Called when warning triggered
        
        self.current_level_index = 0
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
        # Callbacks for getting external metrics
        self._iracing_fps_callback: Optional[Callable[[], float]] = None
        self._encode_lag_callback: Optional[Callable[[], float]] = None
        
        # Metrics history
        self.metrics_history: List[Dict[str, Any]] = []
        self.max_history = 60  # Keep last 60 samples
        
        # Cooldown to prevent rapid oscillation
        self.last_degrade_time = 0
        self.degrade_cooldown_sec = 10
        
        # Current metrics
        self.current_metrics: Dict[str, Any] = {
            'cpu_percent': 0,
            'ram_percent': 0,
            'iracing_fps': 0,
            'encode_fps': 0,
            'encode_lag_ms': 0,
            'dropped_frames': 0,
            'rtt_ms': 0,
        }
    
    @property
    def current_level(self) -> DegradeLevel:
        return self.degrade_levels[self.current_level_index]
    
    def set_iracing_fps_callback(self, callback: Callable[[], float]):
        """Set callback to get current iRacing FPS"""
        self._iracing_fps_callback = callback
    
    def set_encode_lag_callback(self, callback: Callable[[], float]):
        """Set callback to get current encoding lag in ms"""
        self._encode_lag_callback = callback
    
    def start(self):
        """Start monitoring in background thread"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        
        logger.info("[HealthMonitor] Started")
        logger.info(f"[HealthMonitor]   Thresholds: FPS>{self.thresholds.failsafe_fps_min}, "
                   f"CPU<{self.thresholds.failsafe_cpu_max}%, "
                   f"Lag<{self.thresholds.failsafe_encode_lag_ms}ms")
    
    def stop(self):
        """Stop monitoring"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        logger.info("[HealthMonitor] Stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                self._collect_metrics()
                self._check_thresholds()
                self._record_history()
            except Exception as e:
                logger.error(f"[HealthMonitor] Error in monitor loop: {e}")
            
            time.sleep(1)  # Check every second
    
    def _collect_metrics(self):
        """Collect current system metrics"""
        metrics = self.current_metrics
        
        # System metrics via psutil
        if PSUTIL_AVAILABLE:
            metrics['cpu_percent'] = psutil.cpu_percent(interval=None)
            metrics['ram_percent'] = psutil.virtual_memory().percent
        
        # iRacing FPS via callback
        if self._iracing_fps_callback:
            try:
                metrics['iracing_fps'] = self._iracing_fps_callback()
            except Exception:
                pass
        
        # Encoding lag via callback
        if self._encode_lag_callback:
            try:
                metrics['encode_lag_ms'] = self._encode_lag_callback()
            except Exception:
                pass
    
    def _check_thresholds(self):
        """Check thresholds and degrade if needed"""
        now = time.time()
        metrics = self.current_metrics
        warnings: List[str] = []
        should_degrade = False
        
        # Check iRacing FPS
        if metrics['iracing_fps'] > 0:
            if metrics['iracing_fps'] < self.thresholds.failsafe_fps_min:
                warnings.append(f"iracing_fps_low ({metrics['iracing_fps']})")
                should_degrade = True
        
        # Check CPU usage
        if metrics['cpu_percent'] > self.thresholds.failsafe_cpu_max:
            warnings.append(f"cpu_high ({metrics['cpu_percent']}%)")
            should_degrade = True
        
        # Check encoding lag
        if metrics['encode_lag_ms'] > self.thresholds.failsafe_encode_lag_ms:
            warnings.append(f"encode_lag ({metrics['encode_lag_ms']}ms)")
            should_degrade = True
        
        # Emit warnings
        for warning in warnings:
            if self.on_warning:
                self.on_warning(warning)
        
        # Degrade if needed (with cooldown)
        if should_degrade and now - self.last_degrade_time > self.degrade_cooldown_sec:
            self._degrade_one_level()
            self.last_degrade_time = now
    
    def _degrade_one_level(self):
        """Reduce stream quality by one level"""
        if self.current_level_index >= len(self.degrade_levels) - 1:
            logger.warning("[HealthMonitor] Already at lowest quality level")
            return
        
        self.current_level_index += 1
        new_level = self.current_level
        
        logger.warning(f"[HealthMonitor] 📉 Degrading to level {self.current_level_index}: "
                      f"{new_level.resolution} @ {new_level.fps}fps, {new_level.bitrate}kbps")
        
        if new_level.is_disabled:
            logger.error("[HealthMonitor] ⛔ Stream DISABLED due to performance issues")
        
        if self.on_degrade:
            self.on_degrade(new_level)
    
    def reset_quality(self):
        """Reset to highest quality level"""
        if self.current_level_index != 0:
            self.current_level_index = 0
            logger.info("[HealthMonitor] Reset to full quality")
            if self.on_degrade:
                self.on_degrade(self.current_level)
    
    def _record_history(self):
        """Record metrics for history/reporting"""
        self.metrics_history.append({
            **self.current_metrics,
            'timestamp': time.time(),
            'level': self.current_level_index,
        })
        
        # Trim history
        if len(self.metrics_history) > self.max_history:
            self.metrics_history = self.metrics_history[-self.max_history:]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics for health report"""
        return {
            **self.current_metrics,
            'quality_level': self.current_level_index,
            'current_resolution': self.current_level.resolution,
            'current_fps': self.current_level.fps,
            'current_bitrate': self.current_level.bitrate,
            'is_disabled': self.current_level.is_disabled,
        }
    
    def get_health_report(self) -> Dict[str, Any]:
        """Get complete health report for server"""
        return {
            'metrics': self.get_metrics(),
            'thresholds': {
                'fps_min': self.thresholds.failsafe_fps_min,
                'cpu_max': self.thresholds.failsafe_cpu_max,
                'encode_lag_max': self.thresholds.failsafe_encode_lag_ms,
            },
            'history_samples': len(self.metrics_history),
        }


# Singleton instance
_instance: Optional[StreamHealthMonitor] = None


def get_health_monitor() -> StreamHealthMonitor:
    """Get or create the singleton health monitor"""
    global _instance
    if _instance is None:
        _instance = StreamHealthMonitor()
    return _instance
