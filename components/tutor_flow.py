import streamlit as st
import re
from generator import model_manager
from components.export_handler import generate_pdf
from components.session_manager import update_session_state
from components.file_processor import process_uploaded_file  

def render_tutor_flow():
    """Render the tutor content generation flow"""
    st.header("👨‍🏫 Tutor Content Creator")
    render_tutor_info()
    
    # Check if we need to regenerate with a different model
    if st.session_state.get("regenerate_with_new_model") and st.session_state.get("original_topic"):
        handle_tutor_regeneration()
        return
    
    # GET INPUT METHOD FIRST
    input_method = get_tutor_input_method()
    
    if input_method == "Upload Document":
        topic, objectives, student_level, content_type, additional_req, document_text, filename = get_tutor_inputs_from_document()
        if topic and document_text and st.button("🚀 Generate from Document", type="primary", key="generate_from_document"):
            generate_tutor_content_from_document(topic, objectives, student_level, content_type, additional_req, document_text, filename)
    else:
        topic, objectives, student_level, content_type, additional_req = get_tutor_inputs_manual()
        if topic and objectives and st.button("🚀 Create Teaching Content", type="primary", key="generate_tutor_content"):
            generate_tutor_content(topic, objectives, student_level, content_type, additional_req)

def get_tutor_input_method():
    """Let tutor choose between manual input or document upload"""
    st.subheader("📥 Input Method")
    return st.radio(
        "How would you like to provide the content?",
        ["Describe Topic & Objectives", "Upload Document"],
        help="Choose to either describe what you need or upload existing materials to transform"
    )

def get_tutor_inputs_from_document():
    """Get inputs from tutor when uploading a document"""
    st.subheader("📄 Upload Your Document")
    
    uploaded_file = st.file_uploader(
        "Upload your educational document", 
        type=["pdf", "pptx", "docx", "txt"],
        help="Upload lesson plans, curriculum materials, textbook chapters, or any educational content"
    )
    
    document_text = ""
    filename = "content.pdf"
    
    if uploaded_file:
        with st.spinner("📖 Reading your document..."):
            document_text, error = process_uploaded_file(uploaded_file)
        if error:
            st.error(f"❌ {error}")
        else:
            st.success("✅ Document processed successfully!")
            filename = uploaded_file.name
            
            # Show document preview
            with st.expander("📋 Document Preview", expanded=False):
                st.text_area("Extracted Text", document_text[:1000] + "..." if len(document_text) > 1000 else document_text, height=200, key="doc_preview")
    
    st.subheader("🎯 Transformation Instructions")
    
    topic = st.text_input(
        "What topic is this document about?",
        placeholder="e.g., Neural Networks, French Revolution, Calculus Basics",
        help="Briefly describe the main topic of the document"
    )
    
    content_type = st.selectbox(
        "What would you like me to create from this document?",
        ["Lecture Notes", "Study Guide", "Interactive Activity", "Lesson Plan", "Comprehensive Explanation", "Assessment Questions"],
        help="Choose the format you want me to generate based on your document"
    )
    
    student_level = st.selectbox(
        "What level should the content be adapted for?",
        ["Elementary School", "Middle School", "High School", "Undergraduate", "Graduate", "Professional Development"],
        help="Select the target student level for the generated content"
    )
    
    additional_req = st.text_area(
        "Any specific transformation requirements?",
        placeholder="e.g., 'Make it more interactive', 'Simplify the language', 'Add real-world examples', 'Focus on key concepts'",
        help="Specify how you want the content transformed"
    )
    
    # For document-based generation, objectives are optional since they can be extracted
    objectives = st.text_area(
        "Learning Objectives (Optional)",
        placeholder="e.g., 'Students should understand X, apply Y, analyze Z'",
        help="Optional: Specify what students should learn. If empty, I'll infer from the document."
    )
    
    return topic, objectives, student_level, content_type, additional_req, document_text, filename

def get_tutor_inputs_manual():
    """Get all inputs from tutor (original manual method)"""
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

def generate_tutor_content_from_document(topic, objectives, student_level, content_type, additional_req, document_text, filename):
    """Generate content for tutor based on uploaded document"""
    # STORE ORIGINAL INPUTS FOR REGENERATION
    st.session_state.original_topic = topic
    st.session_state.original_objectives = objectives
    st.session_state.original_additional_req = additional_req
    st.session_state.original_document_text = document_text
    st.session_state.original_filename = filename
    
    with st.spinner("📝 Transforming your document into new content..."):
        selected_model = st.session_state.get("selected_model", "groq")
        
        # Build document-based prompt
        if selected_model == "phi3":
            prompt = build_phi3_document_prompt(topic, objectives, student_level, content_type, additional_req, document_text)
        else:
            prompt = build_groq_document_prompt(topic, objectives, student_level, content_type, additional_req, document_text)
        
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
                content_type=f"{content_type} from Document",
                objectives=objectives or "Derived from uploaded document"
            )
            
            # Update session state
            update_session_state(
                original_prompt=prompt,
                generated_output=output,
                feedback_given=False,
                regenerated=False,
                content_source="tutor_document",
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

def build_phi3_document_prompt(topic, objectives, student_level, content_type, additional_req, document_text):
    """Build Phi-3 prompt for document-based content generation"""
    
    content_descriptions = {
        "Lecture Notes": "detailed lecture notes suitable for classroom teaching",
        "Study Guide": "comprehensive study guide for student self-study",
        "Interactive Activity": "engaging interactive learning activities for students",
        "Lesson Plan": "structured lesson plan with timing and activities", 
        "Comprehensive Explanation": "thorough explanatory document",
        "Assessment Questions": "quiz questions, exercises, or assessment materials"
    }
    
    description = content_descriptions.get(content_type, "educational content")
    
    prompt = f"""Transform the provided educational document into {description}.

ORIGINAL DOCUMENT CONTENT:
{document_text}

TOPIC: {topic}
"""
    if objectives:
        prompt += f"\nLEARNING OBJECTIVES: {objectives}"
    
    prompt += f"""
TARGET AUDIENCE: {student_level} students
OUTPUT FORMAT: {content_type}
"""
    if additional_req:
        prompt += f"\nSPECIFIC REQUIREMENTS: {additional_req}"
    
    prompt += f"""

TRANSFORMATION INSTRUCTIONS:
- Create {content_type.lower()} based on the original document content
- Adapt the material for {student_level} students
- Maintain the core educational concepts but reformat for the new purpose
- Use appropriate language and examples for the target level
- Structure the content effectively for {content_type.lower()}

FORBIDDEN:
- Do not simply copy the original content
- Do not use phrases like "based on the document" or "the original content says"
- Do not refer to yourself as an AI or assistant
- Do not include meta-commentary about the transformation process

BEGIN {content_type.upper()}:

"""
    return prompt

def build_groq_document_prompt(topic, objectives, student_level, content_type, additional_req, document_text):
    """Build Groq prompt for document-based content generation"""
    
    prompt = f"""Create {content_type.lower()} based on the following document:

DOCUMENT CONTENT:
{document_text}

TOPIC: {topic}
"""
    if objectives:
        prompt += f"\nLEARNING OBJECTIVES: {objectives}"
    
    prompt += f"""
STUDENT LEVEL: {student_level}
CONTENT TYPE: {content_type}
"""
    if additional_req:
        prompt += f"\nADDITIONAL REQUIREMENTS: {additional_req}"
    
    prompt += f"""

Transform the document content into effective {content_type.lower()} suitable for {student_level} students.
"""
    return prompt

def handle_tutor_regeneration():
    """Handle tutor content regeneration with new model"""
    st.header("👨‍🏫 Tutor Content Creator")
    render_tutor_info()
    
    # Show we're regenerating
    st.info("🔄 Regenerating your content with the new model...")
    
    # Check if this was document-based content
    if st.session_state.get("content_source") == "tutor_document" and st.session_state.get("original_document_text"):
        # Document-based regeneration
        topic = st.session_state.original_topic
        objectives = st.session_state.original_objectives  
        student_level = st.session_state.student_level
        content_type = st.session_state.tutor_content_type
        additional_req = st.session_state.get("original_additional_req", "")
        document_text = st.session_state.original_document_text
        filename = st.session_state.get("original_filename", "content.pdf")
        
        # Show original inputs for context
        with st.expander("📋 Original Inputs (Read-only)", expanded=True):
            st.write(f"**Source Document:** {filename}")
            st.write(f"**Topic:** {topic}")
            st.write(f"**Student Level:** {student_level}")
            st.write(f"**Content Type:** {content_type}")
            if objectives:
                st.write(f"**Learning Objectives:** {objectives}")
            if additional_req:
                st.write(f"**Transformation Requirements:** {additional_req}")
        
        # Regenerate from document
        generate_tutor_content_from_document(topic, objectives, student_level, content_type, additional_req, document_text, filename)
    else:
        # Manual input regeneration (existing code)
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
    - **Describe Topic & Objectives**: Tell me what you want to teach, and I'll generate educational content from scratch
    - **Upload Document**: Upload existing materials (lesson plans, textbooks, etc.) and I'll transform them into new formats like lecture notes, study guides, or interactive activities
    
    **Perfect for**: Converting lesson plans to lecture notes, textbook chapters to study guides, curriculum materials to interactive activities
    """)

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
    try:
        objective_chunks = chunk_objectives(objectives, max_chunk_size=4000)
        
        if not objective_chunks:
            st.info("🔄 Using single processing method for objectives...")
            generate_single_large_tutor_content(topic, objectives, student_level, content_type, additional_req)
            return
        
        st.info(f"📊 Objectives split into {len(objective_chunks)} sections for processing...")
        
        all_outputs = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        selected_model = st.session_state.get("selected_model", "groq")
        
        for i, objective_chunk in enumerate(objective_chunks):
            if not objective_chunk or len(objective_chunk.strip()) == 0:
                continue
                
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
                    # Continue with other chunks instead of stopping completely
                    all_outputs.append(f"[Objective {i+1} processing failed: {output}]")
                    continue
                
                all_outputs.append(output)
                
            except Exception as e:
                st.error(f"❌ Failed to process objective {i+1}: {str(e)}")
                # Continue with other chunks instead of stopping completely
                all_outputs.append(f"[Objective {i+1} processing failed: {str(e)}]")
                continue
        
        # Check if we got any successful outputs
        successful_outputs = [output for output in all_outputs if not output.startswith("[Objective")]
        if not successful_outputs:
            st.error("❌ All objective sections failed to process. Please try again with different content.")
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
        
    except Exception as e:
        st.error(f"❌ Chunked tutor processing failed: {str(e)}")
        # Fallback to single large content processing
        st.info("🔄 Trying alternative processing method...")
        generate_single_large_tutor_content(topic, objectives, student_level, content_type, additional_req)

def chunk_objectives(objectives, max_chunk_size=4000):
    """Split objectives into manageable chunks with robust error handling"""
    if not objectives or len(objectives.strip()) == 0:
        return []
    
    # If objectives are already small enough, return as single chunk
    if len(objectives) <= max_chunk_size:
        return [objectives.strip()]
    
    # Multiple splitting strategies
    objective_items = []
    
    # Try splitting by common delimiters
    for delimiter in [r'\n', r'•', r'-', r'\*', r';']:
        items = re.split(delimiter, objectives)
        items = [item.strip() for item in items if item.strip()]
        if len(items) > 1:
            objective_items = items
            break
    
    # If no delimiters found, split by sentences
    if not objective_items:
        sentences = re.split(r'[.!?]+', objectives)
        objective_items = [s.strip() for s in sentences if s.strip()]
    
    # If still no items, use the original text
    if not objective_items:
        objective_items = [objectives]
    
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
    
    # Final validation
    validated_chunks = []
    for chunk in chunks:
        if len(chunk) > max_chunk_size * 1.2:  # Allow 20% overflow
            # Emergency split by fixed size
            for i in range(0, len(chunk), max_chunk_size):
                sub_chunk = chunk[i:i + max_chunk_size]
                if sub_chunk.strip():
                    validated_chunks.append(sub_chunk.strip())
        else:
            validated_chunks.append(chunk)
    
    return validated_chunks

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
    
    successful_parts = 0
    for i, output in enumerate(outputs):
        # Skip failed sections
        if output.startswith("[Objective"):
            combined += f"## Part {i+1} - Processing Failed\n\n*This section could not be processed due to technical issues.*\n\n---\n\n"
            continue
            
        # Clean up any instructional language
        clean_output = re.sub(r'(?:Here is|I will|This section|Students will|We will).*?(?=\n\n|\n#|\n##|$)', '', output, flags=re.IGNORECASE | re.DOTALL)
        if clean_output.strip():
            section_title = f"## Part {i+1}\n\n"
            combined += section_title + clean_output.strip() + "\n\n---\n\n"
            successful_parts += 1
    
    if successful_parts == 0:
        return "❌ All objective sections failed to process. Please try again with different content."
    
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