"""
Complete iRacing Telemetry Collector
Captures ALL available telemetry fields from iRacing SDK
"""

import irsdk
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CompleteTelemetry:
    """Complete telemetry data structure - ALL iRacing SDK fields"""

    # Session Info
    session_id: str
    session_time: float
    session_tick: int
    session_state: str
    session_flags: int

    # Driver Info
    driver_id: int
    driver_name: str
    driver_car_idx: int
    driver_user_id: int
    driver_team_name: str
    driver_car_number: str
    driver_car_name: str
    driver_car_class: str
    driver_irating: int
    driver_license_level: int

    # Position & Timing
    lap: int
    lap_pct: float
    lap_dist: float
    lap_dist_pct: float
    lap_current_lap_time: float
    lap_last_lap_time: float
    lap_best_lap: int
    lap_best_lap_time: float

    # Sector Timing
    sector: int
    lap_current_sector_time: float
    lap_best_sector_times: List[float]

    # Race Position
    position: int
    position_class: int
    position_in_class: int
    car_idx: int
    is_on_track: bool
    is_in_garage: bool

    # Speed & Motion
    speed: float  # m/s
    velocity_x: float
    velocity_y: float
    velocity_z: float
    yaw: float
    yaw_rate: float
    pitch: float
    pitch_rate: float
    roll: float
    roll_rate: float

    # Position (World Coordinates)
    pos_x: float
    pos_y: float
    pos_z: float

    # G-Forces
    lat_accel: float
    long_accel: float
    vert_accel: float

    # Engine & Drivetrain
    rpm: float
    engine_warnings: int
    fuel_level: float
    fuel_level_pct: float
    fuel_use_per_hour: float
    fuel_pressure: float
    oil_temp: float
    oil_pressure: float
    oil_level: float
    water_temp: float
    water_level: float
    voltage: float
    manifold_pressure: float

    # Transmission
    gear: int
    clutch: float

    # Throttle & Brakes
    throttle: float
    brake: float
    brake_raw: float
    steering_wheel_angle: float
    steering_wheel_angle_max: float
    steering_wheel_pct: float
    steering_wheel_torque: float

    # Tire Temperatures (Celsius)
    lf_temp_cl: float  # Left Front Center Left
    lf_temp_cm: float  # Left Front Center Middle
    lf_temp_cr: float  # Left Front Center Right
    rf_temp_cl: float
    rf_temp_cm: float
    rf_temp_cr: float
    lr_temp_cl: float
    lr_temp_cm: float
    lr_temp_cr: float
    rr_temp_cl: float
    rr_temp_cm: float
    rr_temp_cr: float

    # Tire Wear (0-100%)
    lf_wear_l: float
    lf_wear_m: float
    lf_wear_r: float
    rf_wear_l: float
    rf_wear_m: float
    rf_wear_r: float
    lr_wear_l: float
    lr_wear_m: float
    lr_wear_r: float
    rr_wear_l: float
    rr_wear_m: float
    rr_wear_r: float

    # Tire Pressure (kPa)
    lf_tire_pres: float
    rf_tire_pres: float
    lr_tire_pres: float
    rr_tire_pres: float

    # Tire Cold Pressure (kPa)
    lf_cold_pressure: float
    rf_cold_pressure: float
    lr_cold_pressure: float
    rr_cold_pressure: float

    # Brake Temperatures (Celsius)
    lf_brake_line_press: float
    rf_brake_line_press: float
    lr_brake_line_press: float
    rr_brake_line_press: float

    # Suspension Travel
    lf_shock_defl: float
    rf_shock_defl: float
    lr_shock_defl: float
    rr_shock_defl: float

    # Ride Height
    lf_ride_height: float
    rf_ride_height: float
    lr_ride_height: float
    rr_ride_height: float

    # Damage
    lf_tire_damage: float
    rf_tire_damage: float
    lr_tire_damage: float
    rr_tire_damage: float

    # Weather & Track
    track_temp: float
    track_temp_crew: float
    air_temp: float
    air_pressure: float
    air_density: float
    relative_humidity: float
    fog_level: float
    wind_vel: float
    wind_dir: float
    skies: int
    weather_type: int

    # Track Surface
    track_wetness: int
    precipitation_rate: float

    # Flags
    session_flag: str
    start_lights: int

    # Pit Info
    on_pit_road: bool
    pit_sv_flags: int
    pit_opt_repair_left: float
    pit_repair_left: float

    # Car Setup (if available)
    dcl_lf_brake_bias_adj: float
    dcl_rf_brake_bias_adj: float
    dcl_lf_aero_trim: int
    dcl_rf_aero_trim: int
    dcl_rear_wing_flap: int
    dcl_front_wing_flap: int
    dcl_boost_level: int
    dcl_fuel_mixture: int

    # DRS (Formula cars)
    drs_status: int
    drs_count: int

    # ERS (Hybrid cars)
    ers_store_pct: float
    ers_deploy_mode: int

    # Push to Pass (IndyCar)
    engine_boost_pct: float

    # Multi-car Data
    car_idx_lap: List[int]
    car_idx_lap_completed: List[int]
    car_idx_lap_dist_pct: List[float]
    car_idx_track_surface: List[int]
    car_idx_on_pit_road: List[bool]
    car_idx_position: List[int]
    car_idx_class_position: List[int]
    car_idx_f2_time: List[float]
    car_idx_est_time: List[float]

    # Gaps & Deltas
    lap_delta_to_session_best_lap: float
    lap_delta_to_session_optimal_lap: float
    lap_delta_to_session_last_lap: float

    # Radio
    radio_transmit_car_idx: int
    radio_transmit_radio_idx: int
    radio_transmit_frequency_idx: int

    # Camera
    cam_car_idx: int
    cam_camera_number: int
    cam_camera_state: int
    cam_group_number: int

    # Replay
    replay_frame_num: int
    replay_frame_num_end: int
    replay_session_num: int
    replay_session_time: float

    # Display
    display_units: int

    # Timestamp
    timestamp: float


class CompleteTelemetryCollector:
    """Collects ALL available telemetry from iRacing SDK"""

    def __init__(self):
        self.ir = irsdk.IRSDK()
        self.connected = False
        self.last_update = 0
        logger.info("Complete Telemetry Collector initialized")

    def connect(self) -> bool:
        """Connect to iRacing"""
        if self.ir.startup():
            self.connected = True
            logger.info("✓ Connected to iRacing")
            return True
        else:
            logger.warning("iRacing not running")
            return False

    def disconnect(self):
        """Disconnect from iRacing"""
        self.ir.shutdown()
        self.connected = False
        logger.info("Disconnected from iRacing")

    def get_complete_telemetry(self) -> Optional[CompleteTelemetry]:
        """Get ALL telemetry fields"""
        if not self.connected:
            return None

        try:
            # Session Info
            session_info = self.ir['WeekendInfo']
            driver_info = self.ir['DriverInfo']

            # Get player car index
            player_car_idx = self.ir['PlayerCarIdx']

            # Build complete telemetry
            telemetry = CompleteTelemetry(
                # Session
                session_id=str(session_info.get('SessionID', '')),
                session_time=self.ir['SessionTime'] or 0,
                session_tick=self.ir['SessionTick'] or 0,
                session_state=self.ir['SessionState'] or '',
                session_flags=self.ir['SessionFlags'] or 0,

                # Driver
                driver_id=driver_info['DriverUserID'],
                driver_name=driver_info['DriverUserName'],
                driver_car_idx=player_car_idx,
                driver_user_id=driver_info['DriverUserID'],
                driver_team_name=driver_info.get('DriverTeamName', ''),
                driver_car_number=driver_info.get('DriverCarNumber', ''),
                driver_car_name=driver_info.get('DriverCarName', ''),
                driver_car_class=driver_info.get('DriverCarClass', ''),
                driver_irating=driver_info.get('DriverIRating', 0),
                driver_license_level=driver_info.get('DriverLicenseLevel', 0),

                # Position & Timing
                lap=self.ir['Lap'] or 0,
                lap_pct=self.ir['LapPct'] or 0,
                lap_dist=self.ir['LapDist'] or 0,
                lap_dist_pct=self.ir['LapDistPct'] or 0,
                lap_current_lap_time=self.ir['LapCurrentLapTime'] or 0,
                lap_last_lap_time=self.ir['LapLastLapTime'] or 0,
                lap_best_lap=self.ir['LapBestLap'] or 0,
                lap_best_lap_time=self.ir['LapBestLapTime'] or 0,

                # Sector
                sector=self.ir['Sector'] or 0,
                lap_current_sector_time=self.ir['LapCurrentSectorTime'] or 0,
                lap_best_sector_times=self._safe_list(self.ir['LapBestSectorTime'], 3),

                # Race Position
                position=self.ir['PlayerPosition'] or 0,
                position_class=self.ir['PlayerClassPosition'] or 0,
                position_in_class=self.ir['PlayerClassPosition'] or 0,
                car_idx=player_car_idx,
                is_on_track=self.ir['IsOnTrack'] or False,
                is_in_garage=self.ir['IsInGarage'] or False,

                # Speed & Motion
                speed=self.ir['Speed'] or 0,
                velocity_x=self.ir['VelocityX'] or 0,
                velocity_y=self.ir['VelocityY'] or 0,
                velocity_z=self.ir['VelocityZ'] or 0,
                yaw=self.ir['Yaw'] or 0,
                yaw_rate=self.ir['YawRate'] or 0,
                pitch=self.ir['Pitch'] or 0,
                pitch_rate=self.ir['PitchRate'] or 0,
                roll=self.ir['Roll'] or 0,
                roll_rate=self.ir['RollRate'] or 0,

                # Position
                pos_x=self._safe_array_value(self.ir['CarIdxX'], player_car_idx),
                pos_y=self._safe_array_value(self.ir['CarIdxY'], player_car_idx),
                pos_z=self._safe_array_value(self.ir['CarIdxZ'], player_car_idx),

                # G-Forces
                lat_accel=self.ir['LatAccel'] or 0,
                long_accel=self.ir['LongAccel'] or 0,
                vert_accel=self.ir['VertAccel'] or 0,

                # Engine
                rpm=self.ir['RPM'] or 0,
                engine_warnings=self.ir['EngineWarnings'] or 0,
                fuel_level=self.ir['FuelLevel'] or 0,
                fuel_level_pct=self.ir['FuelLevelPct'] or 0,
                fuel_use_per_hour=self.ir['FuelUsePerHour'] or 0,
                fuel_pressure=self.ir['FuelPress'] or 0,
                oil_temp=self.ir['OilTemp'] or 0,
                oil_pressure=self.ir['OilPress'] or 0,
                oil_level=self.ir['OilLevel'] or 0,
                water_temp=self.ir['WaterTemp'] or 0,
                water_level=self.ir['WaterLevel'] or 0,
                voltage=self.ir['Voltage'] or 0,
                manifold_pressure=self.ir['ManifoldPress'] or 0,

                # Transmission
                gear=self.ir['Gear'] or 0,
                clutch=self.ir['Clutch'] or 0,

                # Controls
                throttle=self.ir['Throttle'] or 0,
                brake=self.ir['Brake'] or 0,
                brake_raw=self.ir['BrakeRaw'] or 0,
                steering_wheel_angle=self.ir['SteeringWheelAngle'] or 0,
                steering_wheel_angle_max=self.ir['SteeringWheelAngleMax'] or 0,
                steering_wheel_pct=self.ir['SteeringWheelPct'] or 0,
                steering_wheel_torque=self.ir['SteeringWheelTorque'] or 0,

                # Tire Temps
                lf_temp_cl=self.ir['LFtempCL'] or 0,
                lf_temp_cm=self.ir['LFtempCM'] or 0,
                lf_temp_cr=self.ir['LFtempCR'] or 0,
                rf_temp_cl=self.ir['RFtempCL'] or 0,
                rf_temp_cm=self.ir['RFtempCM'] or 0,
                rf_temp_cr=self.ir['RFtempCR'] or 0,
                lr_temp_cl=self.ir['LRtempCL'] or 0,
                lr_temp_cm=self.ir['LRtempCM'] or 0,
                lr_temp_cr=self.ir['LRtempCR'] or 0,
                rr_temp_cl=self.ir['RRtempCL'] or 0,
                rr_temp_cm=self.ir['RRtempCM'] or 0,
                rr_temp_cr=self.ir['RRtempCR'] or 0,

                # Tire Wear
                lf_wear_l=self.ir['LFwearL'] or 0,
                lf_wear_m=self.ir['LFwearM'] or 0,
                lf_wear_r=self.ir['LFwearR'] or 0,
                rf_wear_l=self.ir['RFwearL'] or 0,
                rf_wear_m=self.ir['RFwearM'] or 0,
                rf_wear_r=self.ir['RFwearR'] or 0,
                lr_wear_l=self.ir['LRwearL'] or 0,
                lr_wear_m=self.ir['LRwearM'] or 0,
                lr_wear_r=self.ir['LRwearR'] or 0,
                rr_wear_l=self.ir['RRwearL'] or 0,
                rr_wear_m=self.ir['RRwearM'] or 0,
                rr_wear_r=self.ir['RRwearR'] or 0,

                # Tire Pressure
                lf_tire_pres=self.ir['LFtirePres'] or 0,
                rf_tire_pres=self.ir['RFtirePres'] or 0,
                lr_tire_pres=self.ir['LRtirePres'] or 0,
                rr_tire_pres=self.ir['RRtirePres'] or 0,

                # Cold Pressure
                lf_cold_pressure=self.ir['LFcoldPressure'] or 0,
                rf_cold_pressure=self.ir['RFcoldPressure'] or 0,
                lr_cold_pressure=self.ir['LRcoldPressure'] or 0,
                rr_cold_pressure=self.ir['RRcoldPressure'] or 0,

                # Brake Line Pressure
                lf_brake_line_press=self.ir['LFbrakeLinePress'] or 0,
                rf_brake_line_press=self.ir['RFbrakeLinePress'] or 0,
                lr_brake_line_press=self.ir['LRbrakeLinePress'] or 0,
                rr_brake_line_press=self.ir['RRbrakeLinePress'] or 0,

                # Suspension
                lf_shock_defl=self.ir['LFshockDefl'] or 0,
                rf_shock_defl=self.ir['RFshockDefl'] or 0,
                lr_shock_defl=self.ir['LRshockDefl'] or 0,
                rr_shock_defl=self.ir['RRshockDefl'] or 0,

                # Ride Height
                lf_ride_height=self.ir['LFrideHeight'] or 0,
                rf_ride_height=self.ir['RFrideHeight'] or 0,
                lr_ride_height=self.ir['LRrideHeight'] or 0,
                rr_ride_height=self.ir['RRrideHeight'] or 0,

                # Damage
                lf_tire_damage=self.ir['LFtireDamage'] or 0,
                rf_tire_damage=self.ir['RFtireDamage'] or 0,
                lr_tire_damage=self.ir['LRtireDamage'] or 0,
                rr_tire_damage=self.ir['RRtireDamage'] or 0,

                # Weather
                track_temp=self.ir['TrackTemp'] or 0,
                track_temp_crew=self.ir['TrackTempCrew'] or 0,
                air_temp=self.ir['AirTemp'] or 0,
                air_pressure=self.ir['AirPressure'] or 0,
                air_density=self.ir['AirDensity'] or 0,
                relative_humidity=self.ir['RelativeHumidity'] or 0,
                fog_level=self.ir['FogLevel'] or 0,
                wind_vel=self.ir['WindVel'] or 0,
                wind_dir=self.ir['WindDir'] or 0,
                skies=self.ir['Skies'] or 0,
                weather_type=self.ir['WeatherType'] or 0,

                # Track Surface
                track_wetness=self.ir['TrackWetness'] or 0,
                precipitation_rate=self.ir['PrecipitationRate'] or 0,

                # Flags
                session_flag=self._get_flag_string(self.ir['SessionFlags']),
                start_lights=self.ir['StartLights'] or 0,

                # Pit
                on_pit_road=self.ir['OnPitRoad'] or False,
                pit_sv_flags=self.ir['PitSvFlags'] or 0,
                pit_opt_repair_left=self.ir['PitOptRepairLeft'] or 0,
                pit_repair_left=self.ir['PitRepairLeft'] or 0,

                # Setup Adjustments
                dcl_lf_brake_bias_adj=self.ir['dcLFBrakeBiasAdj'] or 0,
                dcl_rf_brake_bias_adj=self.ir['dcRFBrakeBiasAdj'] or 0,
                dcl_lf_aero_trim=self.ir['dcLFAeroTrim'] or 0,
                dcl_rf_aero_trim=self.ir['dcRFAeroTrim'] or 0,
                dcl_rear_wing_flap=self.ir['dcRearWingFlap'] or 0,
                dcl_front_wing_flap=self.ir['dcFrontWingFlap'] or 0,
                dcl_boost_level=self.ir['dcBoostLevel'] or 0,
                dcl_fuel_mixture=self.ir['dcFuelMixture'] or 0,

                # DRS
                drs_status=self.ir['DRS_Status'] or 0,
                drs_count=self.ir['DRS_Count'] or 0,

                # ERS
                ers_store_pct=self.ir['ERS_StorePct'] or 0,
                ers_deploy_mode=self.ir['ERS_DeployMode'] or 0,

                # Boost
                engine_boost_pct=self.ir['EngineBoostPct'] or 0,

                # Multi-car
                car_idx_lap=self._safe_list(self.ir['CarIdxLap'], 64),
                car_idx_lap_completed=self._safe_list(self.ir['CarIdxLapCompleted'], 64),
                car_idx_lap_dist_pct=self._safe_list(self.ir['CarIdxLapDistPct'], 64),
                car_idx_track_surface=self._safe_list(self.ir['CarIdxTrackSurface'], 64),
                car_idx_on_pit_road=self._safe_list(self.ir['CarIdxOnPitRoad'], 64),
                car_idx_position=self._safe_list(self.ir['CarIdxPosition'], 64),
                car_idx_class_position=self._safe_list(self.ir['CarIdxClassPosition'], 64),
                car_idx_f2_time=self._safe_list(self.ir['CarIdxF2Time'], 64),
                car_idx_est_time=self._safe_list(self.ir['CarIdxEstTime'], 64),

                # Deltas
                lap_delta_to_session_best_lap=self.ir['LapDeltaToSessionBestLap'] or 0,
                lap_delta_to_session_optimal_lap=self.ir['LapDeltaToSessionOptimalLap'] or 0,
                lap_delta_to_session_last_lap=self.ir['LapDeltaToSessionLastlLap'] or 0,

                # Radio
                radio_transmit_car_idx=self.ir['RadioTransmitCarIdx'] or -1,
                radio_transmit_radio_idx=self.ir['RadioTransmitRadioIdx'] or -1,
                radio_transmit_frequency_idx=self.ir['RadioTransmitFrequencyIdx'] or -1,

                # Camera
                cam_car_idx=self.ir['CamCarIdx'] or 0,
                cam_camera_number=self.ir['CamCameraNumber'] or 0,
                cam_camera_state=self.ir['CamCameraState'] or 0,
                cam_group_number=self.ir['CamGroupNumber'] or 0,

                # Replay
                replay_frame_num=self.ir['ReplayFrameNum'] or 0,
                replay_frame_num_end=self.ir['ReplayFrameNumEnd'] or 0,
                replay_session_num=self.ir['ReplaySessionNum'] or 0,
                replay_session_time=self.ir['ReplaySessionTime'] or 0,

                # Display
                display_units=self.ir['DisplayUnits'] or 0,

                # Timestamp
                timestamp=time.time()
            )

            self.last_update = time.time()
            return telemetry

        except Exception as e:
            logger.error(f"Error collecting telemetry: {e}")
            return None

    def _safe_array_value(self, arr, idx, default=0):
        """Safely get array value"""
        try:
            if arr and idx < len(arr):
                return arr[idx] or default
            return default
        except:
            return default

    def _safe_list(self, arr, expected_len, default=0):
        """Safely convert array to list"""
        try:
            if arr:
                return list(arr)[:expected_len]
            return [default] * expected_len
        except:
            return [default] * expected_len

    def _get_flag_string(self, flags):
        """Convert flag int to string"""
        if not flags:
            return 'green'

        flag_map = {
            0x00000001: 'checkered',
            0x00000002: 'white',
            0x00000004: 'green',
            0x00000008: 'yellow',
            0x00000010: 'red',
            0x00000020: 'blue',
            0x00000040: 'debris',
            0x00000080: 'crossed',
            0x00000100: 'yellow_waving',
            0x00000200: 'one_lap_to_green',
            0x00000400: 'green_held',
            0x00000800: 'ten_to_go',
            0x00001000: 'five_to_go',
            0x00002000: 'random_waving',
            0x00004000: 'caution',
            0x00008000: 'caution_waving',
            0x00010000: 'black',
            0x00020000: 'disqualify',
            0x00040000: 'repair',
            0x00080000: 'furled',
            0x00100000: 'end_of_session'
        }

        for flag_bit, flag_name in flag_map.items():
            if flags & flag_bit:
                return flag_name

        return 'green'

    def to_dict(self, telemetry: CompleteTelemetry) -> Dict:
        """Convert telemetry to dictionary"""
        return asdict(telemetry)


if __name__ == '__main__':
    print("Complete Telemetry Collector Test")
    print("=" * 70)

    collector = CompleteTelemetryCollector()

    if collector.connect():
        print("✓ Connected to iRacing")
        print("\nCollecting telemetry...")

        telemetry = collector.get_complete_telemetry()
        if telemetry:
            print(f"\n✓ Collected {len(asdict(telemetry))} telemetry fields")
            print(f"  Driver: {telemetry.driver_name}")
            print(f"  Car: {telemetry.driver_car_name}")
            print(f"  Lap: {telemetry.lap}")
            print(f"  Speed: {telemetry.speed * 3.6:.1f} km/h")
            print(f"  Position: P{telemetry.position}")
            print(f"  Fuel: {telemetry.fuel_level:.1f}L")
        else:
            print("❌ Failed to collect telemetry")

        collector.disconnect()
    else:
        print("❌ iRacing not running")

    print("\n" + "=" * 70)
    print("✓ Complete telemetry system ready")
    print(f"  Total fields: {len(CompleteTelemetry.__dataclass_fields__)}")
