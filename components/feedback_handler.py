import streamlit as st
from generator import GroqGenerator
from feedback import save_feedback
from simulate_adapt import adjust_prompt, get_adaptation_explanation
from components.export_handler import generate_pdf
from components.output_renderer import render_output
from db.helpers import save_feedback_to_db

def render_feedback_section():
    """Render the feedback section for 2-step process"""
    # Show adaptation explanation for regenerated content FIRST
    if (st.session_state.generated_output and 
        st.session_state.regenerated and 
        not st.session_state.feedback_given and
        st.session_state.get('show_adaptation_message', True)):
        
        adaptation_explanation = get_adaptation_explanation(
            st.session_state.feedback_complexity,
            st.session_state.feedback_clarity,
            st.session_state.feedback_depth,
            comments=st.session_state.feedback_comments
        )
        
        st.success("✅ Content adapted based on your feedback!")
        st.info(f"**🔄 Adaptations applied based on your feedback:**\n{adaptation_explanation}")
        
        # Mark that we've shown the message
        st.session_state.show_adaptation_message = False
    
    # Show feedback form for current content if no feedback given yet
    if st.session_state.generated_output and not st.session_state.feedback_given:
        render_feedback_form()
    
    # Save to history button
    if (st.session_state.generated_output and 
        not st.session_state.get('saved_to_history', False)):
        st.markdown("---")
        st.write("**💾 Save to History**")
        if st.button("📚 Save to My History", type="secondary"):
            from components.session_manager import save_current_to_history
            entry_id = save_current_to_history()
            if entry_id:
                st.session_state.saved_to_history = True
                st.success("✅ Content saved to history!")
                st.rerun()
    
    # Handle regeneration logic - ONLY for first generation
    if st.session_state.feedback_given and not st.session_state.regenerated:
        handle_first_generation_feedback()
        
def handle_first_generation_feedback():
    """Handle feedback for first generation content - show regenerate button only once"""
    if st.session_state.feedback_complexity == "Just right":
        st.balloons()
        st.success("🎉 Perfect! The content matched your needs perfectly.")
        # No regenerate button for "Just right"
    else:
        # Show regenerate button ONLY for first generation
        if st.button("🔄 Regenerate with Adjustments", type="secondary"):
            regenerate_content()
            
def save_feedback_data(clarity, depth, complexity, comments):
    """Save feedback to PostgreSQL DB - UPDATED for regenerated content"""
    try:
        # Ensure we have a current_history_id
        if not hasattr(st.session_state, 'current_history_id') or not st.session_state.current_history_id:
            # Try to save to history first if not already saved
            from components.session_manager import save_current_to_history
            entry_id = save_current_to_history()
            if not entry_id:
                st.error("❌ Cannot save feedback: Content not saved to history yet.")
                return
        
        # Check if this is feedback for regenerated content
        is_regenerated_feedback = st.session_state.get('regenerated', False)
        regeneration_count = st.session_state.get('regeneration_count', 0)
        regeneration_type = st.session_state.get('regeneration_type', None)
        
        print(f"🔧 DEBUG - Saving regenerated feedback:")
        print(f"  - is_regenerated_feedback: {is_regenerated_feedback}")
        print(f"  - regeneration_count: {regeneration_count}")
        print(f"  - regeneration_type: {regeneration_type}")
        
        feedback_data = {
            "user_id": st.session_state.user_id,
            "content_id": st.session_state.current_history_id,
            "clarity": clarity,
            "depth": depth,
            "complexity": complexity,
            "comments": comments,
            "is_regenerated_feedback": is_regenerated_feedback,
            "regeneration_count": regeneration_count,
            "regeneration_type": regeneration_type
        }

        success = save_feedback_to_db(feedback_data)

        if success:
            st.session_state.feedback_given = True
            st.session_state.feedback_clarity = clarity
            st.session_state.feedback_depth = depth
            st.session_state.feedback_complexity = complexity
            st.session_state.feedback_comments = comments
            st.success("✅ Feedback saved! This helps improve the system.")
        else:
            st.error("❌ Failed to save feedback. Please try again.")
    except Exception as e:
        st.error(f"❌ Error saving feedback: {str(e)}")

def render_feedback_form():
    """Render the feedback collection form"""
    st.markdown("---")
    st.subheader("💬 How Was This Content?")
    
    quality_example, placeholder = get_feedback_examples()
    
    with st.form("feedback_form"):
        # Feedback metrics
        clarity = st.slider("**Clarity** - How clear is the content?", 1, 5, 3,
                          help="1=Very confusing, 5=Extremely clear")
        depth = st.slider("**Depth** - How detailed is the content?", 1, 5, 3,
                        help="1=Too superficial, 5=Perfect depth")
        complexity = st.radio("**Appropriateness**:", 
                            ["Too simple", "Just right", "Too complex"],
                            help="Is the content appropriate for the target level?")
        
        # Detailed feedback
        st.write("**Specific suggestions (be detailed!):**")
        st.caption(quality_example)
        comments = st.text_area(
            "Your feedback:",
            placeholder=placeholder,
            height=120,
            help="Detailed feedback helps improve the system for everyone"
        )
        
        # Submit button
        if st.form_submit_button("📤 Submit Feedback", type="primary"):
            save_feedback_data(clarity, depth, complexity, comments)

def get_feedback_examples():
    """Get feedback examples based on user type"""
    if st.session_state.user_type == "student":
        quality_example = """For example:
• "The explanation of neural networks was clear, but I'd love more real-world examples"
• "The math notation was confusing - could you explain the steps more intuitively?"
• "The analogies really helped me understand! Maybe add a comparison to how the brain learns?"""
        placeholder = "What was confusing? What helped? What would make this even better for your learning?"
    else:
        quality_example = """For example:
• "The lesson structure is good, but could use more interactive activities"
• "The technical depth is appropriate, but consider adding assessment questions"
• "The examples are relevant - maybe include more diverse applications"""
        placeholder = "How could this be more effective for your teaching? What would help your students learn better?"
    
    return quality_example, placeholder

def handle_regeneration():
    """Handle content regeneration based on feedback"""
    if st.session_state.feedback_complexity == "Just right":
        st.balloons()
        st.success("🎉 Perfect! The content matched your needs perfectly.")
        st.session_state.regenerated = True
    else:
        if st.button("🔄 Regenerate with Adjustments", type="secondary"):
            regenerate_content()

def regenerate_content():
    """Regenerate content based on feedback - ONE TIME ONLY"""
    # Use a different approach - store the regeneration request and let the main flow handle it
    st.session_state.pending_regeneration = True
    st.session_state.regeneration_type = 'feedback_adjustment'
    st.rerun()

def handle_pending_regeneration():
    """Handle pending regeneration in the main flow"""
    if st.session_state.get('pending_regeneration'):
        print("🔄 DEBUG: handle_pending_regeneration triggered!")
        # Clear the flag first
        st.session_state.pending_regeneration = False
        
        with st.spinner("🔄 Adapting content based on your feedback..."):
            try:
                print("🔄 DEBUG: Handling pending regeneration...")
                
                # Track regeneration
                st.session_state.regeneration_count = st.session_state.get('regeneration_count', 0) + 1
                st.session_state.regenerated = True  # Mark as regenerated content
                st.session_state.regeneration_type = 'feedback_adjustment'  # Set the type
                
                print(f"🔄 DEBUG: Regeneration count: {st.session_state.regeneration_count}")
                
                # RESET FEEDBACK STATE for the new content
                st.session_state.feedback_given = False
                st.session_state.feedback_clarity = 3
                st.session_state.feedback_depth = 3
                st.session_state.feedback_complexity = "Just right"
                st.session_state.feedback_comments = ""
                st.session_state.saved_to_history = False
                
                # Adjust prompt based on feedback
                adjusted_prompt = adjust_prompt(
                    st.session_state.original_prompt,
                    complexity=st.session_state.feedback_complexity,
                    clarity=st.session_state.feedback_clarity,
                    depth=st.session_state.feedback_depth,
                    user_type=st.session_state.user_type,
                    student_level=st.session_state.student_level,
                    comments=st.session_state.feedback_comments
                )
                
                # Generate new content
                generator = GroqGenerator()
                new_output = generator.generate(adjusted_prompt)
                
                print(f"✅ DEBUG: New content generated, length: {len(new_output)}")
                
                # Generate PDF for the new content
                if st.session_state.user_type == "student":
                    pdf_data = generate_pdf(
                        new_output, 
                        "student", 
                        level=st.session_state.student_level
                    )
                else:
                    pdf_data = generate_pdf(
                        new_output, 
                        "tutor", 
                        level=st.session_state.student_level,
                        topic=st.session_state.tutor_topic,
                        content_type=st.session_state.tutor_content_type,
                        objectives=""
                    )
                
                # Update session state
                st.session_state.generated_output = new_output
                st.session_state.pdf_export_data = pdf_data
                
                print("✅ DEBUG: Regeneration complete, content should display now")
                
            except Exception as e:
                print(f"❌ DEBUG: Regeneration failed: {e}")
                st.error(f"❌ Regeneration failed: {str(e)}")