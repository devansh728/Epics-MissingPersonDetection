import streamlit as st
from database import init_db

st.set_page_config(
    page_title="Missing Person Detection System",
    page_icon="🕵️‍♂️",
    layout="wide",
    initial_sidebar_state="expanded",
)

def main():
    st.title("🕵️‍♂️ Missing Person Detection & AI Surveillance")
    
    st.markdown("""
    ### Welcome to the AI-Powered Missing Person Detection System
    
    This system utilizes advanced AI technologies to assist in locating missing persons.
    
    **Key Features:**
    - **File Complaint:** Report a missing person with details, photos, and voice descriptions.
    - **AI Dashboard:** Police view to track cases, view predictions, and analyze data.
    - **CCTV Scan:** Upload and scan surveillance footage to find matches using Facial Recognition.
    
    ---
    
    **System Status:**
    - Database: SQLite (Initialized)
    - Face Recognition: DeepFace + YOLOv8
    - Route Prediction: Geohashing + Random Walk Model
    """)
    
    # Initialize DB on app start if not exists
    if 'db_initialized' not in st.session_state:
        init_db()
        st.session_state['db_initialized'] = True
        st.success("Database connection established.")

    st.sidebar.info("Select a page from the sidebar to navigate.")

if __name__ == "__main__":
    main()
