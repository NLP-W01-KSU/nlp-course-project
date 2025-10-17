import streamlit as st
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional

class HistoryManager:
    def __init__(self):
        self.history_key = "edugen_history"
    
    def _get_user_id(self) -> str:
        """Get or create a unique user identifier"""
        if 'user_id' not in st.session_state:
            st.session_state.user_id = str(uuid.uuid4())
        return st.session_state.user_id
    
    def save_to_history(self, content_data: Dict) -> str:
        """Save generated content to history"""
        try:
            # Get user-specific history
            user_id = self._get_user_id()
            history = self._load_history()
            
            # Create history entry
            entry_id = str(uuid.uuid4())
            history_entry = {
                "id": entry_id,
                "timestamp": datetime.now().isoformat(),
                "user_type": content_data.get("user_type"),
                "student_level": content_data.get("student_level"),
                "topic": content_data.get("topic", ""),
                "content_type": content_data.get("content_type", ""),
                "prompt": content_data.get("prompt", ""),
                "output": content_data.get("output", ""),
                "pdf_data": content_data.get("pdf_data"),
                "filename": content_data.get("filename", "content.pdf"),
                "feedback_given": content_data.get("feedback_given", False)
            }
            
            # Add to history (newest first)
            if user_id not in history:
                history[user_id] = []
            history[user_id].insert(0, history_entry)
            
            # Keep only last 50 entries per user
            history[user_id] = history[user_id][:50]
            
            # Save to session state
            st.session_state[self.history_key] = history
            
            print(f"✅ Saved to history: {entry_id}")  # Debug
            return entry_id
            
        except Exception as e:
            print(f"Error saving to history: {e}")
            return None
    
    def _load_history(self) -> Dict:
        """Load history from session state"""
        if self.history_key in st.session_state:
            return st.session_state[self.history_key]
        return {}
    
    def get_user_history(self) -> List[Dict]:
        """Get current user's history"""
        user_id = self._get_user_id()
        history = self._load_history()
        user_history = history.get(user_id, [])
        print(f"📖 Loaded {len(user_history)} history entries for user {user_id[:8]}")  # Debug
        return user_history
    
    def get_entry_by_id(self, entry_id: str) -> Optional[Dict]:
        """Get a specific history entry by ID"""
        user_id = self._get_user_id()
        history = self._load_history()
        user_history = history.get(user_id, [])
        
        for entry in user_history:
            if entry["id"] == entry_id:
                return entry
        return None
    
    def delete_entry(self, entry_id: str) -> bool:
        """Delete a specific history entry"""
        try:
            user_id = self._get_user_id()
            history = self._load_history()
            
            if user_id in history:
                history[user_id] = [entry for entry in history[user_id] if entry["id"] != entry_id]
                st.session_state[self.history_key] = history
                return True
            return False
        except Exception as e:
            print(f"Error deleting history entry: {e}")
            return False
    
    def clear_history(self) -> bool:
        """Clear all history for current user"""
        try:
            user_id = self._get_user_id()
            history = self._load_history()
            
            if user_id in history:
                del history[user_id]
                st.session_state[self.history_key] = history
                return True
            return False
        except Exception as e:
            print(f"Error clearing history: {e}")
            return False

# Global history manager instance
history_manager = HistoryManager()