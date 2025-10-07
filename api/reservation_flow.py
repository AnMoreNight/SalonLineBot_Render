"""
Reservation flow system with intent detection, candidate suggestions, and confirmation
"""
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import logging
from api.google_calendar import GoogleCalendarHelper

class ReservationFlow:
    def __init__(self):
        self.user_states = {}  # Store user reservation states
        self.google_calendar = GoogleCalendarHelper()  # Initialize Google Calendar integration
        self.line_configuration = None  # Will be set from main handler
        
        # Service and staff data for confirmation
        self.services = {
            "カット": {"duration": 60, "price": 3000},
            "カラー": {"duration": 120, "price": 8000},
            "パーマ": {"duration": 150, "price": 12000},
            "トリートメント": {"duration": 90, "price": 5000}
        }
        self.staff_members = {
            "田中": {"specialty": "カット・カラー", "experience": "5年"},
            "佐藤": {"specialty": "パーマ・トリートメント", "experience": "3年"},
            "山田": {"specialty": "カット・カラー・パーマ", "experience": "8年"},
            "未指定": {"specialty": "全般", "experience": "担当者決定"}
        }
    
    def _get_available_slots(self, start_date: datetime = None, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Get available time slots from Google Calendar"""
        if start_date is None:
            start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        end_date = start_date + timedelta(days=days_ahead)
        return self.google_calendar.get_available_slots(start_date, end_date)
    
    def detect_intent(self, message: str, user_id: str = None) -> str:
        """Detect user intent from message with context awareness"""
        message_lower = message.lower()
        
        # Check if user is in reservation flow
        if user_id and user_id in self.user_states:
            state = self.user_states[user_id]
            step = state["step"]
            
            # During other reservation steps, treat as reservation flow
            if step in ["service_selection", 'staff_selection', "date_selection", "time_selection", "confirmation"]:
                return "reservation_flow"
        
        # Reservation intent keywords (only when not in flow)
        reservation_keywords = [
            "予約", "予約したい", "予約お願い", "予約できますか",
            "空いてる", "空き", "時間", "いつ", "可能"
        ]
        
        # Cancel intent keywords
        cancel_keywords = [
            "キャンセル", "取り消し", "予約変更", "変更"
        ]
        
        # Priority order: reservation > service_selection > staff_selection > cancel
        if any(keyword in message_lower for keyword in reservation_keywords):
            return "reservation"
        elif any(keyword in message_lower for keyword in cancel_keywords):
            return "cancel"
        else:
            return "general"
    
    def handle_reservation_flow(self, user_id: str, message: str) -> str:
        """Handle the complete reservation flow"""
        if user_id not in self.user_states:
            self.user_states[user_id] = {"step": "start", "data": {}}
        
        # Check for cancellation at any step
        if message.lower() in ["キャンセル", "取り消し", "やめる", "中止"]:
            del self.user_states[user_id]
            return "予約をキャンセルいたします。またのご利用をお待ちしております。"
        
        state = self.user_states[user_id]
        step = state["step"]
        
        if step == "start":
            return self._start_reservation(user_id)
        elif step == "service_selection":
            return self._handle_service_selection(user_id, message)
        elif step == "staff_selection":
            return self._handle_staff_selection(user_id, message)
        elif step == "date_selection":
            return self._handle_date_selection(user_id, message)
        elif step == "time_selection":
            return self._handle_time_selection(user_id, message)
        elif step == "confirmation":
            return self._handle_confirmation(user_id, message)
        else:
            return "予約フローに問題が発生しました。最初からやり直してください。"
    
    def _start_reservation(self, user_id: str) -> str:
        """Start reservation process"""
        self.user_states[user_id]["step"] = "service_selection"
        return """ご予約ありがとうございます！
どのサービスをご希望ですか？

・カット（60分・3,000円）
・カラー（120分・8,000円）
・パーマ（150分・12,000円）
・トリートメント（90分・5,000円）

サービス名をお送りください。

※予約をキャンセルされる場合は「キャンセル」とお送りください。"""
    
    def _handle_service_selection(self, user_id: str, message: str) -> str:
        """Handle service selection"""
        # Check for cancellation first
        if message.lower() in ["キャンセル", "取り消し", "やめる", "中止"]:
            del self.user_states[user_id]
            return "予約をキャンセルいたします。またのご利用をお待ちしております。"
        
        selected_service = None
        message_lower = message.lower()
        
        # More flexible service matching
        service_mapping = {
            "カット": "カット",
            "カラー": "カラー", 
            "パーマ": "パーマ",
            "トリートメント": "トリートメント",
            "cut": "カット",
            "color": "カラー",
            "perm": "パーマ",
            "treatment": "トリートメント"
        }
        
        for keyword, service_name in service_mapping.items():
            if keyword in message_lower:
                selected_service = service_name
                break
        
        if not selected_service:
            return "申し訳ございませんが、そのサービスは提供しておりません。上記のサービスからお選びください。"
        
        self.user_states[user_id]["data"]["service"] = selected_service
        self.user_states[user_id]["step"] = "staff_selection"
        
        return f"""{selected_service}ですね！
担当の美容師をお選びください。

・田中（カット・カラー専門・5年経験）
・佐藤（パーマ・トリートメント専門・3年経験）
・山田（全般対応・8年経験）
・未指定（担当者決定）

美容師名をお送りください。

※予約をキャンセルされる場合は「キャンセル」とお送りください。"""
    
    def _handle_staff_selection(self, user_id: str, message: str) -> str:
        """Handle staff selection"""
        # Check for cancellation first
        if message.lower() in ["キャンセル", "取り消し", "やめる", "中止"]:
            del self.user_states[user_id]
            return "予約をキャンセルいたします。またのご利用をお待ちしております。"
        
        selected_staff = None
        message_lower = message.lower()
        
        # Staff matching
        staff_mapping = {
            "田中": "田中",
            "佐藤": "佐藤", 
            "山田": "山田",
            "未指定": "未指定",
            "担当者": "未指定",
            "美容師": "未指定"
        }
        
        for keyword, staff_name in staff_mapping.items():
            if keyword in message_lower:
                selected_staff = staff_name
                break
        
        if not selected_staff:
            return "申し訳ございませんが、その美容師は選択できません。上記の美容師からお選びください。"
        
        self.user_states[user_id]["data"]["staff"] = selected_staff
        self.user_states[user_id]["step"] = "date_selection"
        
        # Add "さん" only for specific staff members, not for "未指定"
        staff_display = f"{selected_staff}さん" if selected_staff != "未指定" else selected_staff
        
        return f"""{staff_display}ですね！
ご希望の日付をお選びください。

今週の空いている日：
・明日
・明後日
・今週の土曜日

日付をお送りください。

※予約をキャンセルされる場合は「キャンセル」とお送りください。"""
    
    def _handle_date_selection(self, user_id: str, message: str) -> str:
        """Handle date selection"""
        # Check for cancellation first
        if message.lower() in ["キャンセル", "取り消し", "やめる", "中止"]:
            del self.user_states[user_id]
            return "予約をキャンセルいたします。またのご利用をお待ちしております。"
        
        # Simple date parsing (in real implementation, use proper date parsing)
        if "明日" in message:
            selected_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        elif "明後日" in message:
            selected_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
        elif "土曜日" in message or "土曜" in message:
            # Find next Saturday
            days_ahead = 5 - datetime.now().weekday()  # Saturday is 5
            if days_ahead <= 0:
                days_ahead += 7
            selected_date = (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        else:
            return "申し訳ございませんが、その日付は選択できません。上記の日付からお選びください。"
        
        self.user_states[user_id]["data"]["date"] = selected_date
        self.user_states[user_id]["step"] = "time_selection"
        
        # Get available times for selected date from Google Calendar
        available_slots = self._get_available_slots()
        available_times = [slot["time"] for slot in available_slots 
                          if slot["date"] == selected_date and slot["available"]]
        
        if not available_times:
            return f"申し訳ございませんが、{selected_date}は空いている時間がありません。他の日付をお選びください。"
        
        return f"""{selected_date}ですね！
空いている時間帯は以下の通りです：

{chr(10).join([f"・{time}" for time in available_times])}

ご希望の時間をお送りください。

※予約をキャンセルされる場合は「キャンセル」とお送りください。"""
    
    def _handle_time_selection(self, user_id: str, message: str) -> str:
        """Handle time selection"""
        # Check for cancellation first
        if message.lower() in ["キャンセル", "取り消し", "やめる", "中止"]:
            del self.user_states[user_id]
            return "予約をキャンセルいたします。またのご利用をお待ちしております。"
        
        selected_date = self.user_states[user_id]["data"]["date"]
        available_slots = self._get_available_slots()
        available_times = [slot["time"] for slot in available_slots 
                         if slot["date"] == selected_date and slot["available"]]

        # Normalize the input message
        normalized_message = message.strip()
        
        # Check if input is a valid time format
        is_valid_time = False
        selected_time = None
        
        # Convert various time formats to standard HH:MM format
        # Handle "10時" -> "10:00"
        if re.match(r'^(\d{1,2})時$', normalized_message):
            hour = int(re.match(r'^(\d{1,2})時$', normalized_message).group(1))
            if 0 <= hour <= 23:
                normalized_message = f"{hour:02d}:00"
                is_valid_time = True
        # Handle "10時30分" -> "10:30"
        elif re.match(r'^(\d{1,2})時(\d{1,2})分?$', normalized_message):
            match = re.match(r'^(\d{1,2})時(\d{1,2})分?$', normalized_message)
            hour = int(match.group(1))
            minute = int(match.group(2))
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                normalized_message = f"{hour:02d}:{minute:02d}"
                is_valid_time = True
        # Handle "10" -> "10:00"
        elif re.match(r'^(\d{1,2})$', normalized_message):
            hour = int(re.match(r'^(\d{1,2})$', normalized_message).group(1))
            if 0 <= hour <= 23:
                normalized_message = f"{hour:02d}:00"
                is_valid_time = True
        # Handle "10:30" or "10:30分" -> "10:30"
        elif re.match(r'^(\d{1,2}):(\d{1,2})分?$', normalized_message):
            match = re.match(r'^(\d{1,2}):(\d{1,2})分?$', normalized_message)
            hour = int(match.group(1))
            minute = int(match.group(2))
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                normalized_message = f"{hour:02d}:{minute:02d}"
                is_valid_time = True
        # Handle "10：30" (full-width colon)
        elif re.match(r'^(\d{1,2})：(\d{1,2})分?$', normalized_message):
            match = re.match(r'^(\d{1,2})：(\d{1,2})分?$', normalized_message)
            hour = int(match.group(1))
            minute = int(match.group(2))
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                normalized_message = f"{hour:02d}:{minute:02d}"
                is_valid_time = True
        
        # If input is not a valid time format, return error message
        if not is_valid_time:
            return """時間の入力形式が正しくありません。

正しい入力例：
・10時
・15時30分
・14:00
・9

上記の空き時間からお選びください。"""

        # Check if the normalized time is available
        if normalized_message in available_times:
            selected_time = normalized_message
        else:
            return f"申し訳ございませんが、{normalized_message}は空いていません。上記の空き時間からお選びください。"
        
        self.user_states[user_id]["data"]["time"] = selected_time
        self.user_states[user_id]["step"] = "confirmation"
        
        service = self.user_states[user_id]["data"]["service"]
        staff = self.user_states[user_id]["data"]["staff"]
        service_info = self.services[service]
        
        return f"""予約内容の確認です：

📅 日時：{selected_date} {selected_time}
💇 サービス：{service}
👨‍💼 担当者：{staff}
⏱️ 所要時間：{service_info['duration']}分
💰 料金：{service_info['price']:,}円

この内容で予約を確定しますか？
「はい」または「確定」とお送りください。

※予約をキャンセルされる場合は「キャンセル」とお送りください。"""

    def _handle_confirmation(self, user_id: str, message: str) -> str:
        """Handle final confirmation"""
        if "はい" in message or "確定" in message or "お願い" in message:
            # Complete the reservation
            reservation_data = self.user_states[user_id]["data"].copy()
            del self.user_states[user_id]  # Clear user state
            
            # Get client display name
            client_name = self._get_line_display_name(user_id)
            
            # Create calendar event immediately
            calendar_success = self.google_calendar.create_reservation_event(
                reservation_data, 
                client_name
            )
            
            if not calendar_success:
                logging.warning(f"Failed to create calendar event for user {user_id}")
           
            return f"""✅ 予約が確定いたしました！

📅 日時：{reservation_data['date']} {reservation_data['time']}
💇 サービス：{reservation_data['service']}
👨‍💼 担当者：{reservation_data['staff']}

当日はお時間までにお越しください。
ご予約ありがとうございました！"""
        else:
            return "予約をキャンセルいたします。またのご利用をお待ちしております。"
    
    def get_response(self, user_id: str, message: str) -> str:
        """Main entry point for reservation flow"""
        intent = self.detect_intent(message, user_id)
        
        if intent == "reservation":
            return self.handle_reservation_flow(user_id, message)
        elif intent == "reservation_flow":
            return self.handle_reservation_flow(user_id, message)
        elif intent == "cancel":
            return "予約のキャンセルについてですね。お電話でお問い合わせください。"
        else:
            return None  # Let other systems handle this

    def set_line_configuration(self, configuration):
        """Set LINE configuration for getting display names"""
        self.line_configuration = configuration
    
    def _get_line_display_name(self, user_id: str) -> str:
        """Get LINE display name for the user"""
        if not self.line_configuration:
            return "お客様"  # Fallback name
        
        try:
            from linebot.v3.messaging import ApiClient, MessagingApi
            with ApiClient(self.line_configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                profile = line_bot_api.get_profile(user_id)
                return profile.display_name
        except Exception as e:
            logging.error(f"Failed to get LINE display name: {e}")
            return "お客様"  # Fallback name
