"""
Column names for the two IO-VNBD CSV file types, as documented in
README_1.pdf (Tables 3 and 4) and cross-checked in
IO-VNBD-Analysis/IO-VNBD-Repository-Breakdown.md.

IMPORTANT: verify these against the real header row of an actual file
after `git lfs pull` -- the PDF's column order is the documented spec,
not a guarantee of the literal CSV header string. See
`scripts/verify_schema.py`.
"""

V_COLUMNS = [
    "n_gps_satellites",
    "time_of_day_s",
    "lat",
    "lon",
    "velocity_kmh",
    "heading_deg",
    "height_km",
    "vertical_velocity_kmh",
    "sample_period_s",
    "steering_angle_deg",
    "wheel_speed_fl",
    "wheel_speed_fr",
    "wheel_speed_rl",
    "wheel_speed_rr",
    "yaw_rate_degs",
    "indicated_speed_kmh",
    "long_accel_g",
    "lat_accel_g",
    "handbrake",
    "gear_requested",
    "gear",
    "engine_rpm",
    "coolant_temp_c",
    "clutch_position",
    "brake_pressure_psi",
    "brake_position",
    "battery_voltage",
    "air_temp_c",
    "accel_pedal_pct",
]

S_COLUMNS = [
    "gps_lat",
    "gps_lon",
    "gps_alt_m",
    "gps_speed_kmh",
    "gps_accuracy_m",
    "gps_orientation_deg",
    "gps_sats_in_range",
    "time_since_start_ms",
    "date",
    "accel_x",
    "accel_y",
    "accel_z",
    "gravity_x",
    "gravity_y",
    "gravity_z",
    "gyro_yaw",
    "gyro_pitch",
    "gyro_roll",
    "mag_x",
    "mag_y",
    "mag_z",
    "orient_yaw",
    "orient_pitch",
    "orient_roll",
]
