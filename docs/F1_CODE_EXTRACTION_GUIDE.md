# F1 Race Replay - Code Extraction & Adaptation Guide

## Overview

This guide details **exactly what to extract** from the F1 Race Replay project and how to adapt it for ProjectBlackBox with iRacing data.

---

## ❌ What We DON'T Get (F1-Specific)

### F1 Tracks
- **They have**: Monaco, Silverstone, Spa, etc. (F1 circuits)
- **We have**: iRacing tracks (different circuits)
- **Solution**: Generate our own track maps from iRacing telemetry

### F1 Official Data
- **They use**: FastF1 library → jolpica-f1 API → Official F1 data
- **We use**: iRacing SDK → Our own telemetry
- **No conflict**: Different data sources entirely

---

## ✅ What We CAN Extract & Adapt

### 1. **Track Rendering Architecture** 🗺️

**What they do:**
```python
# From arcade_replay.py (conceptual)
class TrackRenderer:
    def __init__(self, track_coordinates):
        self.coordinates = track_coordinates
        self.scale = self.calculate_scale()

    def render(self):
        # Draw track outline
        arcade.draw_line_strip(self.coordinates, color, line_width)

    def draw_driver_position(self, x, y, color):
        # Draw driver dot on track
        arcade.draw_circle_filled(x, y, radius, color)
```

**What we adapt:**
```typescript
// dashboard/src/components/TrackMap/TrackRenderer.ts
export class TrackRenderer {
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private trackCoordinates: [number, number][];
  private scale: number;

  constructor(canvas: HTMLCanvasElement, trackData: TrackData) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d')!;
    this.trackCoordinates = trackData.coordinates;
    this.scale = this.calculateScale();
  }

  renderTrack(): void {
    this.ctx.beginPath();
    this.trackCoordinates.forEach(([x, y], index) => {
      const screenX = this.worldToScreen(x, 'x');
      const screenY = this.worldToScreen(y, 'y');

      if (index === 0) {
        this.ctx.moveTo(screenX, screenY);
      } else {
        this.ctx.lineTo(screenX, screenY);
      }
    });
    this.ctx.closePath();
    this.ctx.strokeStyle = '#444';
    this.ctx.lineWidth = 3;
    this.ctx.stroke();
  }

  renderDrivers(drivers: DriverPosition[]): void {
    drivers.forEach(driver => {
      const screenX = this.worldToScreen(driver.x, 'x');
      const screenY = this.worldToScreen(driver.y, 'y');

      // Draw driver circle
      this.ctx.beginPath();
      this.ctx.arc(screenX, screenY, 8, 0, Math.PI * 2);
      this.ctx.fillStyle = driver.color;
      this.ctx.fill();
      this.ctx.strokeStyle = driver.isPlayer ? '#FFD700' : '#FFF';
      this.ctx.lineWidth = driver.isPlayer ? 3 : 1;
      this.ctx.stroke();

      // Draw driver name
      this.ctx.fillStyle = '#FFF';
      this.ctx.font = '12px Arial';
      this.ctx.fillText(driver.name, screenX + 12, screenY + 4);
    });
  }

  private worldToScreen(value: number, axis: 'x' | 'y'): number {
    // Convert world coordinates to screen pixels
    return (value * this.scale) + this.offset[axis];
  }

  private calculateScale(): number {
    // Auto-scale track to fit canvas
    const bounds = this.calculateBounds(this.trackCoordinates);
    const scaleX = this.canvas.width / (bounds.maxX - bounds.minX);
    const scaleY = this.canvas.height / (bounds.maxY - bounds.minY);
    return Math.min(scaleX, scaleY) * 0.9; // 90% to add padding
  }
}
```

**Extract from F1 project:**
- ✅ Track rendering loop structure
- ✅ Coordinate scaling/transformation logic
- ✅ Driver position rendering
- ✅ Canvas drawing techniques

---

### 2. **Leaderboard Component** 🏆

**What they do:**
```python
# Leaderboard rendering (conceptual)
class Leaderboard:
    def render(self, drivers_data):
        for i, driver in enumerate(sorted_drivers):
            # Draw position, name, gap
            self.draw_text(f"{i+1}. {driver.name}", x, y)
            self.draw_text(f"+{driver.gap:.1f}s", x2, y)
            self.draw_tire_indicator(driver.tire_type, x3, y)
```

**What we adapt:**
```typescript
// dashboard/src/components/Leaderboard/LiveLeaderboard.tsx
interface LeaderboardDriver {
  position: number;
  name: string;
  currentLap: number;
  lastLapTime: number;
  gapToLeader: number;
  gapToAhead: number;
  tireCompound: string;
  status: 'racing' | 'pitting' | 'out';
}

export const LiveLeaderboard: React.FC<{
  drivers: LeaderboardDriver[];
  onDriverClick: (driverId: string) => void;
}> = ({ drivers, onDriverClick }) => {
  return (
    <div className="leaderboard">
      {drivers.map(driver => (
        <div
          key={driver.position}
          className={`leaderboard-row ${driver.status}`}
          onClick={() => onDriverClick(driver.name)}
        >
          <span className="position">{driver.position}</span>
          <span className="name">{driver.name}</span>
          <span className="lap">Lap {driver.currentLap}</span>
          <span className="last-lap">{formatTime(driver.lastLapTime)}</span>
          <span className="gap">
            {driver.position === 1
              ? 'Leader'
              : `+${driver.gapToLeader.toFixed(1)}s`}
          </span>
          <TireIndicator compound={driver.tireCompound} />
          <StatusBadge status={driver.status} />
        </div>
      ))}
    </div>
  );
};
```

**Extract from F1 project:**
- ✅ Leaderboard layout structure
- ✅ Gap calculation display
- ✅ Click-to-select interaction
- ✅ Status indicator patterns

---

### 3. **Replay Control System** ⏯️

**What they do:**
```python
# Playback controls (conceptual)
class ReplayController:
    def __init__(self):
        self.current_time = 0
        self.is_playing = False
        self.playback_speed = 1.0

    def update(self, delta_time):
        if self.is_playing:
            self.current_time += delta_time * self.playback_speed

    def handle_input(self, key):
        if key == arcade.key.SPACE:
            self.toggle_play_pause()
        elif key == arcade.key.LEFT:
            self.seek(-5)  # Rewind 5 seconds
        elif key == arcade.key.RIGHT:
            self.seek(5)   # Forward 5 seconds
```

**What we adapt:**
```typescript
// dashboard/src/hooks/useReplayControls.ts
export const useReplayControls = (duration: number) => {
  const [currentTime, setCurrentTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1.0);
  const animationRef = useRef<number>();
  const lastTimeRef = useRef<number>();

  // Playback loop
  useEffect(() => {
    if (isPlaying) {
      lastTimeRef.current = Date.now();

      const animate = () => {
        const now = Date.now();
        const delta = (now - lastTimeRef.current!) / 1000;
        lastTimeRef.current = now;

        setCurrentTime(prev => {
          const newTime = prev + (delta * playbackSpeed);
          return newTime >= duration ? duration : newTime;
        });

        animationRef.current = requestAnimationFrame(animate);
      };

      animationRef.current = requestAnimationFrame(animate);
    }

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isPlaying, playbackSpeed, duration]);

  // Keyboard controls
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      switch(e.key) {
        case ' ':
          setIsPlaying(prev => !prev);
          break;
        case 'ArrowLeft':
          setCurrentTime(prev => Math.max(0, prev - 5));
          break;
        case 'ArrowRight':
          setCurrentTime(prev => Math.min(duration, prev + 5));
          break;
        case 'ArrowUp':
          setPlaybackSpeed(prev => Math.min(4, prev * 2));
          break;
        case 'ArrowDown':
          setPlaybackSpeed(prev => Math.max(0.5, prev / 2));
          break;
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [duration]);

  return {
    currentTime,
    isPlaying,
    playbackSpeed,
    play: () => setIsPlaying(true),
    pause: () => setIsPlaying(false),
    seek: (time: number) => setCurrentTime(time),
    setSpeed: setPlaybackSpeed
  };
};
```

**Extract from F1 project:**
- ✅ Playback state management
- ✅ Keyboard shortcut mapping
- ✅ Speed control logic
- ✅ Time scrubbing behavior

---

### 4. **Data Processing Pipeline** 📊

**What they do:**
```python
# Data processing (conceptual from FastF1 patterns)
class TelemetryProcessor:
    def process_session(self, session_data):
        # Load telemetry data
        telemetry = self.load_telemetry(session_data)

        # Calculate derived metrics
        telemetry['speed_kmh'] = telemetry['speed'] * 3.6
        telemetry['distance'] = telemetry['speed'].cumsum()

        # Interpolate positions for smooth replay
        telemetry = self.interpolate_positions(telemetry)

        return telemetry

    def interpolate_positions(self, telemetry, target_fps=60):
        # Create smooth animation frames
        timestamps = np.linspace(
            telemetry['time'].min(),
            telemetry['time'].max(),
            num=int((telemetry['time'].max() - telemetry['time'].min()) * target_fps)
        )

        interpolated = pd.DataFrame()
        interpolated['time'] = timestamps

        for column in ['x', 'y', 'speed']:
            interpolated[column] = np.interp(
                timestamps,
                telemetry['time'],
                telemetry[column]
            )

        return interpolated
```

**What we adapt:**
```python
# relay_agent/processors/replay_processor.py
import pandas as pd
import numpy as np
from typing import List, Dict

class ReplayProcessor:
    """Process iRacing telemetry for smooth replay"""

    def __init__(self, target_fps: int = 60):
        self.target_fps = target_fps

    def process_session(self, telemetry_points: List[Dict]) -> pd.DataFrame:
        """Convert raw telemetry to replay-ready dataframe"""
        # Convert to DataFrame
        df = pd.DataFrame(telemetry_points)

        # Sort by timestamp
        df = df.sort_values('timestamp')

        # Calculate derived metrics
        df['time_seconds'] = (df['timestamp'] - df['timestamp'].min()) / 1000
        df['speed_mph'] = df['speed']
        df['speed_kmh'] = df['speed'] * 1.60934

        # Interpolate for smooth playback
        df = self.interpolate_for_replay(df)

        return df

    def interpolate_for_replay(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create smooth frame-by-frame data"""
        start_time = df['time_seconds'].min()
        end_time = df['time_seconds'].max()
        duration = end_time - start_time

        # Create timestamp for each frame
        num_frames = int(duration * self.target_fps)
        frame_times = np.linspace(start_time, end_time, num_frames)

        # Interpolate all numeric columns
        interpolated = pd.DataFrame()
        interpolated['time_seconds'] = frame_times

        numeric_columns = ['x', 'y', 'z', 'speed', 'rpm', 'throttle', 'brake', 'steering']

        for col in numeric_columns:
            if col in df.columns:
                interpolated[col] = np.interp(
                    frame_times,
                    df['time_seconds'],
                    df[col]
                )

        # Copy categorical data (use nearest value)
        for col in ['gear', 'lap_number']:
            if col in df.columns:
                interpolated[col] = np.interp(
                    frame_times,
                    df['time_seconds'],
                    df[col]
                ).astype(int)

        return interpolated

    def get_frame_at_time(self, df: pd.DataFrame, time: float) -> Dict:
        """Get interpolated data for specific time"""
        # Find closest frame
        idx = (df['time_seconds'] - time).abs().idxmin()
        return df.iloc[idx].to_dict()

    def get_all_drivers_at_time(
        self,
        sessions_df: Dict[str, pd.DataFrame],
        time: float
    ) -> List[Dict]:
        """Get all driver positions at specific time"""
        positions = []

        for driver_id, df in sessions_df.items():
            frame = self.get_frame_at_time(df, time)
            frame['driver_id'] = driver_id
            positions.append(frame)

        return positions
```

**Extract from F1 project:**
- ✅ Pandas DataFrame usage for telemetry
- ✅ Interpolation for smooth playback
- ✅ Frame-by-frame data generation
- ✅ Time-based data indexing

---

### 5. **Caching System** 💾

**What they do:**
```python
# Caching processed data
class DataCache:
    def __init__(self, cache_dir='./cache'):
        self.cache_dir = cache_dir

    def get_cached_session(self, session_id):
        cache_file = f"{self.cache_dir}/{session_id}.pkl"
        if os.path.exists(cache_file):
            return pd.read_pickle(cache_file)
        return None

    def save_session(self, session_id, data):
        cache_file = f"{self.cache_dir}/{session_id}.pkl"
        data.to_pickle(cache_file)
```

**What we adapt:**
```python
# relay_agent/cache/replay_cache.py
import os
import pickle
import hashlib
from pathlib import Path
from typing import Any, Optional

class ReplayCache:
    """Cache processed replay data for fast loading"""

    def __init__(self, cache_dir: str = "./replay_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True, parents=True)

    def get_session(self, session_id: str) -> Optional[pd.DataFrame]:
        """Load cached session data"""
        cache_file = self.cache_dir / f"{session_id}.parquet"

        if cache_file.exists():
            return pd.read_parquet(cache_file)
        return None

    def save_session(self, session_id: str, data: pd.DataFrame):
        """Save session data to cache"""
        cache_file = self.cache_dir / f"{session_id}.parquet"
        data.to_parquet(cache_file, compression='gzip')

    def get_track_map(self, track_name: str) -> Optional[Dict]:
        """Load cached track map"""
        cache_file = self.cache_dir / f"track_{track_name}.json"

        if cache_file.exists():
            with open(cache_file, 'r') as f:
                return json.load(f)
        return None

    def save_track_map(self, track_name: str, track_data: Dict):
        """Save track map to cache"""
        cache_file = self.cache_dir / f"track_{track_name}.json"

        with open(cache_file, 'w') as f:
            json.dump(track_data, f)

    def clear_old_caches(self, max_age_days: int = 30):
        """Remove caches older than specified days"""
        import time
        current_time = time.time()

        for cache_file in self.cache_dir.glob("*"):
            file_age_days = (current_time - cache_file.stat().st_mtime) / 86400
            if file_age_days > max_age_days:
                cache_file.unlink()
```

**Extract from F1 project:**
- ✅ Session caching strategy
- ✅ File-based cache management
- ✅ Fast load/save patterns
- ✅ Cache invalidation logic

---

### 6. **Track Map Generation** 🏁

**What they have:**
- Pre-made F1 track coordinates from FastF1

**What we create:**
```python
# relay_agent/track_data/track_generator.py
import numpy as np
from scipy.signal import savgol_filter
from typing import List, Tuple

class TrackGenerator:
    """Generate track maps from iRacing telemetry"""

    def __init__(self):
        self.cache = ReplayCache()

    def generate_from_lap(
        self,
        telemetry_df: pd.DataFrame,
        smooth: bool = True
    ) -> List[Tuple[float, float]]:
        """Generate track outline from one clean lap"""

        # Get first complete lap
        first_lap = telemetry_df[telemetry_df['lap_number'] == 1]

        # Extract X, Y coordinates
        x_coords = first_lap['x'].values
        y_coords = first_lap['y'].values

        # Remove duplicates
        coords = list(zip(x_coords, y_coords))
        coords = self._remove_duplicates(coords)

        if smooth:
            coords = self._smooth_track(coords)

        return coords

    def _smooth_track(
        self,
        coords: List[Tuple[float, float]],
        window: int = 51
    ) -> List[Tuple[float, float]]:
        """Apply Savitzky-Golay filter for smooth track"""
        x_coords = [c[0] for c in coords]
        y_coords = [c[1] for c in coords]

        # Smooth using Savitzky-Golay filter
        x_smooth = savgol_filter(x_coords, window, 3)
        y_smooth = savgol_filter(y_coords, window, 3)

        return list(zip(x_smooth, y_smooth))

    def _remove_duplicates(
        self,
        coords: List[Tuple[float, float]],
        threshold: float = 1.0
    ) -> List[Tuple[float, float]]:
        """Remove duplicate points closer than threshold"""
        if not coords:
            return []

        filtered = [coords[0]]

        for coord in coords[1:]:
            last = filtered[-1]
            distance = np.sqrt(
                (coord[0] - last[0])**2 + (coord[1] - last[1])**2
            )

            if distance >= threshold:
                filtered.append(coord)

        return filtered

    def calculate_track_metadata(
        self,
        coords: List[Tuple[float, float]]
    ) -> Dict:
        """Calculate track bounds and center"""
        x_coords = [c[0] for c in coords]
        y_coords = [c[1] for c in coords]

        return {
            'center': (np.mean(x_coords), np.mean(y_coords)),
            'bounds': {
                'min_x': min(x_coords),
                'max_x': max(x_coords),
                'min_y': min(y_coords),
                'max_y': max(y_coords)
            },
            'length': self._calculate_track_length(coords)
        }

    def _calculate_track_length(
        self,
        coords: List[Tuple[float, float]]
    ) -> float:
        """Calculate total track length"""
        length = 0.0

        for i in range(len(coords) - 1):
            dx = coords[i+1][0] - coords[i][0]
            dy = coords[i+1][1] - coords[i][1]
            length += np.sqrt(dx**2 + dy**2)

        return length
```

**What we CREATE (not extract):**
- ✅ Track generation from iRacing telemetry
- ✅ Coordinate smoothing algorithm
- ✅ Track metadata calculation
- ✅ Auto-caching of generated tracks

---

## 📋 **Complete Extraction Checklist**

### From F1 Race Replay Project:

| Feature | Extract | Adapt | Create New |
|---------|---------|-------|------------|
| **Track Rendering** | ✅ Canvas logic | ✅ Coordinates | ❌ |
| **Driver Positions** | ✅ Rendering code | ✅ Color coding | ❌ |
| **Leaderboard** | ✅ Layout | ✅ Data fields | ❌ |
| **Replay Controls** | ✅ UI pattern | ✅ State management | ❌ |
| **Keyboard Shortcuts** | ✅ Key mappings | ❌ | ❌ |
| **Data Interpolation** | ✅ Algorithm | ✅ For iRacing | ❌ |
| **Caching System** | ✅ Pattern | ✅ File format | ❌ |
| **Track Data** | ❌ | ❌ | ✅ Generate from telemetry |
| **Session Storage** | ✅ Structure | ✅ Our DB | ❌ |

### From FastF1 Library:

| Feature | Learn From | Implement |
|---------|-----------|-----------|
| **Pandas DataFrames** | ✅ Structure | ✅ Our telemetry |
| **API Architecture** | ✅ Patterns | ✅ Our endpoints |
| **Data Validation** | ✅ Methods | ✅ iRacing data |
| **Caching Strategy** | ✅ Approach | ✅ Our cache |
| **Track Circuits** | ❌ F1 only | ✅ Generate ours |

---

## 🎯 **Implementation Priority**

### Phase 1: Core Extraction (Week 1)
1. ✅ Extract track rendering logic
2. ✅ Extract replay control patterns
3. ✅ Implement track generator for iRacing
4. ✅ Create caching system

### Phase 2: UI Components (Week 2)
1. ✅ Extract leaderboard layout
2. ✅ Extract driver position rendering
3. ✅ Adapt keyboard controls
4. ✅ Build React components

### Phase 3: Data Pipeline (Week 3)
1. ✅ Implement Pandas-based processor
2. ✅ Add interpolation logic
3. ✅ Create replay export format
4. ✅ Integrate with backend

### Phase 4: Polish (Week 4)
1. ✅ Optimize rendering performance
2. ✅ Add zoom/pan to track map
3. ✅ Improve cache efficiency
4. ✅ Testing and bug fixes

---

## 💻 **Actual Code to Extract**

### Files to Reference:

1. **`f1_data.py`** (if accessible)
   - Data loading patterns
   - Telemetry processing
   - FastF1 integration patterns

2. **`arcade_replay.py`** (if accessible)
   - Rendering loop structure
   - Input handling
   - UI layout

3. **FastF1 library source** (GitHub)
   - DataFrame extensions
   - Interpolation functions
   - Cache management

### What We DON'T Copy:

❌ F1-specific data fetching (jolpica-f1 API calls)
❌ F1 track coordinates (we generate from iRacing)
❌ F1 driver/team data
❌ Any F1 branding/assets

### What We DO Adapt:

✅ Rendering algorithms (universal)
✅ Control patterns (universal)
✅ Data processing patterns (universal)
✅ UI/UX patterns (universal)

---

## 📚 **Summary: What We Actually Get**

### **1. Code Patterns** (80% of value)
- How to render track on canvas
- How to implement replay controls
- How to structure leaderboard
- How to interpolate telemetry data

### **2. Architecture** (15% of value)
- Separation of data processing and rendering
- Caching strategy
- DataFrame-based data management
- Component structure

### **3. UX/UI Design** (5% of value)
- Keyboard shortcuts
- Color schemes
- Layout patterns
- Interaction patterns

### **4. Actual F1 Data** (0% - we don't use it)
- ❌ We generate our own iRacing track maps
- ❌ We use iRacing telemetry, not F1
- ❌ Different tracks entirely

---

## 🚀 **Next Steps**

1. **Clone the repo** for reference:
   ```bash
   git clone https://github.com/IAmTomShaw/f1-race-replay.git f1-reference
   ```

2. **Study the code patterns** (don't copy-paste)

3. **Adapt for iRacing** using patterns learned

4. **Create our own track generator** from iRacing telemetry

5. **Build React components** using their UI patterns

---

**Bottom Line:** We're extracting **patterns and techniques**, not F1-specific data or code. Everything gets adapted for iRacing!
