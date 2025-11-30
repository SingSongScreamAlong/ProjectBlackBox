"""
Position Data Calibrator
Improves positional accuracy through calibration and filtering
"""

import numpy as np
from typing import List, Dict, Tuple
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PositionCalibrator:
    """Calibrate and improve position data accuracy"""

    def __init__(self):
        self.calibration_data = {}

    def calibrate_from_telemetry(self, telemetry_data: List[Dict]) -> Dict:
        """
        Analyze telemetry to calibrate position data

        Args:
            telemetry_data: List of telemetry samples with position data

        Returns:
            Calibration parameters for improving position accuracy
        """
        logger.info(f"Calibrating position data from {len(telemetry_data)} samples...")

        # Extract positions
        positions = [(s.get('pos_x', 0), s.get('pos_y', 0), s.get('pos_z', 0))
                    for s in telemetry_data]

        raw_positions = [(s.get('pos_x_raw', 0), s.get('pos_y_raw', 0), s.get('pos_z_raw', 0))
                        for s in telemetry_data]

        # Calculate track bounds
        x_coords = [p[0] for p in positions]
        y_coords = [p[1] for p in positions]
        z_coords = [p[2] for p in positions]

        calibration = {
            'bounds': {
                'x_min': float(np.min(x_coords)),
                'x_max': float(np.max(x_coords)),
                'y_min': float(np.min(y_coords)),
                'y_max': float(np.max(y_coords)),
                'z_min': float(np.min(z_coords)),
                'z_max': float(np.max(z_coords)),
            },
            'center': {
                'x': float(np.mean(x_coords)),
                'y': float(np.mean(y_coords)),
                'z': float(np.mean(z_coords)),
            },
            'scale': {
                'x': float(np.max(x_coords) - np.min(x_coords)),
                'y': float(np.max(y_coords) - np.min(y_coords)),
                'z': float(np.max(z_coords) - np.min(z_coords)),
            },
            'track_dimensions': self._calculate_track_dimensions(positions),
            'position_quality': self._assess_position_quality(positions, raw_positions),
            'recommended_smoothing': self._recommend_smoothing(positions, raw_positions)
        }

        logger.info(f"✓ Calibration complete:")
        logger.info(f"  Track dimensions: {calibration['track_dimensions']['width']:.1f}m × {calibration['track_dimensions']['length']:.1f}m")
        logger.info(f"  Position quality: {calibration['position_quality']['score']:.2f}/1.00")
        logger.info(f"  Recommended smoothing: {calibration['recommended_smoothing']['window_size']} samples")

        return calibration

    def _calculate_track_dimensions(self, positions: List[Tuple]) -> Dict:
        """Calculate real-world track dimensions"""
        x_coords = [p[0] for p in positions]
        y_coords = [p[1] for p in positions]

        width = max(x_coords) - min(x_coords)
        length = max(y_coords) - min(y_coords)

        # Calculate approximate track area (convex hull would be more accurate)
        area = width * length

        return {
            'width': float(width),
            'length': float(length),
            'area': float(area),
            'aspect_ratio': float(length / width) if width > 0 else 1.0
        }

    def _assess_position_quality(self, smoothed: List[Tuple], raw: List[Tuple]) -> Dict:
        """Assess quality of position data"""
        if not smoothed or not raw:
            return {'score': 0.0, 'issues': ['No position data']}

        issues = []
        score = 1.0

        # Check for zero positions (indicates missing data)
        zero_count = sum(1 for p in raw if p[0] == 0 and p[1] == 0)
        if zero_count > len(raw) * 0.1:
            issues.append(f'{zero_count} samples have zero position (missing data)')
            score -= 0.3

        # Check for position jumps (teleportation detection)
        jumps = 0
        for i in range(1, len(raw)):
            dist = np.sqrt(
                (raw[i][0] - raw[i-1][0])**2 +
                (raw[i][1] - raw[i-1][1])**2
            )
            # If car "teleports" more than 100m between samples (at 10Hz)
            if dist > 100:
                jumps += 1

        if jumps > 0:
            issues.append(f'{jumps} position jumps detected')
            score -= min(0.4, jumps / len(raw))

        # Check smoothing effectiveness
        raw_variance = np.var([p[0] for p in raw])
        smooth_variance = np.var([p[0] for p in smoothed])

        if raw_variance > 0:
            smoothing_factor = 1 - (smooth_variance / raw_variance)
            if smoothing_factor < 0.1:
                issues.append('Minimal smoothing applied - data may be noisy')
                score -= 0.1

        if not issues:
            issues.append('Position data quality is excellent')

        return {
            'score': max(0.0, score),
            'issues': issues,
            'zero_positions': zero_count,
            'position_jumps': jumps,
            'smoothing_effectiveness': float(smoothing_factor) if raw_variance > 0 else 0.0
        }

    def _recommend_smoothing(self, smoothed: List[Tuple], raw: List[Tuple]) -> Dict:
        """Recommend optimal smoothing parameters"""
        if not raw:
            return {'window_size': 5, 'method': 'moving_average'}

        # Calculate position noise level
        if len(raw) > 10:
            diffs = [
                np.sqrt((raw[i][0] - raw[i-1][0])**2 + (raw[i][1] - raw[i-1][1])**2)
                for i in range(1, len(raw))
            ]
            noise_level = np.std(diffs)

            # Recommend window size based on noise
            if noise_level > 10:  # High noise
                window_size = 10
                method = 'gaussian'
            elif noise_level > 5:  # Medium noise
                window_size = 7
                method = 'moving_average'
            else:  # Low noise
                window_size = 3
                method = 'moving_average'
        else:
            window_size = 5
            method = 'moving_average'

        return {
            'window_size': window_size,
            'method': method,
            'noise_level': float(noise_level) if 'noise_level' in locals() else 0.0
        }

    def apply_kalman_filter(self, positions: List[Tuple]) -> List[Tuple]:
        """Apply Kalman filtering for superior position accuracy"""
        if not positions:
            return []

        logger.info("Applying Kalman filter to position data...")

        # Simple 1D Kalman filter per axis
        filtered = []

        for axis in range(3):  # X, Y, Z
            values = [p[axis] for p in positions]

            # Kalman filter parameters
            process_variance = 1e-5  # How much we trust the model
            measurement_variance = 0.1  # How much we trust the measurements

            # Initial estimates
            estimated_value = values[0]
            estimated_error = 1.0

            filtered_values = []

            for measurement in values:
                # Prediction
                predicted_value = estimated_value
                predicted_error = estimated_error + process_variance

                # Update
                kalman_gain = predicted_error / (predicted_error + measurement_variance)
                estimated_value = predicted_value + kalman_gain * (measurement - predicted_value)
                estimated_error = (1 - kalman_gain) * predicted_error

                filtered_values.append(estimated_value)

            # Store filtered axis
            if axis == 0:
                filtered = [(v, 0, 0) for v in filtered_values]
            elif axis == 1:
                filtered = [(filtered[i][0], v, filtered[i][2])
                           for i, v in enumerate(filtered_values)]
            else:  # axis == 2
                filtered = [(filtered[i][0], filtered[i][1], v)
                           for i, v in enumerate(filtered_values)]

        logger.info(f"✓ Kalman filter applied to {len(filtered)} positions")
        return filtered

    def normalize_to_track(self, positions: List[Tuple], target_width: float = 1000,
                          target_height: float = 1000) -> List[Tuple]:
        """Normalize positions to standard coordinate system"""
        if not positions:
            return []

        x_coords = [p[0] for p in positions]
        y_coords = [p[1] for p in positions]

        x_min, x_max = min(x_coords), max(x_coords)
        y_min, y_max = min(y_coords), max(y_coords)

        x_range = x_max - x_min
        y_range = y_max - y_min

        # Normalize to target dimensions while preserving aspect ratio
        scale = min(target_width / x_range, target_height / y_range) if x_range > 0 and y_range > 0 else 1.0

        normalized = [
            (
                (p[0] - x_min) * scale,
                (p[1] - y_min) * scale,
                p[2]  # Keep Z as-is (elevation)
            )
            for p in positions
        ]

        return normalized

    def validate_position_accuracy(self, telemetry: List[Dict]) -> Dict:
        """Validate position data accuracy against known constraints"""
        positions = [(s.get('pos_x', 0), s.get('pos_y', 0), s.get('pos_z', 0))
                    for s in telemetry]
        distances = [s.get('distance', 0) for s in telemetry]
        speeds = [s.get('speed', 0) for s in telemetry]

        validation = {
            'position_continuity': self._check_continuity(positions),
            'speed_position_correlation': self._check_speed_correlation(positions, speeds, distances),
            'track_closure': self._check_track_closure(positions),
            'elevation_profile': self._analyze_elevation(positions)
        }

        # Overall validity score
        validity_score = (
            validation['position_continuity']['score'] * 0.4 +
            validation['speed_position_correlation']['score'] * 0.3 +
            validation['track_closure']['score'] * 0.2 +
            validation['elevation_profile']['score'] * 0.1
        )

        validation['overall_validity'] = validity_score
        validation['valid'] = validity_score > 0.7

        return validation

    def _check_continuity(self, positions: List[Tuple]) -> Dict:
        """Check if positions form a continuous path"""
        if len(positions) < 2:
            return {'score': 0.0, 'reason': 'Insufficient data'}

        # Calculate distances between consecutive points
        distances = []
        for i in range(1, len(positions)):
            dist = np.sqrt(
                (positions[i][0] - positions[i-1][0])**2 +
                (positions[i][1] - positions[i-1][1])**2
            )
            distances.append(dist)

        avg_dist = np.mean(distances)
        std_dist = np.std(distances)

        # Check for outliers (position jumps)
        outliers = sum(1 for d in distances if d > avg_dist + 3 * std_dist)
        outlier_ratio = outliers / len(distances)

        score = max(0.0, 1.0 - outlier_ratio * 5)

        return {
            'score': score,
            'avg_distance': float(avg_dist),
            'std_distance': float(std_dist),
            'outliers': outliers,
            'outlier_ratio': float(outlier_ratio)
        }

    def _check_speed_correlation(self, positions: List[Tuple], speeds: List[float],
                                distances: List[float]) -> Dict:
        """Verify position changes correlate with speed"""
        if len(positions) < 2 or len(speeds) < 2:
            return {'score': 0.5, 'reason': 'Insufficient data'}

        # Calculate position-based speed
        dt = 0.1  # 10Hz sampling
        position_speeds = []
        for i in range(1, len(positions)):
            dist = np.sqrt(
                (positions[i][0] - positions[i-1][0])**2 +
                (positions[i][1] - positions[i-1][1])**2
            )
            speed = (dist / dt) * 3.6  # Convert to km/h
            position_speeds.append(speed)

        # Compare with reported speeds
        if len(position_speeds) == len(speeds) - 1:
            correlation = np.corrcoef(position_speeds, speeds[1:])[0, 1]
            score = max(0.0, min(1.0, correlation))
        else:
            score = 0.5

        return {
            'score': score,
            'correlation': float(correlation) if 'correlation' in locals() else 0.0
        }

    def _check_track_closure(self, positions: List[Tuple]) -> Dict:
        """Check if track forms a closed loop"""
        if len(positions) < 10:
            return {'score': 0.0, 'reason': 'Insufficient data'}

        # Distance between start and end
        closure_distance = np.sqrt(
            (positions[-1][0] - positions[0][0])**2 +
            (positions[-1][1] - positions[0][1])**2
        )

        # Track perimeter
        total_length = sum(
            np.sqrt((positions[i][0] - positions[i-1][0])**2 +
                   (positions[i][1] - positions[i-1][1])**2)
            for i in range(1, len(positions))
        )

        # Closure ratio (should be small for good tracks)
        closure_ratio = closure_distance / total_length if total_length > 0 else 1.0

        # Score: 1.0 if perfectly closed, 0.0 if completely open
        score = max(0.0, 1.0 - closure_ratio * 10)

        return {
            'score': score,
            'closure_distance': float(closure_distance),
            'total_length': float(total_length),
            'closure_ratio': float(closure_ratio)
        }

    def _analyze_elevation(self, positions: List[Tuple]) -> Dict:
        """Analyze elevation profile"""
        z_coords = [p[2] for p in positions]

        if not z_coords:
            return {'score': 0.5}

        z_range = max(z_coords) - min(z_coords)

        # Reasonable elevation change for a track (most tracks < 200m)
        if z_range < 200:
            score = 1.0
        elif z_range < 500:
            score = 0.7
        else:
            score = 0.3  # Suspicious elevation data

        return {
            'score': score,
            'min_elevation': float(min(z_coords)),
            'max_elevation': float(max(z_coords)),
            'elevation_change': float(z_range)
        }


if __name__ == '__main__':
    print("Position Data Calibrator")
    print("=" * 70)
    print("\nCapabilities:")
    print("  ✓ Calibrate position data from telemetry")
    print("  ✓ Apply Kalman filtering for noise reduction")
    print("  ✓ Validate position accuracy")
    print("  ✓ Normalize coordinates to standard system")
    print("  ✓ Detect position jumps and anomalies")
    print("\nUsage: Import and use with track_analyzer or iracing_track_mapper")
