import os
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv


class GoogleSheetsLogger:
    """Logger for saving bot interactions to Google Sheets"""
    
    def __init__(self):
        self.worksheet = None
        self._setup_connection()
    
    def _setup_connection(self):
        """Setup Google Sheets connection"""
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
            
            # Get spreadsheet and worksheet
            spreadsheet_id = os.getenv("GOOGLE_SHEET_ID")
            if not spreadsheet_id:
                logging.warning("GOOGLE_SHEET_ID not found. Google Sheets logging disabled.")
                return
            
            spreadsheet = gc.open_by_key(spreadsheet_id)
            self.worksheet = spreadsheet.sheet1
            
            # Setup headers if worksheet is empty
            if not self.worksheet.get_all_records():
                self._setup_headers()
            
            logging.info("Google Sheets logger initialized successfully")
            
        except Exception as e:
            logging.error(f"Failed to setup Google Sheets connection: {e}")
            self.worksheet = None
    
    def _setup_headers(self):
        """Setup column headers in the worksheet"""
        if not self.worksheet:
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
            self.worksheet.append_row(headers)
            logging.info("Google Sheets headers setup completed")
        except Exception as e:
            logging.error(f"Failed to setup headers: {e}")
    
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
        """Log a message interaction to Google Sheets"""
        
        if not self.worksheet:
            logging.warning("Google Sheets not available. Skipping log.")
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
            
            # Append to worksheet
            self.worksheet.append_row(row_data)
            logging.info(f"Logged interaction for user {user_id} to Google Sheets")
            
        except Exception as e:
            logging.error(f"Failed to log to Google Sheets: {e}")
    
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
