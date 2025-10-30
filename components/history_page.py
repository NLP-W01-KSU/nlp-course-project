import streamlit as st
import base64
import re
from datetime import datetime

def render_history_page():
    st.header("📚 Your Generated Content History")
    
    # Add refresh button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write("")  # Spacer
    with col2:
        if st.button("🔄 Refresh History", use_container_width=True):
            from components.session_manager import load_user_history_from_db
            load_user_history_from_db()
            st.rerun()
    
    history = st.session_state.get("user_history", [])
    
    if not history:
        render_empty_history()
        return

    render_history_stats(history)
    filtered_history = render_filters(history)
    render_history_entries(filtered_history)

def render_empty_history():
    st.info("""
    ## 🏁 No content generated yet!
    Your generated content will appear here automatically.
    """)
    
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
    total_entries = len(history)
    student_entries = len([h for h in history if h.user_type == 'student'])
    tutor_entries = len([h for h in history if h.user_type == 'tutor'])

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Content", total_entries)
    with col2:
        st.metric("Student Content", student_entries)
    with col3:
        st.metric("Tutor Content", tutor_entries)

def render_filters(history):
    col1, col2, col3 = st.columns(3)

    with col1:
        user_type_filter = st.selectbox("Filter by Type", ["All", "Student", "Tutor"])

    with col2:
        content_type_filter = st.selectbox("Filter by Format", ["All", "Lesson Plan", "Study Guide", "Lecture Notes", "Interactive Activity", "Comprehensive Explanation"])

    with col3:
        search_term = st.text_input("🔍 Search content...")

    filtered_history = history

    if user_type_filter != "All":
        filtered_history = [h for h in filtered_history if h.user_type.lower() == user_type_filter.lower()]

    if content_type_filter != "All":
        filtered_history = [h for h in filtered_history if h.content_type == content_type_filter]

    if search_term:
        filtered_history = [
            h for h in filtered_history 
            if search_term.lower() in (h.output or '').lower()
            or search_term.lower() in (h.topic or '').lower()
            or search_term.lower() in (h.prompt or '').lower()
        ]

    st.caption(f"Showing {len(filtered_history)} of {len(history)} entries")
    return filtered_history

def render_history_entries(history_entries):
    for i, entry in enumerate(history_entries):
        with st.container():
            st.markdown("---")
            col1, col2 = st.columns([3, 1])
            with col1:
                render_entry_header(entry)
                if st.checkbox(f"Show Preview #{i+1}", key=f"preview_{entry.id}"):
                    render_entry_preview(entry)
            with col2:
                render_entry_actions(entry, i)

def render_entry_header(entry):
    user_badge = "🎓 Student" if entry.user_type == "student" else "👨‍🏫 Tutor"
    time_str = entry.created_at.strftime("%b %d, %Y at %H:%M")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        st.write(f"**{user_badge}**")
    with col2:
        if entry.content_type:
            st.write(f"**{entry.content_type}**: {entry.topic}")
        else:
            st.write(f"**{entry.topic}**")
    with col3:
        st.caption(time_str)
        if entry.student_level:
            st.caption(f"Level: {entry.student_level}")

def render_entry_preview(entry):
    preview = (entry.output or '')[:500] + "..." if len(entry.output or '') > 500 else (entry.output or '')
    with st.expander("Content Preview", expanded=True):
        st.markdown(preview)
        if st.checkbox("Show Original Request", key=f"prompt_{entry.id}"):
            st.text_area("Original Prompt", entry.prompt, height=100, key=f"textarea_{entry.id}")

def render_entry_actions(entry, index):
    entry_id = entry.id
    
    # ULTRA SIMPLE CHECK: Just check if PDF data exists and is reasonably long
    has_pdf_data = entry.pdf_base64 and len(entry.pdf_base64) > 1000
    
    if has_pdf_data:
        download_link = create_download_link(entry.pdf_base64, entry.filename or "content.pdf")
        st.markdown(download_link, unsafe_allow_html=True)
        st.caption("✅ PDF ready for download")
    else:
        st.warning("⚠️ PDF needs regeneration")
    
    # Regenerate button
    if st.button("🔄 Regenerate PDF", key=f"regen_pdf_{entry_id}", use_container_width=True):
        with st.spinner("Regenerating PDF..."):
            success = regenerate_pdf_for_history(entry)
            if success:
                st.success("✅ PDF regenerated successfully! Refreshing...")
                st.rerun()
            else:
                st.error("❌ Failed to regenerate PDF")

    # Open button
    if st.button("📝 Open", key=f"open_{entry_id}_{index}", use_container_width=True):
        load_entry_to_editor(entry)

def create_download_link(pdf_data, filename):
    """Create a download link for PDF file - NO VALIDATION"""
    try:
        # Handle the data - if it has data URL prefix, extract base64 part
        if isinstance(pdf_data, str):
            if pdf_data.startswith('data:application/pdf;base64,'):
                base64_data = pdf_data.split(',')[1]
            else:
                base64_data = pdf_data
        else:
            base64_data = pdf_data
        
        # Create safe filename
        safe_filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
        if not safe_filename.endswith('.pdf'):
            safe_filename += '.pdf'
        
        # Create the download link WITHOUT ANY VALIDATION
        href = f'''
        <a href="data:application/pdf;base64,{base64_data}" download="{safe_filename}"
           style="background-color:#4CAF50;color:white;padding:12px 24px;text-align:center;
           text-decoration:none;display:inline-block;border-radius:4px;font-weight:bold;
           border:none;cursor:pointer;width:100%;box-sizing:border-box;"
           onclick="console.log('Downloading PDF: {safe_filename}')">
           📥 Download PDF
        </a>
        '''
        return href
        
    except Exception as e:
        return f'<p style="color: red;">❌ Download error</p>'

def regenerate_pdf_for_history(entry):
    """Regenerate PDF for a history entry"""
    try:
        from utils.pdf_export import export_content_to_pdf
        
        print(f"🔄 Regenerating PDF for entry: {entry.id}")
        
        if entry.user_type == "student":
            pdf_bytes = export_content_to_pdf(
                content=entry.output,
                title=f"Simplified Content - {entry.student_level}",
                student_level=entry.student_level,
                content_type=None,
                objectives=None
            )
        else:
            pdf_bytes = export_content_to_pdf(
                content=entry.output,
                title=f"{entry.content_type} - {entry.topic}",
                student_level=entry.student_level,
                content_type=entry.content_type,
                objectives=""
            )
        
        if pdf_bytes and len(pdf_bytes) > 100:
            print(f"✅ PDF generated: {len(pdf_bytes)} bytes")
            
            # Convert to clean base64
            pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
            print(f"✅ Converted to base64: {len(pdf_base64)} chars")
            
            # Update database
            from db.helpers import update_pdf_data
            success = update_pdf_data(entry.id, pdf_base64)
            
            if success:
                print("✅ PDF saved to database")
                return True
            else:
                print("❌ Failed to save PDF to database")
                return False
        else:
            print("❌ PDF generation failed")
            return False
            
    except Exception as e:
        print(f"❌ Error regenerating PDF: {str(e)}")
        return False

def load_entry_to_editor(entry):
    """Load a history entry back into the main editor"""
    # Clear session state except essentials
    keys_to_preserve = ['user_id', 'current_page']
    preserved = {k: st.session_state[k] for k in keys_to_preserve if k in st.session_state}
    
    for key in list(st.session_state.keys()):
        if key not in keys_to_preserve:
            del st.session_state[key]
    
    # Restore preserved keys
    for k, v in preserved.items():
        st.session_state[k] = v
    
    # Set content data
    st.session_state.generated_output = entry.output
    st.session_state.original_prompt = entry.prompt
    st.session_state.user_type = entry.user_type
    st.session_state.student_level = entry.student_level
    st.session_state.tutor_topic = entry.topic
    st.session_state.tutor_content_type = entry.content_type
    
    # Always regenerate PDF when loading from history
    st.session_state.pdf_export_data = None
    print("🔄 Auto-regenerating PDF for loaded content...")
    
    success = regenerate_pdf_for_history(entry)
    if success:
        # Get updated entry
        from db.helpers import get_entry_by_id
        updated_entry = get_entry_by_id(entry.id)
        if updated_entry and updated_entry.pdf_base64:
            # Store the base64 data directly in session state
            st.session_state.pdf_export_data = updated_entry.pdf_base64
            print("✅ PDF data stored in session")
    
    st.session_state.feedback_given = entry.feedback_given
    st.session_state.regenerated = False
    st.session_state.current_history_id = str(entry.id)
    st.session_state.from_history = True
    st.session_state.saved_to_history = True
    st.session_state.current_page = "generator"
    
    st.rerun()