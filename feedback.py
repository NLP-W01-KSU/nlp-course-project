import json
import os
import re
from datetime import datetime

def save_feedback(prompt, output, clarity, depth, complexity, comments, user_type=None, student_level=None):
    """
    Save user feedback to a JSONL file with additional metadata
    """
    
    # Create feedback directory if it doesn't exist
    os.makedirs("data/feedback", exist_ok=True)
    
    feedback_data = {
        "timestamp": datetime.now().isoformat(),
        "prompt": prompt,
        "output": output,
        "feedback": {
            "clarity": clarity,
            "depth": depth,
            "complexity": complexity,
            "comments": comments
        },
        "metadata": {
            "user_type": user_type,
            "student_level": student_level
        }
    }
    
    # Save to JSONL file
    feedback_file = "data/feedback/feedback.jsonl"
    
    try:
        with open(feedback_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(feedback_data, ensure_ascii=False) + "\n")
        
        print(f"✅ Feedback saved to {feedback_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error saving feedback: {e}")
        return False

def load_feedback_data():
    """Load all feedback data for analysis"""
    feedback_file = "data/feedback/feedback.jsonl"
    
    if not os.path.exists(feedback_file):
        return []
    
    feedback_data = []
    try:
        with open(feedback_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    feedback_data.append(json.loads(line.strip()))
        return feedback_data
    except Exception as e:
        print(f"❌ Error loading feedback data: {e}")
        return []

def get_feedback_stats():
    """Get basic statistics about collected feedback"""
    feedback_data = load_feedback_data()
    
    if not feedback_data:
        return {
            "total_feedback": 0,
            "average_clarity": 0,
            "average_depth": 0,
            "complexity_distribution": {},
            "user_type_distribution": {}
        }
    
    total = len(feedback_data)
    clarity_sum = 0
    depth_sum = 0
    complexity_counts = {}
    user_type_counts = {}
    
    for entry in feedback_data:
        clarity_sum += entry["feedback"]["clarity"]
        depth_sum += entry["feedback"]["depth"]
        
        complexity = entry["feedback"]["complexity"]
        complexity_counts[complexity] = complexity_counts.get(complexity, 0) + 1
        
        user_type = entry["metadata"].get("user_type", "unknown")
        user_type_counts[user_type] = user_type_counts.get(user_type, 0) + 1
    
    return {
        "total_feedback": total,
        "average_clarity": round(clarity_sum / total, 2) if total > 0 else 0,
        "average_depth": round(depth_sum / total, 2) if total > 0 else 0,
        "complexity_distribution": complexity_counts,
        "user_type_distribution": user_type_counts
    }

def is_high_quality_feedback(feedback_entry):
    """
    SIMPLEST VERSION: Length-based filtering after removing emojis
    Only uses high-quality, "just right" feedback for training
    """
    feedback = feedback_entry["feedback"]
    
    # Quality thresholds
    MIN_CLARITY = 4
    MIN_DEPTH = 4
    MIN_COMMENT_LENGTH = 25  # Substantive comments after emoji removal
    MIN_WORD_COUNT = 4       # Minimum words for substance

    # Check ratings (must be high quality)
    if feedback["clarity"] < MIN_CLARITY or feedback["depth"] < MIN_DEPTH:
        return False
    
    # Check complexity (we want "Just right" examples to replicate)
    if feedback["complexity"] != "Just right":
        return False
    
    # Check comments if provided
    comments = feedback.get("comments", "").strip()
    
    if comments:
        # Remove emojis first, then check length
        emoji_pattern = re.compile(
            r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002600-\U000027BF\U0001F900-\U0001F9FF\U0001F018-\U0001F270👍👎😊😐😕❤️🔥]',
            flags=re.UNICODE
        )
        text_without_emojis = emoji_pattern.sub('', comments).strip()
        
        # Now apply length check on the cleaned text
        if len(text_without_emojis) < MIN_COMMENT_LENGTH:
            return False
            
        # Check word count for minimal substance
        word_count = len(text_without_emojis.split())
        if word_count < MIN_WORD_COUNT:
            return False
    
    return True

def prepare_training_data():
    """
    Prepare high-quality feedback for model fine-tuning
    Returns structured training examples
    """
    all_feedback = load_feedback_data()
    
    training_examples = []
    skipped_count = 0
    
    for feedback in all_feedback:
        if is_high_quality_feedback(feedback):
            # Create training example from high-quality feedback
            training_example = {
                "instruction": feedback["prompt"],
                "input": f"Student Level: {feedback['metadata'].get('student_level', 'Unknown')}",
                "output": feedback["output"],
                "metadata": {
                    "user_type": feedback["metadata"].get("user_type"),
                    "clarity_score": feedback["feedback"]["clarity"],
                    "depth_score": feedback["feedback"]["depth"],
                    "comments": feedback["feedback"].get("comments", "")
                }
            }
            training_examples.append(training_example)
        else:
            skipped_count += 1
    
    print(f"✅ Prepared {len(training_examples)} training examples (skipped {skipped_count} low-quality)")
    return training_examples

def get_training_data_stats():
    """
    Get statistics about prepared training data
    """
    training_data = prepare_training_data()
    
    if not training_data:
        return {
            "total_training_examples": 0,
            "user_type_breakdown": {},
            "average_scores": {"clarity": 0, "depth": 0}
        }
    
    user_type_counts = {}
    clarity_sum = 0
    depth_sum = 0
    
    for example in training_data:
        user_type = example["metadata"].get("user_type", "unknown")
        user_type_counts[user_type] = user_type_counts.get(user_type, 0) + 1
        
        clarity_sum += example["metadata"]["clarity_score"]
        depth_sum += example["metadata"]["depth_score"]
    
    return {
        "total_training_examples": len(training_data),
        "user_type_breakdown": user_type_counts,
        "average_scores": {
            "clarity": round(clarity_sum / len(training_data), 2),
            "depth": round(depth_sum / len(training_data), 2)
        }
    }

def export_training_data(output_file="data/training/training_data.jsonl"):
    """
    Export filtered training data to file for fine-tuning
    """
    training_data = prepare_training_data()
    
    if not training_data:
        print("❌ No high-quality training data available")
        return False
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            for example in training_data:
                # Remove metadata for actual training
                training_example = {
                    "instruction": example["instruction"],
                    "input": example["input"],
                    "output": example["output"]
                }
                f.write(json.dumps(training_example, ensure_ascii=False) + "\n")
        
        print(f"✅ Exported {len(training_data)} training examples to {output_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error exporting training data: {e}")
        return False

def get_research_progress():
    """
    Comprehensive research progress dashboard
    """
    feedback_stats = get_feedback_stats()
    training_stats = get_training_data_stats()
    
    return {
        "total_feedback": feedback_stats["total_feedback"],
        "high_quality_examples": training_stats["total_training_examples"],
        "conversion_rate": f"{(training_stats['total_training_examples'] / feedback_stats['total_feedback'] * 100):.1f}%" if feedback_stats['total_feedback'] > 0 else "0%",
        "average_quality": training_stats["average_scores"],
        "user_breakdown": training_stats["user_type_breakdown"]
    }