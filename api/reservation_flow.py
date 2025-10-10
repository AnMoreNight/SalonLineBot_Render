"""
Reservation flow system with intent detection, candidate suggestions, and confirmation
"""
import re
import os
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import logging
try:
    from api.google_calendar import GoogleCalendarHelper
except ImportError:
    from google_calendar import GoogleCalendarHelper

class ReservationFlow:
    def __init__(self):
        self.user_states = {}  # Store user reservation states
        self.google_calendar = GoogleCalendarHelper()  # Initialize Google Calendar integration
        self.line_configuration = None  # Will be set from main handler
        
        # Load services and staff data from JSON
        self.services_data = self._load_services_data()
        self.services = self.services_data.get("services", {})
        self.staff_members = self.services_data.get("staff", {})
        
        # Load keywords from JSON
        self.keywords_data = self._load_keywords_data()
        self.intent_keywords = self.keywords_data.get("intent_keywords", {})
        self.navigation_keywords = self.keywords_data.get("navigation_keywords", {})
        self.staff_keywords = self.keywords_data.get("staff_keywords", {})
        self.confirmation_keywords = self.keywords_data.get("confirmation_keywords", {})
    
    def _load_services_data(self) -> Dict[str, Any]:
        """Load services and staff data from JSON file"""
        try:
            # Get the directory of this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            services_file = os.path.join(current_dir, "data", "services.json")
            
            with open(services_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Failed to load services data: {e}")
            # Return default data if file loading fails
            return {
                "services": {
                    "カット": {"name": "カット", "duration": 60, "price": 3000, "description": "ヘアカットサービス"},
                    "カラー": {"name": "カラー", "duration": 120, "price": 8000, "description": "ヘアカラーサービス"},
                    "パーマ": {"name": "パーマ", "duration": 150, "price": 12000, "description": "パーマサービス"},
                    "トリートメント": {"name": "トリートメント", "duration": 90, "price": 5000, "description": "ヘアトリートメントサービス"}
                },
                "staff": {
                    "田中": {"name": "田中", "specialty": "カット・カラー", "experience": "5年", "email_env": "STAFF_TANAKA_EMAIL"},
                    "佐藤": {"name": "佐藤", "specialty": "パーマ・トリートメント", "experience": "3年", "email_env": "STAFF_SATO_EMAIL"},
                    "山田": {"name": "山田", "specialty": "カット・カラー・パーマ", "experience": "8年", "email_env": "STAFF_YAMADA_EMAIL"},
                    "未指定": {"name": "未指定", "specialty": "全般", "experience": "担当者決定", "email_env": None}
                }
            }
    
    def _load_keywords_data(self) -> Dict[str, Any]:
        """Load keywords data from JSON file"""
        try:
            # Get the directory of this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            keywords_file = os.path.join(current_dir, "data", "keywords.json")
            
            with open(keywords_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Failed to load keywords data: {e}")
            # Return default data if file loading fails
            return {
                "intent_keywords": {
                    "reservation": ["予約", "予約したい", "予約お願い", "予約できますか"],
                    "modify": ["予約変更", "予約修正"],
                    "cancel": ["キャンセル", "取り消し", "やめる", "中止"]
                },
                "navigation_keywords": {
                    "date_change": ["日付変更", "日付を変更", "別の日", "他の日", "日付選択", "日付に戻る"],
                    "service_change": ["サービス変更", "サービスを変更", "別のサービス", "他のサービス", "サービス選択", "サービスに戻る"]
                },
                "staff_keywords": {
                    "田中": ["田中"],
                    "佐藤": ["佐藤"],
                    "山田": ["山田"],
                    "未指定": ["未指定", "担当者", "美容師"]
                },
                "confirmation_keywords": {
                    "yes": ["はい", "確定", "お願い"],
                    "no": ["いいえ", "キャンセル", "やめる"]
                }
            }
    
    def _calculate_time_duration_minutes(self, start_time: str, end_time: str) -> int:
        """Calculate duration in minutes between two time strings (HH:MM format)"""
        try:
            start_hour, start_minute = map(int, start_time.split(':'))
            end_hour, end_minute = map(int, end_time.split(':'))
            
            start_total_minutes = start_hour * 60 + start_minute
            end_total_minutes = end_hour * 60 + end_minute
            
            return end_total_minutes - start_total_minutes
        except (ValueError, IndexError):
            return 0
    
    def _calculate_optimal_end_time(self, start_time: str, service_duration_minutes: int) -> str:
        """Calculate the optimal end time based on start time and service duration"""
        try:
            start_hour, start_minute = map(int, start_time.split(':'))
            start_total_minutes = start_hour * 60 + start_minute
            
            end_total_minutes = start_total_minutes + service_duration_minutes
            
            end_hour = end_total_minutes // 60
            end_minute = end_total_minutes % 60
            
            return f"{end_hour:02d}:{end_minute:02d}"
        except (ValueError, IndexError):
            return start_time
    
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
        calendar_message += "💡 **サービスを変更したい場合は「サービス変更」とお送りください**\n"
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
        
        # Get keywords from JSON data
        reservation_keywords = self.intent_keywords.get("reservation", [])
        cancel_keywords = self.intent_keywords.get("cancel", [])
        modify_keywords = self.intent_keywords.get("modify", [])
        
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
        
        # Check for flow cancellation at any step
        flow_cancel_keywords = self.navigation_keywords.get("flow_cancel", [])
        if message.lower() in flow_cancel_keywords:
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
        
        # Generate service list from JSON data
        service_list = []
        for service_name, service_data in self.services.items():
            duration = service_data.get("duration", 60)
            price = service_data.get("price", 3000)
            service_list.append(f"・{service_name}（{duration}分・{price:,}円）")
        
        services_text = "\n".join(service_list)
        
        return f"""ご予約ありがとうございます！
どのサービスをご希望ですか？

{services_text}

サービス名をお送りください。

※予約をキャンセルされる場合は「キャンセル」とお送りください。"""
    
    def _handle_service_selection(self, user_id: str, message: str) -> str:
        """Handle service selection"""
        # Check for flow cancellation first
        flow_cancel_keywords = self.navigation_keywords.get("flow_cancel", [])
        if message.lower() in flow_cancel_keywords:
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

💡 **サービスを変更したい場合は「サービス変更」とお送りください**
❌ 予約をキャンセルする場合は「キャンセル」とお送りください。"""
    
    def _handle_staff_selection(self, user_id: str, message: str) -> str:
        """Handle staff selection"""
        # Check for flow cancellation first
        flow_cancel_keywords = self.navigation_keywords.get("flow_cancel", [])
        if message.lower() in flow_cancel_keywords:
            del self.user_states[user_id]
            return "予約をキャンセルいたします。またのご利用をお待ちしております。"
        
        # Check for navigation to service selection
        service_change_keywords = self.navigation_keywords.get("service_change", [])
        if message.lower() in service_change_keywords:
            self.user_states[user_id]["step"] = "service_selection"
            return self._start_reservation(user_id)
        
        selected_staff = None
        message_lower = message.lower()
        
        # Staff matching using JSON keywords
        for staff_name, keywords in self.staff_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
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
        # Check for flow cancellation first
        flow_cancel_keywords = self.navigation_keywords.get("flow_cancel", [])
        if message.lower() in flow_cancel_keywords:
            del self.user_states[user_id]
            return "予約をキャンセルいたします。またのご利用をお待ちしております。"
        
        # Check for navigation to service selection
        service_change_keywords = self.navigation_keywords.get("service_change", [])
        if message.lower() in service_change_keywords:
            self.user_states[user_id]["step"] = "service_selection"
            return self._start_reservation(user_id)
        
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

💡 **他の日を選択したい場合は「日付変更」とお送りください**
❌ 予約をキャンセルする場合は「キャンセル」とお送りください"""
    
    def _handle_time_selection(self, user_id: str, message: str) -> str:
        """Handle time selection"""
        # Check for flow cancellation first
        flow_cancel_keywords = self.navigation_keywords.get("flow_cancel", [])
        if message.lower() in flow_cancel_keywords:
            del self.user_states[user_id]
            return "予約をキャンセルいたします。またのご利用をお待ちしております。"
        
        # Check for navigation to date selection
        date_change_keywords = self.navigation_keywords.get("date_change", [])
        if message.lower() in date_change_keywords:
            self.user_states[user_id]["step"] = "date_selection"
            return self._create_calendar_template()
        
        selected_date = self.user_states[user_id]["data"]["date"]
        available_slots = self._get_available_slots(selected_date)
        available_periods = [slot for slot in available_slots if slot["available"]]

        # Parse start and end times from user input
        start_time, end_time = self._parse_time_range(message.strip())
        
        # Store original end time for potential adjustment message
        self.user_states[user_id]["data"]["original_end_time"] = end_time
        
        if not start_time or not end_time:
            return """時間の入力形式が正しくありません。

正しい入力例：
・10:00~11:00
・10:00 11:00
・10時~11時
・10時 11時

上記の空き時間からお選びください。

💡 **他の日を選択したい場合は「日付変更」とお送りください**
❌ 予約をキャンセルする場合は「キャンセル」とお送りください"""

        # Validate that start time is before end time
        if start_time >= end_time:
            # Return to time selection with error message
            self.user_states[user_id]["step"] = "time_selection"
            
            # Get available periods again for display
            available_slots = self._get_available_slots(selected_date)
            available_periods = [slot for slot in available_slots if slot["available"]]
            
            period_strings = []
            for period in available_periods:
                period_start = period["time"]
                period_end = period["end_time"]
                period_strings.append(f"・{period_start}~{period_end}")
            
            return f"""申し訳ございませんが、開始時間（{start_time}）が終了時間（{end_time}）より遅いか同じです。

{selected_date}の空いている時間帯は以下の通りです：

{chr(10).join(period_strings)}

開始時間は終了時間より早い時間を選択してください。

例）10:00~11:00（開始時間 < 終了時間）

💡 **他の日を選択したい場合は「日付変更」とお送りください**
❌ 予約をキャンセルする場合は「キャンセル」とお送りください"""

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
            return f"""申し訳ございませんが、{start_time}~{end_time}は空いていません。上記の空き時間からお選びください。

💡 **他の日を選択したい場合は「日付変更」とお送りください**
❌ 予約をキャンセルする場合は「キャンセル」とお送りください"""
        
        # Validate that the selected time period is sufficient for the service
        service = self.user_states[user_id]["data"]["service"]
        service_info = self.services.get(service, {})
        required_duration = service_info.get("duration", 60)  # Default to 60 minutes
        
        selected_duration = self._calculate_time_duration_minutes(start_time, end_time)
        
        # If selected duration is longer than required, automatically adjust end time
        if selected_duration > required_duration:
            optimal_end_time = self._calculate_optimal_end_time(start_time, required_duration)
            
            # Check if the optimal end time is still within available periods
            is_optimal_valid = False
            for period in available_periods:
                period_start = period["time"]
                period_end = period["end_time"]
                
                if period_start <= start_time and optimal_end_time <= period_end:
                    is_optimal_valid = True
                    break
            
            if is_optimal_valid:
                # Use the optimal end time
                end_time = optimal_end_time
                selected_duration = required_duration
            # If optimal end time is not available, continue with original validation
        
        if selected_duration < required_duration:
            # Return to time selection with error message
            self.user_states[user_id]["step"] = "time_selection"
            
            # Get available periods again for display
            available_slots = self._get_available_slots(selected_date)
            available_periods = [slot for slot in available_slots if slot["available"]]
            
            period_strings = []
            for period in available_periods:
                period_start = period["time"]
                period_end = period["end_time"]
                period_strings.append(f"・{period_start}~{period_end}")
            
            return f"""申し訳ございませんが、選択された時間（{selected_duration}分）では{service}（{required_duration}分）のサービスが完了できません。

{selected_date}の空いている時間帯は以下の通りです：

{chr(10).join(period_strings)}

{service}には最低{required_duration}分必要です。上記の空き時間から{required_duration}分以上の時間を選択してください。

例）{required_duration}分以上の時間帯を選択

💡 **他の日を選択したい場合は「日付変更」とお送りください**
❌ 予約をキャンセルする場合は「キャンセル」とお送りください"""
        
        # Store both start and end times
        self.user_states[user_id]["data"]["start_time"] = start_time
        self.user_states[user_id]["data"]["end_time"] = end_time
        self.user_states[user_id]["data"]["time"] = start_time  # Keep for backward compatibility
        self.user_states[user_id]["step"] = "confirmation"
        
        service = self.user_states[user_id]["data"]["service"]
        staff = self.user_states[user_id]["data"]["staff"]
        service_info = self.services[service]
        
        # Check if end time was automatically adjusted
        original_end_time = self.user_states[user_id]["data"].get("original_end_time")
        adjustment_message = ""
        if original_end_time and original_end_time != end_time:
            adjustment_message = f"\n💡 **終了時間を{service}の所要時間に合わせて{end_time}に調整しました**\n"
        
        return f"""予約内容の確認です：{adjustment_message}
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
        yes_keywords = self.confirmation_keywords.get("yes", [])
        if any(keyword in message for keyword in yes_keywords):
            # Complete the reservation
            reservation_data = self.user_states[user_id]["data"].copy()
            print("reservation_data", reservation_data)
            
            # Generate reservation ID
            reservation_id = self.google_calendar.generate_reservation_id(reservation_data['date'])
            reservation_data['reservation_id'] = reservation_id
            
            # Get client display name
            client_name = self._get_line_display_name(user_id)
            
            # Create calendar event immediately
            calendar_success = self.google_calendar.create_reservation_event(
                reservation_data, 
                client_name
            )
            
            if not calendar_success:
                logging.warning(f"Failed to create calendar event for user {user_id}")
            
            # Save reservation to Google Sheets Reservations sheet
            sheets_success = False
            try:
                from api.google_sheets_logger import GoogleSheetsLogger
                sheets_logger = GoogleSheetsLogger()
                
                # Prepare reservation data for Google Sheets
                service_info = self.services.get(reservation_data['service'], {})
                sheet_reservation_data = {
                    "reservation_id": reservation_id,
                    "client_name": client_name,
                    "date": reservation_data['date'],
                    "start_time": reservation_data.get('start_time', reservation_data.get('time', '')),
                    "end_time": reservation_data.get('end_time', ''),
                    "service": reservation_data['service'],
                    "staff": reservation_data['staff'],
                    "duration": service_info.get('duration', 60),
                    "price": service_info.get('price', 0)
                }
                
                sheets_success = sheets_logger.save_reservation(sheet_reservation_data)
                if sheets_success:
                    logging.info(f"Successfully saved reservation {reservation_id} to Reservations sheet")
                else:
                    logging.error(f"Failed to save reservation {reservation_id} to Reservations sheet")
                    
            except Exception as e:
                logging.error(f"Error saving reservation to Google Sheets: {e}")
                import traceback
                traceback.print_exc()
            
            # Keep reservation data in user state for logging in index.py
            # The user state will be cleared after logging in index.py
            self.user_states[user_id]["data"] = reservation_data
           
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
            # Check if user is providing a reservation ID (starts with "RES-")
            if message.strip().startswith("RES-"):
                return self._handle_reservation_id_cancellation(user_id, message.strip())
            else:
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
        """Show user's reservations and handle cancellation by reservation ID."""
        client_name = self._get_line_display_name(user_id)
        
        try:
            # Get user's reservations from Google Sheets
            from google_sheets_logger import GoogleSheetsLogger
            sheets_logger = GoogleSheetsLogger()
            reservations = sheets_logger.get_user_reservations(client_name)
            
            if not reservations:
                return "現在、登録されているご予約が見つかりませんでした。\n別のお名前でご予約されている場合はスタッフまでお知らせください。"
            
            # Format reservation list
            reservation_list = []
            for i, res in enumerate(reservations, 1):
                reservation_list.append(
                    f"{i}. **{res['reservation_id']}**\n"
                    f"   📅 {res['date']} {res['start_time']}~{res['end_time']}\n"
                    f"   💇 {res['service']} - {res['staff']}"
                )
            
            return f"""ご予約一覧です：

{chr(10).join(reservation_list)}

キャンセルしたい予約の**予約ID**（例：{reservations[0]['reservation_id']}）を入力してください。

❌ キャンセルをやめる場合は「キャンセル」とお送りください。"""
            
        except Exception as e:
            logging.error(f"Cancel request failed: {e}")
            return "申し訳ございません。キャンセルの処理中にエラーが発生しました。少し時間を置いてお試しください。"

    def _handle_reservation_id_cancellation(self, user_id: str, reservation_id: str) -> str:
        """Handle direct reservation cancellation by ID"""
        try:
            # Update status in Google Sheets to "Cancelled"
            from google_sheets_logger import GoogleSheetsLogger
            sheets_logger = GoogleSheetsLogger()
            sheets_success = sheets_logger.update_reservation_status(reservation_id, "Cancelled")
            
            if not sheets_success:
                return "申し訳ございません。キャンセル処理中にエラーが発生しました。\nスタッフまでお問い合わせください。"
            
            # Remove from Google Calendar
            calendar_success = self.google_calendar.cancel_reservation_by_id(reservation_id)
            
            if not calendar_success:
                logging.warning(f"Failed to remove reservation {reservation_id} from Google Calendar")
            
            return f"""✅ 予約のキャンセルが完了しました！

📋 キャンセル内容：
• 予約ID：{reservation_id}

またのご利用をお待ちしております。"""
                
        except Exception as e:
            logging.error(f"Reservation ID cancellation failed: {e}")
            return "申し訳ございません。キャンセル処理中にエラーが発生しました。\nスタッフまでお問い合わせください。"

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


def main():
    """Interactive test function for reservation flow"""
    print("=== Interactive Reservation Flow Tester ===")
    print("Type your messages to test the reservation system interactively!")
    print("Type 'quit' or 'exit' to stop testing.")
    print("Type 'help' to see available commands.")
    print("="*60)
    
    try:
        # Initialize ReservationFlow
        rf = ReservationFlow()
        print("✅ ReservationFlow initialized successfully")
        
        # Test user ID
        test_user_id = "interactive_test_user"
        
        print(f"\n🎯 Ready to test! User ID: {test_user_id}")
        print("💡 Try starting with: 予約したい")
        print("-" * 60)
        
        while True:
            try:
                # Get user input
                user_input = input("\n👤 You: ").strip()
                
                # Handle special commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye! Thanks for testing!")
                    break
                elif user_input.lower() == 'help':
                    print_help()
                    continue
                elif user_input.lower() == 'status':
                    print_user_status(rf, test_user_id)
                    continue
                elif user_input.lower() == 'clear':
                    clear_user_state(rf, test_user_id)
                    continue
                elif user_input.lower() == 'reset':
                    test_user_id = f"interactive_test_user_{int(time.time())}"
                    print(f"🔄 Reset with new user ID: {test_user_id}")
                    continue
                elif not user_input:
                    print("⚠️ Please enter a message or command.")
                    continue
                
                # Get response from reservation flow
                response = rf.get_response(test_user_id, user_input)
                
                # Display response
                print(f"\n🤖 Bot: {response}")
                
                # Show current user state
                if test_user_id in rf.user_states:
                    current_step = rf.user_states[test_user_id].get('step', 'unknown')
                    print(f"📊 Current step: {current_step}")
                else:
                    print("📊 Current step: No active session")
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye! Thanks for testing!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Error during initialization: {e}")
        import traceback
        traceback.print_exc()


def print_help():
    """Print help information for the interactive tester"""
    print("\n" + "="*60)
    print("📖 INTERACTIVE TESTER HELP")
    print("="*60)
    print("🎯 RESERVATION FLOW COMMANDS:")
    print("  • 予約したい, 予約お願い, 予約できますか - Start reservation")
    print("  • カット, カラー, パーマ, トリートメント - Select service")
    print("  • 田中, 佐藤, 山田, 未指定 - Select staff")
    print("  • 2025-01-15 (or any date) - Select date")
    print("  • 10:00~11:00 (or any time range) - Select time")
    print("  • はい, 確定, お願い - Confirm reservation")
    print("  • いいえ, キャンセル, やめる - Cancel reservation")
    print()
    print("🔄 NAVIGATION COMMANDS:")
    print("  • 日付変更, 日付を変更, 別の日 - Go back to date selection")
    print("  • サービス変更, サービスを変更 - Go back to service selection")
    print("  • キャンセル, 取り消し, やめる - Cancel current flow")
    print()
    print("📋 RESERVATION MANAGEMENT:")
    print("  • 予約キャンセル, 予約取り消し - Cancel existing reservation")
    print("  • 予約変更, 予約修正 - Modify existing reservation")
    print()
    print("🛠️ TESTER COMMANDS:")
    print("  • help - Show this help message")
    print("  • status - Show current user state")
    print("  • clear - Clear current user state")
    print("  • reset - Reset with new user ID")
    print("  • quit, exit, q - Exit the tester")
    print("="*60)


def print_user_status(rf, user_id):
    """Print current user state information"""
    print(f"\n📊 USER STATUS: {user_id}")
    print("-" * 40)
    
    if user_id in rf.user_states:
        state = rf.user_states[user_id]
        step = state.get('step', 'unknown')
        data = state.get('data', {})
        
        print(f"Current Step: {step}")
        print("Reservation Data:")
        for key, value in data.items():
            print(f"  • {key}: {value}")
    else:
        print("No active session")
    
    print("-" * 40)


def clear_user_state(rf, user_id):
    """Clear the current user state"""
    if user_id in rf.user_states:
        del rf.user_states[user_id]
        print(f"✅ Cleared user state for {user_id}")
    else:
        print(f"ℹ️ No user state found for {user_id}")


# Import time for reset functionality
import time


if __name__ == "__main__":
    main()
