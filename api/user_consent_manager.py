"""
User consent manager for tracking user consent status
"""
import os
import json
import logging
from typing import Set
from datetime import datetime

class UserConsentManager:
    def __init__(self):
        self.consent_file = "user_consent.json"
        self.consented_users = self._load_consented_users()
    
    def _load_consented_users(self) -> Set[str]:
        """Load the set of users who have consented"""
        try:
            if os.path.exists(self.consent_file):
                with open(self.consent_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return set(data.get('consented_users', []))
            return set()
        except Exception as e:
            logging.error(f"Error loading user consent data: {e}")
            return set()
    
    def _save_consented_users(self):
        """Save the set of consented users to file"""
        try:
            data = {
                'consented_users': list(self.consented_users),
                'last_updated': datetime.now().isoformat()
            }
            with open(self.consent_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"Error saving user consent data: {e}")
    
    def has_user_consented(self, user_id: str) -> bool:
        """Check if user has given consent"""
        return user_id in self.consented_users
    
    def mark_user_consented(self, user_id: str):
        """Mark user as having given consent"""
        self.consented_users.add(user_id)
        self._save_consented_users()
        logging.info(f"Marked user {user_id} as consented")
    
    def revoke_user_consent(self, user_id: str):
        """Revoke user consent"""
        self.consented_users.discard(user_id)
        self._save_consented_users()
        logging.info(f"Revoked consent for user {user_id}")
    
    def get_consented_user_count(self) -> int:
        """Get total number of users who have consented"""
        return len(self.consented_users)
    
    def get_consent_status(self, user_id: str) -> dict:
        """Get detailed consent status for a user"""
        return {
            'user_id': user_id,
            'has_consented': self.has_user_consented(user_id),
            'consent_date': self._get_consent_date(user_id) if self.has_user_consented(user_id) else None
        }
    
    def _get_consent_date(self, user_id: str) -> str:
        """Get the date when user gave consent (simplified - just return current date)"""
        # In a real implementation, you might want to store the actual consent date
        return datetime.now().isoformat()


# Global instance
user_consent_manager = UserConsentManager()
