import pytest
import numpy as np
from utils.gait_utils import calculate_angle, extract_frame_angles, build_gait_signature

def test_calculate_angle():
    # Right angle (90 degrees)
    a = (1, 0)
    b = (0, 0) # vertex
    c = (0, 1)
    assert abs(calculate_angle(a, b, c) - 90.0) < 1e-5
    
    # Straight line (180 degrees)
    a = (1, 0)
    b = (0, 0)
    c = (-1, 0)
    assert abs(calculate_angle(a, b, c) - 180.0) < 1e-5
    
    # Same points (0 degrees)
    a = (1, 0)
    b = (0, 0)
    c = (1, 0)
    assert abs(calculate_angle(a, b, c) - 0.0) < 1e-5

class MockLandmark:
    def __init__(self, x, y):
        self.x = x
        self.y = y

def test_extract_frame_angles():
    # Create 33 mock landmarks
    landmarks = [MockLandmark(0, 0) for _ in range(33)]
    
    # Make left leg a straight line (180 deg knee, 180 deg hip, 180 deg ankle)
    landmarks[11] = MockLandmark(0, 1) # L shoulder
    landmarks[23] = MockLandmark(0, 0) # L hip
    landmarks[25] = MockLandmark(0, -1) # L knee
    landmarks[27] = MockLandmark(0, -2) # L ankle
    landmarks[31] = MockLandmark(0, -3) # L foot
    
    # Make right leg bent (90 deg knee)
    landmarks[12] = MockLandmark(1, 1) # R shoulder
    landmarks[24] = MockLandmark(1, 0) # R hip
    landmarks[26] = MockLandmark(2, 0) # R knee
    landmarks[28] = MockLandmark(2, -1) # R ankle
    landmarks[32] = MockLandmark(1, -1) # R foot
    
    angles = extract_frame_angles(landmarks)
    assert len(angles) == 6
    
    # L_knee = 180
    assert abs(angles[0] - 180.0) < 1e-5
    # R_knee = 90
    assert abs(angles[1] - 90.0) < 1e-5

def test_build_gait_signature():
    # Mock angle buffer: 4 frames, 6 angles each
    buffer = [
        [10, 20, 30, 40, 50, 60],
        [15, 25, 35, 45, 55, 65],
        [10, 20, 30, 40, 50, 60],
        [5,  15, 25, 35, 45, 55]
    ]
    
    sig = build_gait_signature(buffer)
    assert len(sig) == 30 # 6 angles * 5 stats
    
    # Mean of first angle (10, 15, 10, 5) is 10
    assert abs(sig[0] - 10.0) < 1e-5
    
    # Min of first angle is 5
    # indices: means(0-5), stds(6-11), mins(12-17), maxs(18-23), ranges(24-29)
    assert abs(sig[12] - 5.0) < 1e-5
    
    # Max of first angle is 15
    assert abs(sig[18] - 15.0) < 1e-5
    
    # Range of first angle is 10 (15 - 5)
    assert abs(sig[24] - 10.0) < 1e-5

def test_build_gait_signature_empty():
    sig = build_gait_signature([])
    assert len(sig) == 30
    assert np.all(sig == 0)
