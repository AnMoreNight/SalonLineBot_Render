# LINE Notifications Setup Guide

This guide explains how to set up LINE notifications for the salon booking system.

## 📋 Prerequisites

1. **LINE Developer Account**: You need a LINE Developer account
2. **LINE Bot Channel**: You need to create a LINE Bot channel
3. **LINE Messaging API**: Your bot must have Messaging API enabled

## 🔧 Step 1: Get LINE Channel Access Token

### Method 1: From LINE Developers Console (Recommended)

1. **Go to LINE Developers Console**
   - Visit: https://developers.line.biz/console/
   - Log in with your LINE account

2. **Select Your Bot Channel**
   - Click on your bot channel from the list
   - If you don't have one, create a new "Messaging API" channel

3. **Get Channel Access Token**
   - Go to the "Messaging API" tab
   - Scroll down to "Channel access token"
   - Click "Issue" to generate a new token
   - Copy the token (it looks like: `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`)

### Method 2: From Existing Bot (If you already have one)

If you already have a LINE bot running, you can use the same Channel Access Token:

1. Check your existing bot's configuration
2. Look for the Channel Access Token in your environment variables
3. Use the same token for notifications

## 👤 Step 2: Get LINE User ID

The User ID is the LINE ID of the person who should receive notifications (usually the salon owner/manager).

### Method 1: Using LINE Bot (Recommended)

1. **Add your bot as a friend**
   - Scan the QR code or add via LINE ID
   - Send any message to the bot

2. **Check bot logs or database**
   - When a user sends a message, LINE provides the user ID
   - Look for logs containing `user_id` or check your database

3. **Use a test message**
   - Send a message like "test" to your bot
   - Check the logs for the user ID (it looks like: `U1234567890abcdef1234567890abcdef1`)

### Method 2: Using LINE Developers Console

1. **Go to your bot channel**
2. **Check "Webhook" settings**
3. **Look for user IDs in webhook logs**

### Method 3: Programmatically (For testing)

You can create a simple script to capture user IDs:

```python
# Add this to your bot temporarily to capture user IDs
def handle_message(event):
    user_id = event.source.user_id
    print(f"User ID: {user_id}")
    # Send this back to the user so they can see their ID
    reply_message = f"Your LINE User ID is: {user_id}"
    # Send reply...
```

## ⚙️ Step 3: Configure Environment Variables

Add these environment variables to your `.env` file or deployment environment:

```bash
# Notification method (choose one)
NOTIFICATION_METHOD=line

# LINE notification settings
LINE_CHANNEL_ACCESS_TOKEN=your_channel_access_token_here
LINE_NOTIFICATION_USER_ID=your_user_id_here
```

### Example Configuration:

```bash
# For LINE notifications only
NOTIFICATION_METHOD=line
LINE_CHANNEL_ACCESS_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LINE_NOTIFICATION_USER_ID=U1234567890abcdef1234567890abcdef1

# For both Slack and LINE notifications
NOTIFICATION_METHOD=both
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
LINE_CHANNEL_ACCESS_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LINE_NOTIFICATION_USER_ID=U1234567890abcdef1234567890abcdef1
```

## 🧪 Step 4: Testing LINE Notifications

### Test 1: Basic Configuration Test

Run the test script to verify your configuration:

```bash
python test_line_notifications.py
```

### Test 2: Manual Test

You can test manually by sending a test notification:

```python
from api.line_notifier import line_notifier

# Test basic notification
success = line_notifier.send_notification(
    message="🧪 This is a test notification from your salon bot!",
    title="Test Notification"
)

if success:
    print("✅ LINE notification sent successfully!")
else:
    print("❌ Failed to send LINE notification")
```

### Test 3: Full System Test

Test all notification types:

```python
from api.notification_manager import notification_manager

# Test user login
manager.notify_user_login("test_user", "Test User")

# Test reservation confirmation
test_reservation = {
    "reservation_id": "TEST-001",
    "date": "2025-01-20",
    "start_time": "10:00",
    "end_time": "11:00",
    "service": "カット",
    "staff": "田中"
}
manager.notify_reservation_confirmation(test_reservation, "Test Client")
```

## 📱 What LINE Notifications Look Like

LINE notifications will appear as text messages in your LINE chat:

```
📢 🔐 User Login

👤 **User Login**
• User ID: `U1234567890abcdef1234567890abcdef1`
• Display Name: 田中太郎
• Time: 2025-01-20 14:30:25
```

```
📢 📅 New Reservation

✅ **New Reservation Confirmed**
• Reservation ID: `RES-20250120-001`
• Client: 田中太郎
• Date: 2025-01-20
• Time: 10:00~11:00
• Service: カット
• Staff: 田中
• Duration: 60 minutes
• Price: ¥3,000
• Confirmed at: 2025-01-20 14:30:25
```

## 🔍 Troubleshooting

### Common Issues:

1. **"LINE notification not configured"**
   - Check that `LINE_CHANNEL_ACCESS_TOKEN` is set
   - Check that `LINE_NOTIFICATION_USER_ID` is set
   - Verify the token is valid and not expired

2. **"Failed to send LINE notification: 401"**
   - Invalid Channel Access Token
   - Token may have expired (generate a new one)

3. **"Failed to send LINE notification: 403"**
   - User ID is invalid or user has blocked the bot
   - Bot doesn't have permission to send messages to this user

4. **"Failed to send LINE notification: 429"**
   - Rate limit exceeded
   - Wait a moment and try again

### Debug Steps:

1. **Check environment variables:**
   ```python
   import os
   print("Token:", os.getenv("LINE_CHANNEL_ACCESS_TOKEN")[:10] + "...")
   print("User ID:", os.getenv("LINE_NOTIFICATION_USER_ID"))
   ```

2. **Test token validity:**
   ```python
   import requests
   
   token = "your_token_here"
   headers = {'Authorization': f'Bearer {token}'}
   response = requests.get('https://api.line.me/v2/bot/info', headers=headers)
   print("Token valid:", response.status_code == 200)
   ```

3. **Check user relationship:**
   - Make sure the user has added your bot as a friend
   - Send a test message from the user to the bot first

## 🚀 Production Deployment

For production deployment (like Render), add the environment variables:

1. **In Render Dashboard:**
   - Go to your service settings
   - Add environment variables:
     - `NOTIFICATION_METHOD=line`
     - `LINE_CHANNEL_ACCESS_TOKEN=your_token`
     - `LINE_NOTIFICATION_USER_ID=your_user_id`

2. **Verify in logs:**
   - Check that "LINE notifications enabled" appears in startup logs
   - Test with a real reservation to confirm notifications work

## 📞 Support

If you encounter issues:

1. Check the LINE Developers Console for API status
2. Verify your bot channel settings
3. Test with a simple message first
4. Check the application logs for detailed error messages

The LINE notification system is now ready to keep you informed about all salon booking activities!
