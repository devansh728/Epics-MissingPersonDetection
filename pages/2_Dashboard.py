import streamlit as st
from database import get_db_connection
import pandas as pd
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.bhopal_sehore_locations import CCTV_LOCATIONS

st.set_page_config(page_title="Investigation Dashboard", page_icon="🚔", layout="wide")

st.title("🚔 AI Investigation Dashboard")
st.markdown("### Bhopal/Sehore District - Missing Persons")

# Fetch data
conn = get_db_connection()
df = pd.read_sql("SELECT * FROM missing_cases ORDER BY date_reported DESC", conn)

if not df.empty:
    st.markdown(f"### Active Cases ({len(df)})")
    
    # Display cases in a nice format
    for idx, row in df.iterrows():
        with st.expander(f"Case #{row['id']} - {row['name']} (Age: {row['age']})"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**Status:** {row['status']}")
                st.write(f"**Reported:** {row['date_reported']}")
                st.write(f"**Last Seen:** {row['last_seen_location']}")
                st.write(f"**Emotion:** {row['emotion']}")
            
            with col2:
                st.write(f"**Geohash:** {row['last_seen_geohash']}")
                if row['email']:
                    st.write(f"**Email:** {row['email']}")
                st.write(f"**Description:** {row['description'][:100]}...")
            
            with col3:
                if row['image_path'] and os.path.exists(row['image_path']):
                    st.image(row['image_path'], caption="Missing Person Photo", width=150)
    
    st.markdown("---")
    st.markdown("### Route Prediction & CCTV Analysis")
    
    selected_case_id = st.selectbox("Select Case to View Details", df['id'].tolist())
    
    if selected_case_id:
        # Get predictions
        preds = pd.read_sql("SELECT * FROM geohash_predictions WHERE case_id = ? ORDER BY timestamp DESC", 
                           conn, params=(selected_case_id,))
        
        if not preds.empty:
            pred_data = preds.iloc[0]
            path_data = json.loads(pred_data['predicted_path'])
            cctv_videos = json.loads(pred_data['cctv_videos']) if pred_data['cctv_videos'] else []
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Predicted Movement Path")
                
                # Prepare data for map
                map_data = []
                for p in path_data:
                    map_data.append({"lat": p['lat'], "lon": p['lon']})
                
                if map_data:
                    st.map(pd.DataFrame(map_data))
                
                st.markdown("**Path Details:**")
                for i, p in enumerate(path_data[:5]):
                    st.write(f"{i+1}. {p.get('nearest_cctv', 'N/A')} ({p.get('cctv_distance', 0):.0f}m away)")
            
            with col2:
                st.markdown("#### CCTV Locations to Monitor")
                st.write(f"**Total Cameras:** {len(cctv_videos)}")
                
                for cctv in cctv_videos:
                    st.info(f"📹 **{cctv['name']}**\n\nVideo: `{cctv['video_path']}`")
        
        # Show blockchain reports if any
        reports = pd.read_sql("SELECT * FROM blockchain_reports WHERE case_id = ? ORDER BY timestamp DESC", 
                             conn, params=(selected_case_id,))
        
        if not reports.empty:
            st.markdown("---")
            st.markdown("#### Blockchain Reports")
            for idx, report in reports.iterrows():
                st.success(f"🔗 Report #{report['id']}\n\n**Hash:** `{report['blockchain_hash']}`\n\n**Time:** {report['timestamp']}")
        
        # Show scan tasks and progress
        st.markdown("---")
        st.markdown("#### CCTV Scan Tasks")
        
        scan_tasks = pd.read_sql("""
            SELECT * FROM scan_tasks WHERE case_id = ? ORDER BY started_at DESC
        """, conn, params=(selected_case_id,))
        
        if not scan_tasks.empty:
            for idx, task in scan_tasks.iterrows():
                status_emoji = {
                    'pending': '⏳',
                    'in_progress': '🔄',
                    'completed': '✅',
                    'failed': '❌'
                }.get(task['status'], '❓')
                
                with st.expander(f"{status_emoji} Scan Task #{task['id']} - {task['status'].upper()}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Started:** {task['started_at']}")
                        st.write(f"**Total CCTVs:** {task['total_cctvs']}")
                        st.write(f"**Scanned:** {task['scanned_cctvs']}")
                    
                    with col2:
                        if task['completed_at']:
                            st.write(f"**Completed:** {task['completed_at']}")
                        st.write(f"**Status:** {task['status']}")
                    
                    # Progress bar
                    if task['total_cctvs'] > 0:
                        progress = task['scanned_cctvs'] / task['total_cctvs']
                        st.progress(progress)
                        st.write(f"Progress: {progress * 100:.1f}%")
                    
                    # Get scan results
                    scan_results = pd.read_sql("""
                        SELECT csr.*, cl.name as cctv_name
                        FROM cctv_scan_results csr
                        JOIN cctv_locations cl ON csr.cctv_id = cl.id
                        WHERE csr.scan_task_id = ?
                    """, conn, params=(task['id'],))
                    
                    if not scan_results.empty:
                        total_detections = scan_results['detections_found'].sum()
                        st.write(f"**Total Detections:** {total_detections}")
                        
                        # Show results table
                        st.markdown("**Scan Results:**")
                        results_display = scan_results[['cctv_name', 'detections_found', 'scan_duration_seconds']].copy()
                        results_display.columns = ['CCTV Location', 'Detections', 'Duration (s)']
                        st.dataframe(results_display)
                    
                    # PDF report download
                    if task['pdf_report_path'] and os.path.exists(task['pdf_report_path']):
                        with open(task['pdf_report_path'], 'rb') as f:
                            st.download_button(
                                label="📊 Download Aggregate Report (PDF)",
                                data=f,
                                file_name=os.path.basename(task['pdf_report_path']),
                                mime='application/pdf'
                            )
        else:
            st.info("No scan tasks found for this case.")
        
else:
    st.info("No active cases found. File a new complaint to get started.")

# Show CCTV locations map
st.markdown("---")
st.markdown("### CCTV Network - Bhopal/Sehore")

cctv_df = pd.DataFrame([{
    "lat": loc["lat"],
    "lon": loc["lon"],
    "name": loc["name"]
} for loc in CCTV_LOCATIONS])

st.map(cctv_df)

st.markdown("**CCTV Locations:**")
cols = st.columns(2)
for i, loc in enumerate(CCTV_LOCATIONS):
    with cols[i % 2]:
        st.write(f"{i+1}. **{loc['name']}** ({loc['type']})")

conn.close()

