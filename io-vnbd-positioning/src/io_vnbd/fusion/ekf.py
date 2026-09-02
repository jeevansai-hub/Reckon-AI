"""
Simulates a GPS outage on a real run and fuses the sensor/map-matched
estimate back with true GPS on reacquisition via filterpy's
ExtendedKalmanFilter, blending over a 2-5s window rather than snapping
instantly. Not yet implemented -- see PRD SRS-6, Milestone 5.
"""
