from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Any, Optional

# Define State
class AgentState(TypedDict):
    case_id: int
    input_data: dict
    nlp_results: dict
    geo_results: dict
    route_results: dict
    scan_results: bool
    status: str
    error: Optional[str]
    cancelled: bool
    cancellation_reason: Optional[str]

# Import Agents
from .nlp_agent import extract_metadata, transcribe_audio, analyze_emotion, extract_location_from_text
from .geo_agent import process_location, predict_route
from .video_agent import scan_video

# Node Functions
def nlp_node(state: AgentState):
    print("--- NLP Agent ---")
    text = state['input_data'].get('description', '')
    voice_path = state['input_data'].get('voice_path')
    
    transcription = ""
    if voice_path:
        transcription = transcribe_audio(voice_path)
        text += " " + transcription
        
    metadata = extract_metadata(text)
    emotion = analyze_emotion(text)
    
    # Try to extract location from text
    location_from_text = extract_location_from_text(text)
    
    return {
        "nlp_results": {
            "metadata": metadata, 
            "emotion": emotion, 
            "full_text": text,
            "transcription": transcription,
            "location_from_text": location_from_text
        }
    }

def emotion_validation_node(state: AgentState):
    """
    Validate emotion to filter out non-serious complaints.
    Cancels complaints if emotion is happy, joking, or relieved.
    """
    print("--- Emotion Validation Agent ---")
    emotion = state['nlp_results'].get('emotion', '').lower()
    
    # Check if emotion indicates non-serious complaint
    cancel_emotions = ['happy', 'joking', 'laughing', 'relieved', 'happy/relieved']
    
    for cancel_emotion in cancel_emotions:
        if cancel_emotion in emotion:
            print(f"[CANCELLED] Complaint cancelled due to emotion: {emotion}")
            return {
                "cancelled": True,
                "cancellation_reason": f"Complaint appears non-serious based on detected emotion: {emotion}",
                "status": "Cancelled"
            }
    
    # Emotion is serious, continue processing
    print(f"[OK] Emotion '{emotion}' indicates serious complaint. Proceeding.")
    return {
        "cancelled": False,
        "cancellation_reason": None
    }

def should_cancel_complaint(state: AgentState) -> str:
    """
    Conditional function to determine if complaint should be cancelled.
    Returns 'cancel' if cancelled, 'continue' otherwise.
    """
    if state.get('cancelled', False):
        return 'cancel'
    return 'continue'

def geo_node(state: AgentState):
    print("--- Geo Agent ---")
    lat = state['input_data'].get('last_seen_lat')
    lon = state['input_data'].get('last_seen_lon')
    
    if lat and lon:
        res = process_location(lat, lon)
        if not res.get('valid', False):
            return {"geo_results": res, "error": res.get('error')}
        return {"geo_results": res}
    
    # Try to use location from NLP
    location_from_text = state['nlp_results'].get('location_from_text')
    if location_from_text:
        lat = location_from_text['lat']
        lon = location_from_text['lon']
        res = process_location(lat, lon)
        return {"geo_results": res}
    
    return {"geo_results": {}, "error": "No valid location provided"}

def route_node(state: AgentState):
    print("--- Route Agent ---")
    
    # Check if geo processing was successful
    if state.get('error'):
        return {"route_results": {}}
    
    geo_results = state.get('geo_results', {})
    if not geo_results or not geo_results.get('valid', False):
        return {"route_results": {}}
    
    # Get coordinates from input or geo results
    lat = state['input_data'].get('last_seen_lat')
    lon = state['input_data'].get('last_seen_lon')
    time_lost = state['input_data'].get('time_lost')
    
    if not lat or not lon:
        # Try from NLP location
        location_from_text = state['nlp_results'].get('location_from_text')
        if location_from_text:
            lat = location_from_text['lat']
            lon = location_from_text['lon']
    
    if lat and lon:
        route = predict_route(lat, lon, time_lost=time_lost)
        return {"route_results": route}
    
    return {"route_results": {}}

def video_node(state: AgentState):
    print("--- Video Agent ---")
    # This would typically be triggered separately or if a video is provided in the initial state
    # For now, we assume this might be skipped in the initial complaint flow
    return {"scan_results": False}

# Build Graph
workflow = StateGraph(AgentState)

workflow.add_node("nlp", nlp_node)
workflow.add_node("emotion_validation", emotion_validation_node)
workflow.add_node("geo", geo_node)
workflow.add_node("route", route_node)

workflow.set_entry_point("nlp")

workflow.add_edge("nlp", "emotion_validation")

# Conditional edge: if cancelled, go to END; otherwise continue to geo
workflow.add_conditional_edges(
    "emotion_validation",
    should_cancel_complaint,
    {
        "cancel": END,
        "continue": "geo"
    }
)

workflow.add_edge("geo", "route")
workflow.add_edge("route", END)

app = workflow.compile()

def run_complaint_process(input_data):
    """
    Run the agent workflow for a new complaint.
    """
    initial_state = {
        "case_id": 0,  # Placeholder
        "input_data": input_data,
        "nlp_results": {},
        "geo_results": {},
        "route_results": {},
        "scan_results": False,
        "status": "Started",
        "error": None,
        "cancelled": False,
        "cancellation_reason": None
    }
    
    result = app.invoke(initial_state)
    return result

