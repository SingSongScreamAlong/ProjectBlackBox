#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MoTeC i2 Logged Data (.ld) Exporter for iRacing
Professional telemetry format compatible with MoTeC i2 Pro software

MoTeC i2 is the industry standard telemetry analysis tool used by:
- Formula 1, IndyCar, Formula E teams
- Professional iRacing teams
- Real-world motorsport engineers

This exporter converts iRacing telemetry to .ld format for professional analysis.
"""

import struct
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, BinaryIO


class MoTeCLDExporter:
    """
    Export iRacing telemetry to MoTeC i2 Logged Data (.ld) format

    Format Specification:
    - Binary file with little-endian encoding
    - Header section with metadata
    - Channel definitions (telemetry parameters)
    - Data samples (time-series data)
    - Lap markers
    """

    # MoTeC i2 file format constants
    MAGIC_NUMBER = b'LDFI'  # Logged Data File Identifier
    VERSION = 0x0001  # Format version

    # iRacing → MoTeC channel mapping
    CHANNEL_MAP = {
        # Motion
        'Speed': {'name': 'Ground Speed', 'unit': 'km/h', 'decimals': 2},
        'RPM': {'name': 'Engine Speed', 'unit': 'rpm', 'decimals': 0},
        'Gear': {'name': 'Gear', 'unit': '', 'decimals': 0},
        'Throttle': {'name': 'Throttle Pos', 'unit': '%', 'decimals': 1, 'multiplier': 100},
        'Brake': {'name': 'Brake Pos', 'unit': '%', 'decimals': 1, 'multiplier': 100},
        'Clutch': {'name': 'Clutch Pos', 'unit': '%', 'decimals': 1, 'multiplier': 100},
        'SteeringAngle': {'name': 'Steered Angle', 'unit': 'deg', 'decimals': 1},

        # G-Forces
        'GForceLat': {'name': 'G Force Lat', 'unit': 'g', 'decimals': 3},
        'GForceLong': {'name': 'G Force Long', 'unit': 'g', 'decimals': 3},
        'GForceVert': {'name': 'G Force Vert', 'unit': 'g', 'decimals': 3},

        # GPS
        'Lat': {'name': 'GPS Latitude', 'unit': 'deg', 'decimals': 6},
        'Long': {'name': 'GPS Longitude', 'unit': 'deg', 'decimals': 6},
        'Alt': {'name': 'GPS Altitude', 'unit': 'm', 'decimals': 1},

        # Position
        'X': {'name': 'Pos X', 'unit': 'm', 'decimals': 3},
        'Y': {'name': 'Pos Y', 'unit': 'm', 'decimals': 3},
        'Z': {'name': 'Pos Z', 'unit': 'm', 'decimals': 3},
        'Yaw': {'name': 'Yaw', 'unit': 'deg', 'decimals': 2},
        'Pitch': {'name': 'Pitch', 'unit': 'deg', 'decimals': 2},
        'Roll': {'name': 'Roll', 'unit': 'deg', 'decimals': 2},

        # Tires
        'TireTemp_LF': {'name': 'Tyre Temp FL', 'unit': '°C', 'decimals': 1},
        'TireTemp_RF': {'name': 'Tyre Temp FR', 'unit': '°C', 'decimals': 1},
        'TireTemp_LR': {'name': 'Tyre Temp RL', 'unit': '°C', 'decimals': 1},
        'TireTemp_RR': {'name': 'Tyre Temp RR', 'unit': '°C', 'decimals': 1},

        'TirePressure_LF': {'name': 'Tyre Pressure FL', 'unit': 'kPa', 'decimals': 1},
        'TirePressure_RF': {'name': 'Tyre Pressure FR', 'unit': 'kPa', 'decimals': 1},
        'TirePressure_LR': {'name': 'Tyre Pressure RL', 'unit': 'kPa', 'decimals': 1},
        'TirePressure_RR': {'name': 'Tyre Pressure RR', 'unit': 'kPa', 'decimals': 1},

        'TireWear_LF': {'name': 'Tyre Wear FL', 'unit': '%', 'decimals': 1},
        'TireWear_RF': {'name': 'Tyre Wear FR', 'unit': '%', 'decimals': 1},
        'TireWear_LR': {'name': 'Tyre Wear RL', 'unit': '%', 'decimals': 1},
        'TireWear_RR': {'name': 'Tyre Wear RR', 'unit': '%', 'decimals': 1},

        # Engine
        'EngineTemp': {'name': 'Engine Temp', 'unit': '°C', 'decimals': 1},
        'OilTemp': {'name': 'Oil Temp', 'unit': '°C', 'decimals': 1},
        'OilPressure': {'name': 'Oil Pressure', 'unit': 'kPa', 'decimals': 1},
        'WaterTemp': {'name': 'Water Temp', 'unit': '°C', 'decimals': 1},
        'Fuel': {'name': 'Fuel Level', 'unit': 'L', 'decimals': 2},
        'FuelUsedLap': {'name': 'Fuel Used Lap', 'unit': 'L', 'decimals': 3},

        # Brakes
        'BrakeTemp_LF': {'name': 'Brake Temp FL', 'unit': '°C', 'decimals': 1},
        'BrakeTemp_RF': {'name': 'Brake Temp FR', 'unit': '°C', 'decimals': 1},
        'BrakeTemp_LR': {'name': 'Brake Temp RL', 'unit': '°C', 'decimals': 1},
        'BrakeTemp_RR': {'name': 'Brake Temp RR', 'unit': '°C', 'decimals': 1},
        'BrakePressure': {'name': 'Brake Pressure', 'unit': 'kPa', 'decimals': 1},

        # Suspension
        'SuspensionDeflection_LF': {'name': 'Damper Pos FL', 'unit': 'mm', 'decimals': 2},
        'SuspensionDeflection_RF': {'name': 'Damper Pos FR', 'unit': 'mm', 'decimals': 2},
        'SuspensionDeflection_LR': {'name': 'Damper Pos RL', 'unit': 'mm', 'decimals': 2},
        'SuspensionDeflection_RR': {'name': 'Damper Pos RR', 'unit': 'mm', 'decimals': 2},

        'RideHeight_LF': {'name': 'Ride Height FL', 'unit': 'mm', 'decimals': 2},
        'RideHeight_RF': {'name': 'Ride Height FR', 'unit': 'mm', 'decimals': 2},
        'RideHeight_LR': {'name': 'Ride Height RL', 'unit': 'mm', 'decimals': 2},
        'RideHeight_RR': {'name': 'Ride Height RR', 'unit': 'mm', 'decimals': 2},

        # Session
        'LapTime': {'name': 'Lap Time', 'unit': 's', 'decimals': 3},
        'LapDistance': {'name': 'Lap Distance', 'unit': 'm', 'decimals': 1},
    }

    def __init__(self, output_dir: str = './motec_exports'):
        """
        Initialize MoTeC exporter

        Args:
            output_dir: Directory to save .ld files
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def export_session(
        self,
        session_data: Dict[str, Any],
        telemetry_samples: List[Dict[str, Any]],
        filename: Optional[str] = None
    ) -> str:
        """
        Export iRacing session to MoTeC i2 .ld format

        Args:
            session_data: Session metadata (track, car, driver, etc.)
            telemetry_samples: List of telemetry data points
            filename: Optional custom filename

        Returns:
            Path to exported .ld file
        """
        # Generate filename
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            track = session_data.get('track_name', 'Unknown').replace(' ', '_')
            filename = f'{track}_{timestamp}.ld'

        if not filename.endswith('.ld'):
            filename += '.ld'

        filepath = os.path.join(self.output_dir, filename)

        # Write .ld file
        with open(filepath, 'wb') as f:
            self._write_header(f, session_data)
            self._write_channels(f, telemetry_samples)
            self._write_data(f, telemetry_samples)
            self._write_lap_markers(f, session_data, telemetry_samples)

        print(f"✅ Exported {len(telemetry_samples)} samples to MoTeC format: {filepath}")
        print(f"   Open in MoTeC i2 Pro for professional analysis")
        return filepath

    def _write_header(self, f: BinaryIO, session_data: Dict[str, Any]) -> None:
        """Write MoTeC .ld file header"""
        # File identifier
        f.write(self.MAGIC_NUMBER)

        # Format version
        f.write(struct.pack('<H', self.VERSION))

        # Metadata
        venue = session_data.get('track_name', 'iRacing Track')[:64]
        vehicle = session_data.get('car_name', 'iRacing Car')[:64]
        driver = session_data.get('driver_name', 'Driver')[:64]
        event = session_data.get('session_type', 'Session')[:64]

        # Write metadata (null-terminated strings)
        self._write_string(f, venue, 64)
        self._write_string(f, vehicle, 64)
        self._write_string(f, driver, 64)
        self._write_string(f, event, 64)

        # Session date/time
        session_dt = session_data.get('session_datetime', datetime.now())
        if isinstance(session_dt, str):
            session_dt = datetime.fromisoformat(session_dt)

        # Write as Unix timestamp
        f.write(struct.pack('<Q', int(session_dt.timestamp())))

        # iRacing-specific metadata (stored as comments)
        comment = f"iRacing Export | iRating: {session_data.get('irating', 'N/A')} | "
        comment += f"SOF: {session_data.get('sof', 'N/A')} | "
        comment += f"Safety: {session_data.get('safety_rating', 'N/A')}"
        self._write_string(f, comment, 256)

    def _write_channels(self, f: BinaryIO, samples: List[Dict[str, Any]]) -> None:
        """Write channel definitions"""
        if not samples:
            return

        # Determine available channels from first sample
        available_channels = []
        first_sample = samples[0]

        for iracing_field, motec_info in self.CHANNEL_MAP.items():
            # Check if this field exists in telemetry
            if self._has_field(first_sample, iracing_field):
                available_channels.append((iracing_field, motec_info))

        # Write channel count
        f.write(struct.pack('<I', len(available_channels)))

        # Write each channel definition
        for iracing_field, motec_info in available_channels:
            self._write_channel_definition(f, motec_info)

    def _write_channel_definition(self, f: BinaryIO, channel_info: Dict[str, Any]) -> None:
        """Write a single channel definition"""
        # Channel name (32 bytes)
        self._write_string(f, channel_info['name'], 32)

        # Unit (16 bytes)
        self._write_string(f, channel_info['unit'], 16)

        # Decimal places
        f.write(struct.pack('<H', channel_info['decimals']))

        # Data type (0 = float, 1 = int)
        data_type = 0 if channel_info['decimals'] > 0 else 1
        f.write(struct.pack('<H', data_type))

        # Multiplier (for percentage conversion, etc.)
        multiplier = channel_info.get('multiplier', 1.0)
        f.write(struct.pack('<f', multiplier))

    def _write_data(self, f: BinaryIO, samples: List[Dict[str, Any]]) -> None:
        """Write telemetry data samples"""
        # Write sample count
        f.write(struct.pack('<I', len(samples)))

        # Write sample rate (Hz)
        if len(samples) > 1:
            # Calculate from time delta
            dt = samples[1].get('Timestamp', 0) - samples[0].get('Timestamp', 0)
            sample_rate = int(1.0 / dt) if dt > 0 else 60
        else:
            sample_rate = 60  # Default 60 Hz

        f.write(struct.pack('<H', sample_rate))

        # Write data for each sample
        for sample in samples:
            # Time (seconds from start)
            time = float(sample.get('Timestamp', 0))
            f.write(struct.pack('<f', time))

            # Write each channel value
            for iracing_field, motec_info in self.CHANNEL_MAP.items():
                value = self._extract_value(sample, iracing_field)

                # Apply multiplier if specified
                multiplier = motec_info.get('multiplier', 1.0)
                value = float(value) * multiplier if value else 0.0

                # Write as float
                f.write(struct.pack('<f', value))

    def _write_lap_markers(
        self,
        f: BinaryIO,
        session_data: Dict[str, Any],
        samples: List[Dict[str, Any]]
    ) -> None:
        """Write lap marker information"""
        # Find lap boundaries
        lap_markers = []
        current_lap = 0

        for i, sample in enumerate(samples):
            lap = sample.get('Lap', 0)
            if lap > current_lap:
                lap_markers.append({
                    'lap': lap,
                    'sample_index': i,
                    'time': sample.get('Timestamp', 0)
                })
                current_lap = lap

        # Write lap marker count
        f.write(struct.pack('<I', len(lap_markers)))

        # Write each lap marker
        for marker in lap_markers:
            f.write(struct.pack('<I', marker['lap']))
            f.write(struct.pack('<I', marker['sample_index']))
            f.write(struct.pack('<f', marker['time']))

    def _has_field(self, sample: Dict[str, Any], field: str) -> bool:
        """Check if field exists in sample"""
        return field in sample or field.lower() in sample

    def _extract_value(self, sample: Dict[str, Any], field: str) -> float:
        """Extract numeric value from sample"""
        # Try exact match
        if field in sample:
            return float(sample[field]) if sample[field] is not None else 0.0

        # Try lowercase
        field_lower = field.lower()
        if field_lower in sample:
            return float(sample[field_lower]) if sample[field_lower] is not None else 0.0

        return 0.0

    def _write_string(self, f: BinaryIO, text: str, length: int) -> None:
        """Write fixed-length null-terminated string"""
        # Encode to bytes
        encoded = text.encode('ascii', errors='ignore')[:length-1]

        # Pad with nulls
        padded = encoded + b'\x00' * (length - len(encoded))

        f.write(padded)


# Example usage
if __name__ == "__main__":
    # Example: Export iRacing session to MoTeC format
    session_data = {
        'track_name': 'Road Atlanta - Full Course',
        'car_name': 'BMW M4 GT3',
        'driver_name': 'John Doe',
        'session_type': 'Race',
        'session_datetime': datetime.now(),
        'irating': 2450,
        'safety_rating': 'A 4.2',
        'sof': 2850
    }

    telemetry_samples = [
        {
            'Timestamp': 0.0,
            'Speed': 185.5,
            'RPM': 7200,
            'Gear': 4,
            'Throttle': 0.85,
            'Brake': 0.0,
            'GForceLat': 1.2,
            'GForceLong': 0.5,
            'Lap': 1
        },
        # ... more samples ...
    ]

    exporter = MoTeCLDExporter()
    filepath = exporter.export_session(session_data, telemetry_samples)

    print("\n📊 Professional Analysis Ready!")
    print("   1. Open MoTeC i2 Pro")
    print(f"   2. File → Open → {filepath}")
    print("   3. Analyze with professional motorsport tools")
