import streamlit as st
import re

def render_output_section():
    """Render the generated output section - FIXED for regenerated content"""
    if st.session_state.generated_output:
        # ALWAYS render the current content, regardless of regeneration status
        render_output(st.session_state.generated_output)

def render_output(output):
    """Render output with LaTeX support"""
    st.markdown("---")
    st.markdown("### 📘 Generated Content")

    # Extract and render LaTeX
    output = render_latex_expressions(output)
    
    # Render remaining text
    st.markdown(output.strip(), unsafe_allow_html=True)

def render_latex_expressions(output):
    """Extract and render LaTeX expressions from output"""
    latex_patterns = re.findall(r"\$\$(.+?)\$\$|\\\[(.+?)\\\]|\\\((.+?)\\\)", output, re.DOTALL)

    for groups in latex_patterns:
        latex_expr = next(filter(None, groups))
        try:
            st.latex(latex_expr.strip())
        except:
            st.markdown(f"`{latex_expr}`")

        # Clean LaTeX from output for text display
        for g in groups:
            if g:
                output = output.replace(f"$${g}$$", "").replace(f"\\[{g}\\]", "").replace(f"\\({g}\\)", "")
    
    return output