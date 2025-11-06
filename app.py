import sys
import os
import streamlit as st
import re
from components.session_manager import initialize_session_state, clear_session, save_current_to_history, get_or_create_user_id
from components.ui_components import render_header, render_sidebar
from components.student_flow import render_student_flow
from components.tutor_flow import render_tutor_flow
from components.output_renderer import render_output_section
from components.feedback_handler import render_feedback_section
from components.export_handler import render_export_section
from components.history_page import render_history_page

import base64

# Find where the validation error is coming from
original_b64decode = base64.b64decode

def debug_b64decode(data, *args, **kwargs):
    try:
        return original_b64decode(data, *args, **kwargs)
    except Exception as e:
        print(f"🚨 BASE64 DECODE ERROR: {e}")
        print(f"🚨 Data type: {type(data)}")
        print(f"🚨 Data length: {len(data) if data else 0}")
        if data and isinstance(data, str):
            print(f"🚨 Data preview: {data[:100]}...")
        import traceback
        traceback.print_stack()
        raise

base64.b64decode = debug_b64decode

# Streamlit App Configuration
st.set_page_config(page_title="TailorED", layout="wide")

def scroll_to_top():
    """Force scroll to top of page"""
    st.components.v1.html("""
    <script>
        window.scrollTo(0, 0);
        setTimeout(() => window.scrollTo(0, 0), 100);
        setTimeout(() => window.scrollTo({top: 0, behavior: 'smooth'}), 200);
    </script>
    """, height=0)

def main():
    # REMOVED: Manual database initialization (it happens automatically in connection.py)
    # Just check if database is available and show warning if not
    from db.connection import is_database_available
    if not is_database_available():
        st.warning("⚠️ Running without database - history and user data won't be saved")
     
    # Initialize session state
    initialize_session_state()

    # Ensure user ID is stored in session
    if "user_id" not in st.session_state:
        st.session_state.user_id = get_or_create_user_id()

    # Create a scroll anchor at the top
    scroll_anchor = st.empty()
    
    # Render header with navigation
    render_header_with_nav()

    # Render sidebar
    render_sidebar()

    # Handle model regeneration if needed
    if st.session_state.get("regenerate_with_new_model"):
        handle_regeneration()

    # Main application logic based on current page
    handle_page_navigation()

    # Session management
    handle_session_management()

    # Force scroll to top after content generation
    if st.session_state.get("generated_output") and not st.session_state.get("scrolled_to_top", False):
        scroll_to_top()
        st.session_state.scrolled_to_top = True

def render_header_with_nav():
    st.title("🧠 TailorED - AI-Powered Educational Content Generator")
    
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        st.caption("Create, manage, and access your educational content")
    
    with col2:
        if st.button("🔄 New Content", use_container_width=True, key="new_content_btn"):
            st.session_state.current_page = "generator"
            clear_session()
            st.rerun()
    
    with col3:
        if st.button("📚 History", use_container_width=True, key="history_btn"):
            st.session_state.current_page = "history"
            # RELOAD HISTORY WHEN NAVIGATING TO HISTORY PAGE
            from components.session_manager import load_user_history_from_db
            load_user_history_from_db()
            st.rerun()
    
    with col4:
        if st.button("🔬 Research", use_container_width=True, key="research_btn"):
            st.session_state.current_page = "research"
            st.rerun()

def handle_regeneration():
    """Handle model regeneration when user switches models"""
    if st.session_state.get("regenerate_with_new_model"):
        # Clear the flag first to prevent loops
        st.session_state.regenerate_with_new_model = False
        
        # Show regeneration in progress
        regeneration_status = st.empty()
        regeneration_status.info("🔄 Regenerating content with new model...")
        
        # Get the preserved context
        user_type = st.session_state.user_type
        student_level = st.session_state.student_level
        
        # Trigger regeneration based on user type
        if user_type == "student":
            from components.student_flow import generate_student_content
            content_text = st.session_state.get("original_content_text", "")
            if content_text:
                generate_student_content(content_text, student_level, "", "regenerated_content.pdf")
        else:
            from components.tutor_flow import generate_tutor_content
            topic = st.session_state.get("original_topic", "")
            objectives = st.session_state.get("original_objectives", "")
            content_type = st.session_state.get("tutor_content_type", "Comprehensive Explanation")
            if topic and objectives:
                generate_tutor_content(topic, objectives, student_level, content_type, "")
        
        regeneration_status.empty()
        
def handle_page_navigation():
    current_page = st.session_state.get("current_page", "generator")
    
    if current_page == "history":
        # ENSURE HISTORY IS LOADED BEFORE RENDERING
        from components.session_manager import load_user_history_from_db
        load_user_history_from_db()
        render_history_page()
    elif current_page == "research":  
        try:
            from components.research_dashboard import render_research_dashboard
            render_research_dashboard()
        except ImportError as e:
            st.error("🔬 Research Dashboard - Import Error")
            st.code(f"Error: {str(e)}")
            st.info("""
            **To fix this:**
            1. Make sure `components/research_dashboard.py` exists
            2. Check the file has no syntax errors
            3. Restart the Streamlit app
            """)
        except Exception as e:
            st.error("🔬 Research Dashboard - Runtime Error")
            st.code(f"Error: {str(e)}")
            st.info("The research dashboard encountered an error while running.")
    else:
        handle_generator_flow()
        
def handle_generator_flow():
    # DEBUG: Check what's in session state
    print(f"🔍 DEBUG handle_generator_flow:")
    print(f"   - generated_output: {bool(st.session_state.get('generated_output'))}")
    print(f"   - regenerated: {st.session_state.get('regenerated', False)}")
    print(f"   - feedback_given: {st.session_state.get('feedback_given', False)}")
    print(f"   - pending_regeneration: {st.session_state.get('pending_regeneration', False)}")
    
    # Handle pending regeneration FIRST in the generator flow
    if st.session_state.get('pending_regeneration'):
        print("🔄 DEBUG: Handling pending regeneration in generator flow")
        from components.feedback_handler import handle_pending_regeneration
        handle_pending_regeneration()
    
    # Check if we have content to display - REGARDLESS of regeneration status
    if st.session_state.get("generated_output"):
        print("✅ DEBUG: Rendering content sections")
        render_output_section()
        render_export_section()
        render_feedback_section()
        return
    
    # If no content, check if we have a user type selected
    if not st.session_state.user_type:
        render_user_selection()
        return
    
    # If user type is selected but no content, render the appropriate flow
    if st.session_state.user_type == "student":
        render_student_flow()
    else:
        render_tutor_flow()

def render_user_selection():
    st.header("🎯 Welcome to TailorED!")
    st.subheader("Are you a Student or Tutor?")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🎓 I'm a Student", use_container_width=True, key="student_btn"):
            st.session_state.user_type = "student"
            st.session_state.scrolled_to_top = False
            st.rerun()

    with col2:
        if st.button("👨‍🏫 I'm a Tutor", use_container_width=True, key="tutor_btn"):
            st.session_state.user_type = "tutor"
            st.session_state.scrolled_to_top = False
            st.rerun()

def handle_session_management():
    # Only show start over if we have content
    if (st.session_state.get("current_page") == "generator" and 
        st.session_state.get("generated_output") and
        st.button("🆕 Start Over", key="start_over_btn")):
        clear_session()
        st.rerun()

if __name__ == "__main__":
    main()
