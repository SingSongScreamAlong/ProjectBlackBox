"""
Live Mini-Map Visualization System
Real-time track position overlay with car positions, gaps, and racing line
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json


@dataclass
class CarPosition:
    """Car position on track"""
    car_idx: int
    driver_name: str
    car_number: str
    car_class: str
    position: int
    lap: int
    lap_pct: float
    x: float
    y: float
    z: float
    speed: float
    on_track: bool
    in_pit: bool
    gap_to_leader: float
    gap_to_ahead: float
    is_player: bool


class MiniMapGenerator:
    """Generates real-time mini-map visualization data"""

    def __init__(self, track_data: Dict = None):
        self.track_data = track_data or {}
        self.track_bounds = None
        self.scale_factor = 1.0
        self.canvas_width = 400
        self.canvas_height = 400

    def set_track_bounds(self, positions: List[Tuple[float, float]]):
        """Calculate track bounds from position data"""
        if not positions:
            return

        xs = [p[0] for p in positions]
        ys = [p[1] for p in positions]

        self.track_bounds = {
            'min_x': min(xs),
            'max_x': max(xs),
            'min_y': min(ys),
            'max_y': max(ys)
        }

        # Calculate scale to fit canvas
        track_width = self.track_bounds['max_x'] - self.track_bounds['min_x']
        track_height = self.track_bounds['max_y'] - self.track_bounds['min_y']

        scale_x = self.canvas_width / track_width if track_width > 0 else 1
        scale_y = self.canvas_height / track_height if track_height > 0 else 1

        self.scale_factor = min(scale_x, scale_y) * 0.9  # 90% to add margin

    def world_to_canvas(self, x: float, y: float) -> Tuple[int, int]:
        """Convert world coordinates to canvas coordinates"""
        if not self.track_bounds:
            return (200, 200)

        # Translate to origin
        rel_x = x - self.track_bounds['min_x']
        rel_y = y - self.track_bounds['min_y']

        # Scale and add margin
        canvas_x = int(rel_x * self.scale_factor + 20)
        canvas_y = int(self.canvas_height - (rel_y * self.scale_factor + 20))

        return (canvas_x, canvas_y)

    def generate_mini_map_data(self, car_positions: List[CarPosition], track_path: List[Tuple[float, float]] = None) -> Dict:
        """Generate complete mini-map data for visualization"""

        # Ensure bounds are set
        if track_path and not self.track_bounds:
            self.set_track_bounds(track_path)

        # Convert car positions to canvas coordinates
        cars_on_map = []
        for car in car_positions:
            if not car.on_track or car.in_pit:
                continue

            canvas_x, canvas_y = self.world_to_canvas(car.x, car.y)

            cars_on_map.append({
                'carIdx': car.car_idx,
                'driverName': car.driver_name,
                'carNumber': car.car_number,
                'carClass': car.car_class,
                'position': car.position,
                'lap': car.lap,
                'lapPct': car.lap_pct,
                'x': canvas_x,
                'y': canvas_y,
                'speed': car.speed,
                'gapToLeader': car.gap_to_leader,
                'gapToAhead': car.gap_to_ahead,
                'isPlayer': car.is_player,
                'color': self._get_car_color(car)
            })

        # Convert track path to canvas
        track_line = []
        if track_path:
            for x, y in track_path:
                canvas_x, canvas_y = self.world_to_canvas(x, y)
                track_line.append({'x': canvas_x, 'y': canvas_y})

        return {
            'cars': cars_on_map,
            'trackLine': track_line,
            'canvasWidth': self.canvas_width,
            'canvasHeight': self.canvas_height,
            'trackBounds': self.track_bounds,
            'scaleFactor': self.scale_factor
        }

    def _get_car_color(self, car: CarPosition) -> str:
        """Get color for car based on class and status"""
        if car.is_player:
            return '#00FF00'  # Green for player

        # Color by class
        class_colors = {
            'GT3': '#FF4444',
            'GTE': '#4444FF',
            'LMP2': '#FFAA00',
            'LMP1': '#FF00FF',
            'Formula': '#00FFFF',
            'NASCAR': '#FFFF00',
            'IndyCar': '#FF8800'
        }

        for class_name, color in class_colors.items():
            if class_name.lower() in car.car_class.lower():
                return color

        return '#FFFFFF'  # White default

    def generate_sector_map(self, sector_definitions: List[Dict]) -> Dict:
        """Generate sector overlay for mini-map"""
        sectors = []

        for i, sector in enumerate(sector_definitions):
            start_pct = sector.get('start_pct', 0)
            end_pct = sector.get('end_pct', 0)

            sectors.append({
                'number': i + 1,
                'startPct': start_pct,
                'endPct': end_pct,
                'color': f'rgba(255, 255, 255, 0.{i+1})'
            })

        return {'sectors': sectors}

    def generate_flag_zones(self, flag_data: Dict) -> Dict:
        """Generate flag zone overlays"""
        zones = []

        if flag_data.get('yellow_sector'):
            zones.append({
                'type': 'yellow',
                'sector': flag_data['yellow_sector'],
                'color': 'rgba(255, 255, 0, 0.3)'
            })

        if flag_data.get('debris_location'):
            zones.append({
                'type': 'debris',
                'location': flag_data['debris_location'],
                'color': 'rgba(255, 100, 0, 0.5)'
            })

        return {'flagZones': zones}


def create_svg_mini_map(map_data: Dict) -> str:
    """Create SVG mini-map from map data"""
    width = map_data['canvasWidth']
    height = map_data['canvasHeight']

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
    <!-- Background -->
    <rect width="{width}" height="{height}" fill="#1a1a1a"/>

    <!-- Track Line -->
    <path d="'''

    # Add track path
    if map_data['trackLine']:
        svg += f"M {map_data['trackLine'][0]['x']} {map_data['trackLine'][0]['y']} "
        for point in map_data['trackLine'][1:]:
            svg += f"L {point['x']} {point['y']} "

    svg += '''" stroke="#444444" stroke-width="3" fill="none"/>

    <!-- Cars -->'''

    # Add cars
    for car in map_data['cars']:
        svg += f'''
    <circle cx="{car['x']}" cy="{car['y']}" r="6" fill="{car['color']}" stroke="#000000" stroke-width="1"/>
    <text x="{car['x']}" y="{car['y']-10}" fill="{car['color']}" font-size="10" text-anchor="middle">{car['carNumber']}</text>'''

    svg += '''
</svg>'''

    return svg


if __name__ == '__main__':
    print("Mini-Map Visualization System Test")
    print("=" * 70)

    # Test data
    track_path = [(0, 0), (100, 50), (200, 100), (250, 200), (200, 300), (100, 350), (0, 300), (0, 0)]

    cars = [
        CarPosition(0, "Player", "1", "GT3", 1, 5, 0.25, 50, 100, 0, 150, True, False, 0, 0, True),
        CarPosition(1, "Rival", "2", "GT3", 2, 5, 0.20, 25, 75, 0, 145, True, False, 2.5, 2.5, False),
        CarPosition(2, "Opponent", "3", "GT3", 3, 5, 0.15, 10, 50, 0, 140, True, False, 5.0, 2.5, False)
    ]

    generator = MiniMapGenerator()
    generator.set_track_bounds(track_path)

    map_data = generator.generate_mini_map_data(cars, track_path)

    print(f"✓ Generated mini-map with {len(map_data['cars'])} cars")
    print(f"  Track bounds: {map_data['trackBounds']}")
    print(f"  Scale factor: {map_data['scaleFactor']:.2f}")

    svg = create_svg_mini_map(map_data)
    print(f"✓ Generated SVG: {len(svg)} characters")

    print("\n" + "=" * 70)
    print("✓ Mini-map system ready")
