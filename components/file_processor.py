import streamlit as st
import tempfile
import os
from utils.file_utils import extract_text_from_pdf, extract_text_from_pptx, extract_text_from_docx
import logging

# Set up logging
logger = logging.getLogger(__name__)

# File size limits (in bytes)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
RECOMMENDED_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def process_uploaded_file(uploaded_file):
    """Process uploaded file with Hugging Face Spaces compatible approach"""
    logger.info(f"🔄 Starting file processing: {uploaded_file.name}")
    
    # Check file size first
    file_size = len(uploaded_file.getvalue())
    file_size_mb = file_size / (1024 * 1024)
    
    if file_size > MAX_FILE_SIZE:
        return None, f"📁 File too large ({file_size_mb:.1f}MB). Maximum file size is {MAX_FILE_SIZE // (1024*1024)}MB. Please use a smaller file or split your content."
    
    if file_size > RECOMMENDED_FILE_SIZE:
        st.warning(f"⚠️ Large file detected ({file_size_mb:.1f}MB). Processing may take longer. For best results, use files under {RECOMMENDED_FILE_SIZE // (1024*1024)}MB.")
    
    try:
        file_extension = uploaded_file.name.lower()
        file_content = uploaded_file.getvalue()
        
        logger.info(f"📁 Processing {file_extension} file, size: {file_size} bytes")
        
        # For Hugging Face Spaces, use BytesIO for everything
        from io import BytesIO
        
        if file_extension.endswith('.pdf'):
            logger.info("📄 Processing PDF with direct bytes...")
            try:
                # Try using PyMuPDF with bytes
                import fitz
                doc = fitz.open(stream=file_content, filetype="pdf")
                full_text = ""
                for page in doc:
                    full_text += page.get_text()
                doc.close()
                logger.info(f"✅ PDF processed: {len(full_text)} chars")
            except Exception as pdf_error:
                logger.error(f"❌ PDF bytes failed: {pdf_error}")
                # Fallback to very simple temp file approach
                return process_pdf_with_minimal_temp(uploaded_file)
                
        elif file_extension.endswith('.pptx'):
            logger.info("📊 Processing PPTX with BytesIO...")
            from pptx import Presentation
            pptx_file = BytesIO(file_content)
            prs = Presentation(pptx_file)
            full_text = ""
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text:
                        full_text += shape.text + "\n"
            full_text = full_text.strip()
            logger.info(f"✅ PPTX processed: {len(full_text)} chars")
            
        elif file_extension.endswith('.docx'):
            logger.info("📝 Processing DOCX with BytesIO...")
            from docx import Document
            docx_file = BytesIO(file_content)
            doc = Document(docx_file)
            full_text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
            full_text = full_text.strip()
            logger.info(f"✅ DOCX processed: {len(full_text)} chars")
            
        else:
            return None, "Unsupported file type. Please upload PDF, PPTX, or DOCX."

        if not full_text.strip():
            # More specific error message for different scenarios
            if file_size > 20 * 1024 * 1024:  # 20MB
                return None, "No text could be extracted from this large file. The file may contain mostly images or scanned content. Try a smaller file or ensure the file contains extractable text."
            elif file_size > 5 * 1024 * 1024:  # 5MB
                return None, "No text could be extracted. Large files often contain scanned images without OCR text. Try a smaller file or use OCR software first."
            else:
                return None, "No text could be extracted. The file might contain only images, be password protected, or have scanned content without OCR."
            
        return full_text, None
        
    except MemoryError:
        logger.error("❌ Memory error processing large file")
        return None, "File is too large to process and caused memory issues. Please try a smaller file (under 20MB recommended)."
    except Exception as e:
        logger.error(f"❌ File processing failed: {str(e)}")
        if "memory" in str(e).lower() or "large" in str(e).lower():
            return None, "File is too large to process. Please use a smaller file (under 20MB recommended)."
        return None, f"Error processing file: {str(e)}"

def process_pdf_with_minimal_temp(uploaded_file):
    """Minimal temp file approach for PDFs as last resort"""
    try:
        # Check file size first
        file_size = len(uploaded_file.getvalue())
        if file_size > MAX_FILE_SIZE:
            file_size_mb = file_size / (1024 * 1024)
            return None, f"File too large ({file_size_mb:.1f}MB). Maximum file size is {MAX_FILE_SIZE // (1024*1024)}MB."
            
        # Use Streamlit's temp file handling
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        # Extract text
        full_text = extract_text_from_pdf(tmp_path)
        
        # Immediate cleanup
        try:
            os.unlink(tmp_path)
        except:
            pass
            
        return full_text, None
        
    except MemoryError:
        return None, "File is too large to process. Please try a smaller file (under 20MB recommended)."
    except Exception as e:
        # Cleanup on error
        try:
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except:
            pass
        
        if "too large" in str(e).lower():
            return None, str(e)
        return None, f"PDF processing failed: {str(e)}"

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
        # Show file size limits to user
        st.info(f"📁 **File Size Limits:** Maximum {MAX_FILE_SIZE // (1024*1024)}MB, recommended under {RECOMMENDED_FILE_SIZE // (1024*1024)}MB for best performance")
        
        uploaded_file = st.file_uploader(
            "Upload your course material", 
            type=["pdf", "pptx", "docx"],
            help="Upload lecture slides, textbook chapters (max 50MB)"
        )
        if uploaded_file:
            # Show file size info
            file_size = len(uploaded_file.getvalue())
            file_size_mb = file_size / (1024 * 1024)
            st.caption(f"📊 File size: {file_size_mb:.1f}MB")
            
            with st.spinner("📖 Reading your document..."):
                content_text, error = process_uploaded_file(uploaded_file)
                
            if error:
                if "too large" in error.lower():
                    st.error(f"❌ {error}")
                else:
                    st.error(f"❌ {error}")
                    # Show additional help for extraction failures
                    with st.expander("💡 Troubleshooting tips"):
                        st.write("""
                        **If text extraction fails:**
                        - Ensure the file contains selectable text (not just images/scans)
                        - Try a smaller file or extract specific sections
                        - For scanned documents, use OCR software first
                        - Check if the file is password protected
                        - Try converting to a different format
                        """)
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
