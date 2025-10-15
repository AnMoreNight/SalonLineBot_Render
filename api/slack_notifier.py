"""
Slack notification service for salon booking system
"""
import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import requests
from dotenv import load_dotenv

class SlackNotifier:
    def __init__(self):
        load_dotenv()
        self.webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        self.enabled = bool(self.webhook_url)
        
        if not self.enabled:
            logging.warning("Slack webhook URL not configured. Notifications disabled.")
        else:
            logging.info("Slack notifications enabled")
    
    def send_notification(self, message: str, title: str = None, color: str = "good") -> bool:
        """
        Send a notification to Slack
        
        Args:
            message: The main message content
            title: Optional title for the notification
            color: Color for the attachment (good, warning, danger, or hex color)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.enabled:
            logging.debug("Slack notifications disabled, skipping notification")
            return False
        
        try:
            # Prepare the payload
            payload = {
                "attachments": [
                    {
                        "color": color,
                        "title": title,
                        "text": message,
                        "footer": "Salon Booking System",
                        "ts": int(datetime.now().timestamp())
                    }
                ]
            }
            
            # Send the request
            response = requests.post(
                self.webhook_url,
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                logging.info("Slack notification sent successfully")
                return True
            else:
                logging.error(f"Failed to send Slack notification: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logging.error(f"Error sending Slack notification: {e}")
            return False
    
    def notify_user_login(self, user_id: str, display_name: str) -> bool:
        """Send notification when user logs in"""
        message = f"👤 **User Login**\n"
        message += f"• User ID: `{user_id}`\n"
        message += f"• Display Name: {display_name}\n"
        message += f"• Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return self.send_notification(
            message=message,
            title="🔐 User Login",
            color="good"
        )
    
    def notify_reservation_confirmation(self, reservation_data: Dict[str, Any], client_name: str) -> bool:
        """Send notification when reservation is confirmed"""
        message = f"✅ **New Reservation Confirmed**\n"
        message += f"• Reservation ID: `{reservation_data.get('reservation_id', 'N/A')}`\n"
        message += f"• Client: {client_name}\n"
        message += f"• Date: {reservation_data.get('date', 'N/A')}\n"
        message += f"• Time: {reservation_data.get('start_time', 'N/A')}~{reservation_data.get('end_time', 'N/A')}\n"
        message += f"• Service: {reservation_data.get('service', 'N/A')}\n"
        message += f"• Staff: {reservation_data.get('staff', 'N/A')}\n"
        message += f"• Duration: {self._get_service_duration(reservation_data.get('service', ''))} minutes\n"
        message += f"• Price: ¥{self._get_service_price(reservation_data.get('service', '')):,}\n"
        message += f"• Confirmed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return self.send_notification(
            message=message,
            title="📅 New Reservation",
            color="good"
        )
    
    def notify_reservation_modification(self, old_reservation: Dict[str, Any], new_reservation: Dict[str, Any], client_name: str) -> bool:
        """Send notification when reservation is modified"""
        message = f"🔄 **Reservation Modified**\n"
        message += f"• Reservation ID: `{old_reservation.get('reservation_id', 'N/A')}`\n"
        message += f"• Client: {client_name}\n"
        message += f"• Modified at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Show changes
        changes = []
        
        # Date change
        if old_reservation.get('date') != new_reservation.get('date'):
            changes.append(f"📅 Date: {old_reservation.get('date', 'N/A')} → {new_reservation.get('date', 'N/A')}")
        
        # Time change
        old_time = f"{old_reservation.get('start_time', 'N/A')}~{old_reservation.get('end_time', 'N/A')}"
        new_time = f"{new_reservation.get('start_time', 'N/A')}~{new_reservation.get('end_time', 'N/A')}"
        if old_time != new_time:
            changes.append(f"⏰ Time: {old_time} → {new_time}")
        
        # Service change
        if old_reservation.get('service') != new_reservation.get('service'):
            changes.append(f"💇 Service: {old_reservation.get('service', 'N/A')} → {new_reservation.get('service', 'N/A')}")
        
        # Staff change
        if old_reservation.get('staff') != new_reservation.get('staff'):
            changes.append(f"👨‍💼 Staff: {old_reservation.get('staff', 'N/A')} → {new_reservation.get('staff', 'N/A')}")
        
        if changes:
            message += "**Changes:**\n" + "\n".join(f"• {change}" for change in changes)
        else:
            message += "• No changes detected"
        
        return self.send_notification(
            message=message,
            title="✏️ Reservation Modified",
            color="warning"
        )
    
    def notify_reservation_cancellation(self, reservation_data: Dict[str, Any], client_name: str) -> bool:
        """Send notification when reservation is cancelled"""
        message = f"❌ **Reservation Cancelled**\n"
        message += f"• Reservation ID: `{reservation_data.get('reservation_id', 'N/A')}`\n"
        message += f"• Client: {client_name}\n"
        message += f"• Date: {reservation_data.get('date', 'N/A')}\n"
        message += f"• Time: {reservation_data.get('start_time', 'N/A')}~{reservation_data.get('end_time', 'N/A')}\n"
        message += f"• Service: {reservation_data.get('service', 'N/A')}\n"
        message += f"• Staff: {reservation_data.get('staff', 'N/A')}\n"
        message += f"• Cancelled at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return self.send_notification(
            message=message,
            title="🚫 Reservation Cancelled",
            color="danger"
        )
    
    def _get_service_duration(self, service_name: str) -> int:
        """Get service duration in minutes"""
        try:
            # Load services data
            current_dir = os.path.dirname(os.path.abspath(__file__))
            services_file = os.path.join(current_dir, "data", "services.json")
            
            with open(services_file, 'r', encoding='utf-8') as f:
                services_data = json.load(f)
            
            service_info = services_data.get("services", {}).get(service_name, {})
            return service_info.get("duration", 0)
        except Exception:
            return 0
    
    def _get_service_price(self, service_name: str) -> int:
        """Get service price"""
        try:
            # Load services data
            current_dir = os.path.dirname(os.path.abspath(__file__))
            services_file = os.path.join(current_dir, "data", "services.json")
            
            with open(services_file, 'r', encoding='utf-8') as f:
                services_data = json.load(f)
            
            service_info = services_data.get("services", {}).get(service_name, {})
            return service_info.get("price", 0)
        except Exception:
            return 0


# Global instance for easy access
slack_notifier = SlackNotifier()


def send_user_login_notification(user_id: str, display_name: str) -> bool:
    """Convenience function for user login notifications"""
    return slack_notifier.notify_user_login(user_id, display_name)


def send_reservation_confirmation_notification(reservation_data: Dict[str, Any], client_name: str) -> bool:
    """Convenience function for reservation confirmation notifications"""
    return slack_notifier.notify_reservation_confirmation(reservation_data, client_name)


def send_reservation_modification_notification(old_reservation: Dict[str, Any], new_reservation: Dict[str, Any], client_name: str) -> bool:
    """Convenience function for reservation modification notifications"""
    return slack_notifier.notify_reservation_modification(old_reservation, new_reservation, client_name)


def send_reservation_cancellation_notification(reservation_data: Dict[str, Any], client_name: str) -> bool:
    """Convenience function for reservation cancellation notifications"""
    return slack_notifier.notify_reservation_cancellation(reservation_data, client_name)


if __name__ == "__main__":
    # Test the Slack notifier
    notifier = SlackNotifier()
    
    # Test notification
    test_message = "🧪 **Test Notification**\nThis is a test message from the salon booking system."
    success = notifier.send_notification(
        message=test_message,
        title="Test",
        color="good"
    )
    
    if success:
        print("✅ Test notification sent successfully!")
    else:
        print("❌ Failed to send test notification")
