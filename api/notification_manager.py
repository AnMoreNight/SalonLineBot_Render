"""
Unified notification manager for salon booking system
Supports both Slack and LINE notifications
"""
import os
import logging
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

class NotificationManager:
    def __init__(self):
        load_dotenv()
        
        # Get notification method from environment variable
        self.notification_method = os.getenv("NOTIFICATION_METHOD", "slack").lower()
        
        # Initialize notifiers
        self.slack_notifier = None
        self.line_notifier = None
        
        # Initialize based on configuration
        if self.notification_method == "slack":
            try:
                from api.slack_notifier import slack_notifier
                self.slack_notifier = slack_notifier
                logging.info("Slack notifications enabled")
            except Exception as e:
                logging.error(f"Failed to initialize Slack notifier: {e}")
        
        elif self.notification_method == "line":
            try:
                from api.line_notifier import line_notifier
                self.line_notifier = line_notifier
                logging.info("LINE notifications enabled")
            except Exception as e:
                logging.error(f"Failed to initialize LINE notifier: {e}")
        
        elif self.notification_method == "both":
            try:
                from api.slack_notifier import slack_notifier
                from api.line_notifier import line_notifier
                self.slack_notifier = slack_notifier
                self.line_notifier = line_notifier
                logging.info("Both Slack and LINE notifications enabled")
            except Exception as e:
                logging.error(f"Failed to initialize notifiers: {e}")
        
        else:
            logging.warning(f"Unknown notification method: {self.notification_method}. Valid options: slack, line, both")
    
    def is_enabled(self) -> bool:
        """Check if any notification method is enabled"""
        return (self.slack_notifier and self.slack_notifier.enabled) or (self.line_notifier and self.line_notifier.enabled)
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all notification methods"""
        return {
            "method": self.notification_method,
            "slack_enabled": self.slack_notifier and self.slack_notifier.enabled,
            "line_enabled": self.line_notifier and self.line_notifier.enabled,
            "overall_enabled": self.is_enabled()
        }
    
    def notify_user_login(self, user_id: str, display_name: str) -> bool:
        """Send user login notification"""
        success = False
        
        if self.slack_notifier and self.slack_notifier.enabled:
            try:
                if self.slack_notifier.notify_user_login(user_id, display_name):
                    success = True
            except Exception as e:
                logging.error(f"Slack login notification failed: {e}")
        
        if self.line_notifier and self.line_notifier.enabled:
            try:
                if self.line_notifier.notify_user_login(user_id, display_name):
                    success = True
            except Exception as e:
                logging.error(f"LINE login notification failed: {e}")
        
        return success
    
    def notify_reservation_confirmation(self, reservation_data: Dict[str, Any], client_name: str) -> bool:
        """Send reservation confirmation notification"""
        success = False
        
        if self.slack_notifier and self.slack_notifier.enabled:
            try:
                if self.slack_notifier.notify_reservation_confirmation(reservation_data, client_name):
                    success = True
            except Exception as e:
                logging.error(f"Slack reservation confirmation notification failed: {e}")
        
        if self.line_notifier and self.line_notifier.enabled:
            try:
                if self.line_notifier.notify_reservation_confirmation(reservation_data, client_name):
                    success = True
            except Exception as e:
                logging.error(f"LINE reservation confirmation notification failed: {e}")
        
        return success
    
    def notify_reservation_modification(self, old_reservation: Dict[str, Any], new_reservation: Dict[str, Any], client_name: str) -> bool:
        """Send reservation modification notification"""
        success = False
        
        if self.slack_notifier and self.slack_notifier.enabled:
            try:
                if self.slack_notifier.notify_reservation_modification(old_reservation, new_reservation, client_name):
                    success = True
            except Exception as e:
                logging.error(f"Slack reservation modification notification failed: {e}")
        
        if self.line_notifier and self.line_notifier.enabled:
            try:
                if self.line_notifier.notify_reservation_modification(old_reservation, new_reservation, client_name):
                    success = True
            except Exception as e:
                logging.error(f"LINE reservation modification notification failed: {e}")
        
        return success
    
    def notify_reservation_cancellation(self, reservation_data: Dict[str, Any], client_name: str) -> bool:
        """Send reservation cancellation notification"""
        success = False
        
        if self.slack_notifier and self.slack_notifier.enabled:
            try:
                if self.slack_notifier.notify_reservation_cancellation(reservation_data, client_name):
                    success = True
            except Exception as e:
                logging.error(f"Slack reservation cancellation notification failed: {e}")
        
        if self.line_notifier and self.line_notifier.enabled:
            try:
                if self.line_notifier.notify_reservation_cancellation(reservation_data, client_name):
                    success = True
            except Exception as e:
                logging.error(f"LINE reservation cancellation notification failed: {e}")
        
        return success
    
    def notify_reminder_status(self, success_count: int, total_count: int, failed_reservations: List[Dict[str, Any]]) -> bool:
        """Send reminder status notification to manager"""
        success = False
        
        if self.slack_notifier and self.slack_notifier.enabled:
            try:
                if self.slack_notifier.notify_reminder_status(success_count, total_count, failed_reservations):
                    success = True
            except Exception as e:
                logging.error(f"Slack reminder status notification failed: {e}")
        
        if self.line_notifier and self.line_notifier.enabled:
            try:
                if self.line_notifier.notify_reminder_status(success_count, total_count, failed_reservations):
                    success = True
            except Exception as e:
                logging.error(f"LINE reminder status notification failed: {e}")
        
        return success


# Global instance
notification_manager = NotificationManager()


# Convenience functions that use the unified manager
def send_user_login_notification(user_id: str, display_name: str) -> bool:
    """Send user login notification using configured method"""
    return notification_manager.notify_user_login(user_id, display_name)


def send_reservation_confirmation_notification(reservation_data: Dict[str, Any], client_name: str) -> bool:
    """Send reservation confirmation notification using configured method"""
    return notification_manager.notify_reservation_confirmation(reservation_data, client_name)


def send_reservation_modification_notification(old_reservation: Dict[str, Any], new_reservation: Dict[str, Any], client_name: str) -> bool:
    """Send reservation modification notification using configured method"""
    return notification_manager.notify_reservation_modification(old_reservation, new_reservation, client_name)


def send_reservation_cancellation_notification(reservation_data: Dict[str, Any], client_name: str) -> bool:
    """Send reservation cancellation notification using configured method"""
    return notification_manager.notify_reservation_cancellation(reservation_data, client_name)


if __name__ == "__main__":
    # Test the notification manager
    manager = NotificationManager()
    
    print("Notification Manager Status:")
    status = manager.get_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    if manager.is_enabled():
        print("\n✅ Notifications are enabled")
        
        # Test notification
        test_reservation = {
            "reservation_id": "TEST-001",
            "date": "2025-01-20",
            "start_time": "10:00",
            "end_time": "11:00",
            "service": "カット",
            "staff": "田中"
        }
        
        success = manager.notify_reservation_confirmation(test_reservation, "Test User")
        if success:
            print("✅ Test notification sent successfully!")
        else:
            print("❌ Failed to send test notification")
    else:
        print("\n❌ No notifications are enabled")
        print("Configure NOTIFICATION_METHOD environment variable:")
        print("  - 'slack' for Slack notifications")
        print("  - 'line' for LINE notifications") 
        print("  - 'both' for both Slack and LINE notifications")
