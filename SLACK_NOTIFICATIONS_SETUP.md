# Notification System Setup Guide

## Overview

The salon booking system now includes comprehensive notifications for all user actions. You can choose between Slack, LINE, or both notification methods:

**Supported Notification Methods:**
- 📱 **LINE Notifications**: Send notifications directly to LINE chat
- 💬 **Slack Notifications**: Send notifications to Slack channels
- 🔄 **Both**: Send notifications to both LINE and Slack simultaneously

**Notification Types:**

- 🔐 **User Login**: When users interact with the bot
- 📅 **Reservation Confirmation**: When new reservations are created
- ✏️ **Reservation Modification**: When reservations are changed (time, service, staff)
- 🚫 **Reservation Cancellation**: When reservations are cancelled

## Quick Setup

### Choose Your Notification Method

Set the `NOTIFICATION_METHOD` environment variable:

```bash
# For Slack notifications only
NOTIFICATION_METHOD=slack

# For LINE notifications only  
NOTIFICATION_METHOD=line

# For both Slack and LINE notifications
NOTIFICATION_METHOD=both
```

## Slack Setup Instructions

### 1. Create a Slack App

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps)
2. Click "Create New App"
3. Choose "From scratch"
4. Enter app name (e.g., "Salon Booking Bot")
5. Select your workspace

### 2. Enable Incoming Webhooks

1. In your app settings, go to "Incoming Webhooks"
2. Toggle "Activate Incoming Webhooks" to **On**
3. Click "Add New Webhook to Workspace"
4. Choose the channel where you want notifications
5. Click "Allow"
6. Copy the webhook URL (starts with `https://hooks.slack.com/services/...`)

### 3. Configure Environment Variables

Add the webhook URL to your `.env` file:

```bash
# Notification method (choose one)
NOTIFICATION_METHOD=slack

# Slack webhook URL
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

## LINE Setup Instructions

For LINE notifications, see the detailed guide: **LINE_NOTIFICATIONS_SETUP.md**

Quick setup:
1. Get LINE Channel Access Token from LINE Developers Console
2. Get LINE User ID of notification recipient
3. Set environment variables:

```bash
# Notification method
NOTIFICATION_METHOD=line

# LINE configuration
LINE_CHANNEL_ACCESS_TOKEN=your_channel_access_token
LINE_NOTIFICATION_USER_ID=your_user_id
```

### 4. Deploy and Test

1. Deploy your application with the new environment variable
2. Test by making a reservation through the LINE bot
3. Check your Slack channel for notifications

## Notification Types

### User Login
- **Trigger**: When user sends first message to bot
- **Color**: Green
- **Content**: User ID, display name, timestamp

### Reservation Confirmation
- **Trigger**: When reservation is confirmed
- **Color**: Green
- **Content**: Reservation ID, client name, date, time, service, staff, duration, price

### Reservation Modification
- **Trigger**: When reservation is modified (time, service, or staff)
- **Color**: Orange
- **Content**: Reservation ID, client name, before/after changes

### Reservation Cancellation
- **Trigger**: When reservation is cancelled
- **Color**: Red
- **Content**: Reservation ID, client name, date, time, service, staff

## Features

- ✅ **Automatic Notifications**: No manual intervention required
- ✅ **Rich Formatting**: Color-coded messages with emojis
- ✅ **Detailed Information**: All relevant reservation details included
- ✅ **Error Handling**: Graceful fallback if Slack is unavailable
- ✅ **Configurable**: Easy to enable/disable via environment variable

## Troubleshooting

### Notifications Not Working

1. **Check Environment Variable**: Ensure `SLACK_WEBHOOK_URL` is set correctly
2. **Verify Webhook URL**: Test the URL in a browser (should return "ok")
3. **Check Logs**: Look for Slack-related error messages in application logs
4. **Test Manually**: Use the test script to verify functionality

### Test Scripts

**Test Slack notifications:**
```bash
python api/slack_notifier.py
```

**Test LINE notifications:**
```bash
python test_line_notifications.py
```

**Test unified notification system:**
```bash
python api/notification_manager.py
```

These scripts will send test notifications to verify your configuration.

## Security Notes

- Keep your webhook URL secure and private
- Don't commit the webhook URL to version control
- Use environment variables for configuration
- Consider using Slack app permissions for better security

## Customization

You can customize notifications by modifying the notifier files:

**For Slack notifications:** `api/slack_notifier.py`
- Change message formatting
- Add additional notification types
- Modify colors and emojis
- Add custom fields or attachments

**For LINE notifications:** `api/line_notifier.py`
- Change message formatting
- Add additional notification types
- Modify emojis and structure
- Add custom message types

**For unified management:** `api/notification_manager.py`
- Add new notification methods
- Modify notification routing logic
- Add notification filtering or conditions

## Support

If you encounter issues:

1. Check the application logs for error messages
2. Verify your Slack app configuration
3. Test the webhook URL manually
4. Ensure your bot has proper permissions in the Slack workspace
