import streamlit as st
import base64
from datetime import datetime
from components.history_manager import history_manager

def render_history_page():
    """Render the history page with all generated content"""
    st.header("📚 Your Generated Content History")
    
    # Debug information (optional - can be removed later)
    with st.expander("🔧 Debug Info (Click to expand)", expanded=False):
        st.write("Session state keys:", list(st.session_state.keys()))
        st.write("User ID:", st.session_state.get('user_id', 'Not set'))
        history = history_manager.get_user_history()
        st.write("History entries found:", len(history))
        if history:
            st.write("Latest entry:", history[0].get('id', 'No ID'))
    
    # Get user's history
    history = history_manager.get_user_history()
    
    if not history:
        render_empty_history()
        return
    
    # Statistics
    render_history_stats(history)
    
    # Search and filter
    filtered_history = render_filters(history)
    
    # History entries
    render_history_entries(filtered_history)

def render_empty_history():
    """Render empty history state"""
    st.info("""
    ## 🏁 No content generated yet!
    
    Your generated content will appear here automatically. You can:
    - Generate new educational content as a **Student** or **Tutor**
    - Download PDFs at any time
    - View your past generations even after refreshing the page
    - Delete entries you no longer need
    """)
    
    # Debug: Check if we have content in session state but not in history
    if st.session_state.get('generated_output'):
        st.warning("⚠️ You have generated content but it's not in history yet.")
        if st.button("🔄 Save Current Content to History"):
            from components.session_manager import save_current_to_history
            entry_id = save_current_to_history()
            if entry_id:
                st.success(f"✅ Content saved to history! Entry ID: {entry_id}")
                st.rerun()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎓 Start as Student", use_container_width=True):
            st.session_state.user_type = "student"
            st.session_state.current_page = "generator"
            st.rerun()
    with col2:
        if st.button("👨‍🏫 Start as Tutor", use_container_width=True):
            st.session_state.user_type = "tutor"
            st.session_state.current_page = "generator"
            st.rerun()

def render_history_stats(history):
    """Render history statistics"""
    total_entries = len(history)
    student_entries = len([h for h in history if h.get('user_type') == 'student'])
    tutor_entries = len([h for h in history if h.get('user_type') == 'tutor'])
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Content", total_entries)
    with col2:
        st.metric("Student Content", student_entries)
    with col3:
        st.metric("Tutor Content", tutor_entries)
    with col4:
        if st.button("🗑️ Clear All", use_container_width=True):
            if history_manager.clear_history():
                st.success("History cleared!")
                st.rerun()
            else:
                st.error("Failed to clear history")

def render_filters(history):
    """Render filters and return filtered history"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        user_type_filter = st.selectbox(
            "Filter by Type",
            ["All", "Student", "Tutor"]
        )
    
    with col2:
        content_type_filter = st.selectbox(
            "Filter by Format",
            ["All", "Lesson Plan", "Study Guide", "Lecture Notes", "Interactive Activity", "Comprehensive Explanation"]
        )
    
    with col3:
        search_term = st.text_input("🔍 Search content...")
    
    # Apply filters
    filtered_history = history
    
    if user_type_filter != "All":
        filtered_history = [h for h in filtered_history if h.get('user_type', '').lower() == user_type_filter.lower()]
    
    if content_type_filter != "All":
        filtered_history = [h for h in filtered_history if h.get('content_type') == content_type_filter]
    
    if search_term:
        filtered_history = [
            h for h in filtered_history 
            if search_term.lower() in h.get('output', '').lower() 
            or search_term.lower() in h.get('topic', '').lower()
            or search_term.lower() in h.get('prompt', '').lower()
        ]
    
    st.caption(f"Showing {len(filtered_history)} of {len(history)} entries")
    return filtered_history

def render_history_entries(history_entries):
    """Render the history entries"""
    for i, entry in enumerate(history_entries):
        with st.container():
            st.markdown("---")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Entry header
                render_entry_header(entry)
                
                # Quick preview
                if st.checkbox(f"Show Preview #{i+1}", key=f"preview_{entry['id']}"):
                    render_entry_preview(entry)
            
            with col2:
                render_entry_actions(entry)

def render_entry_header(entry):
    """Render history entry header"""
    # User type badge
    user_type = entry.get('user_type', 'unknown')
    user_badge = "🎓 Student" if user_type == "student" else "👨‍🏫 Tutor"
    
    # Timestamp
    timestamp = entry.get('timestamp', '')
    try:
        dt = datetime.fromisoformat(timestamp)
        time_str = dt.strftime("%b %d, %Y at %H:%M")
    except:
        time_str = timestamp
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        st.write(f"**{user_badge}**")
    
    with col2:
        topic = entry.get('topic', 'Generated Content')
        content_type = entry.get('content_type', '')
        if content_type:
            st.write(f"**{content_type}**: {topic}")
        else:
            st.write(f"**{topic}**")
    
    with col3:
        st.caption(time_str)
        
        student_level = entry.get('student_level')
        if student_level:
            st.caption(f"Level: {student_level}")

def render_entry_preview(entry):
    """Render entry content preview"""
    output = entry.get('output', '')
    preview = output[:500] + "..." if len(output) > 500 else output
    
    with st.expander("Content Preview", expanded=True):
        st.markdown(preview)
        
        # Show original prompt
        if st.checkbox("Show Original Request", key=f"prompt_{entry['id']}"):
            st.text_area("Original Prompt", entry.get('prompt', ''), height=100, key=f"textarea_{entry['id']}")

def render_entry_actions(entry):
    """Render action buttons for history entry"""
    entry_id = entry['id']
    
    # Download PDF button
    pdf_data = entry.get('pdf_data')
    if pdf_data:
        filename = entry.get('filename', 'content.pdf')
        download_link = create_download_link(pdf_data, filename)
        st.markdown(download_link, unsafe_allow_html=True)
    else:
        st.warning("No PDF available")
    
    # View in main editor button
    if st.button("📝 Open", key=f"open_{entry_id}", use_container_width=True):
        load_entry_to_editor(entry)
    
    # Delete button
    if st.button("🗑️ Delete", key=f"delete_{entry_id}", use_container_width=True):
        if history_manager.delete_entry(entry_id):
            st.success("Entry deleted!")
            st.rerun()
        else:
            st.error("Failed to delete entry")

def create_download_link(pdf_data, filename):
    """Create PDF download link from base64 data"""
    if isinstance(pdf_data, str):
        # Assume it's already base64 encoded
        b64 = pdf_data
    else:
        # Encode bytes to base64
        b64 = base64.b64encode(pdf_data).decode()
    
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}" style="background-color: #4CAF50; color: white; padding: 8px 16px; text-align: center; text-decoration: none; display: inline-block; border-radius: 4px; font-size: 14px; width: 100%;">📥 Download PDF</a>'
    return href

def load_entry_to_editor(entry):
    """Load a history entry back into the main editor"""
    st.session_state.original_prompt = entry.get('prompt', '')
    st.session_state.generated_output = entry.get('output', '')
    st.session_state.user_type = entry.get('user_type', '')
    st.session_state.student_level = entry.get('student_level', '')
    st.session_state.tutor_topic = entry.get('topic', '')
    st.session_state.tutor_content_type = entry.get('content_type', '')
    st.session_state.pdf_export_data = entry.get('pdf_data')
    st.session_state.feedback_given = entry.get('feedback_given', False)
    st.session_state.regenerated = False
    
    # Switch to main page
    st.session_state.current_page = "generator"
    st.rerun()