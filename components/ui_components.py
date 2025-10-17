import streamlit as st
from feedback import get_research_progress, export_training_data
from generator import MultiGroqGenerator

def render_header():
    """Render the main header"""
    st.title("🧠 EduGen - AI-Powered Educational Content Generator")

def render_sidebar():
    """Render the research progress sidebar"""
    with st.sidebar:
        st.header("🎓 Help Our Research!")
        st.write("**We're training AI to create better educational content for everyone**")
        
        try:
            progress = get_research_progress()
            render_progress_metrics(progress)
            render_quality_indicators(progress)
            render_research_status(progress)
            render_user_diversity(progress)
            
            # Add service status
            render_service_status()
            
        except Exception as e:
            render_default_sidebar()

def render_progress_metrics(progress):
    """Render progress metrics in sidebar"""
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Community Contributions", progress["total_feedback"])
    with col2:
        st.metric("High-Quality Examples", progress["high_quality_examples"])
    
    # Progress bar
    if progress["total_feedback"] > 0:
        render_progress_bar(progress)

def render_progress_bar(progress):
    """Render progress bar towards research goal"""
    st.subheader("📈 Our Progress")
    target_feedback = 100
    progress_percent = min((progress["total_feedback"] / target_feedback) * 100, 100)
    st.progress(progress_percent / 100)
    st.caption(f"Goal: 100 feedback points • {progress['total_feedback']}/100")
    
    if progress["total_feedback"] >= target_feedback:
        st.balloons()
        st.success("🎉 Amazing! We've reached our research goal!")

def render_quality_indicators(progress):
    """Render quality indicators in sidebar"""
    st.subheader("✨ Content Quality")
    col3, col4 = st.columns(2)
    with col3:
        clarity = progress.get("average_quality", {}).get("clarity", 0)
        st.metric("Avg Clarity", f"{clarity}/5")
    with col4:
        depth = progress.get("average_quality", {}).get("depth", 0)
        st.metric("Avg Depth", f"{depth}/5")

def render_research_status(progress):
    """Render research status and export button"""
    st.subheader("🔬 Research Status")
    high_quality_examples = progress.get("high_quality_examples", 0)
    
    if high_quality_examples >= 10:
        st.success("✅ Ready for model training!")
        if st.button("🚀 Export Training Data", use_container_width=True, type="primary", key="export_training_data"):
            if export_training_data():
                st.success("Data exported! Thank you! 🎉")
            else:
                st.error("Export failed - please try again")
    else:
        examples_needed = 10 - high_quality_examples
        st.info(f"🔍 {examples_needed} more high-quality examples needed")

def render_user_diversity(progress):
    """Render user diversity breakdown"""
    user_breakdown = progress.get("user_breakdown", {})
    if user_breakdown:
        st.subheader("👥 Our Community")
        for user_type, count in user_breakdown.items():
            st.write(f"• {user_type.title()}: {count}")

def render_service_status():
    """Render AI service status"""
    st.markdown("---")
    st.subheader("🛜 Service Status")
    
    try:
        generator = MultiGroqGenerator()
        status = generator.get_service_status()
        
        st.write(f"**AI Providers:** {status['healthy_providers']}/{status['total_providers']} available")
        
        for provider in status['providers']:
            st.write(f"{provider['status']} **{provider['name']}**")
            if provider['failures'] > 0:
                st.caption(f"Recent issues: {provider['failures']}")
        
        st.caption(f"**Models:** {', '.join(status['models'])}")
        
    except Exception as e:
        st.warning("⚠️ Unable to check service status")

def render_default_sidebar():
    """Render default sidebar when no progress data"""
    st.info("🌟 Start giving feedback to see our community progress!")
    st.caption("Your feedback directly helps improve AI education for everyone")
    if st.button("🔄 Refresh Progress", use_container_width=True, key="refresh_progress"):
        st.rerun()