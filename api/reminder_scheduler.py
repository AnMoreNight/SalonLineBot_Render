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
    
    def _setup_schedule(self):
        """Setup the daily reminder schedule"""
        # Schedule reminders to run at 9:00 AM daily
        schedule.every().day.at("09:40").do(self._run_reminders)
        
        logging.info("Reminder schedule set: Daily at 9:00 AM")
    
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
        return {
            'enabled': self.enabled,
            'timezone': self.timezone,
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
