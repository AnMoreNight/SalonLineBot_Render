"""
Google Calendar integration for salon reservations
"""
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import pytz
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

class GoogleCalendarHelper:
    def __init__(self):
        load_dotenv()
        self.calendar_id = os.getenv("GOOGLE_CALENDAR_ID")
        self.timezone = os.getenv("GOOGLE_CALENDAR_TIMEZONE", "Asia/Tokyo")
        self.service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

        self.service = None
        try:
            self._authenticate()
        except Exception as e:
            logging.error(f"Failed to initialize Google Calendar: {e}")
            self.service = None
    
    def _authenticate(self):
        """Authenticate with Google Calendar API using service account"""
        try:
            if not self.service_account_json:
                logging.warning("GOOGLE_SERVICE_ACCOUNT_JSON not set, calendar integration disabled")
                return
            
            # Parse service account JSON from environment variable
            try:
                service_account_info = json.loads(self.service_account_json)
            except json.JSONDecodeError as e:
                logging.error(f"Invalid JSON in GOOGLE_SERVICE_ACCOUNT_JSON: {e}")
                return
            
            # Load service account credentials from JSON
            credentials = service_account.Credentials.from_service_account_info(
                service_account_info,
                scopes=['https://www.googleapis.com/auth/calendar']
            )
            
            # Build the service
            self.service = build('calendar', 'v3', credentials=credentials)
            logging.info("Google Calendar API authenticated successfully")
            
        except Exception as e:
            logging.error(f"Failed to authenticate with Google Calendar: {e}")
            self.service = None
    
    def create_reservation_event(self, reservation_data: Dict[str, Any], client_name: str) -> bool:
        """
        Create a calendar event for a completed reservation
        
        Args:
            reservation_data: Dict containing service, staff, date, time
            client_name: Client's display name from LINE
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.service or not self.calendar_id:
            logging.warning("Google Calendar not configured, skipping event creation")
            return False

    def _get_service_duration_minutes(self, service_name: str) -> int:
        """Return duration in minutes for a given service name."""
        service_durations = {
            "カット": 60,
            "カラー": 120,
            "パーマ": 150,
            "トリートメント": 90
        }
        return service_durations.get(service_name, 60)

    def _find_upcoming_event_by_client(self, client_name: str, days_ahead: int = 90) -> Optional[Dict[str, Any]]:
        """Find the next upcoming event for the given client name.

        Tries to match by summary or description containing the client name.
        """
        if not self.service or not self.calendar_id:
            logging.warning("Google Calendar not configured, cannot search events")
            return None

        try:
            now = datetime.utcnow()
            end = now + timedelta(days=days_ahead)
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=now.isoformat() + 'Z',
                timeMax=end.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])
            for event in events:
                summary = event.get('summary', '') or ''
                description = event.get('description', '') or ''
                if client_name and (client_name in summary or client_name in description):
                    return event

            return None
        except Exception as e:
            logging.error(f"Failed to search events: {e}")
            return None

    def cancel_reservation(self, client_name: str) -> bool:
        """Delete the client's upcoming reservation event if found."""
        event = self._find_upcoming_event_by_client(client_name)
        if not event:
            return False
        try:
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event['id']
            ).execute()
            logging.info(f"Cancelled reservation for {client_name}")
            return True
        except Exception as e:
            logging.error(f"Failed to cancel reservation: {e}")
            return False

    def modify_reservation_time(self, client_name: str, new_date: str, new_time: str) -> bool:
        """Update the start/end time for the client's upcoming reservation.

        Keeps other event fields intact; infers duration from summary/description if possible,
        otherwise defaults to 60 minutes.
        """
        event = self._find_upcoming_event_by_client(client_name)
        if not event:
            return False

        # Infer service name from summary like "[予約] カット - Name (Staff)"
        summary = event.get('summary', '')
        inferred_service = None
        try:
            # Extract the part between "[予約] " and " -"
            if summary.startswith("[予約]") and ' -' in summary:
                inferred_service = summary.replace("[予約] ", "", 1).split(" -", 1)[0].strip()
        except Exception:
            pass

        duration_minutes = self._get_service_duration_minutes(inferred_service or "")

        try:
            start_dt = datetime.strptime(f"{new_date} {new_time}", "%Y-%m-%d %H:%M")
            end_dt = start_dt + timedelta(minutes=duration_minutes)
            start_iso = start_dt.isoformat()
            end_iso = end_dt.isoformat()

            event['start'] = {
                'dateTime': start_iso,
                'timeZone': self.timezone,
            }
            event['end'] = {
                'dateTime': end_iso,
                'timeZone': self.timezone,
            }

            updated = self.service.events().update(
                calendarId=self.calendar_id,
                eventId=event['id'],
                body=event
            ).execute()

            logging.info(f"Modified reservation time for {client_name}: {updated.get('htmlLink')}")
            return True
        except Exception as e:
            logging.error(f"Failed to modify reservation time: {e}")
            return False
        
        try:
            # Parse date and time
            date_str = reservation_data['date']
            time_str = reservation_data['time']
            service = reservation_data['service']
            staff = reservation_data['staff']
            
            # Calculate start datetime
            start_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            
            # Get service duration (in minutes)
            service_durations = {
                "カット": 60,
                "カラー": 120,
                "パーマ": 150,
                "トリートメント": 90
            }
            duration_minutes = service_durations.get(service, 60)
            
            # Calculate end datetime
            end_datetime = start_datetime + timedelta(minutes=duration_minutes)
            
            # Format for Google Calendar API
            start_iso = start_datetime.isoformat()
            end_iso = end_datetime.isoformat()
            
            # Build event details
            event_title = f"[予約] {service} - {client_name} ({staff})"
            
            # Get location from KB data if available
            # location = self._get_location_from_kb()
            
            # Build description
            description = f"""
サービス: {service}
担当者: {staff}
お客様: {client_name}
所要時間: {duration_minutes}分
予約元: LINE Bot
            """.strip()
            
            # Create event
            event = {
                'summary': event_title,
                'description': description,
                'start': {
                    'dateTime': start_iso,
                    'timeZone': self.timezone,
                },
                'end': {
                    'dateTime': end_iso,
                    'timeZone': self.timezone,
                },
                # 'location': location,
                # 'reminders': {
                #     'useDefault': False,
                #     'overrides': [
                #         {'method': 'popup', 'minutes': 30},
                #         {'method': 'popup', 'minutes': 60},
                #     ],
                # },
            }
            
            # Add staff as attendee if not "未指定"
            if staff != "未指定":
                staff_email = self._get_staff_email(staff)
                if staff_email:
                    event['attendees'] = [{'email': staff_email}]
            
            # Create the event
            created_event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event
            ).execute()
            
            logging.info(f"Calendar event created: {created_event.get('htmlLink')}")
            return True
            
        except HttpError as e:
            logging.error(f"Google Calendar API error: {e}")
            return False
        except Exception as e:
            logging.error(f"Failed to create calendar event: {e}")
            return False
    
    # def _get_location_from_kb(self) -> str:
    #     """Get location from KB data"""
    #     try:
    #         with open("api/data/kb.json", 'r', encoding='utf-8') as f:
    #             kb_data = json.load(f)
            
    #         for item in kb_data:
    #             if item.get('キー') == 'ADDRESS':
    #                 return item.get('例（置換値）', '')
            
    #         return ""
    #     except Exception as e:
    #         logging.warning(f"Could not load location from KB: {e}")
    #         return ""
    
    def get_available_slots(self, start_date: datetime, end_date: datetime) -> list:
        """
        Get available time slots from Google Calendar
        
        Args:
            start_date: Start date to check availability
            end_date: End date to check availability
            
        Returns:
            list: List of available time slots
        """
        if not self.service or not self.calendar_id:
            logging.warning("Google Calendar not configured, using fallback slots")
            return self._generate_fallback_slots(start_date, end_date)
        
        try:
            # Get events from calendar
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=start_date.isoformat() + 'Z',
                timeMax=end_date.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Generate only available (unselected) slots
            available_slots = self._generate_all_slots(start_date, end_date, events)
            
            return available_slots
            
        except Exception as e:
            logging.error(f"Failed to get available slots from Google Calendar: {e}")
            return self._generate_fallback_slots(start_date, end_date)
    
    def _generate_all_slots(self, start_date: datetime, end_date: datetime, events: list = None) -> list:
        """Generate only unselected (available) time slots for the given date range"""
        slots = []
        current_date = start_date.date()
        end_date_only = end_date.date()
        
        # Business hours: 9:00 to 17:00 (9 AM to 5 PM)
        business_hours = list(range(9, 18))  # 9:00 to 17:00
        
        while current_date <= end_date_only:
            # Skip Sundays (weekday 6)
            if current_date.weekday() != 6:
                for hour in business_hours:
                    # Skip lunch break (12:00-13:00)
                    if hour == 12:
                        continue
                    
                    slot_start = datetime.combine(current_date, datetime.min.time().replace(hour=hour))
                    slot_end = slot_start + timedelta(minutes=60)  # Default 60-minute slots
                    
                    # Make slot times timezone-aware using the configured timezone
                    tz = pytz.timezone(self.timezone)
                    slot_start = tz.localize(slot_start)
                    slot_end = tz.localize(slot_end)
                    
                    # Check if slot conflicts with any event
                    is_available = True
                    if events:
                        for event in events:
                            event_start = datetime.fromisoformat(event['start'].get('dateTime', event['start'].get('date', '')))
                            event_end = datetime.fromisoformat(event['end'].get('dateTime', event['end'].get('date', '')))
                            
                            # Check for overlap
                            if (slot_start < event_end and slot_end > event_start):
                                is_available = False
                                break
                    
                    # Only add available slots
                    if is_available:
                        slots.append({
                            "date": current_date.strftime("%Y-%m-%d"),
                            "time": f"{hour:02d}:00:00",
                            "available": True
                        })
            
            current_date += timedelta(days=1)
        
        return slots
    
    def _generate_fallback_slots(self, start_date: datetime, end_date: datetime) -> list:
        """Generate fallback slots when Google Calendar is not available"""
        return self._generate_all_slots(start_date, end_date, None)
    
    def get_calendar_url(self) -> str:
        """Get the public Google Calendar URL for viewing availability"""
        if not self.calendar_id:
            return "https://calendar.google.com/calendar"
        
        # Create a public calendar URL
        # Format: https://calendar.google.com/calendar/embed?src=CALENDAR_ID
        return f"https://calendar.google.com/calendar/embed?src={self.calendar_id}"
    
    def _get_staff_email(self, staff_name: str) -> Optional[str]:
        """Get staff email from mapping"""
        staff_emails = {
            "田中": os.getenv("STAFF_TANAKA_EMAIL"),
            "佐藤": os.getenv("STAFF_SATO_EMAIL"),
            "山田": os.getenv("STAFF_YAMADA_EMAIL"),
        }
        return staff_emails.get(staff_name)

