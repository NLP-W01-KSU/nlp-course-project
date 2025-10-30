import streamlit as st
from db.helpers import get_research_stats
from generator import model_manager
from export_training_data_from_db import export_training_data_from_db

def render_header():
    st.title("🧠 TailorED - AI-Powered Educational Content Generator")

def render_sidebar():
    with st.sidebar:
        # === RESEARCH MODEL SELECTION ===
        st.subheader("🔬 Research Model Selection")
        
        # Initialize model choice if not exists
        if "selected_model" not in st.session_state:
            st.session_state.selected_model = "groq"
        
        # Check if we have existing content and need to show regeneration prompt
        if (st.session_state.get("generated_output") and 
            st.session_state.get("current_page") == "generator" and
            not st.session_state.get("showing_regeneration_prompt", False)):
            
            # Store current model before potential change
            previous_model = st.session_state.selected_model
            
            # Model selection with regeneration logic
            model_choice = st.radio(
                "Select AI Model:",
                options=[
                    "🧪 Phi-3 (Research Model)", 
                    "📊 Groq (Training Data)"
                ],
                index=0 if st.session_state.selected_model == "phi3" else 1,
                key="research_model_selection"
            )
            
            # Determine new model selection
            new_model = "phi3" if model_choice == "🧪 Phi-3 (Research Model)" else "groq"
            
            # If model changed and we have content, show regeneration prompt
            if new_model != previous_model:
                st.session_state.pending_model_switch = new_model
                st.session_state.previous_model = previous_model
                st.session_state.showing_regeneration_prompt = True
                st.rerun()
                
        else:
            # Normal model selection (no content or prompt already shown)
            model_choice = st.radio(
                "Select AI Model:",
                options=[
                    "🧪 Phi-3 (Research Model)", 
                    "📊 Groq (Training Data)"
                ],
                index=0 if st.session_state.selected_model == "phi3" else 1,
                key="research_model_selection"
            )
            
            # Update model selection
            new_model = "phi3" if model_choice == "🧪 Phi-3 (Research Model)" else "groq"
            if new_model != st.session_state.selected_model:
                st.session_state.selected_model = new_model
                if not st.session_state.get("generated_output"):
                    st.success(f"✅ Switched to {new_model.upper()} model")
        
        # Show current model status
        current_model = st.session_state.selected_model
        if current_model == "phi3":
            st.info("🧪 **Testing Phi-3** - Research model being evaluated")
        else:
            st.success("📊 **Generating Training Data** - Groq outputs will train Phi-3")
        
        # Render regeneration prompt if needed
        if st.session_state.get("showing_regeneration_prompt", False):
            render_regeneration_prompt()
        
        # Research context
        st.markdown("---")
        st.markdown("### 🎯 Research Mission")
        st.markdown("""
        We're **fine-tuning Phi-3 Mini** using Groq's high-quality outputs.
        
        **Your Role:** Compare both models to help improve Phi-3!
        - Use **Groq** to create training examples
        - Use **Phi-3** to test research progress  
        - Switch models to compare outputs on the same content
        """)
        
        st.markdown("---")
        
        st.header("🎓 Research Progress")
        st.write("**Your feedback trains better educational AI**")

        try:
            stats = get_research_stats()
            render_progress_metrics(stats)
            render_quality_indicators(stats)
            render_research_status(stats)
            render_service_status()
        except Exception as e:
            st.error(f"Sidebar failed: {e}")
            render_default_sidebar()

def render_regeneration_prompt():
    """Show prompt to regenerate content with new model"""
    st.markdown("---")
    st.warning("🔄 **Model Changed!**")
    
    previous_model = st.session_state.previous_model
    new_model = st.session_state.pending_model_switch
    
    st.write(f"You switched from **{previous_model.upper()}** to **{new_model.upper()}**.")
    st.write("Would you like to regenerate the same content with the new model?")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("✅ Yes, Regenerate", use_container_width=True, key="confirm_regenerate"):
            # Trigger regeneration with new model
            st.session_state.selected_model = new_model
            st.session_state.regenerate_with_new_model = True
            st.session_state.showing_regeneration_prompt = False
            st.session_state.pending_model_switch = None
            st.session_state.previous_model = None
            st.rerun()
    
    with col2:
        if st.button("❌ No, Keep Current", use_container_width=True, key="keep_current"):
            # Revert to previous model and keep current content
            st.session_state.selected_model = st.session_state.previous_model
            st.session_state.showing_regeneration_prompt = False
            st.session_state.pending_model_switch = None
            st.session_state.previous_model = None
            st.rerun()
    
    with col3:
        if st.button("🏠 Go to Home", use_container_width=True, key="go_home"):
            # Clear content and go to home
            from components.session_manager import clear_session
            clear_session()
            st.session_state.showing_regeneration_prompt = False
            st.session_state.pending_model_switch = None
            st.session_state.previous_model = None
            st.rerun()

def render_progress_metrics(stats):
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Feedback", stats.get("total_feedback", 0))
    
    with col2:
        st.metric("Content Generated", stats.get("total_content", 0))

    if stats.get("total_feedback", 0) > 0:
        render_progress_bar(stats)

def render_progress_bar(stats):
    """Render progress bar towards research goal"""
    st.subheader("📈 Our Progress")
    target_feedback = 100
    total_feedback = stats.get("total_feedback", 0)
    progress_percent = min((total_feedback / target_feedback) * 100, 100)
    st.progress(progress_percent / 100)
    st.caption(f"Goal: 100 feedback points • {total_feedback}/100")
    
    if total_feedback >= target_feedback:
        st.balloons()
        st.success("🎉 Amazing! We've reached our research goal!")

def render_quality_indicators(stats):
    st.subheader("✨ Model Quality Comparison")
    
    # Safely get model scores with fallbacks
    groq_scores = stats.get("groq_scores", {})
    phi3_scores = stats.get("phi3_scores", {})
    
    groq_clarity = groq_scores.get("clarity", 0)
    groq_depth = groq_scores.get("depth", 0)
    phi3_clarity = phi3_scores.get("clarity", 0)
    phi3_depth = phi3_scores.get("depth", 0)
    
    # Groq metrics
    st.markdown("**📊 Groq (Training Data)**")
    col1, col2 = st.columns(2)
    with col1:
        # Show delta if we have both scores
        delta_clarity = None
        if groq_clarity > 0 and phi3_clarity > 0:
            delta_clarity = f"+{groq_clarity - phi3_clarity:.1f}"
        st.metric("Avg Clarity", f"{groq_clarity}/5", delta=delta_clarity)
    with col2:
        delta_depth = None
        if groq_depth > 0 and phi3_depth > 0:
            delta_depth = f"+{groq_depth - phi3_depth:.1f}"
        st.metric("Avg Depth", f"{groq_depth}/5", delta=delta_depth)
    
    # Phi-3 metrics
    st.markdown("**🧪 Phi-3 (Research Model)**")
    col3, col4 = st.columns(2)
    with col3:
        delta_clarity_phi3 = None
        if phi3_clarity > 0 and groq_clarity > 0:
            delta_clarity_phi3 = f"{phi3_clarity - groq_clarity:.1f}"
        st.metric("Avg Clarity", f"{phi3_clarity}/5", delta=delta_clarity_phi3)
    with col4:
        delta_depth_phi3 = None
        if phi3_depth > 0 and groq_depth > 0:
            delta_depth_phi3 = f"{phi3_depth - groq_depth:.1f}"
        st.metric("Avg Depth", f"{phi3_depth}/5", delta=delta_depth_phi3)
    
    # Show quality gap analysis
    if groq_clarity > 0 and phi3_clarity > 0:
        clarity_gap = groq_clarity - phi3_clarity
        depth_gap = groq_depth - phi3_depth
        
        if clarity_gap > 0 or depth_gap > 0:
            st.caption(f"🔍 Quality gap: Clarity +{clarity_gap:.1f}, Depth +{depth_gap:.1f}")
        elif clarity_gap < 0 or depth_gap < 0:
            st.caption(f"🎉 Phi-3 leads: Clarity {abs(clarity_gap):.1f}, Depth {abs(depth_gap):.1f}")
        else:
            st.caption("⚖️ Models performing equally")

def render_research_status(stats):
    st.subheader("🔬 Research Progress")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Groq Data", stats.get("groq_feedback_count", 0))
        st.caption("For fine-tuning")
    
    with col2:
        st.metric("High-Quality Groq", stats.get("high_quality_groq", 0))
        st.caption("Fine-tuning ready")
    
    with col3:
        st.metric("Phi-3 Data", stats.get("phi3_feedback_count", 0))
        st.caption("For comparison")
    
    # Fine-tuning readiness
    target_examples = 50
    high_quality_groq = stats.get("high_quality_groq", 0)
    
    if high_quality_groq >= target_examples:
        st.success("🎉 Ready to fine-tune Phi-3 with Groq data!")
        if st.button("🚀 Export Fine-tuning Data", use_container_width=True, type="primary"):
            from export_training_data_from_db import export_training_data_from_db
            if export_training_data_from_db():
                st.success("✅ Groq data exported for Phi-3 fine-tuning!")
            else:
                st.error("Export failed")
    else:
        needed = target_examples - high_quality_groq
        st.info(f"📊 Need {needed} more high-quality Groq examples")
        progress = high_quality_groq / target_examples if target_examples > 0 else 0
        st.progress(progress)
        st.caption(f"Progress: {high_quality_groq}/{target_examples} examples")

def render_service_status():
    st.markdown("---")
    st.subheader("🛜 Platform Status")
    
    try:
        status = model_manager.get_service_status()
        
        # Create status columns
        col1, col2 = st.columns(2)
        
        with col1:
            # Phi-3 Status
            phi3_status = status["phi3"]
            if phi3_status["server_healthy"] and phi3_status["model_available"]:
                st.success("🧪 Phi-3 Mini")
                st.caption("Research Model • Ready")
            elif phi3_status["server_healthy"]:
                st.warning("🧪 Phi-3 Mini") 
                st.caption("Research Model • Needs Setup")
            else:
                st.error("🧪 Phi-3 Mini")
                st.caption("Research Model • Offline")
        
        with col2:
            # Groq Status
            groq_status = status["groq"]
            healthy_count = groq_status['healthy_providers']
            total_providers = groq_status['total_providers']
            
            if healthy_count == total_providers:
                st.success("📊 Groq API")
                st.caption("Training Data • Fully Operational")
            elif healthy_count > 0:
                st.warning("📊 Groq API")
                st.caption(f"Training Data • {healthy_count}/{total_providers} providers")
            else:
                st.error("📊 Groq API")
                st.caption("Training Data • Offline")
        
        # Quick health indicator
        if status["phi3"]["server_healthy"] and groq_status['healthy_providers'] > 0:
            st.caption("💡 All systems operational - research ready!")
        else:
            st.caption("⚠️ Some services limited - research may be affected")
                
    except Exception as e:
        st.error("❌ Status check failed")
        st.caption("Research platform may have issues")

def render_default_sidebar():
    st.info("🌟 Start generating content to contribute to our research!")
    st.caption("Your feedback on Groq content will train Phi-3 to become a better educational AI")
    if st.button("🔄 Refresh Progress", use_container_width=True, key="refresh_progress"):
        st.rerun()
