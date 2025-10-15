# Slack Notifications Setup Guide

## Overview

The salon booking system now includes comprehensive Slack notifications for all user actions:

- 🔐 **User Login**: When users interact with the bot
- 📅 **Reservation Confirmation**: When new reservations are created
- ✏️ **Reservation Modification**: When reservations are changed (time, service, staff)
- 🚫 **Reservation Cancellation**: When reservations are cancelled

## Setup Instructions

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

### 3. Configure Environment Variable

Add the webhook URL to your `.env` file:

```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
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

### Test Script

Run the test script to verify Slack integration:

```bash
python api/slack_notifier.py
```

This will send a test notification to your configured Slack channel.

## Security Notes

- Keep your webhook URL secure and private
- Don't commit the webhook URL to version control
- Use environment variables for configuration
- Consider using Slack app permissions for better security

## Customization

You can customize notifications by modifying `api/slack_notifier.py`:

- Change message formatting
- Add additional notification types
- Modify colors and emojis
- Add custom fields or attachments

## Support

If you encounter issues:

1. Check the application logs for error messages
2. Verify your Slack app configuration
3. Test the webhook URL manually
4. Ensure your bot has proper permissions in the Slack workspace
