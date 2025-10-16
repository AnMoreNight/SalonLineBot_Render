"""
User consent manager backed by Google Sheets "Users" worksheet
"""
import logging
from typing import Optional
from api.google_sheets_logger import GoogleSheetsLogger


class UserConsentManager:
    def __init__(self):
        self.sheets_logger = GoogleSheetsLogger()

    def has_user_consented(self, user_id: str) -> bool:
        """Check if user has given consent (via Users sheet)"""
        try:
            return self.sheets_logger.has_user_consented(user_id)
        except Exception as e:
            logging.error(f"Consent check failed for {user_id}: {e}")
            return False

    def mark_user_consented(self, user_id: str) -> bool:
        """Mark user as having given consent (and record consent date)"""
        try:
            return self.sheets_logger.mark_user_consented(user_id)
        except Exception as e:
            logging.error(f"Mark consent failed for {user_id}: {e}")
            return False

    def revoke_user_consent(self, user_id: str) -> bool:
        """Revoke user consent"""
        try:
            return self.sheets_logger.revoke_user_consent(user_id)
        except Exception as e:
            logging.error(f"Revoke consent failed for {user_id}: {e}")
            return False

    def get_consented_user_count(self) -> int:
        """Get total number of users who have consented"""
        try:
            # Count directly from sheet records
            records = self.sheets_logger.users_worksheet.get_all_records() if self.sheets_logger.users_worksheet else []
            return sum(1 for r in records if str(r.get('Consented', 'No')).strip().lower() in ("yes", "true", "1", "y"))
        except Exception as e:
            logging.error(f"Failed to count consented users: {e}")
            return 0

    def get_consent_status(self, user_id: str) -> dict:
        """Get detailed consent status for a user"""
        try:
            has_consented = self.has_user_consented(user_id)
            consent_date: Optional[str] = None
            if has_consented and self.sheets_logger.users_worksheet:
                for record in self.sheets_logger.users_worksheet.get_all_records():
                    if record.get('User ID') == user_id:
                        consent_date = record.get('Consent Date')
                        break
            return {
                'user_id': user_id,
                'has_consented': has_consented,
                'consent_date': consent_date
            }
        except Exception as e:
            logging.error(f"Failed to get consent status for {user_id}: {e}")
            return {'user_id': user_id, 'has_consented': False, 'consent_date': None}


# Global instance
user_consent_manager = UserConsentManager()
