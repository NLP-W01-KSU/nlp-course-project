import streamlit as st
from streamlit_js_eval import get_cookie, set_cookie
import uuid
from datetime import datetime
import re
from db.helpers import get_user_history, ensure_user_exists

def get_or_create_user_id():
    """Get user ID from cookie or create new one"""
    user_id = get_cookie("edugen_user_id")
    if not user_id:
        user_id = str(uuid.uuid4())
        set_cookie("edugen_user_id", user_id, duration_days=365)
        print(f"✅ Created new user ID: {user_id}")
    return user_id

def initialize_session_state():
    """Initialize session state and load user data from database"""
    # Initialize user ID first
    if "user_id" not in st.session_state:
        st.session_state.user_id = get_or_create_user_id()
    
    # ALWAYS load user history from database - REMOVE THE CONDITION
    load_user_history_from_db()

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
        "current_page": "generator",
        "current_history_id": None,
        "saved_to_history": False,
        "user_history": [],  # This will be overwritten by load_user_history_from_db()
        "from_history": False,
        "showing_regeneration_prompt": False,
        "pending_model_switch": None,
        "previous_model": None,
        "regenerate_with_new_model": False,
        "scrolled_to_top": False
    }

    for key, value in session_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def load_user_history_from_db():
    """Load user's history from database into session state - CALL THIS ON EVERY LOAD"""
    try:
        # Ensure we have a user_id
        user_id = st.session_state.user_id if hasattr(st.session_state, 'user_id') else get_or_create_user_id()
        history = get_user_history(user_id)
        st.session_state.user_history = history
        print(f"✅ Loaded {len(history)} history entries for user {user_id}")
    except Exception as e:
        print(f"❌ Error loading history from database: {e}")
        st.session_state.user_history = []

def clear_session():
    """Clear session state but preserve user identity and history"""
    preserved_keys = ['user_id', 'current_page']  # REMOVED 'user_history' from preserved keys
    preserved = {k: st.session_state[k] for k in preserved_keys if k in st.session_state}
    
    st.session_state.clear()
    
    # Restore preserved keys
    for k, v in preserved.items():
        st.session_state[k] = v
    
    # Re-initialize defaults AND reload history
    initialize_session_state()

def update_session_state(**kwargs):
    for key, value in kwargs.items():
        st.session_state[key] = value

def save_current_to_history():
    """Save current content to database and update session state"""
    from db.helpers import save_content_to_history
    if st.session_state.generated_output and not st.session_state.regenerated:
        content_data = {
            "user_id": st.session_state.user_id,
            "user_type": st.session_state.user_type,
            "student_level": st.session_state.student_level,
            "topic": st.session_state.tutor_topic if st.session_state.user_type == "tutor" else "Simplified Content",
            "content_type": st.session_state.tutor_content_type if st.session_state.user_type == "tutor" else "Simplified Explanation",
            "prompt": st.session_state.original_prompt,
            "output": st.session_state.generated_output,
            "pdf_base64": st.session_state.pdf_export_data,
            "filename": generate_history_filename(),
            "feedback_given": st.session_state.feedback_given,
            "generated_model": st.session_state.get("generated_model", "groq")
        }
        entry_id = save_content_to_history(content_data)
        if entry_id:
            st.session_state.current_history_id = entry_id
            st.session_state.saved_to_history = True
            # Reload history from database to include new entry
            load_user_history_from_db()
        return entry_id
    return None

def generate_history_filename():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    if st.session_state.user_type == "student":
        level_clean = re.sub(r'[^a-zA-Z0-9]', '_', st.session_state.student_level)
        return f"student_content_{level_clean}_{timestamp}.pdf"
    else:
        topic_clean = re.sub(r'[^a-zA-Z0-9]', '_', st.session_state.tutor_topic)[:20]
        content_type_clean = st.session_state.tutor_content_type.replace(' ', '_')
        return f"{content_type_clean}_{topic_clean}_{timestamp}.pdf"

def get_session_info():
    return {
        "user_id": st.session_state.user_id,
        "user_type": st.session_state.user_type,
        "has_output": bool(st.session_state.generated_output),
        "feedback_given": st.session_state.feedback_given,
        "regenerated": st.session_state.regenerated,
        "current_page": st.session_state.current_page,
        "current_history_id": st.session_state.current_history_id,
        "history_entries": len(st.session_state.user_history)
    }
    
def prepare_for_model_regeneration():
    """Prepare session state for model regeneration while preserving content context"""
    # Preserve the essential content generation context
    preserved_data = {
        'user_type': st.session_state.user_type,
        'student_level': st.session_state.student_level,
        'content_source': st.session_state.content_source,
        'original_prompt': st.session_state.original_prompt,
        # For tutor flow
        'tutor_topic': st.session_state.get('tutor_topic', ''),
        'tutor_content_type': st.session_state.get('tutor_content_type', ''),
        # For student flow  
        'original_filename': st.session_state.get('original_filename', 'content.pdf'),
    }
    
    # Clear generation outputs but keep context
    keys_to_clear = [
        'generated_output', 'pdf_export_data', 'feedback_given', 
        'regenerated', 'current_history_id', 'saved_to_history',
        'feedback_clarity', 'feedback_depth', 'feedback_complexity', 
        'feedback_comments', 'scrolled_to_top'
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    # Restore preserved context
    for key, value in preserved_data.items():
        if value:  # Only restore if we have actual values
            st.session_state[key] = value
    
    st.session_state.regenerate_with_new_model = True