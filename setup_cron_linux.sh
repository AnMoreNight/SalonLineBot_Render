#!/bin/bash
# Cron Job Setup Script for Reminder System (Linux)

echo "🕐 Setting up cron job for reminder system..."

# Get the current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CRON_LOG="$SCRIPT_DIR/cron_reminder.log"

# Check if the application is running
echo "Checking if the application is running..."
if curl -s http://localhost:8000/ > /dev/null; then
    echo "✅ Application is running on localhost:8000"
else
    echo "❌ Application is not running on localhost:8000"
    echo "Please start the application first with: python -m uvicorn api.index:app --host 0.0.0.0 --port 8000"
    exit 1
fi

# Test the endpoint
echo "Testing the reminder endpoint..."
TEST_RESPONSE=$(curl -s -X POST http://localhost:8000/api/run-reminders)
echo "Test response: $TEST_RESPONSE"

# Create cron job entry
CRON_ENTRY="0 9 * * * curl -X POST http://localhost:8000/api/run-reminders >> $CRON_LOG 2>&1"

# Add to crontab
echo "Adding cron job to crontab..."
(crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -

echo "✅ Cron job added successfully!"
echo "📅 Cron job will run daily at 9:00 AM"
echo "📝 Logs will be saved to: $CRON_LOG"
echo ""
echo "📋 Useful commands:"
echo "  View current crontab: crontab -l"
echo "  Edit crontab: crontab -e"
echo "  Remove cron job: crontab -e (then delete the line)"
echo "  View logs: tail -f $CRON_LOG"
echo ""
echo "⚠️  Note: The cron job will only run reminders at 9:00 AM Tokyo time"
echo "   You can disable the Python scheduler by setting REMINDER_SCHEDULER_ENABLED=false"
