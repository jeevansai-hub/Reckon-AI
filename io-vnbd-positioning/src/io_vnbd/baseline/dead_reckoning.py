"""
Classical (non-ML) double-integration dead-reckoning baseline: raw
gravity-corrected acceleration -> velocity -> displacement, with no
learned denoising. Exists purely as the comparison point for the trained
LSTM's ATE/RPE. Not yet implemented -- see PRD SRS-4, Milestone 2
(build in parallel with the LSTM training code, not after -- it needs no
training time and de-risks having zero comparison numbers if training
runs long).
"""
