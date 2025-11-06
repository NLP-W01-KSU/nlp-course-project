import streamlit as st
from streamlit_js_eval import get_cookie, set_cookie
import uuid
from datetime import datetime
import re
from db.helpers import get_user_history, ensure_user_exists

def get_or_create_user_id():
    """Get user ID from cookie or create new one - ENHANCED PERSISTENCE"""
    try:
        # Try multiple cookie names for backward compatibility
        user_id = get_cookie("edugen_user_id")
        
        # If not found, try alternative cookie names
        if not user_id:
            user_id = get_cookie("user_id") or get_cookie("edugen_user")
        
        # If still not found, create new one
        if not user_id:
            user_id = str(uuid.uuid4())
            # Set cookie with multiple fallback names
            set_cookie("edugen_user_id", user_id, duration_days=365)
            set_cookie("user_id", user_id, duration_days=365)  # Backup cookie
            print(f"✅ Created new user ID: {user_id}")
        else:
            print(f"✅ Retrieved existing user ID: {user_id[:8]}...")
            
        return user_id
    except Exception as e:
        # Fallback: use session state only
        print(f"⚠️ Cookie error, using session fallback: {e}")
        if "user_id" not in st.session_state:
            st.session_state.user_id = str(uuid.uuid4())
        return st.session_state.user_id

def initialize_session_state():
    """Initialize session state and load user data from database - ENHANCED"""
    # Initialize user ID first with better persistence
    if "user_id" not in st.session_state:
        st.session_state.user_id = get_or_create_user_id()
    
    # ALWAYS ensure user exists in database
    try:
        ensure_user_exists(st.session_state.user_id)
    except Exception as e:
        print(f"⚠️ User creation warning: {e}")

    # ALWAYS load user history from database
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
        "user_history": [],  
        "from_history": False,
        "showing_regeneration_prompt": False,
        "pending_model_switch": None,
        "previous_model": None,
        "regenerate_with_new_model": False,
        "scrolled_to_top": False,
        "regeneration_count": 0,  
        "regeneration_type": None,  
        "previous_feedback_given": False,
        "pending_regeneration": False,  
        "show_adaptation_message": True,  
        "session_initialized": True,  # NEW: Track initialization
    }

    for key, value in session_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def load_user_history_from_db():
    """Load user's history from database into session state - ENHANCED ERROR HANDLING"""
    try:
        user_id = st.session_state.user_id
        history = get_user_history(user_id)
        st.session_state.user_history = history
        print(f"✅ Loaded {len(history)} history entries for user {user_id[:8]}...")
        
        # If we have history but it's not showing, add a debug message
        if history and not st.session_state.get('user_history'):
            print("⚠️ History loaded but not stored in session state")
            
    except Exception as e:
        print(f"❌ Error loading history from database: {e}")
        st.session_state.user_history = []

def restore_user_session():
    """Attempt to restore user session from multiple sources"""
    try:
        # Try to get user ID from cookies
        user_id = get_or_create_user_id()
        
        # Load history for this user
        history = get_user_history(user_id)
        
        if history:
            print(f"🎯 Restored session for user {user_id[:8]} with {len(history)} history entries")
            return True
        else:
            print(f"🆕 New session for user {user_id[:8]}")
            return False
            
    except Exception as e:
        print(f"❌ Session restoration failed: {e}")
        return False

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
    # Update all the session state values
    for key, value in kwargs.items():
        st.session_state[key] = value
    
    # Auto-save to database if we have new content
    if (st.session_state.get("generated_output") and 
        not st.session_state.get("saved_to_history", False) and 
        not st.session_state.get("regenerated", False)):
        
        save_current_to_history()

def save_current_to_history():
    """Save current content to database and update session state"""
    from db.helpers import save_content_to_history
    
    try:
        if (st.session_state.generated_output and 
            not st.session_state.saved_to_history and 
            not st.session_state.regenerated):
            
            # Handle PDF data - ensure it's base64 string
            pdf_data = st.session_state.pdf_export_data
            if isinstance(pdf_data, bytes):
                import base64
                pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
            elif pdf_data is None:
                pdf_base64 = ""  # Handle case where PDF might be None
            else:
                pdf_base64 = pdf_data  # Assume it's already base64 string
            
            content_data = {
                "user_id": st.session_state.user_id,
                "user_type": st.session_state.user_type,
                "student_level": st.session_state.student_level,
                "topic": st.session_state.tutor_topic if st.session_state.user_type == "tutor" else "Simplified Content",
                "content_type": st.session_state.tutor_content_type if st.session_state.user_type == "tutor" else "Simplified Explanation",
                "prompt": st.session_state.original_prompt,
                "output": st.session_state.generated_output,
                "pdf_base64": pdf_base64,
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
                print(f"✅ Auto-saved content to history: {entry_id}")
                return entry_id
            else:
                print("❌ Failed to auto-save content to history")
                return None
                
        return None
        
    except Exception as e:
        print(f"❌ Error in save_current_to_history: {e}")
        return None
        
# def save_current_to_history():
#     """Save current content to database and update session state"""
#     from db.helpers import save_content_to_history
#     if st.session_state.generated_output and not st.session_state.regenerated:
#         content_data = {
#             "user_id": st.session_state.user_id,
#             "user_type": st.session_state.user_type,
#             "student_level": st.session_state.student_level,
#             "topic": st.session_state.tutor_topic if st.session_state.user_type == "tutor" else "Simplified Content",
#             "content_type": st.session_state.tutor_content_type if st.session_state.user_type == "tutor" else "Simplified Explanation",
#             "prompt": st.session_state.original_prompt,
#             "output": st.session_state.generated_output,
#             "pdf_base64": st.session_state.pdf_export_data,
#             "filename": generate_history_filename(),
#             "feedback_given": st.session_state.feedback_given,
#             "generated_model": st.session_state.get("generated_model", "groq")
#         }
#         entry_id = save_content_to_history(content_data)
#         if entry_id:
#             st.session_state.current_history_id = entry_id
#             st.session_state.saved_to_history = True
#             # Reload history from database to include new entry
#             load_user_history_from_db()
#         return entry_id
#     return None

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
    """Prepare session state for model regeneration - UPDATED tracking"""
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
    
    # Track regeneration
    st.session_state.regeneration_count = st.session_state.get('regeneration_count', 0) + 1
    st.session_state.regeneration_type = 'model_switch'
    
    # Restore preserved context
    for key, value in preserved_data.items():
        if value:  # Only restore if we have actual values
            st.session_state[key] = value
    
    st.session_state.regenerate_with_new_model = True
