import streamlit as st
import base64
import re
from utils.pdf_export import export_content_to_pdf

def render_export_section():
    """Render the export section"""
    if st.session_state.generated_output and not st.session_state.regenerated:
        st.markdown("---")
        st.subheader("📤 Export Content")
        
        # Debug info
        with st.expander("🔧 PDF Debug Info", expanded=False):
            st.write("PDF data type:", type(st.session_state.pdf_export_data))
            st.write("PDF data length:", len(st.session_state.pdf_export_data) if st.session_state.pdf_export_data else 0)
            st.write("From history:", st.session_state.get('from_history', False))
        
        if st.session_state.pdf_export_data:
            filename = generate_filename()
            download_link = create_download_link(st.session_state.pdf_export_data, filename)
            st.markdown(download_link, unsafe_allow_html=True)
            st.caption("💡 This PDF contains properly formatted content suitable for printing or sharing.")
        else:
            st.warning("⚠️ PDF export not available for this content.")
            
            # Try to regenerate PDF
            if st.button("🔄 Regenerate PDF"):
                try:
                    if st.session_state.user_type == "student":
                        pdf_data = generate_pdf(
                            st.session_state.generated_output, 
                            "student", 
                            level=st.session_state.student_level
                        )
                    else:
                        pdf_data = generate_pdf(
                            st.session_state.generated_output, 
                            "tutor", 
                            level=st.session_state.student_level,
                            topic=st.session_state.tutor_topic,
                            content_type=st.session_state.tutor_content_type,
                            objectives=""
                        )
                    
                    if pdf_data:
                        st.session_state.pdf_export_data = pdf_data
                        st.success("✅ PDF regenerated! Try downloading again.")
                        st.rerun()
                    else:
                        st.error("❌ Failed to regenerate PDF.")
                except Exception as e:
                    st.error(f"❌ PDF regeneration error: {str(e)}")

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
    """Create a download link for PDF file with better error handling"""
    try:
        # If it's already a string (base64), skip encoding
        if isinstance(pdf_data, str):
            # Check if it's already a base64 string
            if pdf_data.startswith('data:application/pdf;base64,'):
                # Extract just the base64 part
                b64 = pdf_data.split(',')[1] if ',' in pdf_data else pdf_data
            else:
                b64 = pdf_data
        elif isinstance(pdf_data, bytes):
            b64 = base64.b64encode(pdf_data).decode()
        else:
            st.error(f"❌ Unexpected PDF data type: {type(pdf_data)}")
            return "<p>❌ PDF data format error</p>"
        
        # Create the download link
        href = f'''
        <a href="data:application/pdf;base64,{b64}" download="{filename}"
           style="background-color:#4CAF50;color:white;padding:12px 24px;text-align:center;
           text-decoration:none;display:inline-block;border-radius:4px;font-weight:bold;"
           onclick="console.log('Downloading PDF: {filename}')">
           📥 Download PDF
        </a>
        '''
        return href
        
    except Exception as e:
        error_msg = f"❌ Error creating download link: {str(e)}"
        st.error(error_msg)
        return f'<p style="color: red;">{error_msg}</p>'

def generate_pdf(output, user_type, **kwargs):
    """Generate PDF for download"""
    try:
        if user_type == "student":
            pdf_title = f"Simplified Content - {kwargs.get('level', 'Student')}"
            pdf_bytes = export_content_to_pdf(
                content=output,
                title=pdf_title,
                student_level=kwargs.get('level', ''),
                content_type=None,
                objectives=None
            )
        else:
            pdf_title = f"{kwargs.get('content_type', 'Content')} - {kwargs.get('topic', 'Topic')}"
            pdf_bytes = export_content_to_pdf(
                content=output,
                title=pdf_title,
                student_level=kwargs.get('level', ''),
                content_type=kwargs.get('content_type'),
                objectives=kwargs.get('objectives')
            )
        
        if pdf_bytes and len(pdf_bytes) > 100:
            print(f"✅ PDF generated: {len(pdf_bytes)} bytes")
            # Convert to base64 for session storage
            pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
            return pdf_base64
        else:
            print(f"❌ PDF generation failed")
            return None
        
    except Exception as pdf_error:
        print(f"❌ PDF generation failed: {pdf_error}")
        return None