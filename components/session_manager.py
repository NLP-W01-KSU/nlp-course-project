import streamlit as st
from components.history_manager import history_manager

def initialize_session_state():
    """Initialize all session state variables"""
    session_defaults = {
        "user_type": "",
        "original_prompt": "",
        "generated_output": "",
        "feedback_given": False,
        "regenerated": False,
        "content_source": "",
        "student_level": "",
        "pdf_export_data": None,
        "tutor_topic": "",                    
        "tutor_content_type": "",             
        "feedback_clarity": 3,
        "feedback_depth": 3,
        "feedback_complexity": "Just right",
        "feedback_comments": "",
        "original_filename": "content.pdf",
        "current_page": "generator"
    }
    
    for key, value in session_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
def clear_session():
    """Clear all session state and reset to defaults"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    initialize_session_state()

def update_session_state(**kwargs):
    """Update multiple session state variables"""
    for key, value in kwargs.items():
        st.session_state[key] = value

def save_current_to_history():
    """Save current generated content to history"""
    if (st.session_state.generated_output and 
        not st.session_state.regenerated):
        
        # Prepare history data
        content_data = {
            "user_type": st.session_state.user_type,
            "student_level": st.session_state.student_level,
            "topic": st.session_state.tutor_topic if st.session_state.user_type == "tutor" else "Simplified Content",
            "content_type": st.session_state.tutor_content_type if st.session_state.user_type == "tutor" else "Simplified Explanation",
            "prompt": st.session_state.original_prompt,
            "output": st.session_state.generated_output,
            "pdf_data": st.session_state.pdf_export_data,
            "filename": generate_history_filename(),
            "feedback_given": st.session_state.feedback_given
        }
        
        # Save to history
        entry_id = history_manager.save_to_history(content_data)
        return entry_id
    return None

def generate_history_filename():
    """Generate filename for history entry"""
    import re
    from datetime import datetime
    
    if st.session_state.user_type == "student":
        level_clean = re.sub(r'[^a-zA-Z0-9]', '_', st.session_state.student_level)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        return f"student_content_{level_clean}_{timestamp}.pdf"
    else:
        topic_clean = re.sub(r'[^a-zA-Z0-9]', '_', st.session_state.tutor_topic)[:20]
        content_type_clean = st.session_state.tutor_content_type.replace(' ', '_')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        return f"{content_type_clean}_{topic_clean}_{timestamp}.pdf"

def get_session_info():
    """Get current session information for debugging"""
    return {
        "user_type": st.session_state.user_type,
        "has_output": bool(st.session_state.generated_output),
        "feedback_given": st.session_state.feedback_given,
        "regenerated": st.session_state.regenerated,
        "current_page": st.session_state.current_page
    }