import streamlit as st
import re
from generator import model_manager
from components.export_handler import generate_pdf
from components.session_manager import update_session_state

def render_tutor_flow():
    """Render the tutor content generation flow"""
    st.header("👨‍🏫 Tutor Content Creator")
    render_tutor_info()
    
    # Check if we need to regenerate with a different model
    if st.session_state.get("regenerate_with_new_model") and st.session_state.get("original_topic"):
        handle_tutor_regeneration()
        return
    
    topic, objectives, student_level, content_type, additional_req = get_tutor_inputs()
    
    if topic and objectives and st.button("🚀 Create Teaching Content", type="primary", key="generate_tutor_content"):
        generate_tutor_content(topic, objectives, student_level, content_type, additional_req)

def handle_tutor_regeneration():
    """Handle tutor content regeneration with new model"""
    st.header("👨‍🏫 Tutor Content Creator")
    render_tutor_info()
    
    # Show we're regenerating
    st.info("🔄 Regenerating your content with the new model...")
    
    # Get preserved inputs
    topic = st.session_state.original_topic
    objectives = st.session_state.original_objectives
    student_level = st.session_state.student_level
    content_type = st.session_state.tutor_content_type
    additional_req = st.session_state.get("original_additional_req", "")
    
    # Show original inputs for context
    with st.expander("📋 Original Inputs (Read-only)", expanded=True):
        st.write(f"**Topic:** {topic}")
        st.write(f"**Student Level:** {student_level}")
        st.write(f"**Content Type:** {content_type}")
        st.write(f"**Learning Objectives:** {objectives}")
        if additional_req:
            st.write(f"**Additional Requirements:** {additional_req}")
    
    # Regenerate the content
    generate_tutor_content(topic, objectives, student_level, content_type, additional_req)

def render_tutor_info():
    """Render tutor flow information"""
    st.info("""
    **How this works:** 
    Tell me what topic you want to teach, and I'll generate comprehensive educational content 
    tailored to your students' level and learning objectives.
    """)

def get_tutor_inputs():
    """Get all inputs from tutor"""
    st.subheader("📖 Teaching Topic")
    topic = st.text_area(
        "What topic do you want to teach?",
        placeholder="e.g., Neural Networks, Quantum Computing, Calculus Fundamentals, French Revolution",
        help="Be specific about the topic or concept",
        key="tutor_topic_input"
    )
    
    st.subheader("🎯 Learning Objectives")
    objectives = st.text_area(
        "What should students learn from this?",
        placeholder="e.g., 'Understand backpropagation', 'Apply gradient descent', 'Explain the causes of WWI'",
        help="List the key learning outcomes for students",
        key="tutor_objectives_input"
    )
    
    st.subheader("👥 Student Level")
    student_level = st.selectbox(
        "What level are your students?",
        ["Elementary School", "Middle School", "High School", "Undergraduate", "Graduate", "Professional Development"],
        help="Select the appropriate level for your students",
        key="tutor_student_level"
    )
    
    st.subheader("📝 Content Format")
    content_type = st.selectbox(
        "What type of content do you need?",
        ["Lesson Plan", "Study Guide", "Lecture Notes", "Interactive Activity", "Comprehensive Explanation"],
        help="Choose the format that best suits your teaching needs",
        key="tutor_content_type_select"
    )
    
    st.subheader("⚡ Additional Requirements (Optional)")
    additional_req = st.text_area(
        "Any specific requirements?",
        placeholder="e.g., 'Include code examples', 'Use historical primary sources', 'Focus on practical applications'",
        help="Specify any particular focus or requirements",
        key="tutor_additional_req"
    )
    
    return topic, objectives, student_level, content_type, additional_req

def generate_tutor_content(topic, objectives, student_level, content_type, additional_req):
    """Generate content for tutor with optimized content handling"""
    # STORE ORIGINAL INPUTS FOR REGENERATION
    st.session_state.original_topic = topic
    st.session_state.original_objectives = objectives
    st.session_state.original_additional_req = additional_req
    
    total_content_size = len(topic) + len(objectives) + len(additional_req)
    
    if total_content_size > 15000:
        st.info("📝 Creating comprehensive content with detailed sections...")
        generate_chunked_tutor_content(topic, objectives, student_level, content_type, additional_req)
    elif total_content_size > 8000:
        st.info("📝 Processing your comprehensive teaching content...")
        generate_single_large_tutor_content(topic, objectives, student_level, content_type, additional_req)
    else:
        generate_single_tutor_content(topic, objectives, student_level, content_type, additional_req)

def generate_single_tutor_content(topic, objectives, student_level, content_type, additional_req):
    """Generate content for normal-sized tutor requests"""
    with st.spinner("✍️ Generating educational content..."):
        selected_model = st.session_state.get("selected_model", "groq")
        
        # Use Phi-3 specific prompts if Phi-3 is selected
        if selected_model == "phi3":
            prompt = build_phi3_tutor_prompt(topic, objectives, student_level, content_type, additional_req)
        else:
            prompt = build_groq_tutor_prompt(topic, objectives, student_level, content_type, additional_req)
        
        try:
            output = model_manager.generate(
                prompt,
                selected_model,
                user_type="tutor", 
                student_level=student_level, 
                content_type=content_type
            )
            
            # Check if it's an error message
            if any(msg in output for msg in ["🚫", "📊", "❌", "[Error", "[RateLimit]", "[Quota]", "[Auth]", "[Empty]", "❌ Phi-3 Error:"]):
                st.error(output)
                return
            
            # Generate PDF
            pdf_data = generate_pdf(
                output, 
                "tutor", 
                level=student_level,
                topic=topic,
                content_type=content_type,
                objectives=objectives
            )
            
            # Update session state
            update_session_state(
                original_prompt=prompt,
                generated_output=output,
                feedback_given=False,
                regenerated=False,
                content_source="tutor",
                student_level=student_level,
                tutor_topic=topic,
                tutor_content_type=content_type,
                pdf_export_data=pdf_data,
                saved_to_history=False,
                current_history_id=None,
                generated_model=selected_model
            )
            
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Generation failed: {str(e)}")

def generate_single_large_tutor_content(topic, objectives, student_level, content_type, additional_req):
    """Generate content for large tutor requests using high-capacity models"""
    with st.spinner("✍️ Generating comprehensive educational content..."):
        selected_model = st.session_state.get("selected_model", "groq")
        
        # Use Phi-3 specific prompts if Phi-3 is selected
        if selected_model == "phi3":
            prompt = build_phi3_tutor_prompt(topic, objectives, student_level, content_type, additional_req)
        else:
            prompt = build_groq_tutor_prompt(topic, objectives, student_level, content_type, additional_req)
        
        try:
            if selected_model == "phi3":
                output = model_manager.generate(
                    prompt,
                    selected_model,
                    user_type="tutor",
                    student_level=student_level,
                    content_type=content_type
                )
            else:
                output = model_manager.groq_generator.generate_large_content(prompt)
            
            if any(msg in output for msg in ["🚫", "📊", "❌", "[Error", "[RateLimit]", "[Quota]", "[Auth]", "[Empty]", "❌ Phi-3 Error:"]):
                st.error(output)
                return
            
            # Generate PDF
            pdf_data = generate_pdf(
                output, 
                "tutor", 
                level=student_level,
                topic=topic,
                content_type=content_type,
                objectives=objectives
            )
            
            # Update session state
            update_session_state(
                original_prompt=prompt,
                generated_output=output,
                feedback_given=False,
                regenerated=False,
                content_source="tutor",
                student_level=student_level,
                tutor_topic=topic,
                tutor_content_type=content_type,
                pdf_export_data=pdf_data,
                saved_to_history=False,
                current_history_id=None,
                generated_model=selected_model
            )
            
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Generation failed: {str(e)}")

def generate_chunked_tutor_content(topic, objectives, student_level, content_type, additional_req):
    """Generate comprehensive tutor content by breaking down objectives"""
    objective_chunks = chunk_objectives(objectives, max_chunk_size=4000)
    
    if not objective_chunks:
        generate_single_large_tutor_content(topic, objectives, student_level, content_type, additional_req)
        return
    
    all_outputs = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    selected_model = st.session_state.get("selected_model", "groq")
    
    for i, objective_chunk in enumerate(objective_chunks):
        status_text.text(f"📖 Creating content for learning objective {i+1}/{len(objective_chunks)}...")
        progress_bar.progress((i) / len(objective_chunks))
        
        # Use Phi-3 specific prompts if Phi-3 is selected
        if selected_model == "phi3":
            prompt = build_phi3_tutor_chunk_prompt(topic, objective_chunk, student_level, content_type, additional_req, i+1, len(objective_chunks))
        else:
            prompt = build_groq_tutor_chunk_prompt(topic, objective_chunk, student_level, content_type, additional_req, i+1, len(objective_chunks))
        
        try:
            output = model_manager.generate(
                prompt,
                selected_model,
                user_type="tutor",
                student_level=student_level,
                content_type=content_type
            )
            
            if any(msg in output for msg in ["🚫", "📊", "❌", "[Error", "[RateLimit]", "[Quota]", "[Auth]", "[Empty]", "❌ Phi-3 Error:"]):
                st.error(f"❌ Failed to process objective {i+1}: {output}")
                return
            
            all_outputs.append(output)
            
        except Exception as e:
            st.error(f"❌ Failed to process objective {i+1}: {str(e)}")
            return
    
    # Update progress to complete
    progress_bar.progress(1.0)
    status_text.text("✅ All sections processed! Combining results...")
    
    # Combine all outputs
    final_output = combine_tutor_outputs(all_outputs, topic, student_level, content_type)
    
    # Generate PDF and update session state
    pdf_data = generate_pdf(
        final_output, 
        "tutor", 
        level=student_level,
        topic=topic,
        content_type=content_type,
        objectives=objectives
    )
    
    update_session_state(
        original_prompt=f"{content_type} for {topic} - {student_level} level",
        generated_output=final_output,
        feedback_given=False,
        regenerated=False,
        content_source="tutor",
        student_level=student_level,
        tutor_topic=topic,
        tutor_content_type=content_type,
        pdf_export_data=pdf_data,
        saved_to_history=False,
        current_history_id=None,
        generated_model=selected_model
    )
    
    status_text.text("✅ Content generation complete!")
    st.rerun()

def chunk_objectives(objectives, max_chunk_size=4000):
    """Split objectives into manageable chunks with increased size"""
    objective_items = re.split(r'[\n•\-]', objectives)
    objective_items = [item.strip() for item in objective_items if item.strip()]
    
    chunks = []
    current_chunk = ""
    
    for item in objective_items:
        if len(current_chunk) + len(item) < max_chunk_size:
            if current_chunk:
                current_chunk += "\n• " + item
            else:
                current_chunk = "• " + item
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = "• " + item
    
    if current_chunk:
        chunks.append(current_chunk)
    
    if len(chunks) > 5 and max_chunk_size < 6000:
        return chunk_objectives(objectives, max_chunk_size + 1000)
    
    return chunks

def build_phi3_tutor_chunk_prompt(topic, objective_chunk, student_level, content_type, additional_req, chunk_num, total_chunks):
    """Build Phi-3 specific prompt for a single tutor chunk"""
    prompt = f"""You are creating educational content. Write the actual content that teaches these concepts.

TOPIC: {topic}

CONCEPTS TO EXPLAIN:
{objective_chunk}

AUDIENCE: {student_level} students
FORMAT: {content_type}
"""
    if additional_req:
        prompt += f"\nSPECIFIC FOCUS: {additional_req}"
    
    prompt += f"""

CONTENT REQUIREMENTS:
- Write the actual educational material, not a lesson plan
- Explain concepts clearly with examples
- Use appropriate language for {student_level}
- Include definitions and key information
- Structure the content for learning

FORBIDDEN: Do not include timing, activities, assessments, or teaching instructions.
FORBIDDEN: Do not use phrases like "students will learn" or "this section will cover".

BEGIN CONTENT:

"""
    return prompt

def build_groq_tutor_chunk_prompt(topic, objective_chunk, student_level, content_type, additional_req, chunk_num, total_chunks):
    """Build Groq prompt for a single tutor chunk"""
    prompt = f"""Create educational content for the following:

TOPIC: {topic}

LEARNING OBJECTIVES:
{objective_chunk}

STUDENT LEVEL: {student_level}
CONTENT TYPE: {content_type}
"""
    if additional_req:
        prompt += f"\nADDITIONAL REQUIREMENTS: {additional_req}"
    
    prompt += f"""

Generate comprehensive educational content that directly teaches these concepts.
"""
    return prompt

def combine_tutor_outputs(outputs, topic, student_level, content_type):
    """Combine tutor chunk outputs into a cohesive document"""
    combined = f"# {content_type}: {topic}\n\n"
    combined += f"**Target Level:** {student_level}\n\n"
    
    for i, output in enumerate(outputs):
        # Clean up any instructional language
        clean_output = re.sub(r'(?:Here is|I will|This section|Students will|We will).*?(?=\n\n|\n#|\n##|$)', '', output, flags=re.IGNORECASE | re.DOTALL)
        section_title = f"## Part {i+1}\n\n"
        combined += section_title + clean_output.strip() + "\n\n---\n\n"
    
    return combined

def build_phi3_tutor_prompt(topic, objectives, student_level, content_type, additional_req):
    """Build Phi-3 specific prompt for tutor content generation"""
    
    # Define content type requirements
    content_requirements = {
        "Lesson Plan": {
            "description": "Create a structured lesson plan with timing, activities, and assessments",
            "requirements": [
                "Include learning objectives and outcomes",
                "Provide a timed lesson structure with activities",
                "Include teaching methods and student activities", 
                "Add assessment methods and homework if applicable",
                "Use appropriate pedagogical approaches"
            ],
            "forbidden": []
        },
        "Study Guide": {
            "description": "Create a comprehensive study guide for students",
            "requirements": [
                "Include key concepts and definitions",
                "Provide summaries and review questions",
                "Add practice problems or exercises",
                "Include study tips and strategies",
                "Structure for easy review and self-testing"
            ],
            "forbidden": [
                "Do not include timing or classroom management instructions"
            ]
        },
        "Lecture Notes": {
            "description": "Create detailed lecture notes for teaching",
            "requirements": [
                "Include comprehensive explanations",
                "Provide examples and case studies", 
                "Add key points and summaries",
                "Include relevant diagrams or frameworks if needed",
                "Structure for clear presentation delivery"
            ],
            "forbidden": [
                "Do not include student activities or assessments"
            ]
        },
        "Interactive Activity": {
            "description": "Create engaging interactive learning activities",
            "requirements": [
                "Design hands-on or group activities",
                "Include clear instructions for students",
                "Provide learning objectives for each activity",
                "Add discussion questions or prompts",
                "Include facilitation guidelines if needed"
            ],
            "forbidden": [
                "Do not include lengthy theoretical explanations"
            ]
        },
        "Comprehensive Explanation": {
            "description": "Create a thorough explanatory document",
            "requirements": [
                "Provide in-depth conceptual explanations",
                "Use analogies and real-world examples",
                "Include step-by-step breakdowns of complex ideas",
                "Add visual descriptions or mental models",
                "Structure from basic to advanced concepts"
            ],
            "forbidden": [
                "Do not include activities, assessments, or teaching instructions"
            ]
        }
    }
    
    # Get requirements for the specific content type
    content_spec = content_requirements.get(content_type, content_requirements["Comprehensive Explanation"])
    
    prompt = f"""You are creating educational content for {content_type.lower()}. Write the actual content.

TOPIC: {topic}

LEARNING GOALS:
{objectives}

AUDIENCE: {student_level} students
CONTENT TYPE: {content_type} - {content_spec['description']}
"""
    if additional_req:
        prompt += f"\nSPECIFIC FOCUS: {additional_req}"
    
    prompt += f"""

CONTENT REQUIREMENTS:
- Write the actual educational material
- Explain concepts clearly with examples appropriate for {student_level}
- Use appropriate language and terminology for the audience
- Structure the content logically for learning
"""
    
    # Add content-specific requirements
    for requirement in content_spec['requirements']:
        prompt += f"- {requirement}\n"
    
    # Add content-specific forbidden items
    if content_spec['forbidden']:
        prompt += "\nFORBIDDEN:\n"
        for forbidden in content_spec['forbidden']:
            prompt += f"- {forbidden}\n"
    else:
        # Default forbidden items for content types that need more flexibility
        prompt += "\nFORBIDDEN:\n- Do not use generic phrases like 'this section will cover'\n- Do not create content that is not directly educational\n"
    
    # Add universal forbidden items that apply to all content types
    universal_forbidden = [
        "Do not use phrases like 'students will learn' or 'this teaches'",
        "Do not refer to yourself as an AI or assistant",
        "Do not add meta-commentary about the content"
    ]
    
    for forbidden in universal_forbidden:
        prompt += f"- {forbidden}\n"
    
    prompt += f"""

BEGIN {content_type.upper()} CONTENT:

"""
    return prompt

def build_groq_tutor_prompt(topic, objectives, student_level, content_type, additional_req):
    """Build Groq prompt for tutor content generation"""
    
    content_descriptions = {
        "Lesson Plan": "structured lesson plan with timing, activities, and assessments",
        "Study Guide": "comprehensive study guide with key concepts and practice questions", 
        "Lecture Notes": "detailed lecture notes for teaching delivery",
        "Interactive Activity": "engaging interactive learning activities",
        "Comprehensive Explanation": "thorough explanatory document"
    }
    
    description = content_descriptions.get(content_type, "educational content")
    
    prompt = f"""Create {description} for teaching:

TOPIC: {topic}

LEARNING OBJECTIVES:
{objectives}

STUDENT LEVEL: {student_level}
CONTENT TYPE: {content_type}
"""
    if additional_req:
        prompt += f"\nADDITIONAL REQUIREMENTS: {additional_req}"
    
    prompt += f"""

Generate detailed {content_type.lower()} that achieves the learning objectives.
"""
    return prompt