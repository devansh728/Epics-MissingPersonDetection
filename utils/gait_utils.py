import math
import numpy as np

def calculate_angle(a, b, c):
    """
    Calculate the angle between three points a, b, and c.
    Each point is a tuple or list of (x, y).
    Point b is the vertex.
    Returns the angle in degrees between 0 and 360.
    """
    ang = math.degrees(math.atan2(c[1] - b[1], c[0] - b[0]) - math.atan2(a[1] - b[1], a[0] - b[0]))
    return ang + 360 if ang < 0 else ang

def extract_frame_angles(landmarks):
    """
    Extracts 6 key joint angles from MediaPipe Pose landmarks for a single frame.
    Requires mediapipe pose landmarks (list of objects with .x, .y).
    Angles: [L_knee, R_knee, L_hip, R_hip, L_ankle, R_ankle]
    """
    try:
        # Landmarks mapping (MediaPipe Pose)
        # 11: left_shoulder, 12: right_shoulder
        # 23: left_hip, 24: right_hip
        # 25: left_knee, 26: right_knee
        # 27: left_ankle, 28: right_ankle
        # 31: left_foot_index, 32: right_foot_index

        l_shoulder = [landmarks[11].x, landmarks[11].y]
        r_shoulder = [landmarks[12].x, landmarks[12].y]
        
        l_hip = [landmarks[23].x, landmarks[23].y]
        r_hip = [landmarks[24].x, landmarks[24].y]
        
        l_knee = [landmarks[25].x, landmarks[25].y]
        r_knee = [landmarks[26].x, landmarks[26].y]
        
        l_ankle = [landmarks[27].x, landmarks[27].y]
        r_ankle = [landmarks[28].x, landmarks[28].y]
        
        l_foot = [landmarks[31].x, landmarks[31].y]
        r_foot = [landmarks[32].x, landmarks[32].y]

        # Calculate angles
        l_knee_angle = calculate_angle(l_hip, l_knee, l_ankle)
        r_knee_angle = calculate_angle(r_hip, r_knee, r_ankle)
        
        l_hip_angle = calculate_angle(l_shoulder, l_hip, l_knee)
        r_hip_angle = calculate_angle(r_shoulder, r_hip, r_knee)
        
        l_ankle_angle = calculate_angle(l_knee, l_ankle, l_foot)
        r_ankle_angle = calculate_angle(r_knee, r_ankle, r_foot)

        return [l_knee_angle, r_knee_angle, l_hip_angle, r_hip_angle, l_ankle_angle, r_ankle_angle]
    except Exception as e:
        print(f"Error extracting frame angles: {e}")
        return [0.0] * 6 # Return zeros on failure

def build_gait_signature(angle_buffer):
    """
    Takes a list of frame angles (e.g. 30 frames x 6 angles) and aggregates them
    into a fixed-length statistical feature vector (signature).
    Stats per angle: mean, std, min, max, range -> 6 * 5 = 30 features.
    
    Args:
        angle_buffer (list of lists): The extracted angles for a sequence of frames.
    
    Returns:
        numpy.ndarray: 1D array of 30 features.
    """
    if not angle_buffer or len(angle_buffer) == 0:
        return np.zeros(30)
    
    # Convert to numpy array: shape = (num_frames, 6)
    arr = np.array(angle_buffer)
    
    # Calculate statistics along the time axis (axis 0)
    means = np.mean(arr, axis=0)
    stds = np.std(arr, axis=0)
    mins = np.min(arr, axis=0)
    maxs = np.max(arr, axis=0)
    ranges = maxs - mins
    
    # Concatenate all stats to form a 30-feature vector
    signature = np.concatenate([means, stds, mins, maxs, ranges])
    return signature
