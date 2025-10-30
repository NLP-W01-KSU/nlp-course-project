import streamlit as st
import re
from generator import model_manager
from components.file_processor import get_student_content_input
from components.export_handler import generate_pdf
from components.session_manager import update_session_state

def render_student_flow():
    """Render the student content generation flow"""
    st.header("🎓 Student Learning Assistant")
    render_student_info()
    
    # Check if we need to regenerate with a different model
    if st.session_state.get("regenerate_with_new_model") and st.session_state.get("original_content_text"):
        handle_student_regeneration()
        return
    
    content_text, filename = get_student_content_input()
    student_level = get_student_level()
    specific_help = get_student_context()
    
    if content_text and st.button("🚀 Simplify This Content", type="primary", key="generate_student_content"):
        generate_student_content(content_text, student_level, specific_help, filename)

def handle_student_regeneration():
    """Handle student content regeneration with new model"""
    st.header("🎓 Student Learning Assistant")
    render_student_info()
    
    # Show we're regenerating
    st.info("🔄 Regenerating your content with the new model...")
    
    # Get preserved inputs
    content_text = st.session_state.original_content_text
    student_level = st.session_state.student_level
    specific_help = st.session_state.get("original_specific_help", "")
    filename = st.session_state.get("original_filename", "regenerated_content.pdf")
    
    # Show original inputs for context
    with st.expander("📋 Original Inputs (Read-only)", expanded=True):
        st.write(f"**Student Level:** {student_level}")
        st.write(f"**Content Length:** {len(content_text)} characters")
        if specific_help:
            st.write(f"**Specific Help Requested:** {specific_help}")
    
    # Regenerate the content
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
    """Generate content for student with optimized content handling"""
    # STORE ORIGINAL CONTENT FOR REGENERATION
    st.session_state.original_content_text = content_text
    st.session_state.original_specific_help = specific_help
    st.session_state.original_filename = filename
    
    if len(content_text) > 15000:
        st.info("📝 Your content is quite comprehensive. I'll process it in sections for optimal quality...")
        generate_chunked_content(content_text, student_level, specific_help, filename)
    elif len(content_text) > 8000:
        st.info("📝 Processing your content with optimized models...")
        generate_single_large_content(content_text, student_level, specific_help, filename)
    else:
        generate_single_content(content_text, student_level, specific_help, filename)

def generate_single_content(content_text, student_level, specific_help, filename):
    """Generate content for normal-sized inputs"""
    with st.spinner("✍️ Creating student-friendly explanation..."):
        selected_model = st.session_state.get("selected_model", "groq")
        
        # Use Phi-3 specific prompts if Phi-3 is selected
        if selected_model == "phi3":
            prompt = build_phi3_student_prompt(content_text, student_level, specific_help)
        else:
            prompt = build_groq_student_prompt(content_text, student_level, specific_help)
        
        try:
            output = model_manager.generate(
                prompt, 
                selected_model,
                user_type="student",
                student_level=student_level,
                content_type="simplified_explanation"
            )
            
            if output is None:
                st.error("❌ AI service returned no response")
                return
            
            # Clean the output for Phi-3 specifically
            if selected_model == "phi3":
                output = clean_phi3_output(output)
            
            if any(msg in output for msg in ["🚫", "📊", "❌", "[Error", "[RateLimit]", "[Quota]", "[Auth]", "[Empty]", "❌ Phi-3 Error:"]):
                st.error(output)
                return
            
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
                saved_to_history=False,
                current_history_id=None,
                generated_model=selected_model
            )
            
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Generation failed: {str(e)}")

def generate_single_large_content(content_text, student_level, specific_help, filename):
    """Generate content for large but manageable inputs using high-capacity models"""
    with st.spinner("✍️ Creating comprehensive explanation..."):
        selected_model = st.session_state.get("selected_model", "groq")
        
        # Use Phi-3 specific prompts if Phi-3 is selected
        if selected_model == "phi3":
            prompt = build_phi3_student_prompt(content_text, student_level, specific_help)
        else:
            prompt = build_groq_student_prompt(content_text, student_level, specific_help)
        
        try:
            if selected_model == "phi3":
                output = model_manager.generate(
                    prompt, 
                    selected_model,
                    user_type="student",
                    student_level=student_level,
                    content_type="simplified_explanation"
                )
                output = clean_phi3_output(output)
            else:
                output = model_manager.groq_generator.generate_large_content(prompt)
            
            if any(msg in output for msg in ["🚫", "📊", "❌", "[Error", "[RateLimit]", "[Quota]", "[Auth]", "[Empty]", "❌ Phi-3 Error:"]):
                st.error(output)
                return
            
            # Generate PDF and update session state
            pdf_data = generate_pdf(output, "student", level=student_level)
            
            update_session_state(
                original_prompt=prompt,
                generated_output=output,
                feedback_given=False,
                regenerated=False,
                content_source="student",
                student_level=student_level,
                original_filename=filename,
                pdf_export_data=pdf_data,
                saved_to_history=False,
                current_history_id=None,
                generated_model=selected_model
            )
            
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Generation failed: {str(e)}")

def generate_chunked_content(content_text, student_level, specific_help, filename):
    """Generate content for very large inputs by chunking"""
    chunks = chunk_content(content_text, max_chunk_size=8000)
    
    if not chunks:
        st.error("❌ Unable to process this content. Please try with shorter text.")
        return
    
    all_outputs = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    selected_model = st.session_state.get("selected_model", "groq")
    
    for i, chunk in enumerate(chunks):
        status_text.text(f"📖 Processing section {i+1}/{len(chunks)}...")
        progress_bar.progress((i) / len(chunks))
        
        # Use Phi-3 specific prompts if Phi-3 is selected
        if selected_model == "phi3":
            prompt = build_phi3_chunk_prompt(chunk, student_level, specific_help, i+1, len(chunks))
        else:
            prompt = build_groq_chunk_prompt(chunk, student_level, specific_help, i+1, len(chunks))
        
        try:
            output = model_manager.generate(
                prompt, 
                selected_model,
                user_type="student", 
                student_level=student_level,
                content_type="simplified_explanation"
            )
            
            if selected_model == "phi3":
                output = clean_phi3_output(output)
            
            if any(msg in output for msg in ["🚫", "📊", "❌", "[Error", "[RateLimit]", "[Quota]", "[Auth]", "[Empty]", "❌ Phi-3 Error:"]):
                st.error(f"❌ Failed to process section {i+1}: {output}")
                return
            
            all_outputs.append(output)
            
        except Exception as e:
            st.error(f"❌ Failed to process section {i+1}: {str(e)}")
            return
    
    # Update progress to complete
    progress_bar.progress(1.0)
    status_text.text("✅ All sections processed! Combining results...")
    
    # Combine all outputs
    final_output = combine_chunk_outputs(all_outputs, student_level)
    
    # Generate PDF and update session state
    pdf_data = generate_pdf(final_output, "student", level=student_level)
    
    update_session_state(
        original_prompt=f"Simplified content for {student_level} level",
        generated_output=final_output,
        feedback_given=False,
        regenerated=False,
        content_source="student", 
        student_level=student_level,
        original_filename=filename,
        pdf_export_data=pdf_data,
        saved_to_history=False,
        current_history_id=None,
        generated_model=selected_model
    )
    
    status_text.text("✅ Content generation complete!")
    st.rerun()

def chunk_content(content, max_chunk_size=8000):
    """Split content into manageable chunks based on new limits"""
    paragraphs = re.split(r'\n\s*\n', content)
    chunks = []
    current_chunk = ""
    
    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) < max_chunk_size:
            current_chunk += paragraph + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = paragraph + "\n\n"
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def build_phi3_chunk_prompt(chunk, student_level, specific_help, chunk_num, total_chunks):
    """Build Phi-3 specific prompt for a single chunk - STRICTER VERSION"""
    prompt = f"""TASK: Write the actual simplified explanation for this content section.

CONTENT SECTION {chunk_num}/{total_chunks}:
{chunk}

STUDENT: {student_level}
"""
    if specific_help:
        prompt += f"\nSTUDENT'S REQUEST: {specific_help}"
    
    prompt += f"""

DIRECTIVES:
- WRITE THE ACTUAL EXPLANATION ONLY
- Use simple, clear language for {student_level}
- Break complex ideas into basic concepts
- Use everyday examples and analogies
- Define technical terms in simple words
- Structure with clear headings

STRICT PROHIBITIONS:
- NO instructional language (no "I will explain", "This section describes")
- NO meta-commentary about the explanation
- NO learning objectives or activities
- NO phrases like "students will understand"
- NO references to yourself as AI/assistant

BEGIN EXPLANATION NOW:

"""
    return prompt

def build_groq_chunk_prompt(chunk, student_level, specific_help, chunk_num, total_chunks):
    """Build Groq prompt for a single chunk"""
    prompt = f"""Simplify this content for {student_level} students:

CONTENT SECTION {chunk_num}/{total_chunks}:
{chunk}

STUDENT LEVEL: {student_level}
"""
    if specific_help:
        prompt += f"\nSPECIFIC CONFUSION: {specific_help}"
    
    prompt += f"""

Create a clear, simplified explanation of this content.
"""
    return prompt

def combine_chunk_outputs(outputs, student_level):
    """Combine chunk outputs into a cohesive document"""
    combined = f"# Simplified Content for {student_level} Level\n\n"
    
    for i, output in enumerate(outputs):
        # Clean up any remaining instructional language
        clean_output = clean_phi3_output(output)
        combined += f"## Part {i+1}\n\n{clean_output.strip()}\n\n---\n\n"
    
    return combined

def build_phi3_student_prompt(content_text, student_level, specific_help):
    """Build Phi-3 specific prompt for student content generation - STRICTER VERSION"""
    prompt = f"""TASK: Write the actual simplified explanation for this content.

ORIGINAL CONTENT:
{content_text}

STUDENT: {student_level}
"""
    if specific_help:
        prompt += f"\nSTUDENT'S SPECIFIC REQUEST: {specific_help}"
    
    prompt += f"""

DIRECTIVES:
- WRITE THE ACTUAL EXPLANATION ONLY
- Use simple, clear language appropriate for {student_level}
- Break down complex concepts into basic building blocks
- Use everyday analogies and concrete examples
- Define all technical terms when first used
- Structure logically with clear headings
- Make it engaging and conversational

STRICT PROHIBITIONS:
- NO instructional language (no "I will explain", "Let me break this down")
- NO meta-commentary about the explanation process
- NO learning objectives, activities, or assessments
- NO phrases like "students will learn" or "this explains"
- NO lesson plans or educational frameworks
- NO references to yourself as AI, assistant, or teacher

BEGIN SIMPLIFIED EXPLANATION NOW:

"""
    return prompt

def build_groq_student_prompt(content_text, student_level, specific_help):
    """Build Groq prompt for student content generation"""
    prompt = f"""Create a simplified explanation of this content for {student_level} students:

CONTENT TO SIMPLIFY:
{content_text}

STUDENT LEVEL: {student_level}
"""
    if specific_help:
        prompt += f"\nSPECIFIC CONFUSION: {specific_help}"
    
    prompt += f"""

Provide a clear, easy-to-understand explanation that:
- Breaks down complex concepts into simple terms
- Uses analogies and examples appropriate for {student_level}
- Defines technical terminology clearly
- Structures the content for easy learning
- Focuses on the most important concepts

Make the explanation engaging and accessible.
"""
    return prompt

def clean_phi3_output(output):
    """Clean Phi-3 output to remove instructional language and meta-commentary"""
    # Remove common instructional phrases
    patterns_to_remove = [
        r'Here is.*?explanation:',
        r'I will.*?now:',
        r'Let me.*?concept:',
        r'This section.*?content:',
        r'Below is.*?explanation:',
        r'Here\'s.*?breakdown:',
        r'In this.*?we will',
        r'Students will.*?understand',
        r'We can.*?explain',
        r'The following.*?explains',
        r'This content.*?describes',
        r'As an AI.*?assistant',
    ]
    
    cleaned = output
    for pattern in patterns_to_remove:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    # Remove any empty lines at the start
    cleaned = re.sub(r'^\s*\n+', '', cleaned)
    
    return cleaned.strip()