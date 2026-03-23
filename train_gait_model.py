import os
import cv2
import glob
import joblib
import argparse
import numpy as np
import mediapipe as mp
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix

from utils.gait_utils import extract_frame_angles, build_gait_signature

# Constants
FRAMES_PER_WINDOW = 30
STRIDE = 15 # overlap for sliding window

def get_video_files(directory):
    extensions = ["*.mp4", "*.avi", "*.mov", "*.mkv"]
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(directory, ext)))
    return files

def process_video_for_angles(video_path, pose):
    """
    Reads a video, runs MediaPipe Pose on each frame,
    and returns a list of frame angles.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error opening video: {video_path}")
        return []

    angles_list = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Optional: resize down to speed up mediapipe if needed, but original is fine
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb_frame)
        
        if results.pose_landmarks:
            angles = extract_frame_angles(results.pose_landmarks.landmark)
            angles_list.append(angles)
            
    cap.release()
    return angles_list

def extract_signatures_from_angles(angles_list):
    """
    Applies sliding window over angles_list to extract gait signatures.
    """
    signatures = []
    total_frames = len(angles_list)
    if total_frames < FRAMES_PER_WINDOW:
        return signatures
        
    for i in range(0, total_frames - FRAMES_PER_WINDOW + 1, STRIDE):
        window = angles_list[i : i + FRAMES_PER_WINDOW]
        sig = build_gait_signature(window)
        signatures.append(sig)
        
    return signatures

def main():
    parser = argparse.ArgumentParser(description="Train SVM for Gait Recognition")
    parser.add_argument("--data_dir", type=str, default="gait_training_data", help="Directory containing target/ and others/ folders")
    parser.add_argument("--dry_run", action="store_true", help="Validate folder structure without training")
    parser.add_argument("--model_out", type=str, default="gait_svm_model.pkl", help="Output model filename")
    args = parser.parse_args()

    target_dir = os.path.join(args.data_dir, "target")
    others_dir = os.path.join(args.data_dir, "others")

    if not os.path.exists(target_dir) or not os.path.exists(others_dir):
        print(f"ERROR: Expected '{target_dir}' and '{others_dir}' to exist.")
        return

    target_videos = get_video_files(target_dir)
    others_videos = get_video_files(others_dir)

    print(f"Found {len(target_videos)} target videos.")
    print(f"Found {len(others_videos)} 'other' videos.")

    if args.dry_run:
        print("[DRY RUN] Folder structure is valid. Skipping training.")
        return

    if len(target_videos) == 0 or len(others_videos) == 0:
        print("ERROR: Need at least one video in both 'target/' and 'others/' to train.")
        return

    # Initialize MediaPipe Pose
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1, 
        min_detection_confidence=0.5
    )

    X = []
    y = []

    print("\nProcessing 'target' videos (Label 1)...")
    for vid in target_videos:
        print(f"  -> {os.path.basename(vid)}")
        angles = process_video_for_angles(vid, pose)
        sigs = extract_signatures_from_angles(angles)
        X.extend(sigs)
        y.extend([1] * len(sigs))

    print("\nProcessing 'others' videos (Label 0)...")
    for vid in others_videos:
        print(f"  -> {os.path.basename(vid)}")
        angles = process_video_for_angles(vid, pose)
        sigs = extract_signatures_from_angles(angles)
        X.extend(sigs)
        y.extend([0] * len(sigs))

    pose.close()

    total_samples = len(X)
    print(f"\nExtracted {total_samples} gait signatures in total.")
    if total_samples == 0:
        print("ERROR: No valid signatures extracted. Ensure videos have visible people.")
        return

    X = np.array(X)
    y = np.array(y)

    # Train/Test Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)
    print(f"Training on {len(X_train)} samples, testing on {len(X_test)} samples.")

    # Train SVM
    print("\nTraining SVM Classifier...")
    classifier = SVC(kernel='rbf', probability=True)
    classifier.fit(X_train, y_train)

    # Evaluate
    print("\nModel Evaluation:")
    y_pred = classifier.predict(X_test)
    
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, zero_division=0))

    # Save Model
    joblib.dump(classifier, args.model_out)
    print(f"\n[SUCCESS] Model saved to {args.model_out}")

if __name__ == "__main__":
    main()
