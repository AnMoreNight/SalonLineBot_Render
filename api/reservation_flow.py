"""
Reservation flow system with intent detection, candidate suggestions, and confirmation
"""
import re
import os
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import logging
from api.google_calendar import GoogleCalendarHelper

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
            # If user is in cancel or modify flow, continue the flow regardless of message type
            if step in ["cancel_select_reservation", "cancel_confirm", "modify_select_reservation", "modify_select_field", "modify_confirm"]:
                intent = step.split("_")[0]  # Return "cancel" or "modify"
                logging.info(f"Intent detection - User: {user_id}, Step: {step}, Intent: {intent}")
                return intent
        
        # Check if message is a reservation ID format
        if re.match(r"^RES-\d{8}-\d{4}$", message):
            # If it's a reservation ID but user is not in any flow, we need to determine intent
            # For now, we'll return "general" and let the user specify their intent
            return "general"
        
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
        
        # Parse date from user input - only accept YYYY-MM-DD format
        selected_date = None
        
        # Try to parse YYYY-MM-DD format
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', message)
        if date_match:
            selected_date = date_match.group(1)
            # Validate the date format
            try:
                datetime.strptime(selected_date, "%Y-%m-%d")
            except ValueError:
                selected_date = None
        
        if not selected_date:
            return "申し訳ございませんが、日付の形式が正しくありません。\n「YYYY-MM-DD」の形式で入力してください。\n例）2025-01-15"
        
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
            return self._handle_cancel_request(user_id, message)
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

    def _handle_cancel_request(self, user_id: str, message: str = None) -> str:
        """Handle reservation cancellation with reservation selection"""
        state = self.user_states.get(user_id)
        
        # Check for cancellation of the cancel flow
        flow_cancel_keywords = self.navigation_keywords.get("flow_cancel", [])
        if message and message.lower() in flow_cancel_keywords:
            if user_id in self.user_states:
                del self.user_states[user_id]
            return "キャンセルをキャンセルいたします。またのご利用をお待ちしております。"
        
        # Step 1: Start cancellation flow - show user's reservations
        if not state or state.get("step") not in ["cancel_select_reservation", "cancel_confirm"]:
            self.user_states[user_id] = {"step": "cancel_select_reservation"}
            return self._show_user_reservations_for_cancellation(user_id)
        
        # Step 2: Handle reservation selection
        elif state.get("step") == "cancel_select_reservation":
            return self._handle_cancel_reservation_selection(user_id, message)
        
        # Step 3: Handle confirmation
        elif state.get("step") == "cancel_confirm":
            return self._handle_cancel_confirmation(user_id, message)
        
        return "キャンセルフローに問題が発生しました。最初からやり直してください。"
    
    def _show_user_reservations_for_cancellation(self, user_id: str) -> str:
        """Show user's reservations for cancellation selection"""
        try:
            from api.google_sheets_logger import GoogleSheetsLogger
            sheets_logger = GoogleSheetsLogger()
            client_name = self._get_line_display_name(user_id)
            
            # Get user's reservations
            reservations = sheets_logger.get_user_reservations(client_name)
            logging.info(f"Found {len(reservations) if reservations else 0} reservations for client: {client_name}")
            
            if not reservations:
                return "申し訳ございませんが、あなたの予約が見つかりませんでした。\nスタッフまでお問い合わせください。"
            
            # Store reservations for selection
            self.user_states[user_id]["user_reservations"] = reservations
            
            # Create reservation list
            reservation_list = []
            for i, res in enumerate(reservations[:5], 1):  # Show max 5 reservations
                reservation_list.append(f"{i}️⃣ {res['date']} {res['start_time']}~{res['end_time']} - {res['service']} ({res['reservation_id']})")
            
            return f"""ご予約のキャンセルですね。

あなたの予約一覧：

{chr(10).join(reservation_list)}

キャンセルしたい予約の番号（1-{len(reservations[:5])}）を入力してください。

または、予約IDを直接入力することもできます。
例）RES-20250115-0001

❌ キャンセルをやめる場合は「キャンセル」とお送りください。"""
            
        except Exception as e:
            logging.error(f"Failed to show user reservations for cancellation: {e}")
            return "申し訳ございません。予約検索中にエラーが発生しました。スタッフまでお問い合わせください。"
    
    def _handle_cancel_reservation_selection(self, user_id: str, message: str) -> str:
        """Handle reservation selection for cancellation"""
        state = self.user_states[user_id]
        reservations = state["user_reservations"]
        
        try:
            # Check if message is a reservation ID
            if re.match(r"^RES-\d{8}-\d{4}$", message):
                reservation_id = message
                # Find the reservation
                selected_reservation = None
                logging.info(f"Looking for reservation ID: {reservation_id}")
                logging.info(f"Available reservations: {[res['reservation_id'] for res in reservations]}")
                for res in reservations:
                    if res["reservation_id"] == reservation_id:
                        selected_reservation = res
                        break
                
                if selected_reservation:
                    # Store selected reservation and move to confirmation
                    self.user_states[user_id]["selected_reservation"] = selected_reservation
                    self.user_states[user_id]["step"] = "cancel_confirm"
                    
                    # Get Google Calendar URL
                    calendar_url = self.google_calendar.get_calendar_url()
                    
                    return f"""キャンセルする予約を確認してください：

📋 予約内容：
🆔 予約ID：{selected_reservation['reservation_id']}
📅 日時：{selected_reservation['date']} {selected_reservation['start_time']}~{selected_reservation['end_time']}
💇 サービス：{selected_reservation['service']}
👨‍💼 担当者：{selected_reservation['staff']}

🗓️ **Googleカレンダーで予約状況を確認：**
🔗 {calendar_url}

この予約をキャンセルしますか？
「はい」または「確定」とお送りください。

❌ キャンセルをやめる場合は「キャンセル」とお送りください。"""
                else:
                    return "申し訳ございませんが、その予約IDが見つからないか、あなたの予約ではありません。\n正しい予約IDまたは番号を入力してください。"
            
            # Check if message is a number (reservation selection)
            elif message.isdigit():
                reservation_index = int(message) - 1
                if 0 <= reservation_index < len(reservations):
                    selected_reservation = reservations[reservation_index]
                    
                    # Store selected reservation and move to confirmation
                    self.user_states[user_id]["selected_reservation"] = selected_reservation
                    self.user_states[user_id]["step"] = "cancel_confirm"
                    
                    # Get Google Calendar URL
                    calendar_url = self.google_calendar.get_calendar_url()
                    
                    return f"""キャンセルする予約を確認してください：

📋 予約内容：
🆔 予約ID：{selected_reservation['reservation_id']}
📅 日時：{selected_reservation['date']} {selected_reservation['start_time']}~{selected_reservation['end_time']}
💇 サービス：{selected_reservation['service']}
👨‍💼 担当者：{selected_reservation['staff']}

🗓️ **Googleカレンダーで予約状況を確認：**
🔗 {calendar_url}

この予約をキャンセルしますか？
「はい」または「確定」とお送りください。

❌ キャンセルをやめる場合は「キャンセル」とお送りください。"""
                else:
                    return f"申し訳ございませんが、その番号は選択できません。\n1から{len(reservations)}の番号を入力してください。"
            else:
                return f"申し訳ございませんが、正しい形式で入力してください。\n番号（1-{len(reservations)}）または予約ID（RES-YYYYMMDD-XXXX）を入力してください。"
                
        except Exception as e:
            logging.error(f"Reservation selection for cancellation failed: {e}")
            return "申し訳ございません。予約選択中にエラーが発生しました。スタッフまでお問い合わせください。"
    
    def _handle_cancel_confirmation(self, user_id: str, message: str) -> str:
        """Handle cancellation confirmation"""
        state = self.user_states[user_id]
        reservation = state["selected_reservation"]
        
        # Check for confirmation keywords
        yes_keywords = self.confirmation_keywords.get("yes", [])
        no_keywords = self.confirmation_keywords.get("no", [])
        
        if any(keyword in message for keyword in yes_keywords):
            # Execute cancellation
            return self._execute_reservation_cancellation(user_id, reservation)
        elif any(keyword in message for keyword in no_keywords):
            # Cancel the cancellation
            del self.user_states[user_id]
            return "キャンセルをキャンセルいたします。予約はそのまま残ります。\nまたのご利用をお待ちしております。"
        else:
            return "「はい」または「確定」でキャンセルを確定するか、「キャンセル」で中止してください。"
    
    def _execute_reservation_cancellation(self, user_id: str, reservation: Dict) -> str:
        """Execute the actual reservation cancellation"""
        try:
            from api.google_sheets_logger import GoogleSheetsLogger
            sheets_logger = GoogleSheetsLogger()
            
            reservation_id = reservation["reservation_id"]
            
            # Update status in Google Sheets to "Cancelled"
            sheets_success = sheets_logger.update_reservation_status(reservation_id, "Cancelled")
            
            if not sheets_success:
                return "申し訳ございません。キャンセル処理中にエラーが発生しました。\nスタッフまでお問い合わせください。"
            
            # Remove from Google Calendar
            calendar_success = self.google_calendar.cancel_reservation_by_id(reservation_id)
            
            if not calendar_success:
                logging.warning(f"Failed to remove reservation {reservation_id} from Google Calendar")
            
            # Clear user state
            del self.user_states[user_id]
            
            return f"""✅ 予約のキャンセルが完了しました！

📋 キャンセル内容：
🆔 予約ID：{reservation_id}
📅 日時：{reservation['date']} {reservation['start_time']}~{reservation['end_time']}
💇 サービス：{reservation['service']}
👨‍💼 担当者：{reservation['staff']}

またのご利用をお待ちしております。"""
                
        except Exception as e:
            logging.error(f"Reservation cancellation execution failed: {e}")
            return "申し訳ございません。キャンセル処理中にエラーが発生しました。\nスタッフまでお問い合わせください。"

    def _handle_reservation_id_cancellation(self, user_id: str, reservation_id: str) -> str:
        """Handle direct reservation cancellation by ID"""
        try:
            # Update status in Google Sheets to "Cancelled"
            from api.google_sheets_logger import GoogleSheetsLogger
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


    def _parse_time_range(self, text: str) -> tuple:
        """Parse start and end times from user input.
        Returns tuple of (start_time, end_time) in HH:MM format, or (None, None) if invalid.
        Only supports standard HH:MM format.
        """
        text = text.strip()
        
        # Pattern 1: "10:00~11:00" or "10:00～11:00"
        match = re.search(r'^(\d{1,2}:\d{2})[~～](\d{1,2}:\d{2})$', text)
        if match:
            start_time = match.group(1)
            end_time = match.group(2)
            # Validate time format
            try:
                datetime.strptime(start_time, "%H:%M")
                datetime.strptime(end_time, "%H:%M")
                return start_time, end_time
            except ValueError:
                pass
        
        # Pattern 2: "10:00 11:00" (space separated)
        match = re.search(r'^(\d{1,2}:\d{2})\s+(\d{1,2}:\d{2})$', text)
        if match:
            start_time = match.group(1)
            end_time = match.group(2)
            # Validate time format
            try:
                datetime.strptime(start_time, "%H:%M")
                datetime.strptime(end_time, "%H:%M")
                return start_time, end_time
            except ValueError:
                pass
        
        return None, None

    def _handle_modify_request(self, user_id: str, message: str) -> str:
        """Handle comprehensive reservation modification with enhanced features"""
        state = self.user_states.get(user_id)
        
        # Check for cancellation
        flow_cancel_keywords = self.navigation_keywords.get("flow_cancel", [])
        if message.lower() in flow_cancel_keywords:
            if user_id in self.user_states:
                del self.user_states[user_id]
            return "予約変更をキャンセルいたします。またのご利用をお待ちしております。"
        
        # Step 1: Start modification flow - show user's reservations
        if not state or state.get("step") not in ["modify_select_reservation", "modify_select_field", "modify_confirm"]:
            self.user_states[user_id] = {"step": "modify_select_reservation"}
            return self._show_user_reservations_for_modification(user_id)
        
        # Step 2: Handle reservation selection
        if state.get("step") == "modify_select_reservation":
            return self._handle_modify_reservation_selection(user_id, message)
        
        # Step 3: Handle field selection
        elif state.get("step") == "modify_select_field":
            logging.info(f"Routing to field selection - User: {user_id}, Message: '{message}'")
            return self._handle_field_selection(user_id, message)
        
        # Step 4: Handle confirmation
        elif state.get("step") == "modify_confirm":
            return self._handle_modification_confirmation(user_id, message)
        
        return "予約変更フローに問題が発生しました。最初からやり直してください。"
    
    def _show_user_reservations_for_modification(self, user_id: str) -> str:
        """Show user's reservations for modification selection"""
        try:
            from api.google_sheets_logger import GoogleSheetsLogger
            sheets_logger = GoogleSheetsLogger()
            client_name = self._get_line_display_name(user_id)
            
            # Get user's reservations
            reservations = sheets_logger.get_user_reservations(client_name)
            
            if not reservations:
                return "申し訳ございませんが、あなたの予約が見つかりませんでした。\nスタッフまでお問い合わせください。"
            
            # Store reservations for selection
            self.user_states[user_id]["user_reservations"] = reservations
            
            # Create reservation list
            reservation_list = []
            for i, res in enumerate(reservations[:5], 1):  # Show max 5 reservations
                reservation_list.append(f"{i}️⃣ {res['date']} {res['start_time']}~{res['end_time']} - {res['service']} ({res['reservation_id']})")
            
            return f"""ご予約の変更ですね。

あなたの予約一覧：

{chr(10).join(reservation_list)}

変更したい予約の番号（1-{len(reservations[:5])}）を入力してください。

または、予約IDを直接入力することもできます。
例）RES-20250115-0001

❌ 変更をやめる場合は「キャンセル」とお送りください。"""
            
        except Exception as e:
            logging.error(f"Failed to show user reservations for modification: {e}")
            return "申し訳ございません。予約検索中にエラーが発生しました。スタッフまでお問い合わせください。"
    
    def _handle_modify_reservation_selection(self, user_id: str, message: str) -> str:
        """Handle reservation selection for modification"""
        state = self.user_states[user_id]
        reservations = state["user_reservations"]
        
        try:
            # Check if message is a reservation ID
            if re.match(r"^RES-\d{8}-\d{4}$", message):
                reservation_id = message
                # Find the reservation
                selected_reservation = None
                logging.info(f"Looking for reservation ID: {reservation_id}")
                logging.info(f"Available reservations: {[res['reservation_id'] for res in reservations]}")
                for res in reservations:
                    if res["reservation_id"] == reservation_id:
                        selected_reservation = res
                        break
                
                if selected_reservation:
                    # Store selected reservation and move to field selection
                    self.user_states[user_id]["reservation_data"] = selected_reservation
                    self.user_states[user_id]["step"] = "modify_select_field"
                    
                    # Get Google Calendar URL
                    calendar_url = self.google_calendar.get_calendar_url()
                    
                    return f"""予約が見つかりました！

📋 現在の予約内容：
🆔 予約ID：{selected_reservation['reservation_id']}
📅 日時：{selected_reservation['date']} {selected_reservation['start_time']}~{selected_reservation['end_time']}
💇 サービス：{selected_reservation['service']}
👨‍💼 担当者：{selected_reservation['staff']}

🗓️ **Googleカレンダーで予約状況を確認：**
🔗 {calendar_url}

何を変更しますか？
1️⃣ 日時変更したい
2️⃣ サービス変更したい
3️⃣ 担当者変更したい"""
                else:
                    return "申し訳ございませんが、その予約IDが見つからないか、あなたの予約ではありません。\n正しい予約IDまたは番号を入力してください。"
            
            # Check if message is a number (reservation selection)
            elif message.isdigit():
                reservation_index = int(message) - 1
                if 0 <= reservation_index < len(reservations):
                    selected_reservation = reservations[reservation_index]
                    
                    # Store selected reservation and move to field selection
                    self.user_states[user_id]["reservation_data"] = selected_reservation
                    self.user_states[user_id]["step"] = "modify_select_field"
                    
                    # Get Google Calendar URL
                    calendar_url = self.google_calendar.get_calendar_url()
                    
                    return f"""予約が見つかりました！

📋 現在の予約内容：
🆔 予約ID：{selected_reservation['reservation_id']}
📅 日時：{selected_reservation['date']} {selected_reservation['start_time']}~{selected_reservation['end_time']}
💇 サービス：{selected_reservation['service']}
👨‍💼 担当者：{selected_reservation['staff']}

🗓️ **Googleカレンダーで予約状況を確認：**
🔗 {calendar_url}

何を変更しますか？
1️⃣ 日時変更したい
2️⃣ サービス変更したい
3️⃣ 担当者変更したい"""
                else:
                    return f"申し訳ございませんが、その番号は選択できません。\n1から{len(reservations)}の番号を入力してください。"
            else:
                return f"申し訳ございませんが、正しい形式で入力してください。\n番号（1-{len(reservations)}）または予約ID（RES-YYYYMMDD-XXXX）を入力してください。"
                
        except Exception as e:
            logging.error(f"Reservation selection for modification failed: {e}")
            return "申し訳ございません。予約選択中にエラーが発生しました。スタッフまでお問い合わせください。"
    
    def _handle_field_selection(self, user_id: str, message: str) -> str:
        """Handle field selection for modification"""
        state = self.user_states[user_id]
        reservation = state["reservation_data"]
        
        logging.info(f"Field selection - User: {user_id}, Message: '{message}', State: {state}")
        
        # Check for numeric selection first
        if message.strip() == "1":
            logging.info("Selected time modification (1)")
            return self._handle_time_modification(user_id, message)
        elif message.strip() == "2":
            logging.info("Selected service modification (2)")
            return self._handle_service_modification(user_id, message)
        elif message.strip() == "3":
            logging.info("Selected staff modification (3)")
            return self._handle_staff_modification(user_id, message)
        
        # Check for specific modification types
        time_change_keywords = self.navigation_keywords.get("time_change", [])
        service_change_keywords = self.navigation_keywords.get("service_change", [])
        staff_change_keywords = self.navigation_keywords.get("staff_change", [])
        
        # Normalize message for better matching
        message_normalized = message.strip().lower()
        
        # Check keywords with case-insensitive matching
        if any(keyword.lower() in message_normalized for keyword in time_change_keywords):
            logging.info(f"Selected time modification via keyword: '{message}'")
            return self._handle_time_modification(user_id, message)
        elif any(keyword.lower() in message_normalized for keyword in service_change_keywords):
            logging.info(f"Selected service modification via keyword: '{message}'")
            return self._handle_service_modification(user_id, message)
        elif any(keyword.lower() in message_normalized for keyword in staff_change_keywords):
            logging.info(f"Selected staff modification via keyword: '{message}'")
            return self._handle_staff_modification(user_id, message)
        else:
            return """何を変更しますか？以下のキーワードでお答えください：

1️⃣ 時間変更したい
2️⃣ サービス変更したい  
3️⃣ 担当者変更したい

または、番号（1-3）で選択してください。"""
    
    def _handle_time_modification(self, user_id: str, message: str) -> str:
        """Handle time modification with current reservation inclusion"""
        state = self.user_states[user_id]
        reservation = state["reservation_data"]
        
        # Get available slots including current reservation
        available_slots = self.google_calendar.get_available_slots_for_modification(
            reservation["date"], 
            reservation["reservation_id"]
        )
        
        if not available_slots:
            return f"申し訳ございませんが、{reservation['date']}は空いている時間がありません。\n別の日付での変更をご希望の場合は、スタッフまでお問い合わせください。"
        
        # Store modification type and show available times
        self.user_states[user_id]["modification_type"] = "time"
        self.user_states[user_id]["available_slots"] = available_slots
        self.user_states[user_id]["step"] = "modify_confirm"
        
        # Create time options message
        time_options = []
        for slot in available_slots:
            current_marker = " (現在の予約)" if slot["time"] == reservation["start_time"] else ""
            time_options.append(f"✅ {slot['time']}~{slot['end_time']}{current_marker}")
        
        return f"""時間変更ですね！

📅 {reservation['date']} の利用可能な時間：
{chr(10).join(time_options)}

新しい時間を「開始時間~終了時間」の形式で入力してください。
例）13:00~14:00"""
    
    def _handle_service_modification(self, user_id: str, message: str) -> str:
        """Handle service modification with duration validation"""
        state = self.user_states[user_id]
        reservation = state["reservation_data"]
        
        # Store modification type
        self.user_states[user_id]["modification_type"] = "service"
        self.user_states[user_id]["step"] = "modify_confirm"
        
        # Show available services
        service_options = []
        for service_name, service_info in self.services.items():
            current_marker = " (現在のサービス)" if service_name == reservation["service"] else ""
            service_options.append(f"✅ {service_name} ({service_info['duration']}分・{service_info['price']:,}円){current_marker}")
        
        return f"""サービス変更ですね！

現在のサービス：{reservation['service']} ({reservation['duration']}分)

利用可能なサービス：
{chr(10).join(service_options)}

新しいサービス名を入力してください。"""
    
    def _handle_staff_modification(self, user_id: str, message: str) -> str:
        """Handle staff modification"""
        state = self.user_states[user_id]
        reservation = state["reservation_data"]
        
        # Store modification type
        self.user_states[user_id]["modification_type"] = "staff"
        self.user_states[user_id]["step"] = "modify_confirm"
        
        # Show available staff
        staff_options = []
        for staff_name, staff_info in self.staff_members.items():
            current_marker = " (現在の担当者)" if staff_name == reservation["staff"] else ""
            staff_options.append(f"✅ {staff_name} ({staff_info['specialty']}・{staff_info['experience']}){current_marker}")
        
        return f"""担当者変更ですね！

現在の担当者：{reservation['staff']}

利用可能な担当者：
{chr(10).join(staff_options)}

新しい担当者名を入力してください。"""
    
    def _handle_modification_confirmation(self, user_id: str, message: str) -> str:
        """Handle modification confirmation and execution"""
        state = self.user_states[user_id]
        reservation = state["reservation_data"]
        modification_type = state["modification_type"]
        
        try:
            from api.google_sheets_logger import GoogleSheetsLogger
            sheets_logger = GoogleSheetsLogger()
            
            # Process the modification based on type
            if modification_type == "time":
                return self._process_time_modification(user_id, message, reservation, sheets_logger)
            elif modification_type == "service":
                return self._process_service_modification(user_id, message, reservation, sheets_logger)
            elif modification_type == "staff":
                return self._process_staff_modification(user_id, message, reservation, sheets_logger)
            else:
                return "申し訳ございません。変更処理中にエラーが発生しました。"
                
        except Exception as e:
            logging.error(f"Modification confirmation failed: {e}")
            return "申し訳ございません。変更処理中にエラーが発生しました。スタッフまでお問い合わせください。"
    
    def _process_time_modification(self, user_id: str, message: str, reservation: Dict, sheets_logger) -> str:
        """Process time modification"""
        # Parse time range (ONLY accept time period format)
        start_time, end_time = self._parse_time_range(message)
        
        if not start_time or not end_time:
            return "時間の形式が正しくありません。\n「開始時間~終了時間」の形式で入力してください。\n例）13:00~14:00"
        
        # Validate that the start time is in the available slots
        available_slots = self.user_states[user_id]["available_slots"]
        
        # Check if the start time exists in available slots
        start_time_available = any(slot["time"] == start_time for slot in available_slots)
        
        if not start_time_available:
            return "申し訳ございませんが、その時間は利用できません。\n利用可能な時間から選択してください。"
        
        # Calculate the duration of the input time period
        try:
            from datetime import datetime
            start_dt = datetime.strptime(start_time, "%H:%M")
            end_dt = datetime.strptime(end_time, "%H:%M")
            duration_minutes = int((end_dt - start_dt).total_seconds() / 60)
            
            if duration_minutes <= 0:
                return "終了時間は開始時間より後である必要があります。\n例）13:00~14:00"
        except Exception as e:
            logging.error(f"Error calculating duration: {e}")
            return "時間の形式が正しくありません。\n例）13:00~14:00"
        
        # Update Google Calendar
        calendar_success = self.google_calendar.modify_reservation_time(
            reservation["client_name"], 
            reservation["date"], 
            start_time
        )
        
        if not calendar_success:
            return "申し訳ございません。カレンダーの更新に失敗しました。スタッフまでお問い合わせください。"
        
        # Update Google Sheets
        field_updates = {
            "Start Time": start_time,
            "End Time": end_time
        }
        sheets_success = sheets_logger.update_reservation_data(reservation["reservation_id"], field_updates)
        
        if not sheets_success:
            logging.warning(f"Failed to update sheets for reservation {reservation['reservation_id']}")
        
        # Clear user state
        del self.user_states[user_id]
        
        return f"""✅ 時間変更が完了しました！

📋 変更内容：
🆔 予約ID：{reservation['reservation_id']}
📅 日時：{reservation['date']} {start_time}~{end_time}
💇 サービス：{reservation['service']}
👨‍💼 担当者：{reservation['staff']}

ご予約ありがとうございました！"""
    
    def _process_service_modification(self, user_id: str, message: str, reservation: Dict, sheets_logger) -> str:
        """Process service modification with duration validation"""
        # Normalize and validate service
        message_normalized = message.strip()
        new_service = None
        
        # Try exact match first
        if message_normalized in self.services:
            new_service = message_normalized
        else:
            # Try case-insensitive match
            for service_name in self.services.keys():
                if service_name.lower() == message_normalized.lower():
                    new_service = service_name
                    break
            
            # Try partial match (if user types part of the service name)
            if not new_service:
                for service_name in self.services.keys():
                    if message_normalized in service_name or service_name in message_normalized:
                        new_service = service_name
                        break
        
        if not new_service:
            available_services = "、".join(self.services.keys())
            return f"申し訳ございませんが、そのサービスは提供しておりません。\n\n利用可能なサービス：\n{available_services}\n\n上記から選択してください。"
        new_service_info = self.services[new_service]
        new_duration = new_service_info["duration"]
        new_price = new_service_info["price"]
        
        # Check if the new service can fit in any available slot on the date (ignoring current reservation)
        available_slots = self.google_calendar.get_available_slots_for_service(
            reservation["date"], 
            new_service,
            reservation["reservation_id"]
        )
        
        if not available_slots:
            return f"""申し訳ございませんが、{reservation['date']}には{new_service}（{new_duration}分）が可能な時間がありません。

別の日付または別のサービスをご検討いただくか、スタッフまでお問い合わせください。"""
        
        # Update Google Calendar (recalculate end time)
        calendar_success = self.google_calendar.modify_reservation_time(
            reservation["client_name"], 
            reservation["date"], 
            reservation["start_time"]
        )
        
        if not calendar_success:
            return "申し訳ございません。カレンダーの更新に失敗しました。スタッフまでお問い合わせください。"
        
        # Update Google Sheets
        field_updates = {
            "Service": new_service,
            "Duration (min)": new_duration,
            "Price": new_price
        }
        sheets_success = sheets_logger.update_reservation_data(reservation["reservation_id"], field_updates)
        
        if not sheets_success:
            logging.warning(f"Failed to update sheets for reservation {reservation['reservation_id']}")
        
        # Clear user state
        del self.user_states[user_id]
        
        return f"""✅ サービス変更が完了しました！

📋 変更内容：
🆔 予約ID：{reservation['reservation_id']}
📅 日時：{reservation['date']} {reservation['start_time']}~{reservation['end_time']}
💇 サービス：{new_service} ({new_duration}分・{new_price:,}円)
👨‍💼 担当者：{reservation['staff']}

ご予約ありがとうございました！"""
    
    def _process_staff_modification(self, user_id: str, message: str, reservation: Dict, sheets_logger) -> str:
        """Process staff modification"""
        # Normalize and validate staff
        message_normalized = message.strip()
        new_staff = None
        
        # Try exact match first
        if message_normalized in self.staff_members:
            new_staff = message_normalized
        else:
            # Try case-insensitive match
            for staff_name in self.staff_members.keys():
                if staff_name.lower() == message_normalized.lower():
                    new_staff = staff_name
                    break
            
            # Try partial match (if user types part of the staff name)
            if not new_staff:
                for staff_name in self.staff_members.keys():
                    if message_normalized in staff_name or staff_name in message_normalized:
                        new_staff = staff_name
                        break
        
        if not new_staff:
            available_staff = "、".join(self.staff_members.keys())
            return f"申し訳ございませんが、その担当者は選択できません。\n\n利用可能な担当者：\n{available_staff}\n\n上記から選択してください。"
        
        # Update Google Sheets
        field_updates = {
            "Staff": new_staff
        }
        sheets_success = sheets_logger.update_reservation_data(reservation["reservation_id"], field_updates)
        
        if not sheets_success:
            return "申し訳ございません。担当者の更新に失敗しました。スタッフまでお問い合わせください。"
        
        # Clear user state
        del self.user_states[user_id]
        
        return f"""✅ 担当者変更が完了しました！

📋 変更内容：
🆔 予約ID：{reservation['reservation_id']}
📅 日時：{reservation['date']} {reservation['start_time']}~{reservation['end_time']}
💇 サービス：{reservation['service']}
👨‍💼 担当者：{new_staff}

ご予約ありがとうございました！"""


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
