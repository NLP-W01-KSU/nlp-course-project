import uuid
import base64
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func
from db.models import User, ContentHistory, Feedback
from db.connection import get_db, SessionLocal

# ------------------------------------
# ✅ User Management
# ------------------------------------
def create_user(user_id):
    """Create a new user in the database"""
    with next(get_db()) as db:
        try:
            user = User(id=user_id)
            db.add(user)
            db.commit()
            print(f"✅ Created new user: {user_id}")
            return True
        except SQLAlchemyError as e:
            db.rollback()
            # User likely already exists - this is fine
            return False

def ensure_user_exists(user_id):
    """Ensure user exists in database, create if needed"""
    with next(get_db()) as db:
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            return create_user(user_id)
        return True

# ------------------------------------
# ✅ Content History
# ------------------------------------
def get_user_history(user_id):
    """Get user's content history from database"""
    with next(get_db()) as db:
        try:
            # Ensure user exists first
            ensure_user_exists(user_id)
            
            history = db.query(ContentHistory).filter_by(user_id=user_id).order_by(ContentHistory.created_at.desc()).all()
            print(f"✅ Loaded {len(history)} history entries for user {user_id}")
            return history
        except SQLAlchemyError as e:
            print(f"❌ Error loading user history: {e}")
            return []

def save_content_to_history(data):
    """Save content to history"""
    with next(get_db()) as db:
        try:
            # Ensure user exists
            ensure_user_exists(data["user_id"])
            
            content = ContentHistory(
                id=uuid.uuid4(),
                user_id=data["user_id"],
                prompt=data["prompt"],
                output=data["output"],
                user_type=data["user_type"],
                topic=data["topic"],
                student_level=data["student_level"],
                content_type=data["content_type"],
                filename=data["filename"],
                pdf_base64=data.get("pdf_base64", ""),
                feedback_given=data.get("feedback_given", False),
                generated_model=data.get("generated_model", "groq")
            )
            db.add(content)
            db.commit()
            print(f"✅ Saved content to history: {content.id}")
            return str(content.id)
        except SQLAlchemyError as e:
            db.rollback()
            print(f"❌ Error saving content to history: {e}")
            return None

def update_pdf_data(content_id, pdf_data):
    """Update PDF data for existing content - STORE CLEAN BASE64"""
    with next(get_db()) as db:
        try:
            content = db.query(ContentHistory).filter_by(id=content_id).first()
            if content:
                # Always store as clean base64 string without data URL prefix
                if isinstance(pdf_data, bytes):
                    # Convert bytes to clean base64
                    pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
                elif isinstance(pdf_data, str):
                    # If it's a data URL, extract the base64 part
                    if pdf_data.startswith('data:application/pdf;base64,'):
                        pdf_base64 = pdf_data.split(',')[1]
                    else:
                        # Assume it's already base64
                        pdf_base64 = pdf_data
                else:
                    print(f"❌ Invalid PDF data type: {type(pdf_data)}")
                    return False
                
                # Store clean base64 without any prefixes
                content.pdf_base64 = pdf_base64
                db.commit()
                print(f"✅ Updated PDF data for content: {content_id} (clean base64, {len(pdf_base64)} chars)")
                return True
            else:
                print(f"❌ Content not found: {content_id}")
                return False
        except SQLAlchemyError as e:
            db.rollback()
            print(f"❌ Error updating PDF data: {e}")
            return False

def save_feedback_to_db(data):
    with next(get_db()) as db:
        try:
            ensure_user_exists(data["user_id"])
            
            # Create feedback object with regeneration data
            feedback = Feedback(
                id=uuid.uuid4(),
                user_id=data["user_id"],
                content_id=data["content_id"],
                clarity=data["clarity"],
                depth=data["depth"],
                complexity=data["complexity"],
                comments=data["comments"],
                is_regenerated_feedback=data.get("is_regenerated_feedback", False),
                regeneration_count=data.get("regeneration_count", 0),
                regeneration_type=data.get("regeneration_type")
            )
            
            # Mark content as feedback_given
            content = db.query(ContentHistory).filter_by(id=data["content_id"]).first()
            if content:
                content.feedback_given = True

            db.add(feedback)
            db.commit()
            print(f"✅ Saved feedback: {feedback.id}, Regenerated: {feedback.is_regenerated_feedback}, Type: {feedback.regeneration_type}")
            return str(feedback.id)
            
        except SQLAlchemyError as e:
            db.rollback()
            print(f"❌ Error saving feedback: {e}")
            return None
        
def debug_regeneration_data():
    """Temporary function to debug regeneration data"""
    with next(get_db()) as db:
        try:
            # Check all feedback entries
            all_feedback = db.query(Feedback).all()
            print(f"📊 Total feedback entries: {len(all_feedback)}")
            
            # Check regenerated feedback
            regenerated = db.query(Feedback).filter(
                Feedback.is_regenerated_feedback == True
            ).all()
            print(f"🔄 Regenerated feedback entries: {len(regenerated)}")
            
            # Print details of regenerated entries
            for fb in regenerated:
                print(f"  - ID: {fb.id}, Type: {fb.regeneration_type}, Count: {fb.regeneration_count}")
                
            return len(regenerated)
        except Exception as e:
            print(f"❌ Debug error: {e}")
            return 0

# ------------------------------------
# ✅ Research Statistics
# ------------------------------------
def get_fallback_metrics():
    """Return fallback metrics when database query fails"""
    return {
        "models": {
            "groq": {
                "feedback_count": 0,
                "avg_clarity": 0.0,
                "avg_depth": 0.0,
                "high_quality_count": 0,
                "high_quality_rate": 0.0,
                "satisfaction_rate": 0.0,
                "complexity_distribution": {"Too simple": 0, "Just right": 0, "Too complex": 0},
                "overall_score": 0.0
            },
            "phi3": {
                "feedback_count": 0,
                "avg_clarity": 0.0,
                "avg_depth": 0.0,
                "high_quality_count": 0,
                "high_quality_rate": 0.0,
                "satisfaction_rate": 0.0,
                "complexity_distribution": {"Too simple": 0, "Just right": 0, "Too complex": 0},
                "overall_score": 0.0
            }
        },
        "comparative": {
            "improvement_potential": 0.0,
            "relative_performance": 0.0,
            "quality_gap": {"clarity": 0.0, "depth": 0.0}
        },
        "total_feedback": 0,
        "analysis_timestamp": datetime.now().isoformat()
    }

def get_research_stats():
    """Get basic research statistics for sidebar display - UPDATED with regeneration stats"""
    with next(get_db()) as db:
        try:
            total_feedback = db.query(Feedback).count()
            total_content = db.query(ContentHistory).count()

            # Try to get model-specific stats
            try:
                # Groq stats
                groq_feedback_count = db.query(Feedback).join(ContentHistory).filter(
                    ContentHistory.generated_model == "groq"
                ).count()
                
                high_quality_groq = db.query(Feedback).join(ContentHistory).filter(
                    ContentHistory.generated_model == "groq",
                    Feedback.clarity >= 4,
                    Feedback.depth >= 4,
                    Feedback.complexity == "Just right"
                ).count()

                # Groq average scores - CONVERT ALL TO FLOAT
                groq_avg_clarity_result = db.query(func.avg(Feedback.clarity)).join(ContentHistory).filter(
                    ContentHistory.generated_model == "groq"
                ).scalar()
                groq_avg_clarity = float(groq_avg_clarity_result) if groq_avg_clarity_result else 0.0
                
                groq_avg_depth_result = db.query(func.avg(Feedback.depth)).join(ContentHistory).filter(
                    ContentHistory.generated_model == "groq"
                ).scalar()
                groq_avg_depth = float(groq_avg_depth_result) if groq_avg_depth_result else 0.0

                # Phi-3 stats
                phi3_feedback_count = db.query(Feedback).join(ContentHistory).filter(
                    ContentHistory.generated_model == "phi3"
                ).count()
                
                high_quality_phi3 = db.query(Feedback).join(ContentHistory).filter(
                    ContentHistory.generated_model == "phi3",
                    Feedback.clarity >= 4,
                    Feedback.depth >= 4,
                    Feedback.complexity == "Just right"
                ).count()

                # Phi-3 average scores - CONVERT ALL TO FLOAT
                phi3_avg_clarity_result = db.query(func.avg(Feedback.clarity)).join(ContentHistory).filter(
                    ContentHistory.generated_model == "phi3"
                ).scalar()
                phi3_avg_clarity = float(phi3_avg_clarity_result) if phi3_avg_clarity_result else 0.0
                
                phi3_avg_depth_result = db.query(func.avg(Feedback.depth)).join(ContentHistory).filter(
                    ContentHistory.generated_model == "phi3"
                ).scalar()
                phi3_avg_depth = float(phi3_avg_depth_result) if phi3_avg_depth_result else 0.0

            except Exception as e:
                print(f"⚠️ Model-specific stats not available yet: {e}")
                # Fallback: use overall stats
                groq_feedback_count = total_feedback
                high_quality_groq = db.query(Feedback).filter(
                    Feedback.clarity >= 4,
                    Feedback.depth >= 4,
                    Feedback.complexity == "Just right"
                ).count()
                phi3_feedback_count = 0
                high_quality_phi3 = 0
                
                # Convert overall averages to float
                groq_avg_clarity_result = db.query(func.avg(Feedback.clarity)).scalar()
                groq_avg_clarity = float(groq_avg_clarity_result) if groq_avg_clarity_result else 0.0
                groq_avg_depth_result = db.query(func.avg(Feedback.depth)).scalar()
                groq_avg_depth = float(groq_avg_depth_result) if groq_avg_depth_result else 0.0
                
                phi3_avg_clarity = 0.0
                phi3_avg_depth = 0.0

            # NEW: Regeneration statistics
            try:
                regenerated_feedback_count = db.query(Feedback).filter(
                    Feedback.is_regenerated_feedback == True
                ).count()
                
                # Regeneration by type
                model_switch_count = db.query(Feedback).filter(
                    Feedback.regeneration_type == "model_switch"
                ).count()
                
                feedback_adjustment_count = db.query(Feedback).filter(
                    Feedback.regeneration_type == "feedback_adjustment"
                ).count()
                
                manual_regeneration_count = db.query(Feedback).filter(
                    Feedback.regeneration_type == "manual"
                ).count()
                
                # Regeneration quality analysis
                regenerated_high_quality = db.query(Feedback).filter(
                    Feedback.is_regenerated_feedback == True,
                    Feedback.clarity >= 4,
                    Feedback.depth >= 4,
                    Feedback.complexity == "Just right"
                ).count()
                
                # Average scores for regenerated vs original content
                regenerated_avg_clarity_result = db.query(func.avg(Feedback.clarity)).filter(
                    Feedback.is_regenerated_feedback == True
                ).scalar()
                regenerated_avg_clarity = float(regenerated_avg_clarity_result) if regenerated_avg_clarity_result else 0.0
                
                original_avg_clarity_result = db.query(func.avg(Feedback.clarity)).filter(
                    Feedback.is_regenerated_feedback == False
                ).scalar()
                original_avg_clarity = float(original_avg_clarity_result) if original_avg_clarity_result else 0.0
                
            except Exception as e:
                print(f"⚠️ Regeneration stats not available yet: {e}")
                # Fallback regeneration stats
                regenerated_feedback_count = 0
                model_switch_count = 0
                feedback_adjustment_count = 0
                manual_regeneration_count = 0
                regenerated_high_quality = 0
                regenerated_avg_clarity = 0.0
                original_avg_clarity = 0.0

            # Overall average scores (for backward compatibility) - CONVERT TO FLOAT
            avg_clarity_result = db.query(func.avg(Feedback.clarity)).scalar()
            avg_clarity = float(avg_clarity_result) if avg_clarity_result else 0.0
            avg_depth_result = db.query(func.avg(Feedback.depth)).scalar()
            avg_depth = float(avg_depth_result) if avg_depth_result else 0.0

            # Ensure all required keys are present
            stats = {
                # Fine-tuning progress
                "groq_feedback_count": groq_feedback_count,
                "high_quality_groq": high_quality_groq,
                "groq_scores": {
                    "clarity": round(groq_avg_clarity, 2),
                    "depth": round(groq_avg_depth, 2)
                },
                
                # Research comparison data
                "phi3_feedback_count": phi3_feedback_count,
                "high_quality_phi3": high_quality_phi3,
                "phi3_scores": {
                    "clarity": round(phi3_avg_clarity, 2),
                    "depth": round(phi3_avg_depth, 2)
                },
                
                # NEW: Regeneration statistics
                "regenerated_feedback_count": regenerated_feedback_count,
                "regeneration_types": {
                    "model_switch": model_switch_count,
                    "feedback_adjustment": feedback_adjustment_count,
                    "manual": manual_regeneration_count
                },
                "regenerated_high_quality": regenerated_high_quality,
                "regeneration_quality_comparison": {
                    "regenerated_avg_clarity": round(regenerated_avg_clarity, 2),
                    "original_avg_clarity": round(original_avg_clarity, 2),
                    "quality_gap": round(regenerated_avg_clarity - original_avg_clarity, 2)
                },
                
                # Overall metrics (for backward compatibility)
                "total_feedback": total_feedback,
                "total_content": total_content,
                "average_scores": {
                    "clarity": round(avg_clarity, 2),
                    "depth": round(avg_depth, 2)
                }
            }
            
            print(f"📊 Research stats: Groq clarity={groq_avg_clarity:.2f}, Phi-3 clarity={phi3_avg_clarity:.2f}, Regenerated feedback={regenerated_feedback_count}")
            return stats
            
        except Exception as e:
            print(f"❌ Error getting research stats: {e}")
            # Return safe fallback stats with floats
            return {
                "groq_feedback_count": 0,
                "high_quality_groq": 0,
                "groq_scores": {"clarity": 0.0, "depth": 0.0},
                "phi3_feedback_count": 0,
                "high_quality_phi3": 0,
                "phi3_scores": {"clarity": 0.0, "depth": 0.0},
                "regenerated_feedback_count": 0,
                "regeneration_types": {"model_switch": 0, "feedback_adjustment": 0, "manual": 0},
                "regenerated_high_quality": 0,
                "regeneration_quality_comparison": {
                    "regenerated_avg_clarity": 0.0,
                    "original_avg_clarity": 0.0,
                    "quality_gap": 0.0
                },
                "total_feedback": 0,
                "total_content": 0,
                "average_scores": {"clarity": 0.0, "depth": 0.0}
            }

def get_advanced_research_metrics():
    """Get comprehensive research metrics for visualization"""
    with next(get_db()) as db:
        try:
            # Basic counts
            total_feedback = db.query(Feedback).count()
            
            # Model-specific metrics
            models = ["groq", "phi3"]
            metrics = {}
            
            for model in models:
                # Basic quality metrics
                feedback_count = db.query(Feedback).join(ContentHistory).filter(
                    ContentHistory.generated_model == model
                ).count()
                
                if feedback_count > 0:
                    # Average scores - CONVERT TO FLOAT
                    avg_clarity_result = db.query(func.avg(Feedback.clarity)).join(ContentHistory).filter(
                        ContentHistory.generated_model == model
                    ).scalar()
                    avg_clarity = float(avg_clarity_result) if avg_clarity_result else 0.0
                    
                    avg_depth_result = db.query(func.avg(Feedback.depth)).join(ContentHistory).filter(
                        ContentHistory.generated_model == model
                    ).scalar()
                    avg_depth = float(avg_depth_result) if avg_depth_result else 0.0
                    
                    # High-quality rate (precision-like metric)
                    high_quality_count = db.query(Feedback).join(ContentHistory).filter(
                        ContentHistory.generated_model == model,
                        Feedback.clarity >= 4,
                        Feedback.depth >= 4,
                        Feedback.complexity == "Just right"
                    ).count()
                    
                    high_quality_rate = (high_quality_count / feedback_count) * 100 if feedback_count > 0 else 0
                    
                    # User satisfaction (clarity + depth >= 8)
                    satisfied_count = db.query(Feedback).join(ContentHistory).filter(
                        ContentHistory.generated_model == model,
                        Feedback.clarity + Feedback.depth >= 8
                    ).count()
                    
                    satisfaction_rate = (satisfied_count / feedback_count) * 100 if feedback_count > 0 else 0
                    
                    # Complexity distribution
                    complexity_counts = {}
                    for complexity in ["Too simple", "Just right", "Too complex"]:
                        count = db.query(Feedback).join(ContentHistory).filter(
                            ContentHistory.generated_model == model,
                            Feedback.complexity == complexity
                        ).count()
                        complexity_counts[complexity] = count
                    
                    metrics[model] = {
                        "feedback_count": feedback_count,
                        "avg_clarity": round(avg_clarity, 2),
                        "avg_depth": round(avg_depth, 2),
                        "high_quality_count": high_quality_count,
                        "high_quality_rate": round(high_quality_rate, 1),
                        "satisfaction_rate": round(satisfaction_rate, 1),
                        "complexity_distribution": complexity_counts,
                        "overall_score": round((avg_clarity + avg_depth) / 2, 2)
                    }
                else:
                    metrics[model] = {
                        "feedback_count": 0,
                        "avg_clarity": 0.0,
                        "avg_depth": 0.0,
                        "high_quality_count": 0,
                        "high_quality_rate": 0.0,
                        "satisfaction_rate": 0.0,
                        "complexity_distribution": {"Too simple": 0, "Just right": 0, "Too complex": 0},
                        "overall_score": 0.0
                    }
            
            # Comparative metrics
            if metrics["groq"]["feedback_count"] > 0 and metrics["phi3"]["feedback_count"] > 0:
                groq_score = metrics["groq"]["overall_score"]
                phi3_score = metrics["phi3"]["overall_score"]
                improvement_potential = groq_score - phi3_score
                
                comparative_metrics = {
                    "improvement_potential": round(improvement_potential, 2),
                    "relative_performance": round((phi3_score / groq_score) * 100, 1) if groq_score > 0 else 0,
                    "quality_gap": {
                        "clarity": round(metrics["groq"]["avg_clarity"] - metrics["phi3"]["avg_clarity"], 2),
                        "depth": round(metrics["groq"]["avg_depth"] - metrics["phi3"]["avg_depth"], 2)
                    }
                }
            else:
                comparative_metrics = {
                    "improvement_potential": 0.0,
                    "relative_performance": 0.0,
                    "quality_gap": {"clarity": 0.0, "depth": 0.0}
                }
            
            return {
                "models": metrics,
                "comparative": comparative_metrics,
                "total_feedback": total_feedback,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error getting advanced metrics: {e}")
            return get_fallback_metrics()

def export_research_data_for_analysis():
    """Export comprehensive data for external analysis and visualization"""
    session = SessionLocal()
    try:
        # Get all feedback with content and model information
        query = session.query(
            Feedback.id,
            Feedback.clarity,
            Feedback.depth,
            Feedback.complexity,
            Feedback.comments,
            Feedback.created_at,
            ContentHistory.generated_model,
            ContentHistory.user_type,
            ContentHistory.student_level,
            ContentHistory.content_type,
            ContentHistory.topic
        ).join(ContentHistory).all()
        
        export_data = []
        for row in query:
            export_data.append({
                "feedback_id": str(row.id),
                "clarity": row.clarity,
                "depth": row.depth,
                "complexity": row.complexity,
                "comment_length": len(row.comments or ""),
                "model": row.generated_model,
                "user_type": row.user_type,
                "student_level": row.student_level,
                "content_type": row.content_type,
                "topic": row.topic,
                "timestamp": row.created_at.isoformat() if row.created_at else None
            })
        
        # Save for analysis
        import json
        import os
        os.makedirs("data/analysis", exist_ok=True)
        with open("data/analysis/research_dataset.json", "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Exported {len(export_data)} research data points")
        return export_data
        
    except Exception as e:
        print(f"❌ Error exporting research data: {e}")
        return []
    finally:
        session.close()
        
        
# Add this function to db/helpers.py

def get_entry_by_id(content_id):
    """Get a specific content history entry by ID"""
    with next(get_db()) as db:
        try:
            # Convert string ID to UUID if needed
            if isinstance(content_id, str):
                content_id = uuid.UUID(content_id)
            
            entry = db.query(ContentHistory).filter_by(id=content_id).first()
            if entry:
                print(f"✅ Loaded content entry: {content_id}")
                return entry
            else:
                print(f"❌ Content entry not found: {content_id}")
                return None
        except SQLAlchemyError as e:
            print(f"❌ Error loading content entry: {e}")
            return None
        except ValueError as e:
            print(f"❌ Invalid content ID format: {e}")
            return None