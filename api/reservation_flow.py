"""
Reservation flow system with intent detection, candidate suggestions, and confirmation
"""
import re
from typing import Dict, List, Optional, Any, Union
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
    
    def _get_available_slots(self, selected_date: str = None) -> List[Dict[str, Any]]:
        """Get available time slots from Google Calendar for a specific date"""
        if selected_date is None:
            # If no date specified, get slots for today
            selected_date = datetime.now().strftime("%Y-%m-%d")
        
        # Convert string date to datetime objects for the specific day
        start_date = datetime.strptime(selected_date, "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)  # Next day at 00:00
        
        # Get all slots for the date range and filter for the specific date
        all_slots = self.google_calendar.get_available_slots(start_date, end_date)
        
        # Filter slots for the specific date
        date_slots = [slot for slot in all_slots if slot["date"] == selected_date]
        
        return date_slots
    
    def _create_calendar_template(self) -> str:
        """Create Google Calendar URL for date selection"""
        # Get the Google Calendar URL from the calendar helper
        calendar_url = self.google_calendar.get_calendar_url()
        
        calendar_message = "📅 **ご希望の日付をお選びください**\n\n"
        calendar_message += "🗓️ **Googleカレンダーで空き状況を確認してください：**\n"
        calendar_message += f"🔗 {calendar_url}\n\n"
        calendar_message += "💡 **手順：**\n"
        calendar_message += "1️⃣ 上記リンクをクリックしてGoogleカレンダーを開く\n"
        calendar_message += "2️⃣ 空いている日付を確認\n"
        calendar_message += "3️⃣ 希望の日付を「YYYY-MM-DD」形式で送信\n"
        calendar_message += "📝 例：`2025-01-15`\n\n"
        calendar_message += "❌ 予約をキャンセルする場合は「キャンセル」と送信"
        
        return calendar_message
    
    
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
            "キャンセル", "取り消し", "やめる", "中止"
        ]
        
        # Modify intent keywords
        modify_keywords = [
            "予約変更", "変更", "修正", "時間変更", "日時変更", "予約修正"
        ]
        
        # Priority order: reservation > service_selection > staff_selection > modify > cancel
        if any(keyword in message_lower for keyword in reservation_keywords):
            return "reservation"
        elif any(keyword in message_lower for keyword in modify_keywords):
            return "modify"
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
        
        # Return calendar template for date selection
        return self._create_calendar_template()
    
    def _handle_date_selection(self, user_id: str, message: str) -> str:
        """Handle date selection from calendar template"""
        # Check for cancellation first
        if message.lower() in ["キャンセル", "取り消し", "やめる", "中止"]:
            del self.user_states[user_id]
            return "予約をキャンセルいたします。またのご利用をお待ちしております。"
        
        # Parse date from calendar template response
        selected_date = None
        
        # Try to parse YYYY-MM-DD format (from calendar template)
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', message)
        if date_match:
            selected_date = date_match.group(1)
        else:
            # Try to parse clickable date format [DD] from calendar
            clickable_match = re.search(r'\[(\d{1,2})\]', message)
            if clickable_match:
                day = int(clickable_match.group(1))
                current_date = datetime.now()
                # Create the date for this month
                try:
                    selected_date = f"{current_date.year}-{current_date.month:02d}-{day:02d}"
                    # Validate the date exists
                    datetime.strptime(selected_date, "%Y-%m-%d")
                except ValueError:
                    selected_date = None
            else:
                # Fallback to old text-based parsing for backward compatibility
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
        
        if not selected_date:
            return "申し訳ございませんが、その日付は選択できません。上記の日付からお選びください。"
        
        self.user_states[user_id]["data"]["date"] = selected_date
        self.user_states[user_id]["step"] = "time_selection"
        
        # Get available time periods for selected date from Google Calendar
        available_slots = self._get_available_slots(selected_date)
        available_periods = [slot for slot in available_slots if slot["available"]]
        
        if not available_periods:
            # No available slots for selected date - return to date selection
            self.user_states[user_id]["step"] = "date_selection"
            return f"""申し訳ございませんが、{selected_date}は空いている時間がありません。

他の日付をお選びください。

📅 **Googleカレンダーで空き状況を確認してください：**
🔗 {self.google_calendar.get_calendar_url()}

💡 **手順：**
1️⃣ 上記リンクをクリックしてGoogleカレンダーを開く
2️⃣ 空いている日付を確認
3️⃣ 希望の日付を「YYYY-MM-DD」形式で送信
📝 例：`2025-01-15`

❌ 予約をキャンセルする場合は「キャンセル」と送信"""
        
        # Format available periods for display
        period_strings = []
        for period in available_periods:
            start_time = period["time"]
            end_time = period["end_time"]
            period_strings.append(f"・{start_time}~{end_time}")
        
        return f"""{selected_date}ですね！
空いている時間帯は以下の通りです：

{chr(10).join(period_strings)}

ご希望の開始時間と終了時間をお送りください。
例）10:00~11:00 または 10:00 11:00

※予約をキャンセルされる場合は「キャンセル」とお送りください。"""
    
    def _handle_time_selection(self, user_id: str, message: str) -> str:
        """Handle time selection"""
        # Check for cancellation first
        if message.lower() in ["キャンセル", "取り消し", "やめる", "中止"]:
            del self.user_states[user_id]
            return "予約をキャンセルいたします。またのご利用をお待ちしております。"
        
        selected_date = self.user_states[user_id]["data"]["date"]
        available_slots = self._get_available_slots(selected_date)
        available_periods = [slot for slot in available_slots if slot["available"]]

        # Parse start and end times from user input
        start_time, end_time = self._parse_time_range(message.strip())
        
        if not start_time or not end_time:
            return """時間の入力形式が正しくありません。

正しい入力例：
・10:00~11:00
・10:00 11:00
・10時~11時
・10時 11時

上記の空き時間からお選びください。"""

        # Validate that the time range falls within available periods
        is_valid_range = False
        for period in available_periods:
            period_start = period["time"]
            period_end = period["end_time"]
            
            # Check if the entire time range is within this period
            if period_start <= start_time and end_time <= period_end:
                is_valid_range = True
                break
        
        if not is_valid_range:
            return f"申し訳ございませんが、{start_time}~{end_time}は空いていません。上記の空き時間からお選びください。"
        
        # Store both start and end times
        self.user_states[user_id]["data"]["start_time"] = start_time
        self.user_states[user_id]["data"]["end_time"] = end_time
        self.user_states[user_id]["data"]["time"] = start_time  # Keep for backward compatibility
        self.user_states[user_id]["step"] = "confirmation"
        
        service = self.user_states[user_id]["data"]["service"]
        staff = self.user_states[user_id]["data"]["staff"]
        service_info = self.services[service]
        
        return f"""予約内容の確認です：

📅 日時：{selected_date} {start_time}~{end_time}
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
            
            # Generate reservation ID
            reservation_id = self.google_calendar.generate_reservation_id(reservation_data['date'])
            reservation_data['reservation_id'] = reservation_id
            
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
           
            # Get time range for display
            time_display = reservation_data.get('start_time', reservation_data['time'])
            if 'end_time' in reservation_data:
                time_display = f"{reservation_data['start_time']}~{reservation_data['end_time']}"
            
            return f"""✅ 予約が確定いたしました！

🆔 予約ID：{reservation_id}
📅 日時：{reservation_data['date']} {time_display}
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
        elif intent == "modify":
            return self._handle_modify_request(user_id, message)
        elif intent == "cancel":
            return self._handle_cancel_request(user_id)
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

    def _handle_cancel_request(self, user_id: str) -> str:
        """Cancel existing calendar reservation for the user if present."""
        client_name = self._get_line_display_name(user_id)
        try:
            success = self.google_calendar.cancel_reservation(client_name)
            if success:
                return "ご予約のキャンセルを承りました。\nまたのご利用をお待ちしております。"
            else:
                return "現在、登録されているご予約が見つかりませんでした。\n別のお名前でご予約されている場合はスタッフまでお知らせください。"
        except Exception as e:
            logging.error(f"Cancel request failed: {e}")
            return "申し訳ございません。キャンセルの処理中にエラーが発生しました。少し時間を置いてお試しください。"

    def _parse_datetime_from_text(self, text: str) -> Optional[Dict[str, str]]:
        """Parse date and time from user text. Expected format: YYYY-MM-DD HH:MM.
        Returns dict with keys 'date' and 'time' if both found, else None.
        """
        text = text.strip()
        # Try pattern: 2025-10-07 14:30
        match = re.search(r"(\d{4}-\d{2}-\d{2})\s+(\d{1,2}):(\d{2})", text)
        if match:
            date_part = match.group(1)
            hour = int(match.group(2))
            minute = int(match.group(3))
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return {"date": date_part, "time": f"{hour:02d}:{minute:02d}"}
        
        # Try pattern: 2025-10-07 14:30:00 (with seconds) -> convert to HH:MM
        match = re.search(r"(\d{4}-\d{2}-\d{2})\s+(\d{1,2}):(\d{2}):(\d{2})", text)
        if match:
            date_part = match.group(1)
            hour = int(match.group(2))
            minute = int(match.group(3))
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return {"date": date_part, "time": f"{hour:02d}:{minute:02d}"}
        
        # Try Japanese style like "10月7日 14時30分" → require conversion; keep simple for now
        match2 = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日\s*(\d{1,2})時(\d{1,2})?分?", text)
        if match2:
            y = int(match2.group(1))
            m = int(match2.group(2))
            d = int(match2.group(3))
            hh = int(match2.group(4))
            mm = int(match2.group(5) or 0)
            if 1 <= m <= 12 and 1 <= d <= 31 and 0 <= hh <= 23 and 0 <= mm <= 59:
                return {"date": f"{y:04d}-{m:02d}-{d:02d}", "time": f"{hh:02d}:{mm:02d}"}

        return None

    def _parse_time_range(self, text: str) -> tuple:
        """Parse start and end times from user input.
        Returns tuple of (start_time, end_time) in HH:MM format, or (None, None) if invalid.
        """
        text = text.strip()
        
        # Helper function to normalize time to HH:MM format
        def normalize_time(time_str):
            time_str = time_str.strip()
            
            # Handle "10時" -> "10:00"
            if re.match(r'^(\d{1,2})時$', time_str):
                hour = int(re.match(r'^(\d{1,2})時$', time_str).group(1))
                if 0 <= hour <= 23:
                    return f"{hour:02d}:00"
            
            # Handle "10時30分" -> "10:30"
            elif re.match(r'^(\d{1,2})時(\d{1,2})分?$', time_str):
                match = re.match(r'^(\d{1,2})時(\d{1,2})分?$', time_str)
                hour = int(match.group(1))
                minute = int(match.group(2))
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    return f"{hour:02d}:{minute:02d}"
            
            # Handle "10" -> "10:00"
            elif re.match(r'^(\d{1,2})$', time_str):
                hour = int(re.match(r'^(\d{1,2})$', time_str).group(1))
                if 0 <= hour <= 23:
                    return f"{hour:02d}:00"
            
            # Handle "10:30" or "10:30分" -> "10:30"
            elif re.match(r'^(\d{1,2}):(\d{1,2})分?$', time_str):
                match = re.match(r'^(\d{1,2}):(\d{1,2})分?$', time_str)
                hour = int(match.group(1))
                minute = int(match.group(2))
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    return f"{hour:02d}:{minute:02d}"
            
            # Handle "10：30" (full-width colon) -> "10:30"
            elif re.match(r'^(\d{1,2})：(\d{1,2})分?$', time_str):
                match = re.match(r'^(\d{1,2})：(\d{1,2})分?$', time_str)
                hour = int(match.group(1))
                minute = int(match.group(2))
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    return f"{hour:02d}:{minute:02d}"
            
            # Handle "10:30:00" format (with seconds) -> "10:30"
            elif re.match(r'^(\d{1,2}):(\d{1,2}):(\d{1,2})$', time_str):
                match = re.match(r'^(\d{1,2}):(\d{1,2}):(\d{1,2})$', time_str)
                hour = int(match.group(1))
                minute = int(match.group(2))
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    return f"{hour:02d}:{minute:02d}"
            
            return None
        
        # Try different patterns for time range input
        
        # Pattern 1: "10:00~11:00" or "10:00～11:00"
        match = re.search(r'^(\d{1,2}[:：]\d{1,2}[分]?)[~～](\d{1,2}[:：]\d{1,2}[分]?)$', text)
        if match:
            start_time = normalize_time(match.group(1))
            end_time = normalize_time(match.group(2))
            if start_time and end_time:
                return start_time, end_time
        
        # Pattern 2: "10:00 11:00" (space separated)
        match = re.search(r'^(\d{1,2}[:：]\d{1,2}[分]?)\s+(\d{1,2}[:：]\d{1,2}[分]?)$', text)
        if match:
            start_time = normalize_time(match.group(1))
            end_time = normalize_time(match.group(2))
            if start_time and end_time:
                return start_time, end_time
        
        # Pattern 3: "10時~11時" or "10時～11時"
        match = re.search(r'^(\d{1,2}時\d{1,2}分?)[~～](\d{1,2}時\d{1,2}分?)$', text)
        if match:
            start_time = normalize_time(match.group(1))
            end_time = normalize_time(match.group(2))
            if start_time and end_time:
                return start_time, end_time
        
        # Pattern 4: "10時 11時" (space separated)
        match = re.search(r'^(\d{1,2}時\d{1,2}分?)\s+(\d{1,2}時\d{1,2}分?)$', text)
        if match:
            start_time = normalize_time(match.group(1))
            end_time = normalize_time(match.group(2))
            if start_time and end_time:
                return start_time, end_time
        
        return None, None

    def _handle_modify_request(self, user_id: str, message: str) -> str:
        """Modify existing reservation time via Google Calendar.

        Conversation flow:
        - If we don't yet have new date/time, ask for it in the format "YYYY-MM-DD HH:MM".
        - Once received, perform modification on the user's upcoming reservation.
        """
        state = self.user_states.get(user_id)
        if not state or state.get("step") not in ["modify_waiting", "modify_provide_time"]:
            # Start modify flow
            self.user_states[user_id] = {"step": "modify_waiting"}
            return "ご予約の変更ですね。\n新しい日時を \"YYYY-MM-DD HH:MM\" の形式でお送りください。\n例）2025-10-07 14:30"

        # Try to parse date/time from message
        parsed = self._parse_datetime_from_text(message)
        if not parsed:
            return "日時の形式が正しくありません。\n\"YYYY-MM-DD HH:MM\" の形式でお送りください。\n例）2025-10-07 14:30"

        new_date = parsed["date"]
        new_time = parsed["time"]
        client_name = self._get_line_display_name(user_id)
        try:
            success = self.google_calendar.modify_reservation_time(client_name, new_date, new_time)
            # Clear temporary modify state
            if user_id in self.user_states and self.user_states[user_id].get("step","") in ["modify_waiting", "modify_provide_time"]:
                del self.user_states[user_id]
            if success:
                return f"ご予約の日時を変更しました。\n📅 新しい日時：{new_date} {new_time}"
            else:
                return "現在、変更できるご予約が見つかりませんでした。\n別のお名前でご予約されている場合はスタッフまでお知らせください。"
        except Exception as e:
            logging.error(f"Modify request failed: {e}")
            return "申し訳ございません。変更の処理中にエラーが発生しました。少し時間を置いてお試しください。"
