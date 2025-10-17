import streamlit as st
from generator import MultiGroqGenerator
from components.file_processor import get_student_content_input
from components.export_handler import generate_pdf
from components.session_manager import update_session_state

def render_student_flow():
    """Render the student content generation flow"""
    st.header("🎓 Student Learning Assistant")
    render_student_info()
    
    content_text, filename = get_student_content_input()
    student_level = get_student_level()
    specific_help = get_student_context()
    
    # Use a unique key for the button to prevent re-triggering
    if content_text and st.button("🚀 Simplify This Content", type="primary", key="generate_student_content"):
        generate_student_content(content_text, student_level, specific_help, filename)

def render_student_info():
    """Render student flow information"""
    st.info("""
    **How this works:** 
    Upload your course material or paste difficult content, and I'll generate a simplified, 
    easy-to-understand version tailored to your level.
    """)

def get_student_level():
    """Get student's academic level"""
    st.subheader("🎯 Your Learning Level")
    return st.selectbox(
        "What's your current academic level?",
        ["High School", "Undergraduate (1st-2nd year)", "Undergraduate (3rd-4th year)", "Masters", "PhD"],
        help="This helps me tailor the explanation to your level",
        key="student_level_select"
    )

def get_student_context():
    """Get additional context from student"""
    st.subheader("💡 Additional Context (Optional)")
    return st.text_area(
        "What specifically are you struggling with?",
        placeholder="e.g., 'I don't understand backpropagation' or 'The math notation is confusing'",
        help="Tell me what's confusing you for better help",
        key="student_context_input"
    )

def generate_student_content(content_text, student_level, specific_help, filename):
    """Generate content for student"""
    with st.spinner("✍️ Creating student-friendly explanation..."):
        prompt = build_student_prompt(content_text, student_level, specific_help)
        
        try:
            generator = MultiGroqGenerator()
            output = generator.generate(prompt)
            
            # Check if it's an error message
            if any(msg in output for msg in ["🚫", "📊", "❌"]):
                st.error(output)
                return  # ← CRITICAL: Stop here if it's an error
            
            # Generate PDF first
            pdf_data = generate_pdf(output, "student", level=student_level)
            
            # Update session state
            update_session_state(
                original_prompt=prompt,
                generated_output=output,
                feedback_given=False,
                regenerated=False,
                content_source="student",
                student_level=student_level,
                original_filename=filename,
                pdf_export_data=pdf_data,
                saved_to_history=False
            )
            
            # Force a rerun to show the generated content
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Generation failed: {str(e)}")

def build_student_prompt(content_text, student_level, specific_help):
    """Build prompt for student content generation"""
    prompt = f"""
CONTENT TO SIMPLIFY:
{content_text}

STUDENT LEVEL: {student_level}
"""
    if specific_help:
        prompt += f"\nSPECIFIC CONFUSION: {specific_help}"
    
    prompt += """
    
Please create a simplified, easy-to-understand explanation of this content that is appropriate for the student's level. Focus on:
1. Breaking down complex concepts into simple terms
2. Using analogies and real-world examples
3. Explaining any technical jargon
4. Making it engaging and accessible
5. Addressing any specific confusion mentioned
"""
    return prompt