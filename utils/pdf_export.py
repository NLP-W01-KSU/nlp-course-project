from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import re
from datetime import datetime

def export_content_to_pdf(content, title, student_level, content_type=None, objectives=None):
    """
    Export generated content to a well-formatted PDF
    """
    import io
    buffer = io.BytesIO()
    
    try:
        print(f"🔧 Starting PDF export: title='{title}', content_length={len(content)}")
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            textColor=colors.darkblue,
            alignment=1
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.darkblue,
            spaceBefore=20
        )
        
        subheading_style = ParagraphStyle(
            'CustomSubheading',
            parent=styles['Heading3'],
            fontSize=12,
            spaceAfter=6,
            textColor=colors.darkblue,
            spaceBefore=15
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=12,
            leading=14
        )
        
        metadata_style = ParagraphStyle(
            'Metadata',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.gray,
            spaceAfter=6
        )
        
        # Build story
        story = []
        
        # Title
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 20))
        
        # Metadata
        story.append(Paragraph(f"<b>Target Level:</b> {student_level}", metadata_style))
        if content_type:
            story.append(Paragraph(f"<b>Content Type:</b> {content_type}", metadata_style))
        story.append(Paragraph(f"<b>Generated on:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}", metadata_style))
        story.append(Paragraph("<b>Source:</b> TailorED AI Educational Assistant", metadata_style))
        
        story.append(Spacer(1, 30))
        
        # Learning objectives
        if objectives:
            story.append(Paragraph("Learning Objectives", heading_style))
            objectives_clean = clean_html_content(objectives)
            story.append(Paragraph(objectives_clean, normal_style))
            story.append(Spacer(1, 20))
        
        # Main content
        story.append(Paragraph("Content", heading_style))
        
        # Process content with proper formatting
        content_paragraphs = clean_and_split_content(content)
        print(f"🔧 Processed {len(content_paragraphs)} content paragraphs")
        
        for i, paragraph in enumerate(content_paragraphs):
            try:
                if is_markdown_table(paragraph):
                    # Handle markdown tables
                    try:
                        table_data = parse_markdown_table(paragraph)
                        if table_data:
                            table = Table(table_data)
                            table.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('FONTSIZE', (0, 0), (-1, 0), 12),
                                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                                ('FONTSIZE', (0, 1), (-1, -1), 10),
                                ('GRID', (0, 0), (-1, -1), 1, colors.black)
                            ]))
                            story.append(table)
                            story.append(Spacer(1, 20))
                    except Exception as e:
                        # If table parsing fails, fall back to plain text
                        print(f"⚠️ Table parsing failed for paragraph {i}, using plain text: {e}")
                        clean_para = clean_html_content(paragraph)
                        story.append(Paragraph(clean_para, normal_style))
                        story.append(Spacer(1, 8))
                        
                elif is_heading(paragraph):
                    clean_para = clean_html_content(paragraph)
                    story.append(Paragraph(clean_para, subheading_style))
                    story.append(Spacer(1, 8))
                else:
                    clean_para = clean_html_content(paragraph)
                    formatted_para = format_bullet_points(clean_para)
                    story.append(Paragraph(formatted_para, normal_style))
                    story.append(Spacer(1, 8))
            except Exception as para_error:
                print(f"⚠️ Error processing paragraph {i}: {para_error}")
                # Add a simple paragraph as fallback
                story.append(Paragraph(f"Content section {i+1}", normal_style))
                story.append(Spacer(1, 8))
        
        # Footer note
        story.append(Spacer(1, 30))
        story.append(Paragraph(
            "<i>This content was AI-generated and should be reviewed for accuracy before use in formal educational settings.</i>",
            metadata_style
        ))
        
        # Build PDF
        print("🔧 Building PDF document...")
        doc.build(story)
        
        pdf_data = buffer.getvalue()
        buffer.close()
        
        # Basic validation
        if len(pdf_data) < 100:
            raise ValueError(f"Generated PDF is too small ({len(pdf_data)} bytes), likely empty")
        
        print(f"✅ PDF export successful: {len(pdf_data)} bytes")
        return pdf_data
        
    except Exception as e:
        print(f"❌ PDF export failed: {e}")
        try:
            buffer.close()
        except:
            pass
        
        # Return a simple error PDF as fallback
        return create_error_pdf(str(e))

def create_error_pdf(error_message):
    """Create a simple PDF with error message"""
    import io
    buffer = io.BytesIO()
    
    try:
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        styles = getSampleStyleSheet()
        
        story = []
        story.append(Paragraph("PDF Generation Error", styles['Heading1']))
        story.append(Spacer(1, 20))
        story.append(Paragraph("There was an error generating the PDF:", styles['Normal']))
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"<i>{error_message}</i>", styles['Normal']))
        story.append(Spacer(1, 20))
        story.append(Paragraph("Please try regenerating the content or contact support.", styles['Normal']))
        
        doc.build(story)
        pdf_data = buffer.getvalue()
        buffer.close()
        
        return pdf_data
    except Exception as fallback_error:
        print(f"❌ Even error PDF failed: {fallback_error}")
        return None

def clean_html_content(text):
    """Clean HTML tags and markdown syntax from text"""
    if not text:
        return ""
    
    try:
        # Remove HTML tags but keep the content
        text = re.sub(r'<[^>]+>', '', text)
        
        # Clean up markdown table syntax
        text = re.sub(r'\|+\s*', ' ', text)  # Remove table pipes but keep spaces
        text = re.sub(r'-+\s*', '', text)    # Remove table separator lines
        
        # Clean up other markdown
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)  # Bold
        text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)      # Italic
        text = re.sub(r'`(.*?)`', r'<font face="Courier">\1</font>', text)  # Code
        
        # Handle line breaks properly
        text = re.sub(r'<br/>', '<br/>', text)
        text = re.sub(r'\n', '<br/>', text)
        
        # Clean up extra spaces
        text = re.sub(r' +', ' ', text)
        text = re.sub(r'<br/>\s*<br/>', '<br/><br/>', text)
        
        return text.strip()
    except Exception as e:
        print(f"⚠️ Error cleaning HTML content: {e}")
        return str(text)[:500]  # Return truncated text as fallback

def clean_and_split_content(content):
    """Split content into paragraphs and clean formatting"""
    try:
        # First, extract and handle tables separately
        tables = extract_markdown_tables(content)
        
        # Remove tables from content for paragraph processing
        content_without_tables = remove_markdown_tables(content)
        
        # Split into paragraphs
        paragraphs = re.split(r'\n\s*\n', content_without_tables)
        
        # Clean each paragraph and interleave with tables
        cleaned_paragraphs = []
        current_pos = 0
        
        for para in paragraphs:
            para = para.strip()
            if para and len(para) > 1:
                # Check if there's a table at this position in original content
                for table_start, table_end, table_content in tables:
                    if current_pos <= table_start < current_pos + len(para):
                        cleaned_paragraphs.append(table_content)
                
                cleaned_para = para
                cleaned_paragraphs.append(cleaned_para)
                current_pos += len(para) + 2  # +2 for the newlines
        
        return cleaned_paragraphs
    except Exception as e:
        print(f"⚠️ Error cleaning and splitting content: {e}")
        # Fallback: simple split by paragraphs
        return [p.strip() for p in content.split('\n\n') if p.strip()]

def extract_markdown_tables(content):
    """Extract markdown tables from content"""
    try:
        tables = []
        table_pattern = r'(\|.*\|[\r\n]+\|[\s\-|]*[\r\n]+(?:\|.*\|[\r\n]*)+)'
        
        for match in re.finditer(table_pattern, content):
            table_content = match.group(1)
            tables.append((match.start(), match.end(), table_content))
        
        return tables
    except Exception as e:
        print(f"⚠️ Error extracting markdown tables: {e}")
        return []

def remove_markdown_tables(content):
    """Remove markdown tables from content"""
    try:
        table_pattern = r'(\|.*\|[\r\n]+\|[\s\-|]*[\r\n]+(?:\|.*\|[\r\n]*)+)'
        return re.sub(table_pattern, '', content)
    except Exception as e:
        print(f"⚠️ Error removing markdown tables: {e}")
        return content

def is_markdown_table(text):
    """Check if text is a markdown table"""
    try:
        lines = text.strip().split('\n')
        if len(lines) < 2:
            return False
        
        # Check if it has table structure
        has_pipes = all('|' in line for line in lines[:2])
        has_separator = '---' in lines[1] or '===' in lines[1] if len(lines) > 1 else False
        
        return has_pipes and (has_separator or len(lines) >= 2)
    except Exception as e:
        print(f"⚠️ Error checking markdown table: {e}")
        return False

def parse_markdown_table(table_text):
    """Parse markdown table into 2D array for ReportLab Table"""
    try:
        lines = [line.strip() for line in table_text.split('\n') if line.strip()]
        
        if len(lines) < 2:
            return None
        
        # Remove separator line if present
        if '---' in lines[1] or '===' in lines[1]:
            lines.pop(1)
        
        table_data = []
        for line in lines:
            if line.startswith('|'):
                line = line[1:]
            if line.endswith('|'):
                line = line[:-1]
            
            cells = [cell.strip() for cell in line.split('|')]
            table_data.append(cells)
        
        return table_data
    except Exception as e:
        print(f"⚠️ Error parsing markdown table: {e}")
        return None

def is_heading(text):
    """Check if text appears to be a heading"""
    try:
        if len(text) < 100 and (text.endswith(':') or text.isupper() or looks_like_heading(text)):
            return True
        return False
    except Exception as e:
        print(f"⚠️ Error checking heading: {e}")
        return False

def looks_like_heading(text):
    """Heuristic to detect heading-like text"""
    try:
        heading_indicators = [
            'introduction', 'overview', 'key concepts', 'summary', 'conclusion',
            'examples', 'applications', 'definition', 'theory', 'practice',
            'problem', 'solution', 'advantages', 'disadvantages', 'steps'
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in heading_indicators)
    except Exception as e:
        print(f"⚠️ Error in looks_like_heading: {e}")
        return False

def format_bullet_points(text):
    """Format bullet points and lists for PDF"""
    try:
        lines = text.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if line.startswith(('•', '-', '*')):
                formatted_lines.append(f"&bull; {line[1:].strip()}")
            elif line and line[0].isdigit() and '. ' in line[:5]:
                formatted_lines.append(line)
            else:
                formatted_lines.append(line)
        
        return '<br/>'.join(formatted_lines)
    except Exception as e:
        print(f"⚠️ Error formatting bullet points: {e}")
        return text