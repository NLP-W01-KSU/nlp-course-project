import streamlit as st
import base64
import re
from utils.pdf_export import export_content_to_pdf

def render_export_section():
    """Render the export section"""
    if st.session_state.generated_output and not st.session_state.regenerated:
        st.markdown("---")
        st.subheader("📤 Export Content")
        
        if st.session_state.pdf_export_data:
            filename = generate_filename()
            download_link = create_download_link(st.session_state.pdf_export_data, filename)
            st.markdown(download_link, unsafe_allow_html=True)
            st.caption("💡 This PDF contains properly formatted content suitable for printing or sharing.")
        else:
            st.warning("PDF export not available for this content.")

def generate_filename():
    """Generate appropriate filename based on content type"""
    if st.session_state.user_type == "student":
        level_clean = re.sub(r'[^a-zA-Z0-9]', '_', st.session_state.student_level)
        return f"simplified_content_{level_clean}.pdf"
    else:
        topic_clean = re.sub(r'[^a-zA-Z0-9]', '_', st.session_state.tutor_topic)[:30] if st.session_state.tutor_topic else "teaching_content"
        content_type_clean = st.session_state.tutor_content_type.replace(' ', '_') if st.session_state.tutor_content_type else "content"
        return f"{content_type_clean}_{topic_clean}.pdf"

def create_download_link(pdf_data, filename):
    """Create a download link for PDF file"""
    b64 = base64.b64encode(pdf_data).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}" style="background-color: #4CAF50; color: white; padding: 12px 24px; text-align: center; text-decoration: none; display: inline-block; border-radius: 4px; font-weight: bold;">📥 Download PDF</a>'
    return href

def generate_pdf(output, user_type, **kwargs):
    """Generate PDF for download using the existing pdf_export utility"""
    try:
        if user_type == "student":
            pdf_title = f"Simplified Content - {kwargs.get('level', 'Student')}"
            pdf_data = export_content_to_pdf(
                content=output,
                title=pdf_title,
                student_level=kwargs.get('level', ''),
                content_type=None,
                objectives=None
            )
        else:
            pdf_title = f"{kwargs.get('content_type', 'Content')} - {kwargs.get('topic', 'Topic')}"
            pdf_data = export_content_to_pdf(
                content=output,
                title=pdf_title,
                student_level=kwargs.get('level', ''),
                content_type=kwargs.get('content_type'),
                objectives=kwargs.get('objectives')
            )
        
        return pdf_data
        
    except Exception as pdf_error:
        print(f"PDF generation failed: {pdf_error}")
        return None