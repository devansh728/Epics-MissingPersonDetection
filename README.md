# 🔍 Missing Person Detection & AI Surveillance System

> An intelligent AI-powered system to help locate missing persons using CCTV surveillance, facial recognition, and predictive route analysis for the Bhopal/Sehore region.

## 🌟 What Does This Do?

Imagine someone goes missing. Every second counts. This system:

1. **📝 Takes a complaint** - Upload a photo, describe the person, tell us where they were last seen
2. **🧠 Analyzes with AI** - Uses Google Gemini to understand emotions, extract details, and validate the complaint
3. **🗺️ Predicts their route** - Calculates where they might have gone based on time and location
4. **📹 Scans CCTV footage** - Automatically checks multiple CCTV cameras along the predicted route
5. **🎯 Finds matches** - Uses facial recognition to detect the missing person in video feeds
6. **📧 Alerts you** - Sends email notifications with detailed PDF reports when matches are found

## ✨ Key Features

### 🤖 Smart AI Analysis
- **Emotion Detection** - Filters out non-serious complaints (jokes, pranks)
- **Location Extraction** - Identifies specific landmarks in Bhopal/Sehore
- **Time-Based Prediction** - Calculates search radius based on how long they've been missing

### 🎥 Automated CCTV Scanning
- **Background Processing** - Scans multiple CCTVs without blocking the system
- **Face Recognition** - Uses DeepFace + YOLOv8 for accurate person detection
- **Real-Time Progress** - Live updates on scanning status via WebSocket

### 📊 Professional Reporting
- **PDF Reports** - Detailed reports for each CCTV scan and aggregate summaries
- **Blockchain Verification** - Tamper-proof report hashing for legal validity
- **Email Notifications** - Automatic alerts with PDF attachments

### 🌐 User-Friendly Dashboard
- **Active Cases** - View all missing person cases at a glance
- **Scan Progress** - Real-time progress bars and status updates
- **Match Results** - See detection counts and download reports

## 🚀 Quick Start

### Prerequisites
```bash
Python 3.8+
Webcam or CCTV footage
Google Gemini API key
```

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd missing
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
Create a `.env` file:
```env
GEMINI_API_KEY=your_gemini_api_key_here
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_gmail_app_password
```

4. **Run the application**
```bash
streamlit run app.py
```

5. **Open your browser**
Navigate to `http://localhost:8501`

## 📁 Project Structure

```
missing/
├── agents/              # AI agents (NLP, Geo, Video, Scanning)
├── config/              # Configuration files (Gemini, Email, Locations)
├── pages/               # Streamlit pages (Complaint, Dashboard, Video Scan)
├── utils/               # Utilities (Routes, Notifications, WebSocket, Blockchain)
├── uploads/             # Uploaded photos
├── reports/             # Generated PDF reports
├── output_frames/       # Detected matches
├── database.py          # SQLite database management
├── surveillance.py      # YOLOv8 + DeepFace face recognition
└── app.py              # Main Streamlit application
```

## 🎯 How It Works

### 1. File a Complaint
- Upload a clear photo of the missing person
- Provide name, age, and description
- Select last seen location from 10 CCTV locations
- Specify when they went missing

### 2. AI Processing
- **NLP Agent**: Extracts metadata, analyzes emotion
- **Emotion Validator**: Filters non-serious complaints
- **Geo Agent**: Converts location to geohash coordinates
- **Route Agent**: Predicts likely path based on time elapsed

### 3. Background Scanning
- Automatically selects up to 3 CCTVs along predicted route
- Scans video footage using YOLOv8 for person detection
- Compares faces using DeepFace Facenet512
- Generates individual and aggregate PDF reports

### 4. Notifications
- Email sent when complaint is filed
- Real-time WebSocket updates during scanning
- Email with PDF report when scanning completes
- Blockchain-verified reports for legal use

## 🛠️ Technology Stack

- **Frontend**: Streamlit
- **AI/ML**: Google Gemini 2.5 Flash, YOLOv8, DeepFace
- **Database**: SQLite
- **Workflow**: LangGraph
- **Face Recognition**: Facenet512
- **Object Detection**: YOLOv8n
- **PDF Generation**: ReportLab
- **Email**: SMTP (Gmail)
- **Geospatial**: Geohash

## 📍 Coverage Area

Currently configured for **Bhopal/Sehore region** with 10 CCTV locations:
- Bhopal Junction Railway Station
- Habibganj Railway Station
- MP Nagar Zone 1
- New Market Bhopal
- DB Mall Bhopal
- Sehore Bus Stand
- Sehore Railway Station
- BRTS Corridor - Roshanpura
- Bhopal ISBT
- Ashoka Garden Market

## 🔒 Privacy & Security

- All data stored locally in SQLite database
- Blockchain hashing for report verification
- No external data sharing
- Secure email notifications via Gmail SMTP

## 🐛 Troubleshooting

### Face Detection Fails
- Ensure uploaded photo has a clear, visible face
- Try photos with good lighting and frontal view
- System uses 3-tier fallback (opencv → retinaface → fallback)

### Email Not Sending
- Check `.env` file has correct Gmail credentials
- Use Gmail App Password, not regular password
- Enable "Less secure app access" in Gmail settings

### Dashboard Crashes
- Run `python fix_timestamps.py` to fix old data
- Run `python migrate_db.py` to update database schema

## 📧 Contact

For questions or support, please contact the development team.

## 📄 License

This project is developed for educational and humanitarian purposes.

---

**Made with ❤️ to help reunite families**
