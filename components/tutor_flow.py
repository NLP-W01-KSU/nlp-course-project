# import streamlit as st
# from generator import GroqGenerator
# from components.export_handler import generate_pdf
# from components.session_manager import update_session_state

# def render_tutor_flow():
#     """Render the tutor content generation flow"""
#     st.header("👨‍🏫 Tutor Content Creator")
#     render_tutor_info()
    
#     topic, objectives, student_level, content_type, additional_req = get_tutor_inputs()
    
#     if topic and objectives and st.button("🚀 Create Teaching Content", type="primary"):
#         generate_tutor_content(topic, objectives, student_level, content_type, additional_req)

# def render_tutor_info():
#     """Render tutor flow information"""
#     st.info("""
#     **How this works:** 
#     Tell me what topic you want to teach, and I'll generate comprehensive educational content 
#     tailored to your students' level and learning objectives.
#     """)

# def get_tutor_inputs():
#     """Get all inputs from tutor"""
#     st.subheader("📖 Teaching Topic")
#     topic = st.text_area(
#         "What topic do you want to teach?",
#         placeholder="e.g., Neural Networks, Quantum Computing, Calculus Fundamentals, French Revolution",
#         help="Be specific about the topic or concept"
#     )
    
#     st.subheader("🎯 Learning Objectives")
#     objectives = st.text_area(
#         "What should students learn from this?",
#         placeholder="e.g., 'Understand backpropagation', 'Apply gradient descent', 'Explain the causes of WWI'",
#         help="List the key learning outcomes for students"
#     )
    
#     st.subheader("👥 Student Level")
#     student_level = st.selectbox(
#         "What level are your students?",
#         ["Elementary School", "Middle School", "High School", "Undergraduate", "Graduate", "Professional Development"],
#         help="Select the appropriate level for your students"
#     )
    
#     st.subheader("📝 Content Format")
#     content_type = st.selectbox(
#         "What type of content do you need?",
#         ["Lesson Plan", "Study Guide", "Lecture Notes", "Interactive Activity", "Comprehensive Explanation"],
#         help="Choose the format that best suits your teaching needs"
#     )
    
#     st.subheader("⚡ Additional Requirements (Optional)")
#     additional_req = st.text_area(
#         "Any specific requirements?",
#         placeholder="e.g., 'Include code examples', 'Use historical primary sources', 'Focus on practical applications'",
#         help="Specify any particular focus or requirements"
#     )
    
#     return topic, objectives, student_level, content_type, additional_req

# def generate_tutor_content(topic, objectives, student_level, content_type, additional_req):
#     """Generate content for tutor"""
#     with st.spinner("✍️ Generating educational content..."):
#         prompt = build_tutor_prompt(topic, objectives, student_level, content_type, additional_req)
        
#         try:
#             generator = GroqGenerator()
#             output = generator.generate(prompt)
            
#             # Generate PDF
#             pdf_data = generate_pdf(
#                 output, 
#                 "tutor", 
#                 level=student_level,
#                 topic=topic,
#                 content_type=content_type,
#                 objectives=objectives
#             )
            
#             # Update session state
#             update_session_state(
#                 original_prompt=prompt,
#                 generated_output=output,
#                 feedback_given=False,
#                 regenerated=False,
#                 content_source="tutor",
#                 student_level=student_level,
#                 tutor_topic=topic,
#                 tutor_content_type=content_type,
#                 pdf_export_data=pdf_data,
#                 saved_to_history=False
#             )
            
#             st.rerun()
            
#         except Exception as e:
#             st.error(f"❌ Generation failed: {str(e)}")

# def build_tutor_prompt(topic, objectives, student_level, content_type, additional_req):
#     """Build prompt for tutor content generation"""
#     prompt = f"""
# TOPIC TO TEACH: {topic}

# LEARNING OBJECTIVES:
# {objectives}

# STUDENT LEVEL: {student_level}
# CONTENT TYPE: {content_type}
# """
#     if additional_req:
#         prompt += f"\nADDITIONAL REQUIREMENTS: {additional_req}"
    
#     prompt += f"""
    
# Please create {content_type.lower()} for teaching this topic. The content should be:
# 1. Appropriate for {student_level} students
# 2. Aligned with the learning objectives
# 3. Engaging and pedagogically sound
# 4. Structured for effective learning
# 5. Practical and applicable
# """
#     return prompt


import streamlit as st
from generator import MultiGroqGenerator
from components.export_handler import generate_pdf
from components.session_manager import update_session_state

def render_tutor_flow():
    """Render the tutor content generation flow"""
    st.header("👨‍🏫 Tutor Content Creator")
    render_tutor_info()
    
    topic, objectives, student_level, content_type, additional_req = get_tutor_inputs()
    
    if topic and objectives and st.button("🚀 Create Teaching Content", type="primary", key="generate_tutor_content"):
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
        key="tutor_content_type_select"  # Different key from session state
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
    """Generate content for tutor"""
    with st.spinner("✍️ Generating educational content..."):
        prompt = build_tutor_prompt(topic, objectives, student_level, content_type, additional_req)
        
        try:
            generator = MultiGroqGenerator()
            output = generator.generate(prompt)
            
            # Check if it's an error message
            if any(msg in output for msg in ["🚫", "📊", "❌"]):
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
            
            # Update session state - use different variable names to avoid widget conflicts
            update_session_state(
                original_prompt=prompt,
                generated_output=output,
                feedback_given=False,
                regenerated=False,
                content_source="tutor",
                student_level=student_level,
                tutor_topic=topic,
                tutor_content_type=content_type,  # This is safe now - different from widget key
                pdf_export_data=pdf_data,
                saved_to_history=False
            )
            
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Generation failed: {str(e)}")

def build_tutor_prompt(topic, objectives, student_level, content_type, additional_req):
    """Build prompt for tutor content generation"""
    prompt = f"""
TOPIC TO TEACH: {topic}

LEARNING OBJECTIVES:
{objectives}

STUDENT LEVEL: {student_level}
CONTENT TYPE: {content_type}
"""
    if additional_req:
        prompt += f"\nADDITIONAL REQUIREMENTS: {additional_req}"
    
    prompt += f"""
    
Please create {content_type.lower()} for teaching this topic. The content should be:
1. Appropriate for {student_level} students
2. Aligned with the learning objectives
3. Engaging and pedagogically sound
4. Structured for effective learning
5. Practical and applicable
"""
    return prompt