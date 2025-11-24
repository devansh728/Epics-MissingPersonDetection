import streamlit as st
import cv2
import numpy as np
from database import get_db_connection
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.bhopal_sehore_locations import CCTV_LOCATIONS, get_location_by_name

st.set_page_config(page_title="File Complaint", page_icon="📝")

st.title("📝 File New Missing Person Complaint")
st.markdown("### Bhopal/Sehore District")

with st.form("complaint_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input("Full Name *")
        age = st.number_input("Age *", min_value=0, max_value=120)
        email = st.text_input("Email for Notifications", placeholder="your-email@example.com")
        
        # Time when person went missing
        import datetime
        default_time = datetime.datetime.now() - datetime.timedelta(hours=1)
        time_lost = st.datetime_input("Time Person Went Missing *", value=default_time, max_value=datetime.datetime.now())
        
        # Location input options
        location_method = st.radio("Location Input Method", ["Select from List", "Enter Coordinates"])
        
        if location_method == "Select from List":
            location_names = [loc["name"] for loc in CCTV_LOCATIONS]
            selected_location = st.selectbox("Last Seen Location *", [""] + location_names)
            last_seen_location = selected_location
        else:
            last_seen_location = st.text_input("Last Seen Location (Lat, Lon) *", 
                                              placeholder="e.g., 23.2699, 77.4026 (Bhopal Junction)")
    
    with col2:
        description = st.text_area("Physical Description & Details *")
        uploaded_photo = st.file_uploader("Upload Recent Photo *", type=['jpg', 'jpeg', 'png'])
        voice_note = st.file_uploader("Upload Voice Note (Optional)", type=['wav', 'mp3', 'ogg'])

    submitted = st.form_submit_button("Submit Complaint")

    if submitted:
        if not name or not uploaded_photo or not last_seen_location:
            st.error("Please fill in all required fields (Name, Photo, Location).")
        else:
            # Save uploaded files
            os.makedirs("uploads", exist_ok=True)
            photo_path = os.path.join("uploads", uploaded_photo.name)
            with open(photo_path, "wb") as f:
                f.write(uploaded_photo.getbuffer())
            
            voice_path = None
            if voice_note:
                voice_path = os.path.join("uploads", voice_note.name)
                with open(voice_path, "wb") as f:
                    f.write(voice_note.getbuffer())
            
            # Parse location
            lat, lon = None, None
            location_name = ""
            
            if location_method == "Select from List" and selected_location:
                coords = get_location_by_name(selected_location)
                if coords:
                    lat, lon = coords["lat"], coords["lon"]
                    location_name = selected_location
            else:
                try:
                    lat, lon = map(float, last_seen_location.split(","))
                    location_name = f"Lat: {lat}, Lon: {lon}"
                except ValueError:
                    st.error("Invalid location format. Use 'Lat, Lon' (e.g. 23.2699, 77.4026)")
                    st.stop()
            
            if not lat or not lon:
                st.error("Could not determine location coordinates.")
                st.stop()

            # Prepare input for agent
            input_data = {
                "name": name,
                "age": age,
                "description": description,
                "photo_path": photo_path,
                "voice_path": voice_path,
                "last_seen_lat": lat,
                "last_seen_lon": lon,
                "email": email,
                "time_lost": time_lost.isoformat() if time_lost else None
            }
            
            with st.spinner("Processing complaint with AI Agents..."):
                from agents.graph import run_complaint_process
                result = run_complaint_process(input_data)
                
                # Check if complaint was cancelled due to emotion
                if result.get('cancelled', False):
                    st.warning(f"⚠️ **Complaint Not Filed**")
                    st.info(f"**Reason:** {result.get('cancellation_reason', 'Unknown')}")
                    st.markdown("""
                    ### Why was my complaint cancelled?
                    
                    Our AI system detected that the emotional tone of your complaint suggests it may not be a serious missing person case. 
                    This could happen if:
                    - The description contains joking or humorous language
                    - The tone suggests the person has been found or the situation is resolved
                    - The complaint appears to be a test or non-serious inquiry
                    
                    **If this is a genuine missing person case**, please:
                    1. Rewrite your description with serious, factual language
                    2. Focus on when and where the person was last seen
                    3. Include physical description and circumstances
                    4. Avoid humor or casual language
                    
                    You can submit a new complaint using the form above.
                    """)
                    st.stop()
                
                # Check for other errors
                if result.get('error'):
                    st.error(f"Error: {result['error']}")
                    st.stop()
                
                # Save to DB
                conn = get_db_connection()
                c = conn.cursor()
                
                # Extract results
                nlp = result.get('nlp_results', {})
                geo = result.get('geo_results', {})
                route = result.get('route_results', {})
                
                # Insert into missing_cases
                c.execute('''
                    INSERT INTO missing_cases (name, age, description, last_seen_geohash, last_seen_location, 
                                              time_lost, transcript, emotion, image_path, email)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (name, age, nlp.get('full_text', description), geo.get('geohash', ''), 
                      location_name, time_lost.isoformat() if time_lost else None,
                      nlp.get('transcription', ''), nlp.get('emotion', ''), photo_path, email))
                
                case_id = c.lastrowid
                
                # Save route prediction
                import json
                route_data = route.get('route', [])
                cctv_videos = route.get('cctv_videos', [])
                
                c.execute('''
                    INSERT INTO geohash_predictions (case_id, start_geohash, predicted_path, cctv_videos)
                    VALUES (?, ?, ?, ?)
                ''', (case_id, geo.get('geohash', ''), json.dumps(route_data), json.dumps(cctv_videos)))
                
                conn.commit()
                conn.close()
                
            st.success(f"✅ Complaint filed successfully! Case ID: {case_id}")
            
            # Display results
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### AI Analysis")
                st.write(f"**Emotion Detected:** {nlp.get('emotion', 'N/A')}")
                st.write(f"**Nearest CCTV:** {geo.get('nearest_cctv', 'N/A')}")
                st.write(f"**Distance:** {geo.get('cctv_distance', 'N/A')} meters")
                
                # Display time analysis if available
                time_analysis = route.get('time_analysis')
                if time_analysis:
                    st.markdown("### Time-Based Analysis")
                    st.write(f"**Time Elapsed:** {time_analysis.get('hours_elapsed', 0):.2f} hours")
                    st.write(f"**Search Radius:** {time_analysis.get('search_radius_km', 0):.2f} km")
                    st.write(f"**Max Walking Distance:** {time_analysis.get('max_walking_distance_km', 0):.2f} km")
                
            with col2:
                st.markdown("### Route Prediction")
                st.write(f"**CCTV Locations to Monitor:** {route.get('num_cctv_locations', 0)}")
                if cctv_videos:
                    st.write("**Cameras:**")
                    for cctv in cctv_videos[:5]:
                        st.write(f"- {cctv.get('name', 'N/A')}")
            
            # Send email notification if email provided
            if email:
                with st.spinner("Sending email notification..."):
                    from agents.notification_agent import notify_case_filed
                    notification_result = notify_case_filed(case_id, route_data)
                    if notification_result.get('email_sent'):
                        st.success("📧 Email notification sent!")
                    else:
                        st.warning("⚠️ Email notification failed (check email configuration)")
            
            # Start background CCTV scanning
            if cctv_videos and len(cctv_videos) > 0:
                st.info("🔍 Starting background CCTV scanning...")
                
                from agents.scanning_agent import start_background_scan
                
                scan_task_id = start_background_scan(
                    case_id,
                    cctv_videos,
                    photo_path
                )
                
                if scan_task_id:
                    st.success(f"✅ Background scan started! Scan Task ID: {scan_task_id}")
                    st.info("You will receive an email notification when the scan is complete.")
                    st.info("Check the Dashboard for real-time progress updates.")
                else:
                    st.warning("⚠️ Failed to start background scan")

