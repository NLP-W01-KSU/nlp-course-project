def adjust_prompt(original_prompt, complexity=None, clarity=None, depth=None, user_type=None, student_level=None):
    """
    Enhanced prompt adjustment based on user feedback
    Simulates adaptive behavior for the demo
    """
    
    adjustments = []
    new_prompt = original_prompt
    
    # Complexity adjustments
    if complexity == "Too complex":
        adjustments.append("simplify the language and use more analogies")
        if user_type == "student":
            new_prompt = f"Explain this in simpler, more beginner-friendly terms with practical examples: {original_prompt}"
        else:
            new_prompt = f"Create a more accessible version suitable for {student_level} students: {original_prompt}"
            
    elif complexity == "Too simple":
        adjustments.append("add more technical depth and advanced concepts")
        new_prompt = f"Expand this with more technical details, deeper insights, and advanced applications: {original_prompt}"

    # Clarity adjustments
    if clarity and clarity <= 2:
        adjustments.append("improve structure and clarity")
        if "Explain this in simpler terms" not in new_prompt and "Create a more accessible version" not in new_prompt:
            new_prompt = f"Make this extremely clear and well-structured with step-by-step explanation: {original_prompt}"
    
    if clarity and clarity >= 4:
        adjustments.append("maintain high clarity")
        # Already good clarity, no adjustment needed

    # Depth adjustments  
    if depth and depth <= 2:
        adjustments.append("add more foundational content")
        if "Expand this with more technical details" not in new_prompt:
            new_prompt = f"Provide more basic foundation and introductory content: {original_prompt}"
    
    if depth and depth >= 4:
        adjustments.append("include advanced insights")
        if "Expand this with more technical details" not in new_prompt:
            new_prompt = f"Include more advanced insights, real-world applications, and deeper analysis: {original_prompt}"

    # If no specific adjustments but we have feedback, add general improvement
    if not adjustments and (complexity or clarity or depth):
        new_prompt = f"Improve this content based on user feedback about appropriateness and clarity: {original_prompt}"
    
    # Add learning level context if available
    if student_level and student_level != "Unknown":
        if "suitable for" not in new_prompt and "for {student_level}" not in new_prompt:
            new_prompt = f"{new_prompt} - Tailor for {student_level} level"
    
    print(f"🔄 Adaptation applied: {adjustments}")
    return new_prompt

def get_adaptation_explanation(complexity, clarity, depth):
    """Generate a user-friendly explanation of what adaptations were made"""
    explanations = []
    
    if complexity == "Too complex":
        explanations.append("• Simplified language and added analogies")
    elif complexity == "Too simple":
        explanations.append("• Added more technical depth and advanced concepts")
    
    if clarity and clarity <= 2:
        explanations.append("• Improved structure and step-by-step explanation")
    
    if depth and depth <= 2:
        explanations.append("• Added more foundational content")
    elif depth and depth >= 4:
        explanations.append("• Included advanced insights and applications")
    
    if not explanations:
        explanations.append("• General improvements based on your feedback")
    
    return "\n".join(explanations)