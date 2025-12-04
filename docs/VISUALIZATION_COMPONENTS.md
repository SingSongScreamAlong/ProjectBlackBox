# Professional Racing Visualization Components

F1 Manager-quality visualization system for ProjectBlackBox. Works with **all iRacing racing types**: oval, road courses, IndyCar, endurance, GT, and more.

## 🎨 Components Overview

### 1. **Track3DVisualization** - 3D Track Renderer

Professional Three.js-based 3D track visualization with realistic lighting and effects.

**Features:**
- ✅ 3D track rendering from telemetry coordinates
- ✅ Universal support (oval, road, street circuits)
- ✅ Real-time driver positions with motion trails
- ✅ Multiple camera modes (orbit, follow, broadcast, helicopter)
- ✅ Post-processing effects (bloom, shadows)
- ✅ Sector markers and start/finish line
- ✅ Interactive controls

**Usage:**
```tsx
import { Track3DVisualization } from './components';

<Track3DVisualization
  trackData={trackCoordinates}
  drivers={driverPositions}
  isLive={true}
/>
```

**Props:**
- `trackData`: Array of `{x, y, z, sectorIndex?}` coordinates
- `drivers`: Array of driver positions with `{driverId, name, x, y, z, speed, teamColor}`
- `isLive`: Boolean for live indicator
- `className`: Optional CSS class

**Camera Modes:**
- **Orbit**: Free camera control (mouse drag to rotate)
- **Follow**: Follows selected driver
- **Broadcast**: Cinematic sweeping camera
- **Helicopter**: Top-down overview

**Files:**
- `dashboard/src/components/Track3D/Track3DRenderer.ts` - Core Three.js class
- `dashboard/src/components/Track3D/Track3DVisualization.tsx` - React wrapper

---

### 2. **TimingTower** - Live Timing Display

Professional timing tower with real-time positions, gaps, and sector times.

**Features:**
- ✅ Live position tracking with animated transitions
- ✅ Sector times with color coding (purple=fastest, green=personal best, yellow=slow)
- ✅ Gap to leader and interval to car ahead
- ✅ Tire compound indicators
- ✅ Pit stop and retirement status
- ✅ Position change indicators
- ✅ Last lap and best lap times

**Usage:**
```tsx
import { TimingTower } from './components';

<TimingTower
  drivers={driverTimingData}
  showSectorTimes={true}
  showTireInfo={true}
  highlightedDriverId={selectedId}
/>
```

**Props:**
- `drivers`: Array of `DriverTiming` objects
- `showSectorTimes`: Show/hide sector time columns
- `showTireInfo`: Show/hide tire compound info
- `highlightedDriverId`: Highlight specific driver
- `className`: Optional CSS class

**Data Structure:**
```typescript
interface DriverTiming {
  position: number;
  driverId: string;
  driverName: string;
  driverNumber: string;
  teamColor: string;
  lastLapTime?: number; // milliseconds
  bestLapTime?: number;
  gap?: number | 'LEADER' | 'LAP';
  interval?: number;
  sectorTimes: {
    sector1?: number;
    sector1Status?: 'fastest' | 'personal-best' | 'normal' | 'slow';
    // ... sector2, sector3
  };
  tireCompound?: 'SOFT' | 'MEDIUM' | 'HARD' | 'INTERMEDIATE' | 'WET';
  tireLaps: number;
  positionChange: number; // +/- from start
  isInPit: boolean;
  isRetired: boolean;
}
```

**File:**
- `dashboard/src/components/TimingTower/TimingTower.tsx`

---

### 3. **TelemetryGraphs** - Advanced Telemetry Analysis

Professional telemetry graphs with driver comparison support.

**Features:**
- ✅ Speed graph (km/h over distance)
- ✅ Throttle & brake graph (combined area chart)
- ✅ Steering angle graph
- ✅ Gear & RPM graph
- ✅ Driver comparison overlays (dashed lines)
- ✅ Synchronized tooltips
- ✅ Professional Recharts rendering

**Usage:**
```tsx
import { TelemetryGraphs } from './components';

<TelemetryGraphs
  data={telemetryData}
  comparisonData={comparisonTelemetry}
  driverName="Driver 1"
  comparisonDriverName="Driver 2"
  showSpeed={true}
  showThrottle={true}
  showBrake={true}
  showSteering={true}
  height={250}
/>
```

**Props:**
- `data`: Primary driver telemetry array
- `comparisonData`: Optional comparison driver data
- `driverName`, `comparisonDriverName`: Display names
- `showSpeed`, `showThrottle`, `showBrake`, `showSteering`, `showGear`, `showRPM`: Toggle graphs
- `height`: Graph height in pixels
- `className`: Optional CSS class

**Data Structure:**
```typescript
interface TelemetryDataPoint {
  timestamp: number;
  distance: number; // meters
  speed: number; // km/h
  throttle: number; // 0-100%
  brake: number; // 0-100%
  steering: number; // -90 to +90 degrees
  gear: number; // 1-8
  rpm: number; // engine RPM
}
```

**File:**
- `dashboard/src/components/Telemetry/TelemetryGraphs.tsx`

---

### 4. **TireStrategyVisualization** - Tire Strategy Timeline

Visual timeline of tire strategies and pit stops.

**Features:**
- ✅ Visual stint timeline with tire compounds
- ✅ Pit stop markers with duration
- ✅ Tire degradation warnings
- ✅ Current lap indicator
- ✅ Strategy comparison across all drivers
- ✅ Predicted pit stops
- ✅ Statistics summary

**Usage:**
```tsx
import { TireStrategyVisualization } from './components';

<TireStrategyVisualization
  strategies={driverStrategies}
  totalLaps={50}
  currentLap={35}
  highlightedDriverId={selectedId}
/>
```

**Props:**
- `strategies`: Array of driver strategy objects
- `totalLaps`: Total race laps
- `currentLap`: Current lap number
- `highlightedDriverId`: Highlight specific driver
- `className`: Optional CSS class

**Tire Compounds:**
- 🔴 **SOFT** - Red (fastest, wears quickly)
- 🟡 **MEDIUM** - Yellow (balanced)
- ⚪ **HARD** - White (slowest, most durable)
- 🟢 **INTERMEDIATE** - Green (light rain)
- 🔵 **WET** - Blue (heavy rain)

**Data Structure:**
```typescript
interface DriverStrategy {
  driverId: string;
  driverName: string;
  teamColor: string;
  totalPitStops: number;
  predictedStops?: number;
  stints: Array<{
    compound: TireCompound;
    startLap: number;
    endLap: number;
    lapCount: number;
    degradation?: number; // 0-100%
    isCurrentStint: boolean;
  }>;
  pitStops: Array<{
    lap: number;
    duration: number; // seconds
    reason: 'tire-change' | 'damage' | 'fuel' | 'penalty';
  }>;
}
```

**File:**
- `dashboard/src/components/Strategy/TireStrategyVisualization.tsx`

---

### 5. **TrackMapGenerator** - 2D Track Map

D3.js-powered track map with real-time driver positions.

**Features:**
- ✅ Auto-generates track from telemetry coordinates
- ✅ Works for ANY track type (oval, road, etc.)
- ✅ Sector color coding
- ✅ Start/finish line marker
- ✅ Real-time driver positions
- ✅ Driver numbers on map
- ✅ Interactive tooltips
- ✅ Driver list with positions

**Usage:**
```tsx
import { TrackMapGenerator } from './components';

<TrackMapGenerator
  trackData={trackCoordinates}
  drivers={driverMapPositions}
  width={600}
  height={400}
  showSectors={true}
  showDriverNumbers={true}
  highlightedDriverId={selectedId}
/>
```

**Props:**
- `trackData`: Array of track coordinates
- `drivers`: Array of driver positions
- `width`, `height`: Canvas dimensions
- `showSectors`: Show sector colors
- `showDriverNumbers`: Show driver numbers on map
- `highlightedDriverId`: Highlight specific driver
- `className`: Optional CSS class

**File:**
- `dashboard/src/components/TrackMap/TrackMapGenerator.tsx`

---

### 6. **RacingDashboard** - Complete Dashboard

Integrated dashboard combining all components with view switching.

**Features:**
- ✅ Multiple view modes (3D Track, Timing, Telemetry, Strategy)
- ✅ Professional glassmorphism UI
- ✅ Live indicator
- ✅ Session info display
- ✅ Footer statistics
- ✅ Mock data for demonstration

**Usage:**
```tsx
import { RacingDashboard } from './components';

<RacingDashboard
  sessionId="abc123"
  isLive={true}
/>
```

**View Modes:**
1. **3D Track**: 3D visualization + 2D track map
2. **Timing**: Professional timing tower
3. **Telemetry**: Advanced telemetry graphs
4. **Strategy**: Tire strategy visualization

**File:**
- `dashboard/src/components/RacingDashboard/RacingDashboard.tsx`

---

## 🎨 Professional UI Theme

Global glassmorphism theme with F1 Manager-quality styling.

**Features:**
- ✅ Glassmorphism cards with backdrop blur
- ✅ Professional color palette
- ✅ Racing-specific utilities (position badges, sector colors, tire colors)
- ✅ Live indicators and animations
- ✅ Responsive grid system
- ✅ Toast notifications
- ✅ Loading skeletons
- ✅ Custom scrollbars

**Usage:**
```tsx
// Import in your App.tsx or index.tsx
import './styles/professional-racing-theme.css';

// Use classes
<div className="glass-card">
  <button className="btn-primary">Action</button>
  <div className="live-indicator">LIVE</div>
</div>
```

**CSS Variables:**
```css
--brand-primary: #ef4444;
--sector-1: #22c55e;
--sector-2: #eab308;
--sector-3: #9333ea;
--tire-soft: #ef4444;
--tire-medium: #eab308;
--tire-hard: #f0f0f0;
```

**File:**
- `dashboard/src/styles/professional-racing-theme.css`

---

## 🚀 Quick Start

### 1. Import Components
```tsx
import {
  Track3DVisualization,
  TimingTower,
  TelemetryGraphs,
  TireStrategyVisualization,
  TrackMapGenerator,
  RacingDashboard
} from './components';

// Import theme
import './styles/professional-racing-theme.css';
```

### 2. Use Pre-built Dashboard
```tsx
function App() {
  return (
    <RacingDashboard
      sessionId="live-session-123"
      isLive={true}
    />
  );
}
```

### 3. Or Build Custom Layout
```tsx
function CustomDashboard() {
  return (
    <div className="dashboard-grid">
      <div className="grid-col-span-8">
        <Track3DVisualization
          trackData={trackData}
          drivers={drivers}
          isLive={true}
        />
      </div>
      <div className="grid-col-span-4">
        <TimingTower
          drivers={driverTimingData}
          showSectorTimes={true}
        />
      </div>
      <div className="grid-col-span-12">
        <TelemetryGraphs
          data={telemetryData}
          showSpeed={true}
          showThrottle={true}
          showBrake={true}
        />
      </div>
    </div>
  );
}
```

---

## 🏎️ Universal Racing Support

These components work with **ALL iRacing racing types**:

- ✅ **Oval Racing** - NASCAR, IndyCar ovals
- ✅ **Road Courses** - Road America, Watkins Glen, Spa
- ✅ **Street Circuits** - Long Beach, Belle Isle
- ✅ **IndyCar** - Both road and oval configurations
- ✅ **Endurance** - 24h races, multi-class
- ✅ **GT Racing** - IMSA, GT3, GT4
- ✅ **Prototype** - LMP2, DPi
- ✅ **Formula** - Formula cars on road courses

The track visualization **automatically adapts** based on telemetry coordinates. No pre-made track models needed!

---

## 📊 Data Integration

### WebSocket Connection (TODO)
```typescript
// In production, connect to WebSocketService
import { WebSocketService } from '../services/WebSocketService';

useEffect(() => {
  const ws = new WebSocketService();

  ws.subscribe('telemetry', (data) => {
    updateTelemetryData(data);
  });

  ws.subscribe('timing', (data) => {
    updateTimingData(data);
  });

  return () => ws.disconnect();
}, []);
```

### Mock Data (Development)
All components include mock data in `RacingDashboard.tsx` for testing and demonstration.

---

## 🎯 Performance Optimization

### Three.js Optimization
- LOD (Level of Detail) for distant objects
- Geometry instancing for repeated elements
- Post-processing only when needed
- Configurable shadow quality

### React Optimization
- Memoized calculations with `useMemo`
- Animated lists with `AnimatePresence`
- Lazy loading for heavy components
- Virtual scrolling for large lists

### Best Practices
- Use `React.memo()` for static components
- Debounce WebSocket updates (60fps max)
- Implement data windowing for telemetry
- Use Web Workers for heavy calculations

---

## 📁 File Structure

```
dashboard/src/
├── components/
│   ├── Track3D/
│   │   ├── Track3DRenderer.ts       # Three.js core
│   │   └── Track3DVisualization.tsx # React wrapper
│   ├── TimingTower/
│   │   └── TimingTower.tsx
│   ├── Telemetry/
│   │   └── TelemetryGraphs.tsx
│   ├── Strategy/
│   │   └── TireStrategyVisualization.tsx
│   ├── TrackMap/
│   │   └── TrackMapGenerator.tsx
│   ├── RacingDashboard/
│   │   └── RacingDashboard.tsx      # Integrated dashboard
│   └── index.ts                      # Component exports
├── styles/
│   └── professional-racing-theme.css # Global theme
└── ...
```

---

## 🔧 Dependencies

All dependencies already installed:

```json
{
  "three": "^0.x.x",
  "@react-three/fiber": "^8.x.x",
  "@react-three/drei": "^9.x.x",
  "@react-three/postprocessing": "^2.x.x",
  "recharts": "^2.x.x",
  "d3": "^7.x.x",
  "framer-motion": "^10.x.x",
  "gsap": "^3.x.x",
  "react-icons": "^4.x.x",
  "@radix-ui/react-slider": "^1.x.x",
  "@radix-ui/react-select": "^2.x.x",
  "@radix-ui/react-tooltip": "^1.x.x",
  "date-fns": "^2.x.x"
}
```

---

## 🎓 Additional Resources

- **Three.js Documentation**: https://threejs.org/docs/
- **Recharts Documentation**: https://recharts.org/
- **D3.js Documentation**: https://d3js.org/
- **Framer Motion**: https://www.framer.com/motion/

---

## 💡 Tips & Tricks

### Camera Control
- **Mouse drag** to rotate in orbit mode
- **Scroll wheel** to zoom
- **Right-click drag** to pan
- Press **camera buttons** to switch modes

### Performance
- Reduce `trackWidth` in Track3DRenderer for simpler geometry
- Lower shadow map size for better FPS
- Disable post-processing effects on low-end hardware
- Use `React.memo()` for components that don't update frequently

### Customization
- Edit CSS variables in `professional-racing-theme.css`
- Modify team colors in driver data
- Adjust graph colors in component props
- Customize camera positions in Track3DRenderer

---

## 🐛 Troubleshooting

**3D track not rendering:**
- Check trackData has valid x, y, z coordinates
- Ensure container has width and height
- Check browser WebGL support

**Graphs not showing:**
- Verify data array is not empty
- Check data structure matches interface
- Ensure Recharts dependencies installed

**Performance issues:**
- Reduce number of track points (use sampling)
- Lower shadow quality
- Disable bloom effects
- Limit driver trail length

---

## 🏁 Next Steps

1. **Connect to WebSocket** - Replace mock data with real-time telemetry
2. **Add Replay Controls** - Implement pause, rewind, playback speed
3. **Export Functionality** - Allow exporting telemetry to CSV/JSON
4. **Session Recording** - Record and replay entire sessions
5. **Multi-class Support** - Color-code different car classes
6. **Weather Overlay** - Show track temperature, rain, wind
7. **Incident Detection** - Highlight crashes, off-tracks
8. **Comparative Analysis** - Compare multiple laps/drivers side-by-side

---

Built with ❤️ for iRacing enthusiasts
