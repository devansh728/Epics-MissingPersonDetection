"""
combined_surveillance.py

Combined Face + Gait Recognition Surveillance System

Features:
- YOLOv8 person detection (ultralytics)
- DeepSort (deep_sort_realtime) tracking
- DeepFace (Facenet512) face embeddings & verification
- OpenGait gait embedding (GaitGL/GaitBase) for gait matching
- Fusion logic: face match (high confidence) OR gait match (backup) OR weighted score
- Saves detected person crops, matched frames, and logs to CSV + terminal
- SQLite database for storing target person embeddings (face + gait)

Assumptions & Requirements:
- Python 3.9+ (recommended 3.10/3.11)
- Virtualenv active
- Install required packages (CPU-friendly):
    pip install ultralytics deepface opencv-python-headless numpy pandas
    pip install deep-sort-realtime    # tracker
    pip install onnxruntime           # sometimes used by models

- OpenGait must be cloned and pretrained weights downloaded (see OpenGait README)
  Place OpenGait at ./OpenGait (or update OPENGAIT_ROOT below)

How it works (short):
1. Load target person's face image or folder of face images and a target walking video (optional)
2. Create and store target face embedding(s) in SQLite
3. If provided, create target gait embedding from target walking video using OpenGait
4. Process surveillance video: YOLOv8 detect person boxes -> DeepSort tracking
   - For each track: accumulate person crops (for gait silhouettes) and face crops
   - Periodically compute face embedding and compare with target
   - When track has sufficient silhouette frames, compute gait embedding and compare
   - Apply fusion logic and raise match
5. Save matched frames and logs

Usage example:
    python combined_surveillance.py \
        --target_face target_person.jpg \
        --target_walk target_walk.mp4 \
        --video cctv.mp4

Note: if you don't have OpenGait, the script will continue with face-only mode.

"""

import os
import cv2
import time
import sqlite3
import csv
import argparse
import numpy as np
import pandas as pd
from ultralytics import YOLO
from deepface import DeepFace
from deep_sort_realtime.deepsort_tracker import DeepSort

# Attempt import for OpenGait (optional)
OPENGAIT_ROOT = "./OpenGait"
USE_OPENGAIT = False
try:
    import torch
    import sys
    sys.path.append(os.path.join(OPENGAIT_ROOT))
    from lib.config import get_cfg
    from lib.modeling import make_model
    from lib.utils.data import load_silhouettes
    USE_OPENGAIT = True
except Exception:
    # OpenGait not available; continue in face-only mode
    USE_OPENGAIT = False

# ------------------------
# Configuration
# ------------------------
YOLO_MODEL = "yolov8n.pt"
DB_PATH = "combined_face_gait.db"
OUTPUT_DIR = "combined_output"
DETECTED_DIR = os.path.join(OUTPUT_DIR, "detected_people")
MATCHED_DIR = os.path.join(OUTPUT_DIR, "matches")
LOG_CSV = os.path.join(OUTPUT_DIR, "detections_log.csv")

# thresholds
FACE_SIM_THRESHOLD = 0.55      # Facenet512 cosine similarity
GAIT_SIM_THRESHOLD = 0.70      # OpenGait similarity
WEIGHT_FACE = 0.8
WEIGHT_GAIT = 0.2

# gait settings
SILHOUETTE_MIN_FRAMES = 16     # minimum silhouette frames for reliable gait emb
TRACK_SIL_BUFFER = 64          # max silhouettes to store per track

# processing settings
FRAME_SKIP = 1                 # process every frame
DETECT_CONF = 0.25
IOU = 0.45

# ------------------------
# Utilities: FS, DB, Logging
# ------------------------

def ensure_dirs():
    os.makedirs(DETECTED_DIR, exist_ok=True)
    os.makedirs(MATCHED_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def init_database(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS persons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            face_embedding BLOB,
            gait_embedding BLOB
        )
    ''')
    conn.commit()
    return conn


def save_face_embedding(conn, name, emb: np.ndarray):
    cur = conn.cursor()
    emb_bytes = emb.astype(np.float32).tobytes()
    cur.execute('INSERT OR REPLACE INTO persons (name, face_embedding) VALUES (?, ?)', (name, emb_bytes))
    conn.commit()


def save_gait_embedding(conn, name, emb: np.ndarray):
    cur = conn.cursor()
    emb_bytes = emb.astype(np.float32).tobytes()
    cur.execute('UPDATE persons SET gait_embedding=? WHERE name=?', (emb_bytes, name))
    conn.commit()


def load_face_embedding(conn, name):
    cur = conn.cursor()
    cur.execute('SELECT face_embedding FROM persons WHERE name=?', (name,))
    row = cur.fetchone()
    if row and row[0]:
        return np.frombuffer(row[0], dtype=np.float32)
    return None


def load_gait_embedding(conn, name):
    cur = conn.cursor()
    cur.execute('SELECT gait_embedding FROM persons WHERE name=?', (name,))
    row = cur.fetchone()
    if row and row[0]:
        return np.frombuffer(row[0], dtype=np.float32)
    return None


def append_log(row):
    write_header = not os.path.exists(LOG_CSV)
    with open(LOG_CSV, 'a', newline='') as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(['timestamp','frame','track_id','bbox','face_sim','gait_sim','fused_score','match','saved_path'])
        writer.writerow(row)

# ------------------------
# Face Embedding utils
# ------------------------

def get_face_embedding_from_image(img_bgr, detector_backend='opencv', enforce=True):
    """Return 512-d embedding (Facenet512) or None"""
    try:
        # DeepFace.represent accepts either path or numpy image
        rep = DeepFace.represent(img_path=img_bgr, model_name='Facenet512', detector_backend=detector_backend, enforce_detection=enforce)
        if isinstance(rep, list) and len(rep) > 0:
            emb = np.array(rep[0]['embedding'], dtype=np.float32)
            return emb
    except Exception:
        return None
    return None

# ------------------------
# OpenGait utils (optional)
# ------------------------

def load_opengait_model(model_name='GaitGL'):
    cfg = get_cfg()
    cfg.merge_from_file(os.path.join(OPENGAIT_ROOT, 'configs', f'{model_name}.yaml'))
    cfg.DATASET.PROTOCOL = 'CASIA-B'

    model = make_model(cfg)
    weights_path = os.path.join(OPENGAIT_ROOT, 'output', model_name, f'{model_name}_CASIA-B.pth')
    if not os.path.exists(weights_path):
        raise FileNotFoundError(f'OpenGait weights not found at {weights_path}')
    model.load_state_dict(torch.load(weights_path, map_location='cpu'))
    model.eval()
    return model, cfg


def compute_gait_embedding_opengait(model, cfg, silhouette_dir):
    seq = load_silhouettes(silhouette_dir)
    if seq is None:
        return None
    seq_t = torch.tensor(seq).unsqueeze(0).float()
    with torch.no_grad():
        features = model(seq_t)
        emb = features['embeddings'].cpu().numpy()[0]
    return emb

# ------------------------
# Silhouette extraction helpers
# ------------------------

def silhouette_from_crop(crop_bgr):
    gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return mask

# ------------------------
# Main pipeline
# ------------------------

def combined_pipeline(target_face_path=None, target_walk_video=None, surveillance_video=None, name='target_person'):
    ensure_dirs()
    conn = init_database()

    # 1) Load YOLO & DeepSort
    print('[INFO] Loading YOLO model...')
    yolo = YOLO(YOLO_MODEL)
    tracker = DeepSort(max_age=30)

    # 2) Prepare target face embedding (single or folder)
    if target_face_path:
        print(f'[INFO] Loading target face image: {target_face_path}')
        target_img = cv2.imread(target_face_path)
        if target_img is None:
            raise FileNotFoundError('Target face image not found')
        face_emb = get_face_embedding_from_image(target_img, detector_backend='opencv', enforce=True)
        if face_emb is None:
            print('[WARN] Could not extract face embedding with strict detection; trying enforce=False')
            face_emb = get_face_embedding_from_image(target_img, detector_backend='opencv', enforce=False)
        if face_emb is None:
            raise RuntimeError('Failed to get face embedding from target image')
        save_face_embedding(conn, name, face_emb)
        print('[OK] Target face embedding saved to DB')
    else:
        print('[WARN] No target face provided; face matching disabled')

    # 3) Prepare target gait embedding (optional)
    gait_model = None
    target_gait_emb = None
    if USE_OPENGAIT and target_walk_video:
        print('[INFO] OpenGait available — computing target gait embedding...')
        try:
            gait_model, gait_cfg = load_opengait_model('GaitGL')
            # extract silhouettes to temp folder
            tmp_target_sil = os.path.join('tmp_target_sil')
            os.makedirs(tmp_target_sil, exist_ok=True)
            cap = cv2.VideoCapture(target_walk_video)
            idx = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                idx += 1
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                cv2.imwrite(os.path.join(tmp_target_sil, f"{idx:04d}.png"), mask)
            cap.release()
            target_gait_emb = compute_gait_embedding_opengait(gait_model, gait_cfg, tmp_target_sil)
            if target_gait_emb is not None:
                save_gait_embedding(conn, name, target_gait_emb)
                print('[OK] Target gait embedding saved to DB')
            else:
                print('[WARN] Target gait embedding not computed (not enough silhouettes)')
        except Exception as e:
            print('[WARN] OpenGait failed:', e)
            gait_model = None
    else:
        if target_walk_video:
            print('[WARN] OpenGait not available; skipping gait creation')

    # reload stored embeddings
    stored_face_emb = load_face_embedding(conn, name)
    stored_gait_emb = load_gait_embedding(conn, name)

    # 4) Open surveillance video
    cap = cv2.VideoCapture(surveillance_video)
    if not cap.isOpened():
        raise FileNotFoundError('Surveillance video not found or cannot be opened')

    frame_idx = 0
    found_matches = 0

    # per-track buffers: face embeddings list, silhouettes list (for gait)
    tracks_data = {}

    print('[INFO] Starting surveillance processing...')

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_idx += 1
        if frame_idx % FRAME_SKIP != 0:
            continue

        t0 = time.time()
        h, w = frame.shape[:2]

        results = yolo(frame, imgsz=640, conf=DETECT_CONF, iou=IOU)[0]
        detections = []
        if hasattr(results, 'boxes') and len(results.boxes) > 0:
            for box in results.boxes:
                cls = int(box.cls[0].numpy())
                if cls != 0:
                    continue
                conf = float(box.conf[0].numpy())
                x1, y1, x2, y2 = map(int, box.xyxy[0].numpy())
                x1 = max(0, x1); y1 = max(0, y1)
                x2 = min(w-1, x2); y2 = min(h-1, y2)
                detections.append(([x1, y1, x2, y2], conf, None))

        tracks = tracker.update_tracks(detections, frame=frame)

        # process tracks
        for tr in tracks:
            if not tr.is_confirmed():
                continue
            track_id = tr.track_id
            l, t, r, b = map(int, tr.to_ltrb())
            if track_id not in tracks_data:
                tracks_data[track_id] = {'faces': [], 'sils': [], 'last_seen': frame_idx}
            tracks_data[track_id]['last_seen'] = frame_idx

            crop = frame[t:b, l:r]
            if crop.size == 0:
                continue

            # Save a detected crop for debugging
            crop_fname = os.path.join(DETECTED_DIR, f"frame{frame_idx}_track{track_id}.jpg")
            cv2.imwrite(crop_fname, crop)

            # 1) Face attempt on crop
            face_emb = get_face_embedding_from_image(crop, detector_backend='opencv', enforce=False)
            if face_emb is not None:
                tracks_data[track_id]['faces'].append((frame_idx, face_emb))
                # keep at most last few
                if len(tracks_data[track_id]['faces']) > 8:
                    tracks_data[track_id]['faces'].pop(0)

            # 2) Silhouette for gait
            sil = silhouette_from_crop(crop)
            tracks_data[track_id]['sils'].append(sil)
            if len(tracks_data[track_id]['sils']) > TRACK_SIL_BUFFER:
                tracks_data[track_id]['sils'].pop(0)

            # Evaluate the track for matching
            face_sim = None
            gait_sim = None
            fused_score = None
            match_flag = False

            # face-based decision (use most recent face)
            if stored_face_emb is not None and len(tracks_data[track_id]['faces']) > 0:
                # use last face
                last_face_emb = tracks_data[track_id]['faces'][-1][1]
                face_sim = float(np.dot(stored_face_emb / np.linalg.norm(stored_face_emb), last_face_emb / np.linalg.norm(last_face_emb)))
                if face_sim >= FACE_SIM_THRESHOLD:
                    fused_score = face_sim  # face dominates
                    match_flag = True

            # gait-based decision (if OpenGait available and enough silhouettes)
            if not match_flag and USE_OPENGAIT and gait_model is not None and len(tracks_data[track_id]['sils']) >= SILHOUETTE_MIN_FRAMES:
                # write temp sil frames
                tmp_dir = os.path.join('tmp_tracks', f'track_{track_id}')
                os.makedirs(tmp_dir, exist_ok=True)
                # select last SILHOUETTE_MIN_FRAMES frames
                sel = tracks_data[track_id]['sils'][-SILHOUETTE_MIN_FRAMES:]
                for i, im in enumerate(sel):
                    cv2.imwrite(os.path.join(tmp_dir, f"{i:04d}.png"), im)
                try:
                    emb = compute_gait_embedding_opengait(gait_model, gait_cfg, tmp_dir)
                    if emb is not None and stored_gait_emb is not None:
                        gait_sim = cosine_similarity(stored_gait_emb, emb)
                        if gait_sim >= GAIT_SIM_THRESHOLD:
                            fused_score = gait_sim
                            match_flag = True
                        else:
                            # compute weighted fusion if face exists
                            if face_sim is not None:
                                fused_score = WEIGHT_FACE * face_sim + WEIGHT_GAIT * gait_sim
                                if fused_score >= FACE_SIM_THRESHOLD:  # some fused threshold
                                    match_flag = True
                except Exception as e:
                    print('[WARN] Gait embedding failed for track', track_id, e)

            # Log + Save if match
            saved_path = ''
            if match_flag:
                found_matches += 1
                ts = time.strftime('%Y%m%d_%H%M%S')
                match_fname = os.path.join(MATCHED_DIR, f"match_frame{frame_idx}_track{track_id}_{ts}.jpg")
                # annotate
                out_frame = frame.copy()
                cv2.rectangle(out_frame, (l, t), (r, b), (0,255,0), 2)
                label = f"MATCH id{track_id}"
                if fused_score is not None:
                    label += f" {fused_score:.2f}"
                cv2.putText(out_frame, label, (l, max(0, t-10)), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)
                cv2.imwrite(match_fname, out_frame)
                saved_path = match_fname
                print(f"[MATCH] Frame {frame_idx} track {track_id} saved to {match_fname} (face_sim={face_sim}, gait_sim={gait_sim}, fused={fused_score})")

            # Write log entry
            bbox = f"{l},{t},{r},{b}"
            append_log([time.strftime('%Y-%m-%d %H:%M:%S'), frame_idx, track_id, bbox, face_sim, gait_sim, fused_score, match_flag, saved_path])

        # Optional: cleanup old tracks_data entries not seen recently
        to_delete = []
        for tid, d in tracks_data.items():
            if frame_idx - d['last_seen'] > 300:  # not seen for 300 frames
                to_delete.append(tid)
        for tid in to_delete:
            del tracks_data[tid]

        # display
        disp = cv2.resize(frame, (min(1000, frame.shape[1]), int(frame.shape[0]*min(1000/frame.shape[1],1))))
        cv2.imshow('Combined Surveillance', disp)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print('[INFO] User exit')
            break

        t1 = time.time()
        # print per-frame timing
        print(f"[TIMING] Frame {frame_idx} processed in {(t1-t0):.2f}s | active tracks: {len(tracks_data)}")

    cap.release()
    cv2.destroyAllWindows()
    conn.close()

    print('[INFO] Processing complete. Matches found:', found_matches)

# ------------------------
# helpers: fusion & similarity
# ------------------------

def compute_gait_embedding_opengait(model, cfg, silhouette_dir):
    # wrapper referencing previously imported function if present
    return compute_gait_embedding_opengait_inner(model, cfg, silhouette_dir)


def compute_gait_embedding_opengait_inner(model, cfg, silhouette_dir):
    # inlined minimal implementation using OpenGait's load_silhouettes & model
    seq = load_silhouettes(silhouette_dir)
    if seq is None:
        return None
    seq_t = torch.tensor(seq).unsqueeze(0).float()
    with torch.no_grad():
        features = model(seq_t)
        emb = features['embeddings'].cpu().numpy()[0]
    return emb


def cosine_similarity(a, b):
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)
    return float(np.dot(a, b))

# ------------------------
# entrypoint
# ------------------------
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Combined Face+Gait Surveillance')
    parser.add_argument('--target_face', type=str, help='Path to target face image (jpg/png)')
    parser.add_argument('--target_walk', type=str, help='Path to target walking video (optional)')
    parser.add_argument('--video', type=str, required=True, help='Surveillance video path')
    parser.add_argument('--name', type=str, default='target_person', help='Name to store in DB')
    args = parser.parse_args()

    combined_pipeline(args.target_face, args.target_walk, args.video, args.name)
