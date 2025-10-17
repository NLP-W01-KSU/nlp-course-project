import streamlit as st
import tempfile
import os
from utils.file_utils import extract_text_from_pdf, extract_text_from_pptx, extract_text_from_docx

def process_uploaded_file(uploaded_file):
    """Process uploaded file and extract text with proper error handling"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name

        file_extension = uploaded_file.name.lower()
        
        if file_extension.endswith('.pdf'):
            full_text = extract_text_from_pdf(tmp_path)
        elif file_extension.endswith('.pptx'):
            full_text = extract_text_from_pptx(tmp_path)
        elif file_extension.endswith('.docx'):
            full_text = extract_text_from_docx(tmp_path)
        else:
            return None, "Unsupported file type"

        # Clean up temp file
        os.unlink(tmp_path)

        if not full_text.strip():
            return None, "No text could be extracted from the file"
            
        return full_text, None
        
    except Exception as e:
        # Clean up temp file if it exists
        try:
            if 'tmp_path' in locals():
                os.unlink(tmp_path)
        except:
            pass
        return None, f"Error processing file: {str(e)}"

def get_student_content_input():
    """Get content input from student (file upload or text)"""
    st.subheader("📚 Provide Your Learning Material")
    content_source = st.radio(
        "How would you like to provide the content?",
        ["Upload File (PDF, PPTX, DOCX)", "Paste Text"],
        key="student_source"
    )
    
    content_text = ""
    filename = "simplified_content"
    
    if content_source == "Upload File (PDF, PPTX, DOCX)":
        uploaded_file = st.file_uploader(
            "Upload your course material", 
            type=["pdf", "pptx", "docx"],
            help="Upload lecture slides, textbook chapters, or any difficult course material"
        )
        if uploaded_file:
            with st.spinner("📖 Reading your document..."):
                content_text, error = process_uploaded_file(uploaded_file)
            if error:
                st.error(f"❌ {error}")
            else:
                st.success("✅ Document processed successfully!")
                filename = uploaded_file.name
    else:
        content_text = st.text_area(
            "Paste the content you want to simplify:",
            height=200,
            placeholder="Paste complex textbook content, lecture notes, or any difficult learning material here..."
        )
    
    return content_text, filename