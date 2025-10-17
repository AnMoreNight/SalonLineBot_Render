"""
Reminder system for salon booking system
Sends reminder messages to users about their reservations the day before
"""
import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv

class ReminderSystem:
    def __init__(self):
        load_dotenv()
        self.line_channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
        self.enabled = bool(self.line_channel_access_token)
        
        if not self.enabled:
            logging.warning("LINE Channel Access Token not configured. Reminder system disabled.")
        else:
            print("Reminder system enabled")
    
    def get_tomorrow_reservations(self) -> List[Dict[str, Any]]:
        """Get all reservations for tomorrow (Tokyo timezone)"""
        try:
            from api.google_calendar import GoogleCalendarHelper
            from api.google_sheets_logger import GoogleSheetsLogger
            
            # Get tomorrow's date in Tokyo timezone
            import pytz
            tokyo_tz = pytz.timezone('Asia/Tokyo')
            tomorrow = (datetime.now(tokyo_tz) + timedelta(days=1)).strftime("%Y-%m-%d")
            print(f"Getting reservations for tomorrow: {tomorrow} (Tokyo timezone)")
            
            # Get reservations from Google Calendar
            calendar_helper = GoogleCalendarHelper()
            events = calendar_helper.get_events_for_date(tomorrow)
            
            # Parse reservations from events
            reservations = []
            for event in events:
                reservation = self._parse_event_to_reservation(event)
                if reservation:
                    reservations.append(reservation)
            
            # Also get from Google Sheets as backup
            try:
                sheets_logger = GoogleSheetsLogger()
                sheets_reservations = sheets_logger.get_reservations_for_date(tomorrow)
                
                # Merge and deduplicate
                existing_ids = {r.get('reservation_id') for r in reservations}
                for sheet_res in sheets_reservations:
                    if sheet_res.get('reservation_id') not in existing_ids:
                        reservations.append(sheet_res)
                        
            except Exception as e:
                logging.warning(f"Could not get reservations from sheets: {e}")
            
            print(f"Found {len(reservations)} reservations for {tomorrow}")
            return reservations
            
        except Exception as e:
            logging.error(f"Error getting tomorrow's reservations: {e}")
            return []
    
    def _parse_event_to_reservation(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse Google Calendar event to reservation format"""
        try:
            summary = event.get('summary', '')
            description = event.get('description', '')
            start_time = event.get('start', {}).get('dateTime', '')
            end_time = event.get('end', {}).get('dateTime', '')
            
            # Extract reservation ID from description
            reservation_id = None
            if '予約ID:' in description:
                reservation_id = description.split('予約ID:')[1].split('\n')[0].strip()
            
            # Parse summary format: "[予約] SERVICE - CLIENT (STAFF)"
            import re
            match = re.search(r"^\[予約\] (.+) - (.+) \((.+)\)$", summary)
            if not match:
                return None
            
            service = match.group(1)
            client_name = match.group(2)
            staff = match.group(3)
            
            # Parse datetime
            if start_time:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                # Convert to local time
                import pytz
                tz = pytz.timezone('Asia/Tokyo')
                start_dt = start_dt.astimezone(tz)
                
                date = start_dt.strftime("%Y-%m-%d")
                start_time_str = start_dt.strftime("%H:%M")
                
                if end_time:
                    end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                    end_dt = end_dt.astimezone(tz)
                    end_time_str = end_dt.strftime("%H:%M")
                else:
                    end_time_str = ""
                
                return {
                    'reservation_id': reservation_id,
                    'date': date,
                    'start_time': start_time_str,
                    'end_time': end_time_str,
                    'service': service,
                    'staff': staff,
                    'client_name': client_name
                }
            
            return None
            
        except Exception as e:
            logging.error(f"Error parsing event to reservation: {e}")
            return None
    
    def _load_kb_data(self) -> Dict[str, str]:
        """Load data from kb.json file"""
        try:
            # Try multiple possible paths for different deployment environments
            possible_paths = []
            
            # Try different base directories
            base_dirs = [
                os.path.dirname(os.path.abspath(__file__)),  # Current module directory
                os.getcwd(),  # Current working directory
                os.path.join(os.getcwd(), 'api'),  # api subdirectory of working directory
            ]
            
            for base_dir in base_dirs:
                possible_paths.append(os.path.join(base_dir, "data", "kb.json"))
                possible_paths.append(os.path.join(base_dir, "api", "data", "kb.json"))
                # Try with uppercase KB.json (for Render deployment)
                possible_paths.append(os.path.join(base_dir, "data", "KB.json"))
                possible_paths.append(os.path.join(base_dir, "api", "data", "KB.json"))
            
            # Debug: Print all attempted paths and their status
            print(f"DEBUG: Attempting to load KB data in ReminderSystem")
            for kb_file in possible_paths:
                exists = os.path.exists(kb_file)
                is_file = os.path.isfile(kb_file) if exists else False
                print(f"DEBUG: Path: {kb_file} - Exists: {exists}, IsFile: {is_file}")
            
            # Try each possible path
            for kb_file in possible_paths:
                try:
                    if not os.path.exists(kb_file):
                        print(f"DEBUG: Path does not exist: {kb_file}")
                        continue
                    
                    if not os.path.isfile(kb_file):
                        print(f"DEBUG: Path is not a file: {kb_file}")
                        continue
                    
                    print(f"DEBUG: Attempting to open: {kb_file}")
                    with open(kb_file, 'r', encoding='utf-8') as f:
                        kb_data = json.load(f)
                    
                    print(f"DEBUG: Successfully loaded KB data from: {kb_file}")
                    
                    # Convert array format to dictionary
                    kb_dict = {}
                    for item in kb_data:
                        key = item.get('キー', '')
                        value = item.get('例（置換値）', '')
                        kb_dict[key] = value
                    
                    return kb_dict
                except (FileNotFoundError, OSError) as e:
                    print(f"DEBUG: Failed to load from {kb_file}: {e}")
                    continue
                except json.JSONDecodeError as e:
                    print(f"DEBUG: JSON decode error from {kb_file}: {e}")
                    continue
            
            # If none of the paths worked, raise an error
            raise FileNotFoundError(f"Could not find kb.json file. Tried paths: {possible_paths}")
            
        except Exception as e:
            logging.error(f"Error loading kb.json: {e}")
            return {}
    
    def _get_service_duration(self, service_name: str) -> str:
        """Get service duration in minutes"""
        try:
            # Load services data
            current_dir = os.path.dirname(os.path.abspath(__file__))
            services_file = os.path.join(current_dir, "data", "services.json")
            
            with open(services_file, 'r', encoding='utf-8') as f:
                services_data = json.load(f)
            
            service_info = services_data.get("services", {}).get(service_name, {})
            duration = service_info.get("duration", 0)
            return f"{duration}分"
        except Exception:
            return "N/A"
    
    def send_reminder_to_user(self, reservation: Dict[str, Any], user_id: str) -> bool:
        """Send reminder message to a specific user"""
        try:
            # Load KB data
            kb_data = self._load_kb_data()
            
            # Get reservation details
            user_name = reservation.get('client_name', 'N/A')
            reservation_date = reservation.get('date', 'N/A')
            start_time = reservation.get('start_time', 'N/A')
            service = reservation.get('service', 'N/A')
            staff = reservation.get('staff', 'N/A')
            duration = self._get_service_duration(service)
            
            # Get KB data with fallbacks
            cancel_deadline = kb_data.get('CANCEL_POLICY', '来店の2時間前まで')
            salon_phone = kb_data.get('PHONE', '03-1234-5678')
            salon_name = kb_data.get('SALON_NAME', 'SalonAI 表参道店')
            
            # Prepare reminder message using the template format
            message = f"{user_name} 様\n"
            message += f"明日（{reservation_date}）{start_time} から {service}（担当：{staff}）のご予約です。\n\n"
            message += f"・所要時間：{duration}\n"
            message += f"・変更／キャンセル：変更・キャンセルされる場合は{cancel_deadline}までに「時間を変更したい」「予約をキャンセル」したいとお送りして指示に従ってください。\n\n"
            message += f"内容の確認：\n"
            message += f"ご不明点は {salon_phone} まで。{salon_name}"
            
            # Send LINE message
            payload = {
                "to": user_id,
                "messages": [
                    {
                        "type": "text",
                        "text": message
                    }
                ]
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.line_channel_access_token}'
            }
            
            response = requests.post(
                'https://api.line.me/v2/bot/message/push',
                data=json.dumps(payload),
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"Reminder sent successfully to user {user_id} for reservation {reservation.get('reservation_id')}")
                return True
            else:
                logging.error(f"Failed to send reminder to user {user_id}: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logging.error(f"Error sending reminder to user {user_id}: {e}")
            return False
    
    def get_user_id_for_reservation(self, reservation: Dict[str, Any]) -> Optional[str]:
        """Get LINE user ID for a reservation"""
        try:
            # Try to get user ID from Google Sheets
            from api.google_sheets_logger import GoogleSheetsLogger
            sheets_logger = GoogleSheetsLogger()
            
            reservation_id = reservation.get('reservation_id')
            if reservation_id:
                user_id = sheets_logger.get_user_id_for_reservation(reservation_id)
                if user_id:
                    return user_id
            
            # If not found in sheets, we might need to implement a user mapping system
            # For now, return None (this would need to be enhanced based on your user tracking)
            logging.warning(f"Could not find user ID for reservation {reservation_id}")
            return None
            
        except Exception as e:
            logging.error(f"Error getting user ID for reservation: {e}")
            return None
    
    def send_reminder_notification_to_manager(self, success_count: int, total_count: int, failed_reservations: List[Dict[str, Any]]) -> bool:
        """Send notification to manager about reminder status"""
        try:
            from api.notification_manager import notification_manager
            
            # Use the notification manager to send reminder status
            return notification_manager.notify_reminder_status(success_count, total_count, failed_reservations)
            
        except Exception as e:
            logging.error(f"Error sending reminder notification to manager: {e}")
            return False
    
    
    def run_daily_reminders(self) -> Dict[str, Any]:
        """Run daily reminder process"""
        print("Starting daily reminder process...")
        
        # Get tomorrow's reservations
        reservations = self.get_tomorrow_reservations()
        
        success_count = 0
        failed_reservations = []
        
        # Send reminders to each user
        for reservation in reservations:
            user_id = self.get_user_id_for_reservation(reservation)
            
            if user_id:
                if self.send_reminder_to_user(reservation, user_id):
                    success_count += 1
                else:
                    failed_reservations.append(reservation)
            else:
                logging.warning(f"Could not find user ID for reservation {reservation.get('reservation_id')}")
                failed_reservations.append(reservation)
        
        # Send notification to manager
        self.send_reminder_notification_to_manager(success_count, len(reservations), failed_reservations)
        
        result = {
            'success_count': success_count,
            'total_count': len(reservations),
            'failed_reservations': failed_reservations
        }
        
        print(f"Daily reminder process completed: {success_count}/{len(reservations)} sent successfully")
        return result


# Global instance
reminder_system = ReminderSystem()


def run_daily_reminders():
    """Convenience function to run daily reminders"""
    return reminder_system.run_daily_reminders()


