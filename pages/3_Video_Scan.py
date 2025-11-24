import streamlit as st
import os
import tempfile
import pandas as pd
import json
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db_connection
from config.bhopal_sehore_locations import CCTV_LOCATIONS

st.set_page_config(page_title="CCTV Video Scan", page_icon="📹")

st.title("📹 CCTV Video Surveillance Scan")
st.markdown("### Bhopal/Sehore District")

# Get active cases
conn = get_db_connection()
cases = pd.read_sql("SELECT id, name, image_path, last_seen_location FROM missing_cases WHERE status='Active'", conn)

if cases.empty:
    st.warning("No active cases to scan for. Please file a complaint first.")
else:
    st.markdown(f"### Active Cases: {len(cases)}")
    
    selected_case_id = st.selectbox("Select Case to Scan For", 
                                    cases['id'].tolist(),
                                    format_func=lambda x: f"Case #{x} - {cases[cases['id']==x]['name'].values[0]}")
    
    if selected_case_id:
        case_data = cases[cases['id'] == selected_case_id].iloc[0]
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Name:** {case_data['name']}")
            st.write(f"**Last Seen:** {case_data['last_seen_location']}")
        
        with col2:
            if case_data['image_path'] and os.path.exists(case_data['image_path']):
                st.image(case_data['image_path'], caption="Target Person", width=150)
        
        st.markdown("---")
        
        # Get predicted CCTV locations for this case
        preds = pd.read_sql("SELECT * FROM geohash_predictions WHERE case_id = ? ORDER BY timestamp DESC", 
                           conn, params=(selected_case_id,))
        
        if not preds.empty:
            cctv_videos = json.loads(preds.iloc[0]['cctv_videos']) if preds.iloc[0]['cctv_videos'] else []
            
            if cctv_videos:
                st.success(f"📍 **{len(cctv_videos)} CCTV locations** identified based on route prediction")
                
                st.markdown("### Recommended CCTV Cameras to Scan:")
                for i, cctv in enumerate(cctv_videos):
                    st.info(f"{i+1}. **{cctv['name']}** - `{cctv['video_path']}`")
                
                st.markdown("---")
                
                # Option to scan specific CCTV or upload custom video
                scan_mode = st.radio("Scan Mode", ["Scan Predicted CCTVs", "Upload Custom Video"])
                
                if scan_mode == "Scan Predicted CCTVs":
                    if st.button("🔍 Start Automated Scan of All Predicted CCTVs"):
                        st.warning("⚠️ Automated CCTV scanning requires actual video files at the specified paths.")
                        st.info("For this prototype, please ensure CCTV video files exist at the paths shown above, or use 'Upload Custom Video' mode.")
                        
                        # In production, this would iterate through cctv_videos and scan each one
                        # for cctv in cctv_videos:
                        #     scan_video(selected_case_id, cctv['video_path'], case_data['image_path'])
                
                else:  # Upload Custom Video
                    uploaded_video = st.file_uploader("Upload Video File", type=['mp4', 'avi', 'mov'])
                    
                    if uploaded_video is not None:
                        tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') 
                        tfile.write(uploaded_video.read())
                        video_path = tfile.name
                        tfile.close()
                        
                        st.video(video_path)
                        
                        if st.button("🔍 Start Scan"):
                            with st.spinner("Scanning video for matches..."):
                                from agents.video_agent import scan_video
                                
                                # Run scan
                                found = scan_video(selected_case_id, video_path, case_data['image_path'])
                                
                                if found:
                                    st.success("✅ Scan complete! Matches may have been found.")
                                    st.info("Check the `output_frames/matches` folder for matched frames.")
                                    
                                    # In production, parse the output folder and display matches
                                    # Generate blockchain report
                                    st.markdown("### Generating Blockchain Report...")
                                    
                                    from utils.blockchain_utils import create_blockchain_report
                                    from agents.notification_agent import notify_match_found
                                    
                                    # Mock match data (in production, get from surveillance.py output)
                                    match_data = {
                                        "frame_number": 100,
                                        "score": 0.85,
                                        "saved_img_path": "output_frames/matches/match_example.jpg"
                                    }
                                    
                                    # Find which CCTV location this video corresponds to
                                    location_data = cctv_videos[0] if cctv_videos else {
                                        "id": 1,
                                        "name": "Unknown Location",
                                        "geohash": "",
                                        "lat": 0,
                                        "lon": 0
                                    }
                                    
                                    # Create blockchain report
                                    blockchain_report = create_blockchain_report(selected_case_id, match_data, location_data)
                                    
                                    st.success(f"🔗 **Blockchain Report Generated**")
                                    st.code(f"Hash: {blockchain_report['blockchain_hash']}")
                                    
                                    # Save to database
                                    cursor = conn.cursor()
                                    cursor.execute("""
                                        INSERT INTO blockchain_reports (case_id, report_data, blockchain_hash)
                                        VALUES (?, ?, ?)
                                    """, (selected_case_id, str(blockchain_report['report']), blockchain_report['blockchain_hash']))
                                    conn.commit()
                                    
                                    # Send notification
                                    st.markdown("### Sending Email Notification...")
                                    notify_result = notify_match_found(selected_case_id, match_data, location_data)
                                    
                                    if notify_result.get('email_sent'):
                                        st.success("📧 Email notification sent!")
                                    else:
                                        st.warning("⚠️ Email notification failed (check configuration)")
                                    
                                else:
                                    st.info("No matches found in this video.")
            else:
                st.warning("No CCTV predictions available for this case.")
        else:
            st.warning("No route prediction found for this case.")

conn.close()

