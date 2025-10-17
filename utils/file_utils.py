import os
import fitz  # PyMuPDF
from pptx import Presentation
from docx import Document

def extract_text_from_pdf(pdf_path):
    """Extracts text from PDF files."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"File not found: {pdf_path}")

    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    doc.close()
    return full_text.strip()

def extract_text_from_pptx(pptx_path):
    """Extracts text from PowerPoint (PPTX) files."""
    if not os.path.exists(pptx_path):
        raise FileNotFoundError(f"File not found: {pptx_path}")

    prs = Presentation(pptx_path)
    full_text = ""
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                full_text += shape.text + "\n"
    return full_text.strip()

def extract_text_from_docx(docx_path):
    """Extracts text from Word (DOCX) files."""
    if not os.path.exists(docx_path):
        raise FileNotFoundError(f"File not found: {docx_path}")

    doc = Document(docx_path)
    full_text = "\n".join([para.text for para in doc.paragraphs])
    return full_text.strip()