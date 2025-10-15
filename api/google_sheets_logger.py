import os
import json
import logging
from datetime import datetime
import re
from typing import Optional, Dict, Any, List
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv


class GoogleSheetsLogger:
    """Logger for saving bot interactions to Google Sheets
    
    This class handles two separate functionalities:
    1. Message logging (saved to main Sheet1)
    2. Reservation management (saved to separate Reservations sheet)
    """
    
    def __init__(self):
        self.message_worksheet = None  # For message logging (Sheet1)
        self.reservations_worksheet = None  # For reservation data (Reservations sheet)
        self._setup_connection()
    
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
            if not self.message_worksheet.get_all_records():
                self._setup_message_headers()
            
            # Setup reservations worksheet (separate sheet)
            self.reservations_worksheet = self._get_reservations_worksheet()
            
            logging.info("Google Sheets logger initialized successfully")
            logging.info("Message logging: Sheet1, Reservation data: Reservations sheet")
            
        except Exception as e:
            logging.error(f"Failed to setup Google Sheets connection: {e}")
            self.message_worksheet = None
            self.reservations_worksheet = None
    
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
            logging.info("Message logging headers setup completed in Sheet1")
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
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
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
            logging.info(f"Logged message interaction for user {user_id} to Sheet1")
            
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
            except gspread.WorksheetNotFound:
                # Create new reservations worksheet
                reservations_worksheet = spreadsheet.add_worksheet(
                    title="Reservations", 
                    rows=1000, 
                    cols=10
                )
                # Setup headers for reservations
                self._setup_reservations_headers(reservations_worksheet)
            
            # Store the worksheet for future use
            self.reservations_worksheet = reservations_worksheet
            return reservations_worksheet
            
        except Exception as e:
            logging.error(f"Failed to get reservations worksheet: {e}")
            return None
    
    def _setup_reservations_headers(self, worksheet):
        """Setup headers for the reservations worksheet"""
        headers = [
            "Reservation ID",
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
                logging.info("Reservations worksheet headers setup completed")
            else:
                logging.info("Reservations worksheet headers already exist")
        except Exception as e:
            logging.error(f"Failed to setup reservations headers: {e}")
    
    def save_reservation(self, reservation_data: Dict[str, Any]) -> bool:
        """Save a new reservation to the reservations worksheet"""
        reservations_worksheet = self._get_reservations_worksheet()
        if not reservations_worksheet:
            return False
        
        try:
            row_data = [
                reservation_data.get("reservation_id", ""),
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
            logging.info(f"Saved reservation {reservation_data.get('reservation_id')} to Google Sheets")
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
                "Reservation ID",
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
                "Reservation ID",
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
                    # Update the status in column J (10th column)
                    reservations_worksheet.update_cell(i, 10, status)
                    logging.info(f"Updated reservation {reservation_id} status to {status}")
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
                "Reservation ID",
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
                "Reservation ID",
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
                    
                    logging.info(f"Updated reservation {reservation_id} with fields: {list(field_updates.keys())}")
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
            # Get all records
            records = self.reservations_worksheet.get_all_records()
            
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
            # Get all records
            records = self.reservations_worksheet.get_all_records()
            
            # Find the reservation
            for record in records:
                if record.get('Reservation ID') == reservation_id:
                    return record.get('User ID', '')
            
            logging.warning(f"Reservation {reservation_id} not found in sheets")
            return None
            
        except Exception as e:
            logging.error(f"Error getting user ID for reservation {reservation_id}: {e}")
            return None