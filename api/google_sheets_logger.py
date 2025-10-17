import os
import json
import logging
from datetime import datetime
import re
from typing import Optional, Dict, Any, List
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv
import pytz


class GoogleSheetsLogger:
    """Logger for saving bot interactions to Google Sheets
    
    This class handles two separate functionalities:
    1. Message logging (saved to main Sheet1)
    2. Reservation management (saved to separate Reservations sheet)
    """
    
    def __init__(self):
        self.message_worksheet = None  # For message logging (Sheet1)
        self.reservations_worksheet = None  # For reservation data (Reservations sheet)
        self.users_worksheet = None  # For user data (Users sheet)
        self.tokyo_tz = pytz.timezone('Asia/Tokyo')
        self._setup_connection()
    
    def _get_tokyo_timestamp(self) -> str:
        """Get current timestamp in Tokyo timezone"""
        tokyo_time = datetime.now(self.tokyo_tz)
        return tokyo_time.strftime("%Y-%m-%d %H:%M:%S")
    
    def _setup_connection(self):
        """Setup Google Sheets connection for both message logging and reservations"""
        load_dotenv()
        try:
            # Get credentials from environment variable
            credentials_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
            if not credentials_json:
                logging.warning("GOOGLE_SERVICE_ACCOUNT_JSON not found. Google Sheets logging disabled.")
                return
            
            # Parse credentials
            credentials_info = json.loads(credentials_json)
            
            # Setup scope for Google Sheets
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # Create credentials
            creds = ServiceAccountCredentials.from_json_keyfile_dict(
                credentials_info, scope
            )
            
            # Authorize and create client
            gc = gspread.authorize(creds)
            
            # Get spreadsheet
            spreadsheet_id = os.getenv("GOOGLE_SHEET_ID")
            if not spreadsheet_id:
                logging.warning("GOOGLE_SHEET_ID not found. Google Sheets logging disabled.")
                return
            
            spreadsheet = gc.open_by_key(spreadsheet_id)
            
            # Setup message logging worksheet (Sheet1)
            self.message_worksheet = spreadsheet.sheet1
            
            # Define expected headers to avoid duplicate header issues
            expected_headers = [
                "Timestamp",
                "User ID",
                "User Name", 
                "Message Type",
                "User Message",
                "Bot Response",
                "Action Type",
                "Reservation Data",
                "KB Category",
                "Processing Time (ms)"
            ]
            
            try:
                # Try to get records with expected headers
                records = self.message_worksheet.get_all_records(expected_headers=expected_headers)
                if not records:
                    self._setup_message_headers()
            except Exception as header_error:
                logging.warning(f"Header issue detected, attempting to fix: {header_error}")
                # Clear the worksheet and reset headers
                self.message_worksheet.clear()
                self._setup_message_headers()
            
            # Setup reservations worksheet (separate sheet)
            self.reservations_worksheet = self._get_reservations_worksheet()
            
            # Setup users worksheet (separate sheet)
            self.users_worksheet = self._get_users_worksheet()
            
            print("Google Sheets logger initialized successfully")
            print("Message logging: Sheet1, Reservation data: Reservations sheet, User data: Users sheet")
            
        except Exception as e:
            logging.error(f"Failed to setup Google Sheets connection: {e}")
            self.message_worksheet = None
            self.reservations_worksheet = None
            self.users_worksheet = None
    
    def _setup_message_headers(self):
        """Setup column headers for message logging in Sheet1"""
        if not self.message_worksheet:
            return
        
        headers = [
            "Timestamp",
            "User ID",
            "User Name", 
            "Message Type",
            "User Message",
            "Bot Response",
            "Action Type",
            "Reservation Data",
            "KB Category",
            "Processing Time (ms)"
        ]
        
        try:
            self.message_worksheet.append_row(headers)
            print("Message logging headers setup completed in Sheet1")
        except Exception as e:
            logging.error(f"Failed to setup message headers: {e}")
    
    def log_message(self, 
                   user_id: str,
                   user_message: str,
                   bot_response: str,
                   user_name: str = "",
                   message_type: str = "text",
                   action_type: str = "message",
                   reservation_data: Optional[Dict[str, Any]] = None,
                   kb_category: Optional[str] = None,
                   processing_time: Optional[float] = None):
        """Log a message interaction to Google Sheets (Sheet1)"""
        
        if not self.message_worksheet:
            logging.warning("Message logging worksheet not available. Skipping log.")
            return
        
        try:
            # Prepare data for logging
            timestamp = self._get_tokyo_timestamp()
            
            # Convert reservation data to string if present
            reservation_str = ""
            if reservation_data:
                reservation_str = json.dumps(reservation_data, ensure_ascii=False)
            
            # Prepare row data
            row_data = [
                timestamp,
                user_id,
                user_name,
                message_type,
                user_message,
                bot_response,
                action_type,
                reservation_str,
                kb_category or "",
                f"{processing_time:.2f}" if processing_time else ""
            ]
            
            # Append to message logging worksheet (Sheet1)
            self.message_worksheet.append_row(row_data)
            print(f"Logged message interaction for user {user_id} to Sheet1")
            
        except Exception as e:
            logging.error(f"Failed to log message to Google Sheets: {e}")
    
    def log_reservation_action(self,
                             user_id: str,
                             action: str,
                             user_name: str = "",
                             reservation_data: Optional[Dict[str, Any]] = None,
                             user_message: str = "",
                             bot_response: str = ""):
        """Log reservation-specific actions"""
        
        self.log_message(
            user_id=user_id,
            user_message=user_message,
            bot_response=bot_response,
            user_name=user_name,
            message_type="reservation",
            action_type=action,
            reservation_data=reservation_data
        )
    
    def log_faq_interaction(self,
                           user_id: str,
                           user_message: str,
                           bot_response: str,
                           user_name: str = "",
                           kb_category: str = "",
                           processing_time: Optional[float] = None):
        """Log FAQ interactions"""
        
        self.log_message(
            user_id=user_id,
            user_message=user_message,
            bot_response=bot_response,
            user_name=user_name,
            message_type="faq",
            action_type="knowledge_base",
            kb_category=kb_category,
            processing_time=processing_time
        )
    
    def log_error(self,
                 user_id: str,
                 error_message: str,
                 user_name: str = "",
                 user_message: str = "",
                 bot_response: str = ""):
        """Log error interactions"""
        
        self.log_message(
            user_id=user_id,
            user_message=user_message,
            bot_response=bot_response,
            user_name=user_name,
            message_type="error",
            action_type="error",
            kb_category="error"
        )
    
    def _get_reservations_worksheet(self):
        """Get or create the reservations worksheet"""
        if self.reservations_worksheet:
            return self.reservations_worksheet
            
        try:
            load_dotenv()
            credentials_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
            if not credentials_json:
                return None
            
            credentials_info = json.loads(credentials_json)
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            creds = ServiceAccountCredentials.from_json_keyfile_dict(
                credentials_info, scope
            )
            gc = gspread.authorize(creds)
            
            spreadsheet_id = os.getenv("GOOGLE_SHEET_ID")
            if not spreadsheet_id:
                return None
            
            spreadsheet = gc.open_by_key(spreadsheet_id)
            
            # Try to get existing reservations worksheet
            try:
                reservations_worksheet = spreadsheet.worksheet("Reservations")
                print("Found existing Reservations worksheet")
                
                # Check and fix headers if needed
                expected_headers = [
                    "Timestamp",
                    "Reservation ID", 
                    "User ID",
                    "Client Name",
                    "Date",
                    "Start Time",
                    "End Time",
                    "Service",
                    "Staff",
                    "Duration (min)",
                    "Price",
                    "Status"
                ]
                
                try:
                    records = reservations_worksheet.get_all_records(expected_headers=expected_headers)
                    if not records:
                        self._setup_reservations_headers(reservations_worksheet)
                except Exception as header_error:
                    print(f"Header issue detected in Reservations sheet, attempting to fix: {header_error}")
                    reservations_worksheet.clear()
                    self._setup_reservations_headers(reservations_worksheet)
                    
            except gspread.WorksheetNotFound:
                # Create new reservations worksheet
                reservations_worksheet = spreadsheet.add_worksheet(
                    title="Reservations", 
                    rows=1000, 
                    cols=12
                )
                # Setup headers for reservations
                self._setup_reservations_headers(reservations_worksheet)
                print("Created new Reservations worksheet")
            
            # Store the worksheet for future use
            self.reservations_worksheet = reservations_worksheet
            return reservations_worksheet
            
        except Exception as e:
            logging.error(f"Failed to get reservations worksheet: {e}")
            return None
    
    def _get_users_worksheet(self):
        """Get or create the users worksheet"""
        if self.users_worksheet:
            return self.users_worksheet
            
        try:
            load_dotenv()
            credentials_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
            if not credentials_json:
                return None
            
            credentials_info = json.loads(credentials_json)
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            creds = ServiceAccountCredentials.from_json_keyfile_dict(
                credentials_info, scope
            )
            gc = gspread.authorize(creds)
            
            spreadsheet_id = os.getenv("GOOGLE_SHEET_ID")
            if not spreadsheet_id:
                return None
            
            spreadsheet = gc.open_by_key(spreadsheet_id)
            
            # Try to get existing users worksheet
            try:
                users_worksheet = spreadsheet.worksheet("Users")
                # Check if headers are set up correctly
                existing_records = users_worksheet.get_all_records()
                if not existing_records or not self._has_correct_headers(existing_records):
                    print("Users worksheet exists but headers need setup")
                    # Clear the worksheet and set up headers properly
                    users_worksheet.clear()
                    self._setup_users_headers(users_worksheet)
            except gspread.WorksheetNotFound:
                # Create new users worksheet
                users_worksheet = spreadsheet.add_worksheet(
                    title="Users", 
                    rows=1000, 
                    cols=10
                )
                # Setup headers for users
                self._setup_users_headers(users_worksheet)
            
            # Store the worksheet for future use
            self.users_worksheet = users_worksheet
            return users_worksheet
            
        except Exception as e:
            logging.error(f"Failed to get users worksheet: {e}")
            return None
    
    def _has_correct_headers(self, records: list) -> bool:
        """Check if the Users worksheet has the correct headers"""
        if not records:
            return False
        
        # Get the first record (which should be the headers)
        first_record = records[0]
        expected_headers = [
            "Timestamp",
            "User ID",
            "Display Name",
            "Phone Number",
            "Status",
            "Notes",
            "Consented",
            "Consent Date",
            "First Seen",
            "Last Seen"
        ]
        
        # Check if all expected headers are present
        for header in expected_headers:
            if header not in first_record:
                return False
        
        return True
    
    def _setup_users_headers(self, worksheet):
        """Setup headers for the users worksheet"""
        headers = [
            "Timestamp",
            "User ID",
            "Display Name",
            "Phone Number",
            "Status",
            "Notes",
            "Consented",
            "Consent Date",
            "First Seen",
            "Last Seen"
        ]
        worksheet.append_row(headers)
        print("Users worksheet headers set up successfully")
    
    def _setup_reservations_headers(self, worksheet):
        """Setup headers for the reservations worksheet"""
        headers = [
            "Timestamp",
            "Reservation ID",
            "User ID",
            "Client Name",
            "Date",
            "Start Time",
            "End Time",
            "Service",
            "Staff",
            "Duration (min)",
            "Price",
            "Status"
        ]
        
        try:
            # Check if headers already exist
            existing_records = worksheet.get_all_records()
            if not existing_records:
                # Only add headers if worksheet is empty
                worksheet.append_row(headers)
                print("Reservations worksheet headers setup completed")
            else:
                print("Reservations worksheet headers already exist")
        except Exception as e:
            logging.error(f"Failed to setup reservations headers: {e}")
    
    def save_reservation(self, reservation_data: Dict[str, Any]) -> bool:
        """Save a new reservation to the reservations worksheet"""
        reservations_worksheet = self._get_reservations_worksheet()
        if not reservations_worksheet:
            return False
        
        try:
            # Get Tokyo timezone timestamp
            timestamp = self._get_tokyo_timestamp()
            
            row_data = [
                timestamp,  # Add timestamp as first column
                reservation_data.get("reservation_id", ""),
                reservation_data.get("user_id", ""),  # Add user ID column
                reservation_data.get("client_name", ""),
                reservation_data.get("date", ""),
                reservation_data.get("start_time", ""),
                reservation_data.get("end_time", ""),
                reservation_data.get("service", ""),
                reservation_data.get("staff", ""),
                reservation_data.get("duration", ""),
                reservation_data.get("price", ""),
                "Confirmed"  # Default status
            ]
            
            reservations_worksheet.append_row(row_data)
            print(f"Saved reservation {reservation_data.get('reservation_id')} to Google Sheets")
            return True
            
        except Exception as e:
            logging.error(f"Failed to save reservation to Google Sheets: {e}")
            return False
    
    def get_all_reservations(self) -> list:
        """Get all reservations from the reservations worksheet"""
        reservations_worksheet = self._get_reservations_worksheet()
        if not reservations_worksheet:
            return []
        
        try:
            # Define expected headers to avoid duplicate header issues
            expected_headers = [
                "Timestamp",
                "Reservation ID", 
                "User ID",
                "Client Name",
                "Date",
                "Start Time",
                "End Time",
                "Service",
                "Staff",
                "Duration (min)",
                "Price",
                "Status"
            ]
            
            records = reservations_worksheet.get_all_records(expected_headers=expected_headers)
            # Filter out header row and return only confirmed reservations
            reservations = []
            for record in records:
                if record.get("Reservation ID") and record.get("Status") == "Confirmed":
                    reservations.append({
                        "reservation_id": record.get("Reservation ID"),
                        "client_name": record.get("Client Name"),
                        "date": record.get("Date"),
                        "start_time": record.get("Start Time"),
                        "end_time": record.get("End Time"),
                        "service": record.get("Service"),
                        "staff": record.get("Staff"),
                        "duration": record.get("Duration (min)"),
                        "price": record.get("Price"),
                        "status": record.get("Status")
                    })
            return reservations
            
        except Exception as e:
            logging.error(f"Failed to get reservations from Google Sheets: {e}")
            return []
    
    def get_user_reservations(self, client_name: str) -> list:
        """Get reservations for a specific client"""
        all_reservations = self.get_all_reservations()
        return [res for res in all_reservations if res["client_name"] == client_name]
    
    def update_reservation_status(self, reservation_id: str, status: str) -> bool:
        """Update the status of a reservation"""
        reservations_worksheet = self._get_reservations_worksheet()
        if not reservations_worksheet:
            return False
        
        try:
            # Define expected headers to avoid duplicate header issues
            expected_headers = [
                "Timestamp",
                "Reservation ID", 
                "User ID",
                "Client Name",
                "Date",
                "Start Time",
                "End Time",
                "Service",
                "Staff",
                "Duration (min)",
                "Price",
                "Status"
            ]
            
            # Find the row with the reservation ID
            records = reservations_worksheet.get_all_records(expected_headers=expected_headers)
            for i, record in enumerate(records, 2):  # Start from row 2 (skip header)
                if record.get("Reservation ID") == reservation_id:
                    # Update the status in column L (12th column)
                    reservations_worksheet.update_cell(i, 12, status)
                    print(f"Updated reservation {reservation_id} status to {status}")
                    return True
            
            logging.warning(f"Reservation {reservation_id} not found for status update")
            return False
            
        except Exception as e:
            logging.error(f"Failed to update reservation status: {e}")
            return False
    
    def get_reservation_by_id(self, reservation_id: str) -> Optional[Dict[str, Any]]:
        """Get reservation details by reservation ID"""
        reservations_worksheet = self._get_reservations_worksheet()
        if not reservations_worksheet:
            return None
        
        try:
            expected_headers = [
                "Timestamp",
                "Reservation ID", 
                "User ID",
                "Client Name",
                "Date",
                "Start Time",
                "End Time",
                "Service",
                "Staff",
                "Duration (min)",
                "Price",
                "Status"
            ]
            
            records = reservations_worksheet.get_all_records(expected_headers=expected_headers)
            for record in records:
                if record.get("Reservation ID") == reservation_id:
                    return {
                        "reservation_id": record.get("Reservation ID"),
                        "user_id": record.get("User ID"),
                        "client_name": record.get("Client Name"),
                        "date": record.get("Date"),
                        "start_time": record.get("Start Time"),
                        "end_time": record.get("End Time"),
                        "service": record.get("Service"),
                        "staff": record.get("Staff"),
                        "duration": record.get("Duration (min)"),
                        "price": record.get("Price"),
                        "status": record.get("Status")
                    }
            
            return None
            
        except Exception as e:
            logging.error(f"Failed to get reservation by ID: {e}")
            return None
    
    def update_reservation_data(self, reservation_id: str, field_updates: Dict[str, Any]) -> bool:
        """Update specific fields of a reservation"""
        reservations_worksheet = self._get_reservations_worksheet()
        if not reservations_worksheet:
            return False
        
        try:
            expected_headers = [
                "Timestamp",
                "Reservation ID", 
                "User ID",
                "Client Name",
                "Date",
                "Start Time",
                "End Time",
                "Service",
                "Staff",
                "Duration (min)",
                "Price",
                "Status"
            ]
            
            # Find the row with the reservation ID
            records = reservations_worksheet.get_all_records(expected_headers=expected_headers)
            for i, record in enumerate(records, 2):  # Start from row 2 (skip header)
                if record.get("Reservation ID") == reservation_id:
                    # Update specific fields
                    for field, value in field_updates.items():
                        if field in expected_headers:
                            column_index = expected_headers.index(field) + 1  # 1-based indexing
                            reservations_worksheet.update_cell(i, column_index, value)
                    
                    print(f"Updated reservation {reservation_id} with fields: {list(field_updates.keys())}")
                    return True
            
            logging.warning(f"Reservation {reservation_id} not found for data update")
            return False
            
        except Exception as e:
            logging.error(f"Failed to update reservation data: {e}")
            return False
    
    def get_reservations_for_date(self, date_str: str) -> List[Dict[str, Any]]:
        """Get all reservations for a specific date"""
        if not self.reservations_worksheet:
            logging.warning("Reservations worksheet not available")
            return []
        
        try:
            # Define expected headers
            expected_headers = [
                "Timestamp",
                "Reservation ID", 
                "User ID",
                "Client Name",
                "Date",
                "Start Time",
                "End Time",
                "Service",
                "Staff",
                "Duration (min)",
                "Price",
                "Status"
            ]
            
            # Get all records with expected headers
            records = self.reservations_worksheet.get_all_records(expected_headers=expected_headers)
            
            # Filter by date
            date_reservations = []
            for record in records:
                if record.get('Date') == date_str:
                    # Convert to our reservation format
                    reservation = {
                        'reservation_id': record.get('Reservation ID', ''),
                        'date': record.get('Date', ''),
                        'start_time': record.get('Start Time', ''),
                        'end_time': record.get('End Time', ''),
                        'service': record.get('Service', ''),
                        'staff': record.get('Staff', ''),
                        'client_name': record.get('Client Name', ''),
                        'user_id': record.get('User ID', ''),
                        'duration': record.get('Duration', ''),
                        'price': record.get('Price', '')
                    }
                    date_reservations.append(reservation)
            
            return date_reservations
            
        except Exception as e:
            logging.error(f"Error getting reservations for date {date_str}: {e}")
            return []
    
    def get_user_id_for_reservation(self, reservation_id: str) -> Optional[str]:
        """Get user ID for a specific reservation"""
        if not self.reservations_worksheet:
            logging.warning("Reservations worksheet not available")
            return None
        
        try:
            # Define expected headers
            expected_headers = [
                "Timestamp",
                "Reservation ID", 
                "User ID",
                "Client Name",
                "Date",
                "Start Time",
                "End Time",
                "Service",
                "Staff",
                "Duration (min)",
                "Price",
                "Status"
            ]
            
            # Get all records with expected headers
            records = self.reservations_worksheet.get_all_records(expected_headers=expected_headers)
            
            # Find the reservation
            for record in records:
                if record.get('Reservation ID') == reservation_id:
                    user_id = record.get('User ID', '')
                    return user_id if user_id else None
            
            logging.warning(f"Reservation {reservation_id} not found in sheets")
            return None
            
        except Exception as e:
            logging.error(f"Error getting user ID for reservation {reservation_id}: {e}")
            return None
    
    def log_new_user(self, user_id: str, display_name: str, phone_number: str = ""):
        """Log new user data to the Users sheet"""
        if not self.users_worksheet:
            logging.warning("Users worksheet not available. Cannot log user data.")
            # Try to get the worksheet again
            self.users_worksheet = self._get_users_worksheet()
            if not self.users_worksheet:
                logging.error("Failed to get Users worksheet after retry")
                return False
        
        try:
            print(f"Attempting to log new user: {display_name} ({user_id})")
            
            # Check if user already exists
            existing_records = self.users_worksheet.get_all_records()
            print(f"Found {len(existing_records)} existing records in Users sheet")
            
            for record in existing_records:
                if record.get('User ID') == user_id:
                    print(f"User {user_id} already exists in Users sheet")
                    return True
            
            # Prepare user data
            timestamp = self._get_tokyo_timestamp()
            user_data = [
                timestamp,                 # Timestamp
                user_id,                   # User ID
                display_name,              # Display Name
                phone_number,              # Phone Number
                "Active",                 # Status
                "Added via LINE Bot",     # Notes
                "No",                     # Consented (Yes/No)
                "",                       # Consent Date
                timestamp,                 # First Seen
                timestamp                  # Last Seen
            ]
            
            print(f"Adding user data: {user_data}")
            
            # Add user to sheet
            self.users_worksheet.append_row(user_data)
            print(f"Successfully logged new user: {display_name} ({user_id})")
            return True
            
        except Exception as e:
            logging.error(f"Failed to log user data: {e}")
            return False
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user data by user ID from Users sheet"""
        if not self.users_worksheet:
            return None
        
        try:
            records = self.users_worksheet.get_all_records()
            for record in records:
                if record.get('User ID') == user_id:
                    return record
            return None
            
        except Exception as e:
            logging.error(f"Error getting user by ID {user_id}: {e}")
            return None
    
    def update_user_status(self, user_id: str, status: str, notes: str = ""):
        """Update user status in Users sheet"""
        if not self.users_worksheet:
            return False
        
        try:
            records = self.users_worksheet.get_all_records()
            for i, record in enumerate(records, start=2):  # Start from row 2 (skip header)
                if record.get('User ID') == user_id:
                    # Update status
                    self.users_worksheet.update_cell(i, 5, status)  # Status column (5th)
                    if notes:
                        self.users_worksheet.update_cell(i, 6, notes)  # Notes column (6th)
                    
                    print(f"Updated user {user_id} status to: {status}")
                    return True
            logging.warning(f"User {user_id} not found for status update")
            return False
        except Exception as e:
            logging.error(f"Error updating user status: {e}")
            return False
    # -----------------------------
    # Users sheet consent/session helpers
    # -----------------------------
    def has_user_consented(self, user_id: str) -> bool:
        if not self.users_worksheet:
            return False
        try:
            records = self.users_worksheet.get_all_records()
            for record in records:
                if record.get('User ID') == user_id:
                    return str(record.get('Consented', 'No')).strip().lower() in ("yes", "true", "1", "y")
            return False
        except Exception as e:
            logging.error(f"Error checking consent for {user_id}: {e}")
            return False

    def mark_user_consented(self, user_id: str) -> bool:
        if not self.users_worksheet:
            return False
        try:
            records = self.users_worksheet.get_all_records()
            for i, record in enumerate(records, start=2):
                if record.get('User ID') == user_id:
                    timestamp = self._get_tokyo_timestamp()
                    self.users_worksheet.update_cell(i, 7, "Yes")        # Consented
                    self.users_worksheet.update_cell(i, 8, timestamp)      # Consent Date
                    print(f"Marked consented in Users sheet: {user_id}")
                    return True
            # If not found, create a new user row first
            self.log_new_user(user_id, display_name="", phone_number="")
            return self.mark_user_consented(user_id)
        except Exception as e:
            logging.error(f"Error marking consent for {user_id}: {e}")
            return False

    def revoke_user_consent(self, user_id: str) -> bool:
        if not self.users_worksheet:
            return False
        try:
            records = self.users_worksheet.get_all_records()
            for i, record in enumerate(records, start=2):
                if record.get('User ID') == user_id:
                    self.users_worksheet.update_cell(i, 7, "No")         # Consented
                    self.users_worksheet.update_cell(i, 8, "")            # Consent Date
                    print(f"Revoked consent in Users sheet: {user_id}")
                    return True
            return False
        except Exception as e:
            logging.error(f"Error revoking consent for {user_id}: {e}")
            return False

    def is_new_user(self, user_id: str) -> bool:
        if not self.users_worksheet:
            return True
        try:
            records = self.users_worksheet.get_all_records()
            for record in records:
                if record.get('User ID') == user_id:
                    return False
            return True
        except Exception:
            return True

    def mark_user_seen(self, user_id: str) -> bool:
        if not self.users_worksheet:
            return False
        try:
            timestamp = self._get_tokyo_timestamp()
            records = self.users_worksheet.get_all_records()
            for i, record in enumerate(records, start=2):
                if record.get('User ID') == user_id:
                    self.users_worksheet.update_cell(i, 10, timestamp)     # Last Seen
                    return True
            # If user not found, create with first/last seen set
            self.log_new_user(user_id, display_name="", phone_number="")
            return True
        except Exception as e:
            logging.error(f"Error marking user seen for {user_id}: {e}")
            return False
            
            logging.warning(f"User {user_id} not found for status update")
            return False
            
        except Exception as e:
            logging.error(f"Error updating user status: {e}")
            return False