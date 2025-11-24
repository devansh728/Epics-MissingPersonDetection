"""
Gemini API Configuration for NLP Tasks
"""
import os
from typing import Optional

# Gemini API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Model Selection
GEMINI_TEXT_MODEL = "gemini-pro"
GEMINI_VISION_MODEL = "gemini-pro-vision"

# Retry Configuration
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2
REQUEST_TIMEOUT = 30

# Rate Limiting
MAX_REQUESTS_PER_MINUTE = 60

# Prompt Templates for NLP Tasks
METADATA_EXTRACTION_PROMPT = """
Analyze the following text about a missing person and extract structured metadata.

Text: {text}

Extract and return in JSON format:
1. Names mentioned (people, places)
2. Locations (cities, landmarks, addresses)
3. Dates and times mentioned
4. Important keywords and descriptive terms

Return ONLY valid JSON with keys: names, locations, dates, keywords
"""

EMOTION_ANALYSIS_PROMPT = """
Analyze the emotional tone of this missing person report.

Text: {text}

Determine the primary emotion from these categories:
- Anxious/Worried (genuine concern, fear, panic)
- Sad (grief, depression, upset)
- Angry (frustration, fury)
- Happy/Relieved (joy, relief, happiness)
- Joking (humorous, not serious, playful)
- Concerned (serious concern without extreme emotion)

Return ONLY the emotion category name, nothing else.
"""

LOCATION_EXTRACTION_PROMPT = """
Extract location information from this text about a missing person in Bhopal/Sehore region.

Text: {text}

Known locations in the region:
- Bhopal Junction Railway Station
- Sehore Bus Stand
- MP Nagar Zone 1
- Habibganj Railway Station
- New Market Bhopal
- BRTS Corridor - Roshanpura
- Sehore Railway Station
- DB Mall Bhopal
- Bhopal ISBT (Bus Stand)
- Ashoka Garden Market

If you find a matching location, return JSON with: {{"name": "location_name", "found": true}}
If no location found, return: {{"name": "", "found": false}}

Return ONLY valid JSON.
"""

AUDIO_TRANSCRIPTION_PROMPT = """
Transcribe the following audio content accurately.
Focus on clarity and include all spoken words.
"""

def get_gemini_api_key() -> Optional[str]:
    """
    Get Gemini API key from environment variable.
    Returns None if not configured.
    """
    api_key = os.getenv("GEMINI_API_KEY", GEMINI_API_KEY)
    if not api_key or api_key == "":
        print("[WARNING] GEMINI_API_KEY not configured. Falling back to simple methods.")
        return None
    return api_key

def is_gemini_configured() -> bool:
    """Check if Gemini API is properly configured."""
    return get_gemini_api_key() is not None

def get_model_config():
    """Get Gemini model configuration."""
    return {
        "text_model": GEMINI_TEXT_MODEL,
        "vision_model": GEMINI_VISION_MODEL,
        "max_retries": MAX_RETRIES,
        "retry_delay": RETRY_DELAY_SECONDS,
        "timeout": REQUEST_TIMEOUT
    }
