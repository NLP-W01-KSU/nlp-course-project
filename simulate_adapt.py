def adjust_prompt(original_prompt, complexity=None, clarity=None, depth=None, user_type=None, student_level=None, comments=""):
    """
    Enhanced prompt adjustment based on user feedback
    """
    
    adjustments = []
    new_prompt = original_prompt
    
    # Priority 1: Complexity adjustments (most impactful)
    if complexity == "Too complex":
        adjustments.append("simplified language and added analogies")
        if user_type == "student":
            new_prompt = f"Explain this in simpler, more beginner-friendly terms with practical examples and everyday analogies: {original_prompt}"
        else:
            new_prompt = f"Create a more accessible version suitable for {student_level} students with clear examples: {original_prompt}"
            
    elif complexity == "Too simple":
        adjustments.append("added technical depth and advanced concepts")
        new_prompt = f"Expand this with more technical details, deeper insights, and advanced applications while maintaining clarity: {original_prompt}"

    # Priority 2: Use specific comments if available (most targeted)
    elif comments and len(comments.strip()) > 10:
        # Extract key requests from user comments
        user_requests = extract_requests_from_comments(comments)
        if user_requests:
            adjustments.append(f"addressed: {', '.join(user_requests)}")
            new_prompt = f"{original_prompt}. Specifically: {', '.join(user_requests)}"
    
    # Priority 3: Clarity adjustments
    elif clarity and clarity <= 2:
        adjustments.append("improved structure and clarity")
        new_prompt = f"Make this extremely clear and well-structured with step-by-step explanation and better organization: {original_prompt}"
    
    # Priority 4: Depth adjustments  
    elif depth and depth <= 2:
        adjustments.append("added foundational content")
        new_prompt = f"Provide more basic foundation, introductory content, and build up gradually: {original_prompt}"
    
    elif depth and depth >= 4:
        adjustments.append("included advanced insights")
        new_prompt = f"Include more advanced insights, real-world applications, case studies, and deeper analysis: {original_prompt}"
    
    # Priority 5: General improvement fallback
    elif complexity or clarity or depth:
        adjustments.append("general improvements based on feedback")
        new_prompt = f"Improve this content to be more effective for learning: {original_prompt}"
    
    # Always add learning level context
    if student_level and student_level != "Unknown":
        if "suitable for" not in new_prompt and f"for {student_level}" not in new_prompt:
            new_prompt = f"{new_prompt} - Tailor specifically for {student_level} level understanding"
    
    print(f"🔄 Adaptation applied: {adjustments}")
    return new_prompt

def extract_requests_from_comments(comments):
    """Extract specific requests from user comments"""
    requests = []
    comment_lower = comments.lower()
    
    # Look for specific requests in comments
    if any(word in comment_lower for word in ['example', 'examples']):
        requests.append("more practical examples")
    
    if any(word in comment_lower for word in ['confusing', 'unclear', 'hard to understand']):
        requests.append("clearer explanations")
    
    if any(word in comment_lower for word in ['analogy', 'metaphor', 'comparison']):
        requests.append("better analogies")
    
    if any(word in comment_lower for word in ['step by step', 'step-by-step', 'break down']):
        requests.append("step-by-step breakdown")
    
    if any(word in comment_lower for word in ['real world', 'real-world', 'practical']):
        requests.append("real-world applications")
    
    if any(word in comment_lower for word in ['visual', 'diagram', 'chart']):
        requests.append("visual explanations")
    
    return requests

def get_adaptation_explanation(complexity, clarity, depth, comments=""):
    """Generate a user-friendly explanation of what adaptations were made"""
    explanations = []
    
    # Use comments for most specific explanations
    if comments and len(comments.strip()) > 10:
        user_requests = extract_requests_from_comments(comments)
        if user_requests:
            explanations.append(f"• Addressed your specific requests: {', '.join(user_requests)}")
    
    # Fall back to rating-based explanations
    if not explanations:
        if complexity == "Too complex":
            explanations.append("• Simplified language and added everyday analogies")
        elif complexity == "Too simple":
            explanations.append("• Added more technical depth and advanced concepts")
        
        if clarity and clarity <= 2:
            explanations.append("• Improved structure with step-by-step explanations")
        elif clarity and clarity >= 4:
            explanations.append("• Maintained the clear structure you liked")
        
        if depth and depth <= 2:
            explanations.append("• Added more foundational content and basics")
        elif depth and depth >= 4:
            explanations.append("• Included advanced insights and applications")
    
    # Final fallback
    if not explanations:
        if comments:
            explanations.append("• Incorporated your detailed feedback")
        else:
            explanations.append("• Made general improvements based on your ratings")
    
    return "\n".join(explanations)