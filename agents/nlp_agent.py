"""
NLP and Voice Agents using Google Gemini API with fallback mechanisms
"""
import sys
import os
import json
import time

# Suppress warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# Import Gemini configuration
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.gemini_config import (
    get_gemini_api_key, 
    is_gemini_configured,
    METADATA_EXTRACTION_PROMPT,
    EMOTION_ANALYSIS_PROMPT,
    LOCATION_EXTRACTION_PROMPT,
    MAX_RETRIES,
    RETRY_DELAY_SECONDS
)

# Try to import Gemini API
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("[WARNING] google-generativeai not installed. Using fallback methods.")

# Initialize Gemini if available
if GEMINI_AVAILABLE and is_gemini_configured():
    try:
        genai.configure(api_key=get_gemini_api_key())
        gemini_model = genai.GenerativeModel('gemini-pro')
        print("[INFO] Gemini API initialized successfully.")
    except Exception as e:
        print(f"[WARNING] Failed to initialize Gemini API: {e}")
        GEMINI_AVAILABLE = False
else:
    GEMINI_AVAILABLE = False
    print("[INFO] Using fallback NLP methods (Gemini not configured).")


def call_gemini_with_retry(prompt, max_retries=MAX_RETRIES):
    """
    Call Gemini API with retry logic.
    Returns response text or None on failure.
    """
    if not GEMINI_AVAILABLE:
        return None
    
    for attempt in range(max_retries):
        try:
            response = gemini_model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"[WARNING] Gemini API call failed (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(RETRY_DELAY_SECONDS)
    
    return None


def extract_metadata(text):
    """
    Extract metadata from text using Gemini API with fallback.
    """
    # Try Gemini API first
    if GEMINI_AVAILABLE:
        try:
            prompt = METADATA_EXTRACTION_PROMPT.format(text=text)
            response = call_gemini_with_retry(prompt)
            
            if response:
                # Parse JSON response
                # Clean response (remove markdown code blocks if present)
                response = response.strip()
                if response.startswith("```json"):
                    response = response[7:]
                if response.startswith("```"):
                    response = response[3:]
                if response.endswith("```"):
                    response = response[:-3]
                response = response.strip()
                
                data = json.loads(response)
                return data
        except Exception as e:
            print(f"[WARNING] Gemini metadata extraction failed: {e}. Using fallback.")
    
    # Fallback: Simple keyword extraction
    try:
        data = {
            "names": [],
            "locations": [],
            "dates": [],
            "keywords": []
        }
        
        # Simple heuristic for prototype
        words = text.split()
        for word in words:
            if word and len(word) > 2 and word[0].isupper():
                data["keywords"].append(word)
        
        # Extract location references for Bhopal/Sehore
        location_keywords = [
            "bhopal", "sehore", "junction", "station", "bus stand", "market",
            "mp nagar", "habibganj", "isbt", "brts", "ashoka garden", "db mall"
        ]
        
        text_lower = text.lower()
        for keyword in location_keywords:
            if keyword in text_lower:
                data["locations"].append(keyword)
        
        return data
    except Exception as e:
        print(f"[ERROR] Fallback metadata extraction failed: {e}")
        return {"names": [], "locations": [], "dates": [], "keywords": []}


def transcribe_audio(audio_path):
    """
    Transcribe audio to text using Gemini API with fallback.
    Note: Gemini Pro doesn't support audio directly, so we use fallback.
    For production, consider using Gemini 1.5 Pro or Google Speech-to-Text API.
    """
    try:
        # Check if file exists
        if not os.path.exists(audio_path):
            return "Audio file not found."
        
        # Fallback: Return placeholder
        # In production, integrate Google Speech-to-Text API or Gemini 1.5 Pro
        return f"[Audio transcription not available - file: {os.path.basename(audio_path)}]"
        
    except Exception as e:
        print(f"[ERROR] Audio transcription failed: {e}")
        return "Transcription failed."


def analyze_emotion(text):
    """
    Analyze emotion from text using Gemini API with fallback.
    """
    # Try Gemini API first
    if GEMINI_AVAILABLE:
        try:
            prompt = EMOTION_ANALYSIS_PROMPT.format(text=text)
            response = call_gemini_with_retry(prompt)
            
            if response:
                # Clean and return emotion
                emotion = response.strip()
                # Validate emotion is one of expected categories
                valid_emotions = [
                    "Anxious/Worried", "Sad", "Angry", "Happy/Relieved", 
                    "Joking", "Concerned"
                ]
                for valid_emotion in valid_emotions:
                    if valid_emotion.lower() in emotion.lower():
                        return valid_emotion
                return emotion  # Return as-is if not in list
        except Exception as e:
            print(f"[WARNING] Gemini emotion analysis failed: {e}. Using fallback.")
    
    # Fallback: Simple keyword-based emotion detection
    try:
        text_lower = text.lower()
        
        # Check for joking/humor indicators
        if any(word in text_lower for word in ["haha", "lol", "joke", "joking", "kidding", "funny", "laugh"]):
            return "Joking"
        
        # Check for happy/relieved
        if any(word in text_lower for word in ["happy", "relieved", "glad", "joy", "found"]):
            return "Happy/Relieved"
        
        # Check for worried/anxious
        if any(word in text_lower for word in ["worried", "anxious", "scared", "afraid", "panic", "fear"]):
            return "Anxious/Worried"
        
        # Check for sad
        if any(word in text_lower for word in ["sad", "crying", "depressed", "upset", "heartbroken"]):
            return "Sad"
        
        # Check for angry
        if any(word in text_lower for word in ["angry", "furious", "mad", "rage"]):
            return "Angry"
        
        # Default to concerned
        return "Concerned"
            
    except Exception as e:
        print(f"[ERROR] Fallback emotion analysis failed: {e}")
        return "Unknown"


def extract_location_from_text(text):
    """
    Extract Bhopal/Sehore location references from text using Gemini API with fallback.
    """
    from config.bhopal_sehore_locations import get_location_by_name
    
    # Try Gemini API first
    if GEMINI_AVAILABLE:
        try:
            prompt = LOCATION_EXTRACTION_PROMPT.format(text=text)
            response = call_gemini_with_retry(prompt)
            
            if response:
                # Parse JSON response
                response = response.strip()
                if response.startswith("```json"):
                    response = response[7:]
                if response.startswith("```"):
                    response = response[3:]
                if response.endswith("```"):
                    response = response[:-3]
                response = response.strip()
                
                data = json.loads(response)
                
                if data.get("found") and data.get("name"):
                    coords = get_location_by_name(data["name"])
                    if coords:
                        return {
                            "name": data["name"],
                            "lat": coords["lat"],
                            "lon": coords["lon"],
                            "geohash": coords["geohash"]
                        }
        except Exception as e:
            print(f"[WARNING] Gemini location extraction failed: {e}. Using fallback.")
    
    # Fallback: Simple keyword matching
    try:
        text_lower = text.lower()
        
        # Check for known locations
        location_names = [
            "bhopal junction", "sehore bus stand", "mp nagar", "habibganj",
            "new market", "brts", "roshanpura", "sehore station", "db mall",
            "isbt", "ashoka garden"
        ]
        
        for loc_name in location_names:
            if loc_name in text_lower:
                coords = get_location_by_name(loc_name)
                if coords:
                    return {
                        "name": loc_name,
                        "lat": coords["lat"],
                        "lon": coords["lon"],
                        "geohash": coords["geohash"]
                    }
        
        return None
    except Exception as e:
        print(f"[ERROR] Fallback location extraction failed: {e}")
        return None

