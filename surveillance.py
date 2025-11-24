"""
surveillance_yolo_deepface.py
YOLOv8 (person detector) + DeepFace (Facenet512) surveillance script.
Saves detected person crops and matched frames to disk and logs output to terminal.
"""

import os
import cv2
import time
import sqlite3
import numpy as np
from ultralytics import YOLO
from deepface import DeepFace

# -------------
# Config
# -------------
YOLO_MODEL = "yolov8n.pt"  # small and fast
DB_PATH = "face_db.sqlite"
OUTPUT_DIR = "output_frames"
DETECTED_DIR = os.path.join(OUTPUT_DIR, "detected_people")
MATCHED_DIR = os.path.join(OUTPUT_DIR, "matches")
FRAME_SAVE_EVERY = 30  # save a detected-person crop every N frames (for debugging)
FRAME_SKIP = 5  # process every FRAME_SKIP-th frame (1 = all frames)
SIMILARITY_THRESHOLD = 0.55  # cosine similarity threshold for Facenet512
MAX_PERSON_BOX_AREA_RATIO = (
    0.95  # ignore boxes that are almost full frame (can be false person)
)


# -------------
# Utilities: File / DB
# -------------
def ensure_dirs():
    os.makedirs(DETECTED_DIR, exist_ok=True)
    os.makedirs(MATCHED_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def init_database(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS persons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            embedding BLOB
        )
    """
    )
    conn.commit()
    return conn


def save_embedding(conn, name, embedding: np.ndarray):
    cur = conn.cursor()
    emb_bytes = embedding.astype(np.float32).tobytes()
    cur.execute(
        "INSERT OR REPLACE INTO persons (name, embedding) VALUES (?, ?)",
        (name, emb_bytes),
    )
    conn.commit()


def load_embedding(conn, name):
    cur = conn.cursor()
    cur.execute("SELECT embedding FROM persons WHERE name=?", (name,))
    row = cur.fetchone()
    if row:
        return np.frombuffer(row[0], dtype=np.float32)
    return None


# -------------
# Embedding / similarity
# -------------
def cosine_similarity(a: np.ndarray, b: np.ndarray):
    if a is None or b is None:
        return -1.0
    a = a.astype(np.float32)
    b = b.astype(np.float32)
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return -1.0
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)
    return float(np.dot(a, b))


def get_face_embedding_from_image(img_bgr):
    """
    Input: BGR numpy image (cropped face or full image)
    Returns: 512-dim embedding (np.float32) or None
    Uses multiple fallback strategies to extract face embeddings even from challenging images.
    """
    # Strategy 1: Try with opencv detector (fast, less strict)
    try:
        faces = DeepFace.extract_faces(
            img_path=img_bgr,
            detector_backend="opencv",
            enforce_detection=False,  # More lenient
            align=True,
        )

        if faces and len(faces) > 0:
            # Choose largest detected face
            face_candidates = []
            for f in faces:
                face_img = f.get("face")
                area = 0
                fa = f.get("facial_area")
                if fa:
                    area = fa.get("w", 0) * fa.get("h", 0)
                face_candidates.append((area, face_img))

            face_candidates.sort(key=lambda x: x[0], reverse=True)
            chosen_face = face_candidates[0][1]

            try:
                rep = DeepFace.represent(
                    img_path=chosen_face,
                    model_name="Facenet512",
                    enforce_detection=False,
                )
                emb = np.array(rep[0]["embedding"], dtype=np.float32)
                print(f"[INFO] Successfully extracted face embedding (opencv detector)")
                return emb
            except Exception as e:
                print(f"[WARNING] Failed to get embedding from extracted face: {e}")
    except Exception as e:
        print(f"[WARNING] Face extraction failed: {e}")

    # Strategy 2: Try direct representation with retinaface (more accurate)
    try:
        rep = DeepFace.represent(
            img_path=img_bgr,
            model_name="Facenet512",
            detector_backend="retinaface",
            enforce_detection=False,
        )
        emb = np.array(rep[0]["embedding"], dtype=np.float32)
        print(f"[INFO] Successfully extracted face embedding (retinaface detector)")
        return emb
    except Exception as e:
        print(f"[WARNING] Retinaface detection failed: {e}")

    # Strategy 3: Final fallback - use opencv with no enforcement
    try:
        rep = DeepFace.represent(
            img_path=img_bgr,
            model_name="Facenet512",
            detector_backend="opencv",
            enforce_detection=False,
        )
        emb = np.array(rep[0]["embedding"], dtype=np.float32)
        print(f"[INFO] Successfully extracted face embedding (fallback opencv)")
        return emb
    except Exception as e:
        print(f"[ERROR] All face detection strategies failed: {e}")
        return None


# -------------
# Main pipeline
# -------------
def surveillance_yolo_deepface(target_image_path, video_path):
    ensure_dirs()
    conn = init_database()

    print("\n[INFO] Loading YOLOv8 model...")
    model = YOLO(YOLO_MODEL)  # will auto-download yolov8n weights if not present

    print("[INFO] Encoding target person image (DeepFace Facenet512).")
    target_bgr = cv2.imread(target_image_path)
    if target_bgr is None:
        print(f"[ERROR] Cannot load target image at: {target_image_path}")
        return {"success": False, "error": "Cannot load target image", "matches": []}

    target_emb = get_face_embedding_from_image(target_bgr)
    if target_emb is None:
        print(
            "[ERROR] Could not extract embedding from target image. Make sure target image has a clear face."
        )
        return {
            "success": False,
            "error": "Could not extract embedding from target image",
            "matches": [],
        }

    save_embedding(conn, "target_person", target_emb)
    print("[OK] Target embedding saved to DB.")

    stored_emb = load_embedding(conn, "target_person")
    if stored_emb is None:
        print("[ERROR] Failed to load stored embedding from DB.")
        return {
            "success": False,
            "error": "Failed to load stored embedding from DB",
            "matches": [],
        }

    # open video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"[ERROR] Failed to open video: {video_path}")
        return {
            "success": False,
            "error": f"Failed to open video: {video_path}",
            "matches": [],
        }

    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    print(f"[INFO] Video opened. FPS={fps:.2f}")

    frame_idx = 0
    found_any = False
    last_save_idx = 0
    matches = []  # Store match information

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_idx += 1

        # frame skipping for speed
        if frame_idx % FRAME_SKIP != 0:
            continue

        t0 = time.time()
        h, w = frame.shape[:2]
        print(f"\n[LOG] Frame {frame_idx} - size: {w}x{h}")

        # Run YOLO detection (person class id = 0)
        # ultralytics returns results; use model.predict or model(frame)
        results = model(
            frame, imgsz=640, conf=0.25, iou=0.45
        )  # adjust conf threshold if needed
        # results is list-like; take first
        try:
            dets = results[0].boxes.cpu().numpy()
            # boxes: xyxy, confidence, cls
        except Exception:
            dets = []

        persons = []
        if hasattr(results[0], "boxes") and len(results[0].boxes) > 0:
            for box in results[0].boxes:
                cls = int(box.cls.cpu().numpy()[0])
                conf = float(box.conf.cpu().numpy()[0])
                x1, y1, x2, y2 = map(int, box.xyxy.cpu().numpy()[0])
                # keep only person class (0)
                if cls != 0:
                    continue
                # clamp
                x1 = max(0, x1)
                y1 = max(0, y1)
                x2 = min(w - 1, x2)
                y2 = min(h - 1, y2)
                box_w = x2 - x1
                box_h = y2 - y1
                # filter suspiciously big boxes (full-frame false positives)
                if (box_w * box_h) > (w * h * MAX_PERSON_BOX_AREA_RATIO):
                    continue
                persons.append((x1, y1, x2, y2, conf))

        if len(persons) == 0:
            print("[LOG] No person boxes detected by YOLO in this frame.")
            # optionally, fallback to face detect on entire frame (skip for speed)
            continue

        print(f"[LOG] YOLO detected {len(persons)} person(s).")

        # Examine each person crop for face + embedding
        for pid, (x1, y1, x2, y2, conf) in enumerate(persons):
            crop = frame[y1:y2, x1:x2].copy()
            if crop.size == 0:
                continue

            # Save some detected crops for debugging
            if (frame_idx - last_save_idx) >= FRAME_SAVE_EVERY:
                fname = os.path.join(
                    DETECTED_DIR, f"frame{frame_idx}_person{pid+1}.jpg"
                )
                cv2.imwrite(fname, crop)
                last_save_idx = frame_idx
                print(f"    [SAVE] Saved detected person crop: {fname}")

            # Attempt face embedding on the person crop
            emb = get_face_embedding_from_image(crop)
            if emb is None:
                print(
                    f"    > Person #{pid+1}: No face found inside person box (or embedding failed)."
                )
                continue

            similarity = cosine_similarity(stored_emb, emb)
            print(
                f"    > Person #{pid+1} embedding similarity = {similarity:.4f} (conf={conf:.2f})"
            )

            if similarity >= SIMILARITY_THRESHOLD:
                found_any = True
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                match_fname = os.path.join(
                    MATCHED_DIR, f"match_frame{frame_idx}_person{pid+1}_{timestamp}.jpg"
                )
                # draw bounding box + label on original frame
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(
                    frame,
                    f"MATCH {similarity:.2f}",
                    (x1, max(0, y1 - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    (0, 255, 0),
                    2,
                )
                cv2.imwrite(match_fname, frame)

                # Store match information
                matches.append(
                    {
                        "frame": frame_idx,
                        "person_id": pid + 1,
                        "similarity": round(similarity, 4),
                        "confidence": round(conf, 2),
                        "image_path": match_fname,
                        "timestamp": timestamp,
                    }
                )

                print("\n========== MATCH FOUND ==========")
                print(
                    f"  Frame: {frame_idx}, Person #{pid+1}, Similarity: {similarity:.4f}"
                )
                print(f"  Saved matched frame to: {match_fname}")
                print("=================================\n")
                # optional: break if you want to stop at first match
                # break

        # show frame (optional)
        # convert to smaller window for display performance
        display_frame = frame.copy()
        maxw = 1000
        if display_frame.shape[1] > maxw:
            scale = maxw / display_frame.shape[1]
            display_frame = cv2.resize(
                display_frame,
                (
                    int(display_frame.shape[1] * scale),
                    int(display_frame.shape[0] * scale),
                ),
            )
        cv2.imshow("Surveillance (press q to quit)", display_frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            print("[INFO] Exiting on user request.")
            break

        t1 = time.time()
        print(f"[TIMING] Frame {frame_idx} processed in {(t1 - t0):.2f}s")

    cap.release()
    cv2.destroyAllWindows()
    conn.close()

    if found_any:
        print(
            "\n[SUCCESS] One or more matches were found. Check the `output_frames/matches` folder."
        )
    else:
        print(
            "\n[INFO] Target person NOT found in the video. Check `output_frames/detected_people` for crops to debug."
        )
    print("[INFO] Done.")

    # Return results
    return {
        "success": True,
        "matches_found": len(matches),
        "matches": matches,
        "total_frames": frame_idx,
    }


# -------------
# Run as script
# -------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="YOLOv8 + DeepFace surveillance")
    parser.add_argument(
        "--target",
        type=str,
        default="target-person.jpg",
        help="Path to target person image",
    )
    parser.add_argument(
        "--video", type=str, default="yest-video.mp4", help="Path to input video"
    )
    parser.add_argument(
        "--yolo", type=str, default=YOLO_MODEL, help="YOLO model name or .pt path"
    )
    parser.add_argument(
        "--thresh",
        type=float,
        default=SIMILARITY_THRESHOLD,
        help="Cosine similarity threshold",
    )
    parser.add_argument(
        "--skip",
        type=int,
        default=FRAME_SKIP,
        help="Frame skip (process every Nth frame)",
    )
    args = parser.parse_args()

    # update config from args
    YOLO_MODEL = args.yolo
    SIMILARITY_THRESHOLD = args.thresh
    FRAME_SKIP = max(1, int(args.skip))

    surveillance_yolo_deepface(args.target, args.video)
