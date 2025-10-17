"""
Scheduler for running daily reminder tasks
Runs at 9:00 AM daily to send reservation reminders
"""
import os
import time
import logging
import schedule
from datetime import datetime, timedelta
from dotenv import load_dotenv

class ReminderScheduler:
    def __init__(self):
        load_dotenv()
        self.enabled = os.getenv("REMINDER_SCHEDULER_ENABLED", "true").lower() == "true"
        self.timezone = os.getenv("TIMEZONE", "Asia/Tokyo")
        
        if self.enabled:
            logging.info("Reminder scheduler enabled")
            self._setup_schedule()
        else:
            logging.info("Reminder scheduler disabled")
    
    def _load_kb_data(self):
        """Load data from kb.json file"""
        try:
            import json
            
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
            
            # Try each possible path
            for kb_file in possible_paths:
                try:
                    with open(kb_file, 'r', encoding='utf-8') as f:
                        kb_data = json.load(f)
                    
                    # Convert array format to dictionary
                    kb_dict = {}
                    for item in kb_data:
                        key = item.get('キー', '')
                        value = item.get('例（置換値）', '')
                        kb_dict[key] = value
                    
                    return kb_dict
                except (FileNotFoundError, OSError):
                    continue
            
            # If none of the paths worked, raise an error
            raise FileNotFoundError(f"Could not find kb.json file. Tried paths: {possible_paths}")
            
        except Exception as e:
            logging.error(f"Error loading kb.json: {e}")
            return {}
    
    def _setup_schedule(self):
        """Setup the daily reminder schedule"""
        # Load reminder time from kb.json
        kb_data = self._load_kb_data()
        remind_time = kb_data.get('REMIND_TIME', '来店前日 09:00 自動配信')
        from datetime import datetime
        import pytz
        tokyo_tz = pytz.timezone('Asia/Tokyo')
        current_tokyo_time = datetime.now(tokyo_tz)
        logging.info(f"Current time(From reminder Scheduler): {current_tokyo_time.strftime('%Y-%m-%d %H:%M:%S')}")
        # Extract time from the string (e.g., "来店前日 09:00 自動配信" -> "09:00")
        import re
        time_match = re.search(r'(\d{2}):(\d{2})', remind_time)
        if time_match:
            schedule_time = f"{time_match.group(1)}:{time_match.group(2)}"
        else:
            schedule_time = "09:00"  # Default fallback
            logging.warning(f"Could not parse time from REMIND_TIME: {remind_time}, using default: {schedule_time}")
        logging.info("schedule time:", schedule_time)
        # Schedule reminders at the configured time
        schedule.every().day.at(schedule_time).do(self._run_reminders)
        
        logging.info(f"Reminder schedule set: Daily at {schedule_time} (from kb.json: {remind_time})")
    
    def _run_reminders(self):
        """Run the daily reminder process"""
        try:
            logging.info("Starting scheduled reminder process...")
            
            from api.reminder_system import reminder_system
            
            # Run the reminder system
            result = reminder_system.run_daily_reminders()
            
            # Log the results
            logging.info(f"Reminder process completed: {result['success_count']}/{result['total_count']} sent successfully")
            
            # Log any failures
            if result['failed_reservations']:
                logging.warning(f"Failed to send {len(result['failed_reservations'])} reminders")
                for res in result['failed_reservations']:
                    logging.warning(f"Failed reminder: {res.get('client_name', 'N/A')} - {res.get('date', 'N/A')} {res.get('start_time', 'N/A')}")
            
        except Exception as e:
            logging.error(f"Error in scheduled reminder process: {e}")
            import traceback
            traceback.print_exc()
    
    def run_scheduler(self):
        """Run the scheduler loop"""
        if not self.enabled:
            logging.info("Scheduler is disabled, not running")
            return
        
        logging.info("Starting reminder scheduler...")
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                logging.info("Scheduler stopped by user")
                break
            except Exception as e:
                logging.error(f"Error in scheduler loop: {e}")
                time.sleep(60)  # Wait a minute before retrying
    
    def run_reminders_now(self):
        """Manually run reminders (for testing)"""
        logging.info("Manually running reminders...")
        self._run_reminders()
    
    def get_next_run_time(self):
        """Get the next scheduled run time"""
        if not self.enabled:
            return None
        
        jobs = schedule.get_jobs()
        if jobs:
            return jobs[0].next_run
        return None
    
    def get_status(self):
        """Get scheduler status"""
        # Get configured reminder time from kb.json
        kb_data = self._load_kb_data()
        remind_time = kb_data.get('REMIND_TIME', '来店前日 09:00 自動配信')
        
        return {
            'enabled': self.enabled,
            'timezone': self.timezone,
            'remind_time': remind_time,
            'next_run': self.get_next_run_time(),
            'jobs_count': len(schedule.get_jobs())
        }


# Global instance
reminder_scheduler = ReminderScheduler()


def start_reminder_scheduler():
    """Start the reminder scheduler"""
    reminder_scheduler.run_scheduler()


def run_reminders_manually():
    """Manually run reminders (for testing)"""
    reminder_scheduler.run_reminders_now()


if __name__ == "__main__":
    # Test the scheduler
    print("🧪 Testing Reminder Scheduler")
    print("=" * 50)
    
    scheduler = ReminderScheduler()
    
    print(f"📊 Scheduler Status:")
    status = scheduler.get_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    print()
    
    if scheduler.enabled:
        print("✅ Scheduler is enabled")
        print("⏰ Next run time:", scheduler.get_next_run_time())
        print()
        
        # Test manual run
        print("🧪 Testing manual reminder run...")
        scheduler.run_reminders_now()
        
    else:
        print("❌ Scheduler is disabled")
        print("Set REMINDER_SCHEDULER_ENABLED=true to enable")
    
    print("\n✅ Scheduler test completed!")
