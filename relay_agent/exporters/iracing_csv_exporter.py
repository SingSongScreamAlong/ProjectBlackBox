#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
iRacing Enhanced CSV Exporter
Exports complete iRacing telemetry data with 50+ fields for professional analysis
"""

import csv
import os
from datetime import datetime
from typing import List, Dict, Any, Optional


class iRacingCSVExporter:
    """
    Enhanced CSV exporter for iRacing telemetry data
    Exports 50+ fields including all tire data, incidents, flags, and session info
    """

    # CSV column definitions - complete iRacing telemetry
    TELEMETRY_COLUMNS = [
        # Time & Position
        'Timestamp', 'Lap', 'Sector', 'LapDistPct', 'LapTime', 'LapTimeRaw',

        # Speed & Motion
        'Speed', 'RPM', 'Gear', 'Throttle', 'Brake', 'Clutch', 'Steering',

        # GPS Position & Orientation
        'Lat', 'Long', 'Alt', 'X', 'Y', 'Z', 'Yaw', 'Pitch', 'Roll',

        # G-Forces
        'GForceLat', 'GForceLong', 'GForceVert',

        # Tires - Left Front (4 temp zones + pressure + wear)
        'TireTempL_LF', 'TireTempM_LF', 'TireTempR_LF', 'TireTempI_LF',
        'TirePressure_LF', 'TireWear_LF',

        # Tires - Right Front
        'TireTempL_RF', 'TireTempM_RF', 'TireTempR_RF', 'TireTempI_RF',
        'TirePressure_RF', 'TireWear_RF',

        # Tires - Left Rear
        'TireTempL_LR', 'TireTempM_LR', 'TireTempR_LR', 'TireTempI_LR',
        'TirePressure_LR', 'TireWear_LR',

        # Tires - Right Rear
        'TireTempL_RR', 'TireTempM_RR', 'TireTempR_RR', 'TireTempI_RR',
        'TirePressure_RR', 'TireWear_RR',

        # Brakes
        'BrakeTemp_LF', 'BrakeTemp_RF', 'BrakeTemp_LR', 'BrakeTemp_RR',
        'BrakePressure',

        # Engine & Fluids
        'EngineTemp', 'OilTemp', 'OilPressure', 'WaterTemp', 'WaterLevel',
        'Fuel', 'FuelUsedLap', 'FuelPressure',

        # Suspension
        'SuspensionDeflection_LF', 'SuspensionDeflection_RF',
        'SuspensionDeflection_LR', 'SuspensionDeflection_RR',
        'RideHeight_LF', 'RideHeight_RF', 'RideHeight_LR', 'RideHeight_RR',

        # Aero & Setup
        'DragCoeff', 'DownforceFront', 'DownforceRear',
        'WingAngleFront', 'WingAngleRear',

        # Track Conditions
        'TrackTemp', 'AirTemp', 'TrackWetness', 'WindSpeed', 'WindDir', 'Humidity',

        # Session State
        'OnTrack', 'InPits', 'SessionTime', 'SessionState', 'SessionFlags',

        # Relative Position
        'Position', 'ClassPosition', 'CarsInClass',
        'GapToLeader', 'GapToNext', 'GapToPrev',

        # Incidents & Warnings (iRacing-specific)
        'IncidentCount', 'IncidentPoints',
        'BlackFlag', 'BlueFlag', 'YellowFlag', 'WhiteFlag', 'CheckeredFlag',

        # iRacing Session Info
        'SOF', 'iRating', 'SafetyRating'
    ]

    # Session header information
    SESSION_HEADER_FIELDS = [
        'SessionType', 'TrackName', 'TrackConfig', 'CarName',
        'DateTime', 'DriverName', 'iRating', 'SafetyRating', 'SOF'
    ]

    def __init__(self, output_dir: str = './exports'):
        """
        Initialize the CSV exporter

        Args:
            output_dir: Directory to save exported CSV files
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
        Export a complete iRacing session to enhanced CSV format

        Args:
            session_data: Session metadata (track, car, driver, etc.)
            telemetry_samples: List of telemetry data points
            filename: Optional custom filename (auto-generated if not provided)

        Returns:
            Path to the exported CSV file
        """
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            track = session_data.get('track_name', 'unknown').replace(' ', '_')
            filename = f'iracing_telemetry_{track}_{timestamp}.csv'

        filepath = os.path.join(self.output_dir, filename)

        # Write CSV file
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # Write session header
            self._write_session_header(writer, session_data)

            # Write blank line separator
            writer.writerow([])

            # Write telemetry column headers
            writer.writerow(self.TELEMETRY_COLUMNS)

            # Write telemetry data
            for sample in telemetry_samples:
                self._write_telemetry_row(writer, sample)

        print(f"Exported {len(telemetry_samples)} telemetry samples to {filepath}")
        return filepath

    def _write_session_header(self, writer: csv.writer, session_data: Dict[str, Any]) -> None:
        """Write session metadata as header rows"""
        writer.writerow(['# iRacing Session Export - Enhanced Telemetry'])
        writer.writerow(['# Generated by BlackBox Telemetry System'])
        writer.writerow(['# Export Date/Time', datetime.now().isoformat()])
        writer.writerow([])

        # Session information
        writer.writerow(['# Session Information'])
        writer.writerow(['Session Type', session_data.get('session_type', 'Unknown')])
        writer.writerow(['Track', session_data.get('track_name', 'Unknown')])
        writer.writerow(['Configuration', session_data.get('track_config', 'Unknown')])
        writer.writerow(['Car', session_data.get('car_name', 'Unknown')])
        writer.writerow(['Date/Time', session_data.get('session_datetime', 'Unknown')])
        writer.writerow([])

        # Driver information
        writer.writerow(['# Driver Information'])
        writer.writerow(['Driver Name', session_data.get('driver_name', 'Unknown')])
        writer.writerow(['iRating', session_data.get('irating', 'N/A')])
        writer.writerow(['Safety Rating', session_data.get('safety_rating', 'N/A')])
        writer.writerow(['Strength of Field', session_data.get('sof', 'N/A')])
        writer.writerow([])

        # Session results
        writer.writerow(['# Session Results'])
        writer.writerow(['Best Lap Time', session_data.get('best_lap_time', 'N/A')])
        writer.writerow(['Total Laps', session_data.get('total_laps', 'N/A')])
        writer.writerow(['Total Incidents', session_data.get('total_incidents', 'N/A')])
        writer.writerow(['Finish Position', session_data.get('finish_position', 'N/A')])

    def _write_telemetry_row(self, writer: csv.writer, sample: Dict[str, Any]) -> None:
        """
        Write a single telemetry sample as a CSV row

        Args:
            writer: CSV writer object
            sample: Telemetry data sample
        """
        row = []

        for column in self.TELEMETRY_COLUMNS:
            # Map column name to data field
            # Handle different naming conventions
            value = self._extract_value(sample, column)
            row.append(value)

        writer.writerow(row)

    def _extract_value(self, sample: Dict[str, Any], column: str) -> Any:
        """
        Extract value from telemetry sample, handling various field name formats

        Args:
            sample: Telemetry data sample
            column: Column name to extract

        Returns:
            Value for the column, or empty string if not found
        """
        # Try exact match first
        if column in sample:
            return sample[column]

        # Try lowercase
        column_lower = column.lower()
        if column_lower in sample:
            return sample[column_lower]

        # Try snake_case conversion
        column_snake = self._to_snake_case(column)
        if column_snake in sample:
            return sample[column_snake]

        # Handle nested data structures
        if '.' in column:
            parts = column.split('.')
            value = sample
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return ''
            return value

        # Handle special cases
        if column.startswith('TireTemp') or column.startswith('TirePressure') or column.startswith('TireWear'):
            return self._extract_tire_data(sample, column)

        if column.startswith('BrakeTemp'):
            return self._extract_brake_data(sample, column)

        if column.endswith('Flag'):
            return self._extract_flag_data(sample, column)

        # Return empty string if not found
        return ''

    def _extract_tire_data(self, sample: Dict[str, Any], column: str) -> Any:
        """Extract tire-specific data from various formats"""
        # Parse column name: TireTempL_LF -> tire temp, left zone, left front
        if 'tires' in sample:
            tires = sample['tires']
            # Extract corner (LF, RF, LR, RR)
            corner = column.split('_')[-1]  # LF, RF, LR, RR

            if corner in tires:
                tire = tires[corner]

                # Extract measurement type
                if 'TireTemp' in column:
                    if 'temperature' in tire:
                        temps = tire['temperature']
                        if 'L' in column:
                            return temps.get('left', '')
                        elif 'M' in column:
                            return temps.get('middle', '')
                        elif 'R' in column:
                            return temps.get('right', '')
                        elif 'I' in column:
                            return temps.get('inner', '')
                elif 'TirePressure' in column:
                    return tire.get('pressure', '')
                elif 'TireWear' in column:
                    return tire.get('wear', '')

        return ''

    def _extract_brake_data(self, sample: Dict[str, Any], column: str) -> Any:
        """Extract brake temperature data"""
        if 'brakes' in sample:
            corner = column.split('_')[-1]
            return sample['brakes'].get(corner, {}).get('temperature', '')
        return ''

    def _extract_flag_data(self, sample: Dict[str, Any], column: str) -> Any:
        """Extract flag state data"""
        if 'flags' in sample:
            flag_name = column.replace('Flag', '').lower()
            return 1 if sample['flags'].get(flag_name, False) else 0
        return 0

    @staticmethod
    def _to_snake_case(text: str) -> str:
        """Convert CamelCase to snake_case"""
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


# Example usage
if __name__ == "__main__":
    # Example session data
    session_data = {
        'session_type': 'Race',
        'track_name': 'Road Atlanta',
        'track_config': 'Full Course',
        'car_name': 'BMW M4 GT3',
        'session_datetime': '2025-11-29 14:30:00',
        'driver_name': 'John Doe',
        'irating': 2450,
        'safety_rating': 'A 4.2',
        'sof': 2850,
        'best_lap_time': '1:22.431',
        'total_laps': 15,
        'total_incidents': 2,
        'finish_position': 3
    }

    # Example telemetry sample
    telemetry_samples = [
        {
            'Timestamp': 1000.123,
            'Lap': 1,
            'Speed': 185.5,
            'RPM': 7200,
            'Gear': 4,
            'Throttle': 0.85,
            'Brake': 0.0,
            # ... (would include all 100+ fields in real data)
        }
    ]

    # Export
    exporter = iRacingCSVExporter(output_dir='./telemetry_exports')
    filepath = exporter.export_session(session_data, telemetry_samples)
    print(f"CSV exported to: {filepath}")
