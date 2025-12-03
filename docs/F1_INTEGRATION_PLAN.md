# F1 Race Replay Integration Plan

## Overview

Integrating features from the F1 Race Replay project and FastF1 library into ProjectBlackBox to enhance track visualization, replay capabilities, and telemetry insights.

---

## Key Features to Integrate

### 1. **Interactive Track Map Visualization** 🗺️

**From F1 Project:**
- Real-time driver positions rendered on track
- Multiple drivers visible simultaneously
- Color-coded by driver/team

**Adaptation for iRacing:**
```typescript
// dashboard/src/components/TrackMap/InteractiveTrackMap.tsx

interface TrackMapProps {
  trackName: string;
  drivers: DriverPosition[];
  currentTime: number;
  onDriverSelect: (driverId: string) => void;
}

interface DriverPosition {
  driverId: string;
  name: string;
  position: { x: number; y: number; z: number };
  speed: number;
  gear: number;
  lapNumber: number;
  trackPosition: number; // 0-1, normalized position on track
  color: string;
  isPlayer: boolean;
}

export const InteractiveTrackMap: React.FC<TrackMapProps> = ({
  trackName,
  drivers,
  currentTime,
  onDriverSelect
}) => {
  // Canvas-based rendering of track outline
  // Plot driver positions as dots/cars
  // Click handler for driver selection
  // Zoom/pan controls
};
```

### 2. **Replay Controls** ⏯️

**From F1 Project:**
- Pause/Play
- Rewind/Fast-forward
- Speed control (0.5x - 4x)
- Scrub timeline

**Implementation:**
```typescript
// dashboard/src/components/Replay/ReplayControls.tsx

interface ReplayControlsProps {
  duration: number;
  currentTime: number;
  isPlaying: boolean;
  playbackSpeed: number;
  onPlay: () => void;
  onPause: () => void;
  onSeek: (time: number) => void;
  onSpeedChange: (speed: number) => void;
}

export const ReplayControls: React.FC<ReplayControlsProps> = (props) => {
  return (
    <div className="replay-controls">
      {/* Timeline scrubber */}
      <TimelineScrubber
        duration={props.duration}
        currentTime={props.currentTime}
        onSeek={props.onSeek}
      />

      {/* Play/Pause */}
      <button onClick={props.isPlaying ? props.onPause : props.onPlay}>
        {props.isPlaying ? '⏸' : '▶'}
      </button>

      {/* Speed controls */}
      <select value={props.playbackSpeed} onChange={(e) => props.onSpeedChange(Number(e.target.value))}>
        <option value={0.5}>0.5x</option>
        <option value={1}>1x</option>
        <option value={2}>2x</option>
        <option value={4}>4x</option>
      </select>

      {/* Keyboard shortcuts */}
      {/* Space: Play/Pause */}
      {/* Left/Right: -/+ 5 seconds */}
      {/* Up/Down: Speed up/down */}
    </div>
  );
};
```

### 3. **Live Leaderboard** 🏆

**From F1 Project:**
- Position, driver name, gap to leader
- Tire compound indicator
- Status (OUT, PIT, etc.)

**For iRacing:**
```typescript
// dashboard/src/components/Leaderboard/LiveLeaderboard.tsx

interface LeaderboardEntry {
  position: number;
  driverId: string;
  name: string;
  currentLap: number;
  lastLapTime: number;
  bestLapTime: number;
  gapToLeader: number;
  gapToAhead: number;
  tireType: string;
  tireWear: number;
  pitStops: number;
  status: 'racing' | 'pitting' | 'out' | 'dnf';
  isSelected: boolean;
}

export const LiveLeaderboard: React.FC<{
  entries: LeaderboardEntry[];
  onDriverSelect: (driverId: string) => void;
}> = ({ entries, onDriverSelect }) => {
  return (
    <div className="leaderboard">
      <table>
        <thead>
          <tr>
            <th>Pos</th>
            <th>Driver</th>
            <th>Lap</th>
            <th>Last</th>
            <th>Best</th>
            <th>Gap</th>
            <th>Tires</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {entries.map(entry => (
            <tr
              key={entry.driverId}
              onClick={() => onDriverSelect(entry.driverId)}
              className={entry.isSelected ? 'selected' : ''}
            >
              <td>{entry.position}</td>
              <td>{entry.name}</td>
              <td>{entry.currentLap}</td>
              <td>{formatLapTime(entry.lastLapTime)}</td>
              <td>{formatLapTime(entry.bestLapTime)}</td>
              <td>{formatGap(entry.gapToLeader)}</td>
              <td>
                <TireIndicator type={entry.tireType} wear={entry.tireWear} />
              </td>
              <td>
                <StatusBadge status={entry.status} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
```

### 4. **Telemetry Insights Panel** 📊

**From F1 Project:**
- Speed, Gear, DRS status, Current lap
- Interactive selection

**For iRacing:**
```typescript
// dashboard/src/components/TelemetryPanel/TelemetryInsightsPanel.tsx

interface TelemetryInsights {
  driverId: string;
  driverName: string;

  // Current values
  speed: number;
  rpm: number;
  gear: number;
  throttle: number;
  brake: number;
  steering: number;

  // Lap info
  currentLap: number;
  currentLapTime: number;
  lastLapTime: number;
  bestLapTime: number;
  sector: number;
  sectorTime: number;

  // Car state
  fuelLevel: number;
  fuelPerLap: number;
  tireTemps: TireTemperatures;
  tireWear: TireWear;

  // Position
  trackPosition: number;
  racePosition: number;
  classPosition: number;

  // G-Forces
  gForce: { lateral: number; longitudinal: number; vertical: number };
}

export const TelemetryInsightsPanel: React.FC<{
  insights: TelemetryInsights | null;
  onClose: () => void;
}> = ({ insights, onClose }) => {
  if (!insights) return null;

  return (
    <div className="telemetry-insights-panel">
      <div className="panel-header">
        <h3>{insights.driverName}</h3>
        <button onClick={onClose}>✕</button>
      </div>

      <div className="metrics-grid">
        {/* Speed & RPM */}
        <MetricCard label="Speed" value={`${insights.speed.toFixed(1)} mph`} />
        <MetricCard label="RPM" value={insights.rpm} />
        <MetricCard label="Gear" value={insights.gear} />

        {/* Inputs */}
        <InputBar label="Throttle" value={insights.throttle} color="green" />
        <InputBar label="Brake" value={insights.brake} color="red" />
        <InputBar label="Steering" value={Math.abs(insights.steering)} color="blue" />

        {/* Lap Times */}
        <MetricCard label="Current Lap" value={formatLapTime(insights.currentLapTime)} />
        <MetricCard label="Last Lap" value={formatLapTime(insights.lastLapTime)} />
        <MetricCard label="Best Lap" value={formatLapTime(insights.bestLapTime)} />

        {/* Position */}
        <MetricCard label="Position" value={`P${insights.racePosition}`} />
        <MetricCard label="Track Pos" value={`${(insights.trackPosition * 100).toFixed(1)}%`} />

        {/* Fuel */}
        <MetricCard label="Fuel" value={`${insights.fuelLevel.toFixed(1)}L`} />
        <MetricCard label="Per Lap" value={`${insights.fuelPerLap.toFixed(2)}L`} />

        {/* Tires */}
        <TireTemperatureWidget temps={insights.tireTemps} wear={insights.tireWear} />

        {/* G-Forces */}
        <GForceDisplay gForce={insights.gForce} />
      </div>
    </div>
  );
};
```

### 5. **FastF1-Inspired Data Processing** 🔧

**Telemetry Data Structure:**
```python
# relay_agent/processors/telemetry_processor.py

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class TelemetryPoint:
    """Single telemetry data point"""
    timestamp: float
    session_id: str
    driver_id: str

    # Position
    track_position: float  # 0-1 normalized
    lap_number: int
    lap_distance: float
    x: float
    y: float
    z: float

    # Motion
    speed: float
    rpm: int
    gear: int
    throttle: float
    brake: float
    steering: float

    # G-Forces
    g_lat: float
    g_long: float
    g_vert: float

    # Tires
    tire_temp_fl: float
    tire_temp_fr: float
    tire_temp_rl: float
    tire_temp_rr: float

    tire_wear_fl: float
    tire_wear_fr: float
    tire_wear_rl: float
    tire_wear_rr: float

class TelemetryDataFrame:
    """FastF1-inspired telemetry data structure"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.df = pd.DataFrame()
        self._cache = {}

    def add_telemetry(self, point: TelemetryPoint):
        """Add telemetry point to dataframe"""
        new_row = pd.DataFrame([point.__dict__])
        self.df = pd.concat([self.df, new_row], ignore_index=True)

    def get_lap(self, lap_number: int, driver_id: Optional[str] = None) -> pd.DataFrame:
        """Get telemetry for specific lap"""
        mask = self.df['lap_number'] == lap_number
        if driver_id:
            mask &= self.df['driver_id'] == driver_id
        return self.df[mask]

    def get_driver(self, driver_id: str) -> pd.DataFrame:
        """Get all telemetry for specific driver"""
        return self.df[self.df['driver_id'] == driver_id]

    def get_fastest_lap(self, driver_id: Optional[str] = None) -> pd.DataFrame:
        """Get fastest lap telemetry"""
        df = self.df if driver_id is None else self.get_driver(driver_id)

        # Calculate lap times
        lap_times = df.groupby('lap_number')['timestamp'].agg(['min', 'max'])
        lap_times['duration'] = lap_times['max'] - lap_times['min']
        fastest_lap = lap_times['duration'].idxmin()

        return self.get_lap(fastest_lap, driver_id)

    def interpolate_position(self, timestamp: float) -> Dict[str, Dict]:
        """Interpolate all driver positions at specific timestamp"""
        positions = {}
        for driver_id in self.df['driver_id'].unique():
            driver_df = self.get_driver(driver_id)

            # Find surrounding telemetry points
            before = driver_df[driver_df['timestamp'] <= timestamp].iloc[-1] if len(driver_df[driver_df['timestamp'] <= timestamp]) > 0 else None
            after = driver_df[driver_df['timestamp'] >= timestamp].iloc[0] if len(driver_df[driver_df['timestamp'] >= timestamp]) > 0 else None

            if before is not None and after is not None:
                # Linear interpolation
                ratio = (timestamp - before['timestamp']) / (after['timestamp'] - before['timestamp'])
                positions[driver_id] = {
                    'x': before['x'] + (after['x'] - before['x']) * ratio,
                    'y': before['y'] + (after['y'] - before['y']) * ratio,
                    'z': before['z'] + (after['z'] - before['z']) * ratio,
                    'speed': before['speed'] + (after['speed'] - before['speed']) * ratio,
                    'track_position': before['track_position'] + (after['track_position'] - before['track_position']) * ratio
                }

        return positions

    def export_for_replay(self, output_path: str):
        """Export dataframe to efficient replay format"""
        # Compress and save for fast loading
        self.df.to_parquet(output_path, compression='gzip')

    @classmethod
    def load_replay(cls, input_path: str) -> 'TelemetryDataFrame':
        """Load replay data"""
        instance = cls(session_id='replay')
        instance.df = pd.read_parquet(input_path)
        return instance
```

### 6. **Track Map Data Acquisition** 🏁

**For iRacing Tracks:**
```python
# relay_agent/track_data/track_mapper.py

import json
from pathlib import Path
from typing import Dict, List, Tuple

class TrackMapper:
    """Generate and cache track maps from telemetry data"""

    def __init__(self, cache_dir: str = "./track_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def generate_track_outline(self, telemetry_df: pd.DataFrame) -> List[Tuple[float, float]]:
        """Generate track outline from telemetry GPS coordinates"""
        # Get a complete lap from a single driver
        first_driver = telemetry_df['driver_id'].iloc[0]
        first_lap = telemetry_df[
            (telemetry_df['driver_id'] == first_driver) &
            (telemetry_df['lap_number'] == 1)
        ]

        # Extract X, Y coordinates
        coordinates = list(zip(first_lap['x'], first_lap['y']))

        # Smooth the coordinates
        coordinates = self._smooth_coordinates(coordinates)

        return coordinates

    def _smooth_coordinates(self, coords: List[Tuple[float, float]], window: int = 10) -> List[Tuple[float, float]]:
        """Apply moving average smoothing"""
        x_coords = [c[0] for c in coords]
        y_coords = [c[1] for c in coords]

        x_smooth = np.convolve(x_coords, np.ones(window)/window, mode='valid')
        y_smooth = np.convolve(y_coords, np.ones(window)/window, mode='valid')

        return list(zip(x_smooth, y_smooth))

    def save_track_map(self, track_name: str, coordinates: List[Tuple[float, float]]):
        """Save track map to cache"""
        track_file = self.cache_dir / f"{track_name}.json"
        with open(track_file, 'w') as f:
            json.dump({
                'track_name': track_name,
                'coordinates': coordinates,
                'center': self._calculate_center(coordinates),
                'bounds': self._calculate_bounds(coordinates)
            }, f)

    def load_track_map(self, track_name: str) -> Optional[Dict]:
        """Load track map from cache"""
        track_file = self.cache_dir / f"{track_name}.json"
        if track_file.exists():
            with open(track_file, 'r') as f:
                return json.load(f)
        return None

    def _calculate_center(self, coords: List[Tuple[float, float]]) -> Tuple[float, float]:
        """Calculate track center point"""
        x_coords = [c[0] for c in coords]
        y_coords = [c[1] for c in coords]
        return (np.mean(x_coords), np.mean(y_coords))

    def _calculate_bounds(self, coords: List[Tuple[float, float]]) -> Dict:
        """Calculate bounding box"""
        x_coords = [c[0] for c in coords]
        y_coords = [c[1] for c in coords]
        return {
            'min_x': min(x_coords),
            'max_x': max(x_coords),
            'min_y': min(y_coords),
            'max_y': max(y_coords)
        }
```

### 7. **Caching System** 💾

**Like FastF1's caching:**
```python
# relay_agent/cache/session_cache.py

import pickle
import hashlib
from pathlib import Path
from typing import Any, Optional

class SessionCache:
    """Cache system for processed telemetry data"""

    def __init__(self, cache_dir: str = "./cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def _generate_key(self, session_id: str, data_type: str) -> str:
        """Generate cache key"""
        key_string = f"{session_id}_{data_type}"
        return hashlib.md5(key_string.encode()).hexdigest()

    def get(self, session_id: str, data_type: str) -> Optional[Any]:
        """Retrieve cached data"""
        key = self._generate_key(session_id, data_type)
        cache_file = self.cache_dir / f"{key}.pkl"

        if cache_file.exists():
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        return None

    def set(self, session_id: str, data_type: str, data: Any):
        """Store data in cache"""
        key = self._generate_key(session_id, data_type)
        cache_file = self.cache_dir / f"{key}.pkl"

        with open(cache_file, 'wb') as f:
            pickle.dump(data, f)

    def clear(self, session_id: Optional[str] = None):
        """Clear cache"""
        if session_id:
            # Clear specific session
            for cache_file in self.cache_dir.glob(f"{session_id}_*.pkl"):
                cache_file.unlink()
        else:
            # Clear all
            for cache_file in self.cache_dir.glob("*.pkl"):
                cache_file.unlink()
```

---

## Implementation Plan

### Phase 1: Track Map Visualization (Week 1)

**Tasks:**
1. Create `TrackMapper` class to generate track outlines from telemetry
2. Build `InteractiveTrackMap` React component with Canvas rendering
3. Add track map cache system
4. Integrate with existing dashboard

**Files to Create:**
- `relay_agent/track_data/track_mapper.py`
- `dashboard/src/components/TrackMap/InteractiveTrackMap.tsx`
- `dashboard/src/components/TrackMap/TrackCanvas.tsx`
- `dashboard/src/hooks/useTrackMap.ts`

### Phase 2: Replay System (Week 2)

**Tasks:**
1. Create `TelemetryDataFrame` class (FastF1-inspired)
2. Build replay controls component
3. Add timeline scrubber
4. Implement playback speed control
5. Add keyboard shortcuts

**Files to Create:**
- `relay_agent/processors/telemetry_processor.py`
- `dashboard/src/components/Replay/ReplayControls.tsx`
- `dashboard/src/components/Replay/TimelineScrubber.tsx`
- `dashboard/src/services/ReplayService.ts`
- `dashboard/src/hooks/useReplayControls.ts`

### Phase 3: Live Leaderboard (Week 3)

**Tasks:**
1. Create `LiveLeaderboard` component
2. Add position calculation logic
3. Implement gap calculations
4. Add tire/pit stop tracking
5. Driver selection integration

**Files to Create:**
- `dashboard/src/components/Leaderboard/LiveLeaderboard.tsx`
- `dashboard/src/components/Leaderboard/TireIndicator.tsx`
- `dashboard/src/components/Leaderboard/StatusBadge.tsx`
- `dashboard/src/services/LeaderboardService.ts`

### Phase 4: Telemetry Insights Panel (Week 4)

**Tasks:**
1. Create `TelemetryInsightsPanel` component
2. Add metric cards and gauges
3. Implement input bars (throttle/brake/steering)
4. Add tire temperature visualization
5. G-force display

**Files to Create:**
- `dashboard/src/components/TelemetryPanel/TelemetryInsightsPanel.tsx`
- `dashboard/src/components/TelemetryPanel/MetricCard.tsx`
- `dashboard/src/components/TelemetryPanel/InputBar.tsx`
- `dashboard/src/components/TelemetryPanel/TireTemperatureWidget.tsx`
- `dashboard/src/components/TelemetryPanel/GForceDisplay.tsx`

### Phase 5: Integration & Polish (Week 5)

**Tasks:**
1. Integrate all components into main dashboard
2. Add caching system for replays
3. Performance optimization
4. Testing and bug fixes
5. Documentation

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    ENHANCED DASHBOARD                        │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │         Interactive Track Map                       │    │
│  │  - Real-time driver positions                       │    │
│  │  - Click to select driver                           │    │
│  │  - Zoom/Pan controls                                │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌──────────────────┐  ┌───────────────────────────────┐  │
│  │  Live Leaderboard │  │  Telemetry Insights Panel     │  │
│  │  - Positions      │  │  - Speed, RPM, Gear           │  │
│  │  - Lap times      │  │  - Inputs (Throttle/Brake)    │  │
│  │  - Gaps           │  │  - Tire temps & wear          │  │
│  │  - Tire status    │  │  - G-Forces                   │  │
│  └──────────────────┘  └───────────────────────────────┘  │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │         Replay Controls                             │    │
│  │  [◀◀] [⏸/▶] [▶▶]  [━━━━━●━━━━━]  [1x▼]        │    │
│  │  Rewind Play FF    Timeline      Speed             │    │
│  └────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
                           ▲
                           │ WebSocket
                           │
┌──────────────────────────┴───────────────────────────────────┐
│               BACKEND (DigitalOcean)                          │
│                                                               │
│  ┌─────────────────────┐  ┌──────────────────────────────┐  │
│  │ Telemetry Processor │  │  Track Mapper                │  │
│  │ (FastF1-inspired)   │  │  - Generate track outlines   │  │
│  │ - Pandas DataFrames │  │  - Cache track maps          │  │
│  │ - Interpolation     │  │  - Position calculation      │  │
│  │ - Lap analysis      │  └──────────────────────────────┘  │
│  └─────────────────────┘                                     │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           PostgreSQL + TimescaleDB                    │   │
│  │           - Time-series telemetry data               │   │
│  │           - Session replays                           │   │
│  └──────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────┘
```

---

## Benefits of Integration

### 1. **Professional Race Analysis**
- Track map visualization matches broadcast quality
- Replay system enables detailed lap analysis
- Compare driver performance side-by-side

### 2. **Better User Experience**
- Click driver on leaderboard → See their telemetry
- Scrub timeline to any moment in session
- Intuitive controls (keyboard shortcuts)

### 3. **Coaching Enhancement**
- AI can reference specific moments: "Look at turn 3 at 2:15"
- Compare fastest lap vs current lap visually
- Identify braking points, apex speeds, throttle application

### 4. **Commercial Value**
- Professional-grade visualization attracts serious racers
- Replay functionality enables post-race analysis subscriptions
- Track map becomes a premium feature

---

## Licensing Considerations

### F1 Race Replay Project
- **License**: MIT (permissive)
- **Can**: Use code, modify, integrate
- **Must**: Include MIT license notice
- **Attribution**: Credit IAmTomShaw in documentation

### FastF1
- **License**: MIT (permissive)
- **Can**: Learn from architecture, adapt patterns
- **Cannot**: Use F1 official data (your project uses iRacing data)
- **Recommendation**: Implement similar patterns, not copy code

---

## Next Steps

1. **Start with Track Map** (highest visual impact)
   - Implement `TrackMapper` in Python
   - Create track outline from telemetry
   - Build Canvas-based React component

2. **Add Replay Controls** (enables offline analysis)
   - Create `TelemetryDataFrame` structure
   - Build timeline scrubber
   - Add playback controls

3. **Enhance Leaderboard** (improves race awareness)
   - Add gap calculations
   - Implement tire tracking
   - Driver selection integration

Want me to start implementing any of these features? I can begin with the track map visualization or replay system!
