# Missing Person Detection System - Bhopal/Sehore Region

## Overview
Complete Missing Person Detection & AI surveillance system specifically designed for Bhopal/Sehore district. Features include:
- **10 Fixed CCTV Locations** with real coordinates
- **Regional Validation** (only accepts Bhopal/Sehore locations)
- **AI Route Prediction** biased toward known landmarks
- **Blockchain-style Reporting** with SHA256 hashing
- **Email Notifications** via Gmail SMTP
- **Hugging Face Models** for NLP, emotion detection, and voice transcription (CPU-compatible)

## Prerequisites
- Python 3.11+
- `surveillance.py` (must be in the root directory)
- Gmail account with App Password (for email notifications)

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Email (Optional)
To enable email notifications, set environment variables or edit `config/email_config.py`:
```python
SENDER_EMAIL = "your-email@gmail.com"
SENDER_PASSWORD = "your-app-password"  # Gmail App Password
```

To create a Gmail App Password:
1. Go to Google Account settings
2. Security → 2-Step Verification → App passwords
3. Generate a new app password for "Mail"

### 3. Initialize Database
The database will be automatically initialized on first run, including:
- Missing cases table
- CCTV locations (10 fixed locations in Bhopal/Sehore)
- Blockchain reports table
- Route predictions table

## Running the Application

### Start the Streamlit App
Double-click `run_app.bat` or run:
```bash
streamlit run app.py
```

## Features

### 1. File Missing Complaint
- Upload photo and details of missing person
- Select location from dropdown (10 CCTV locations) or enter coordinates
- Optional voice note upload
- AI analyzes emotion and extracts metadata
- System predicts likely movement route
- Email notification sent (if configured)

### 2. AI Investigation Dashboard
- View all active cases
- See predicted routes on map
- Monitor CCTV locations along predicted path
- View blockchain reports for matches
- Display CCTV network coverage

### 3. CCTV Video Scan
- Select case to scan for
- System recommends CCTV cameras based on route prediction
- Upload video or scan predicted CCTVs
- Generates blockchain report for matches
- Sends email alert when match found

## 10 CCTV Locations (Bhopal/Sehore)

1. **Bhopal Junction Railway Station** (23.2699, 77.4026)
2. **Sehore Bus Stand** (23.2020, 77.0847)
3. **MP Nagar Zone 1** (23.2327, 77.4278)
4. **Habibganj Railway Station** (23.2285, 77.4385)
5. **New Market Bhopal** (23.2599, 77.4126)
6. **BRTS Corridor - Roshanpura** (23.2156, 77.4304)
7. **Sehore Railway Station** (23.2000, 77.0833)
8. **DB Mall Bhopal** (23.2420, 77.4347)
9. **Bhopal ISBT (Bus Stand)** (23.2543, 77.4071)
10. **Ashoka Garden Market** (23.2156, 77.4481)

## Regional Features

### Location Validation
- System only accepts locations within Bhopal/Sehore district boundaries
- Lat: 22.9 to 23.5, Lon: 77.0 to 77.7

### Route Prediction
- Uses urban path model biased toward CCTV locations
- Predicts 5 steps of likely movement
- Matches predictions to nearest CCTV cameras
- Provides video paths for scanning

### Blockchain Reports
- SHA256 hash generated for each match report
- Includes case ID, location, confidence score, timestamp
- Stored in database for verification
- Included in email notifications

## AI Models (CPU-Compatible)

### NLP & Emotion
- Simple keyword-based extraction (prototype)
- Can be enhanced with Hugging Face transformers:
  - `dslim/bert-base-NER` for named entity recognition
  - `bhadresh-savani/distilbert-base-uncased-emotion` for emotion

### Voice Transcription
- Placeholder implementation (prototype)
- Can be enhanced with `openai/whisper-tiny` from Hugging Face

## Directory Structure
```
d:/dev/missing/
├── app.py                          # Main Streamlit app
├── database.py                     # Database management
├── requirements.txt                # Dependencies
├── surveillance.py                 # Face detection (existing)
├── config/
│   ├── bhopal_sehore_locations.py # CCTV locations
│   └── email_config.py            # Email settings
├── agents/
│   ├── graph.py                   # LangGraph workflow
│   ├── nlp_agent.py              # NLP & voice
│   ├── geo_agent.py              # Geohashing & validation
│   ├── video_agent.py            # Video scanning
│   └── notification_agent.py     # Email & blockchain
├── utils/
│   ├── geohash_utils.py          # Geohashing
│   ├── route_utils.py            # Route prediction
│   ├── blockchain_utils.py       # Blockchain hashing
│   └── notification_utils.py     # Email sending
└── pages/
    ├── 1_File_Complaint.py       # Complaint form
    ├── 2_Dashboard.py            # Investigation dashboard
    └── 3_Video_Scan.py           # Video scanning
```

## Notes
- For production use, uncomment Hugging Face model code in `agents/nlp_agent.py`
- CCTV video files should be placed at paths specified in configuration
- Email notifications require Gmail App Password configuration
- System runs entirely on CPU (no GPU required)
