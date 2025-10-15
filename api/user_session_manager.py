"""
User session manager for tracking user interactions
"""
import os
import json
import logging
from typing import Set
from datetime import datetime, timedelta

class UserSessionManager:
    def __init__(self):
        self.seen_users_file = "user_sessions.json"
        self.seen_users = self._load_seen_users()
    
    def _load_seen_users(self) -> Set[str]:
        """Load the set of users who have been seen before"""
        try:
            if os.path.exists(self.seen_users_file):
                with open(self.seen_users_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Convert list back to set
                    return set(data.get('seen_users', []))
            return set()
        except Exception as e:
            logging.error(f"Error loading user sessions: {e}")
            return set()
    
    def _save_seen_users(self):
        """Save the set of seen users to file"""
        try:
            data = {
                'seen_users': list(self.seen_users),
                'last_updated': datetime.now().isoformat()
            }
            with open(self.seen_users_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"Error saving user sessions: {e}")
    
    def is_new_user(self, user_id: str) -> bool:
        """Check if this is a new user (first time interacting with bot)"""
        return user_id not in self.seen_users
    
    def mark_user_seen(self, user_id: str):
        """Mark a user as seen (they have interacted with the bot)"""
        self.seen_users.add(user_id)
        self._save_seen_users()
        logging.info(f"Marked user {user_id} as seen")
    
    def get_user_count(self) -> int:
        """Get total number of unique users who have interacted with the bot"""
        return len(self.seen_users)
    
    def cleanup_old_sessions(self, days_old: int = 30):
        """Clean up old session data (optional maintenance function)"""
        # For now, we keep all users indefinitely
        # In the future, you might want to implement cleanup based on last activity
        pass


# Global instance
user_session_manager = UserSessionManager()
