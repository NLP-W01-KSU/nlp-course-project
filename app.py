import streamlit as st
from components.session_manager import initialize_session_state, clear_session, save_current_to_history
from components.ui_components import render_header, render_sidebar
from components.student_flow import render_student_flow
from components.tutor_flow import render_tutor_flow
from components.output_renderer import render_output_section
from components.feedback_handler import render_feedback_section
from components.export_handler import render_export_section
from components.history_page import render_history_page

# Streamlit App Configuration
st.set_page_config(page_title="EduGen", layout="wide")

def main():
    # Initialize session state
    initialize_session_state()
    
    # Render header with navigation
    render_header_with_nav()
    
    # Render sidebar
    render_sidebar()
    
    # Main application logic based on current page
    handle_page_navigation()
    
    # Session management
    handle_session_management()

def render_header_with_nav():
    """Render header with navigation"""
    st.title("🧠 EduGen - AI-Powered Educational Content Generator")
    
    # Navigation
    col1, col2, col3 = st.columns([2, 1, 1])
    
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
            st.rerun()

def handle_page_navigation():
    """Handle navigation between different pages"""
    current_page = st.session_state.get("current_page", "generator")
    
    if current_page == "history":
        render_history_page()
    else:  # generator page
        handle_generator_flow()

def handle_generator_flow():
    """Handle the main generator flow"""
    # No user type selected - show welcome
    if not st.session_state.user_type:
        render_user_selection()
        return
    
    # User selected but no content generated
    if not st.session_state.generated_output:
        if st.session_state.user_type == "student":
            render_student_flow()
        else:
            render_tutor_flow()
        return
    
    # Content generated - show output and feedback
    render_output_section()
    render_export_section()
    render_feedback_section()
    
    # Auto-save to history when content is generated
    if not st.session_state.get('saved_to_history', False):
        entry_id = save_current_to_history()
        if entry_id:
            st.session_state.saved_to_history = True
            st.session_state.current_history_id = entry_id
            # No rerun here to avoid infinite loops

def render_user_selection():
    """Render user type selection screen"""
    st.header("🎯 Welcome to EduGen!")
    st.subheader("Are you a Student or Tutor?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🎓 I'm a Student", use_container_width=True, key="student_btn"):
            st.session_state.user_type = "student"
            st.rerun()
            
    with col2:
        if st.button("👨‍🏫 I'm a Tutor", use_container_width=True, key="tutor_btn"):
            st.session_state.user_type = "tutor"
            st.rerun()

def handle_session_management():
    """Handle session reset and cleanup"""
    # Only show on generator page when we have content
    if (st.session_state.get("current_page") == "generator" and 
        st.session_state.generated_output and
        (st.session_state.regenerated or st.button("🆕 Start Over", key="start_over_btn"))):
        clear_session()
        st.rerun()

if __name__ == "__main__":
    main()