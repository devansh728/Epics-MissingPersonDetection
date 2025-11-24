# 🧠 Missing Person Detection – Full Prototype Specification

You are an advanced software architecture & development AI.  
Your task: generate a fully working prototype for a Missing Person Detection & AI surveillance system, consisting of modular backend services and a Streamlit frontend. The system will operate on SQLite and integrate geohashing + route prediction.

---

## 🟦 Phase 1 — Base Technologies & Architecture

- Python
- Streamlit (frontend UI)
- SQLite database
- LangGraph for agent-based microservices
- Multimedia processing with OpenCV
- Geohashing & minimal route prediction engine
- Optional libraries: transformers, torch, tensorflow (CPU), librosa, soundfile, smaller whisper model, or use pre-trained models from Hugging Face model hub for NLP, emotion detection & voice transcription (free, open source, ready-to-use, CPU-compatible)
- **Reuse existing surveillance Python code:**  
  `surveillance.py` (face detection from video; do **not** rewrite)

- **Deployment:** The final system must run locally.

- **Note:** My python version is Python 3.11.9, installed dependencies according to that only in virtual enviroment only.

---

## 🟥 Phase 2 — Database Schema (SQLite)

**Create the following SQLite tables:**

### `missing_cases`
| id | name | age | description | last_seen_geohash | date_reported | embedding | transcript | emotion |

### `videos_scanned`
| id | case_id | video_name | matches_found | timestamp |

### `match_logs`
| id | case_id | frame | score | saved_img_path | timestamp |

---

## 🟩 Phase 3 — Streamlit Frontend Pages

**Create a web UI with these sections:**

1. **File New Missing Complaint**
    - User uploads: 
        - Face photo
        - Optional voice description
        - Optional additional images
        - Last seen location (map input)
    - System actions:
        - Speech-to-text transcription
        - Emotion recognition
        - NLP key info extraction
        - Save result to DB

2. **AI Investigation Dashboard (Police mode)**
    - Shows all cases, face images, predicted geohashes, movement predictions, and path probability

3. **CCTV Video Scan Page**
    - User uploads CCTV video
    - System runs face-matching logic from `surveillance.py`:
        - Extracts frames, checks for face matches, saves & displays matched frames in the UI

---

## 🟨 Phase 4 — Agent Architecture (LangGraph)

**Implement the following agents:**

- **Agent 1: Complaint NLP Agent**  
  Extracts metadata using LLM; stores results in DB

- **Agent 2: Voice-to-Text Agent**  
  Uses Whisper/Google STT; returns transcript + emotional state

- **Agent 3: Geo-Intelligence Agent**  
  Converts lat/lon → geohash; calculates surrounding geohashes

- **Agent 4: Route Prediction Agent**  
  Applies random-directional walk with human speed ~4 km/h; simulates urban bias; predicts next 4–8 geohashes

- **Agent 5: Video Scan Agent**  
  Runs detection using `surveillance.py` (must reuse)

- **Agent 6: Notifications Agent**  
  Logs results, displays UI output, triggers alerts if matches found

---

## 🟧 Phase 5 — Geohashing Integration

- Use Python geohash library:
    ```
    import geohash
    loc = geohash.encode(lat, lon, precision=8)
    ```
- Store geohashes in the DB

---

## 🟥 Phase 6 — Route Prediction Engine

- Directional walk model (random, human walking speed 3.5–5 km/h)
- Urban path bias
- Output sequence:
    ```
    [(lat1, lon1, geohash1), (lat2, lon2, geohash2), ...]
    ```

---

## 🟩 Phase 7 — Face Recognition Code Integration

- Integrate the **existing** face-matching/video-scanning logic from `surveillance.py`  
  (uses YOLOv8 + DeepFace + tracking)
- Expose an API:
    ```
    def scan_video_for_person(case_id, video_file):
        return list_of_matching_frames
    ```

---

## 🟦 Phase 8 — Output & Reporting

- **After scan:**  
    - Save matched frames
    - Store results in DB
    - Show results in Streamlit UI
    - Generate:
        - Summary report
        - Time & location of matches
        - Confidence score

---

## 🟪 Phase 9 — Deliverables

- Complete Python project repository
- Streamlit app
- All agents as separate files
- SQLite database file
- Working geohashing + route prediction
- CCTV face detection functionality from `surveillance.py` (no rewriting)
- Demo-ready prototype
- Example dummy data for testing
- Fake sample video/image generator (if needed)
- Step-by-step instructions (Windows/Colab)
- One-command startup script

---

## 🏁 Final Condition

- **You must NOT rewrite or replace** the face-matching logic in `surveillance.py`.  
- All surveillance/person-matching code must call/reuse this existing file.
