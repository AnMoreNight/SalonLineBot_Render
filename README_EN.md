# SalonAI LINE Bot - Complete Documentation

A comprehensive LINE bot for salon reservations with AI-powered FAQ responses, Google Calendar integration, and automated reminder system.

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Architecture](#architecture)
4. [Prerequisites](#prerequisites)
5. [Installation & Setup](#installation--setup)
6. [Environment Variables](#environment-variables)
7. [Deployment](#deployment)
8. [API Endpoints](#api-endpoints)
9. [Configuration Files](#configuration-files)
10. [User Flows](#user-flows)
11. [Troubleshooting](#troubleshooting)
12. [Maintenance](#maintenance)

## Overview

SalonAI LINE Bot is a sophisticated reservation management system that provides:

- **Intelligent FAQ System**: RAG (Retrieval-Augmented Generation) + ChatGPT integration
- **Reservation Management**: Create, modify, cancel reservations with Google Calendar sync
- **Multi-Platform Notifications**: Slack and LINE notifications for managers
- **Automated Reminders**: Daily reminder system for upcoming appointments
- **User Consent Management**: GDPR-compliant user consent tracking
- **Comprehensive Logging**: All interactions logged to Google Sheets

## Features

### 🤖 AI-Powered FAQ System
- **RAG System**: Keyword-based matching with KB data
- **ChatGPT Integration**: Natural language responses
- **Fallback System**: Direct KB responses when API unavailable
- **Template Processing**: Dynamic answer generation from KB facts

### 📅 Reservation Management
- **Create Reservations**: Date, time, service, and staff selection
- **Modify Reservations**: Change date, time, service, or staff
- **Cancel Reservations**: Full cancellation with calendar sync
- **Re-reservation**: Cancel and create new reservation in one flow
- **Availability Checking**: Real-time slot availability
- **Conflict Prevention**: Prevents double-booking and time conflicts

### 🔔 Notification System
- **Multi-Platform**: Slack and LINE notifications
- **Configurable**: Choose notification method via environment variable
- **Manager Notifications**: User login, reservation confirmations, modifications, cancellations
- **Reminder Status**: Daily reminder execution reports

### ⏰ Automated Reminders
- **Daily Reminders**: Sends reminders at configurable time (default: 9:00 AM)
- **Tokyo Timezone**: All times calculated in Asia/Tokyo timezone
- **Manager Reports**: Success/failure status notifications
- **Cron Integration**: External cron job support

### 📊 Data Management
- **Google Sheets Integration**: Comprehensive logging and user management
- **User Tracking**: Session management and consent tracking
- **Reservation History**: Complete reservation lifecycle tracking
- **Analytics**: Message logging with processing time metrics

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   LINE Users    │◄──►│   LINE Bot API   │◄──►│  FastAPI App    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
                       ┌────────────────────────────────┼────────────────────────────────┐
                       │                                │                                │
                       ▼                                ▼                                ▼
              ┌─────────────────┐              ┌─────────────────┐              ┌─────────────────┐
              │ Google Calendar │              │   Google Sheets │              │  Notification   │
              │   (Reservations)│              │   (Logging)     │              │   (Slack/LINE)  │
              └─────────────────┘              └─────────────────┘              └─────────────────┘
                       │                                │                                │
                       ▼                                ▼                                ▼
              ┌─────────────────┐              ┌─────────────────┐              ┌─────────────────┐
              │   OpenAI API    │              │   Reminder      │              │   User Session  │
              │   (ChatGPT)     │              │   Scheduler     │              │   Management    │
              └─────────────────┘              └─────────────────┘              └─────────────────┘
```

## Prerequisites

### Required Accounts & Services
1. **LINE Developer Account**: For LINE Bot credentials
2. **Google Cloud Platform**: For Calendar and Sheets APIs
3. **OpenAI Account**: For ChatGPT integration (optional)
4. **Slack Workspace**: For manager notifications (optional)
5. **Render Account**: For deployment (or any cloud platform)

### Required Credentials
- LINE Channel Access Token
- LINE Channel Secret
- Google Service Account JSON (Calendar + Sheets)
- Google Sheet ID
- OpenAI API Key (optional)
- Slack Webhook URL (optional)

## Installation & Setup

### 1. Clone Repository
```bash
git clone <repository-url>
cd salonLineBot
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Google Cloud Setup

#### Calendar API
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google Calendar API
4. Create a Service Account
5. Download JSON credentials
6. Share your calendar with the service account email

#### Sheets API
1. Enable Google Sheets API in the same project
2. Use the same Service Account
3. Create a Google Sheet for logging
4. Share the sheet with the service account email
5. Copy the Sheet ID from the URL

### 4. LINE Bot Setup
1. Go to [LINE Developers Console](https://developers.line.biz/)
2. Create a new provider and channel
3. Set channel type to "Messaging API"
4. Copy Channel Access Token and Channel Secret
5. Set webhook URL (after deployment)

### 5. OpenAI Setup (Optional)
1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Create an API key
3. Add billing information

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Bot Channel Access Token | `abc123...` |
| `LINE_CHANNEL_SECRET` | LINE Bot Channel Secret | `def456...` |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Google Service Account JSON | `{"type": "service_account"...}` |
| `GOOGLE_SHEET_ID` | Google Sheet ID for logging | `1ABC...XYZ` |

### Optional Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `OPENAI_API_KEY` | OpenAI API key for ChatGPT | None | `sk-...` |
| `SLACK_WEBHOOK_URL` | Slack webhook URL | None | `https://hooks.slack.com/...` |
| `LINE_CHANNEL_ACCESS_TOKEN_MANAGER` | LINE token for manager notifications | None | `abc123...` |
| `NOTIFICATION_METHOD` | Notification method | `slack` | `slack`, `line`, `both` |
| `GOOGLE_CALENDAR_ID` | Google Calendar ID | Primary calendar | `primary` |

### Environment Variable Setup

#### Local Development
Create a `.env` file:
```env
LINE_CHANNEL_ACCESS_TOKEN=your_line_token
LINE_CHANNEL_SECRET=your_line_secret
GOOGLE_SERVICE_ACCOUNT_JSON={"type": "service_account", ...}
GOOGLE_SHEET_ID=your_sheet_id
OPENAI_API_KEY=your_openai_key
SLACK_WEBHOOK_URL=your_slack_webhook
NOTIFICATION_METHOD=slack
```

#### Production (Render)
Add environment variables in Render dashboard:
1. Go to your service settings
2. Navigate to "Environment" tab
3. Add each variable with its value

## Deployment

### Render Deployment

1. **Connect Repository**:
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" → "Web Service"
   - Connect GitHub and select repository

2. **Configure Service**:
   - **Name**: `salon-line-bot`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python -m uvicorn api.index:app --host 0.0.0.0 --port $PORT`

3. **Set Environment Variables**:
   - Add all required environment variables
   - Ensure JSON values are properly formatted

4. **Deploy**:
   - Click "Create Web Service"
   - Wait for deployment to complete

5. **Configure Webhook**:
   - Copy the service URL
   - Set webhook URL in LINE Developers Console: `https://your-service.onrender.com/api/callback`

### Alternative Deployment Platforms

#### Heroku
```bash
# Install Heroku CLI
# Create Procfile (already included)
# Deploy
git push heroku main
```

#### Railway
```bash
# Install Railway CLI
# Connect repository
# Set environment variables
# Deploy automatically
```

## API Endpoints

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/api/callback` | POST | LINE Bot webhook |
| `/api/run-reminders` | POST | Trigger reminder system |
| `/api/reminder-status` | GET | Check reminder system status |

### Webhook Endpoint Details

#### `/api/callback` (POST)
- **Purpose**: Receives LINE Bot events
- **Authentication**: LINE signature verification
- **Events Handled**:
  - `MessageEvent`: Text messages, follow events
  - `FollowEvent`: User adds bot as friend
  - `PostbackEvent`: Button interactions

#### `/api/run-reminders` (POST)
- **Purpose**: External cron job trigger
- **Authentication**: None (consider adding API key)
- **Response**: JSON with execution results

## Configuration Files

### `/api/data/kb.json`
Knowledge base containing salon information:
```json
{
  "SALON_NAME": "SalonAI 表参道店",
  "PHONE": "03-1234-5678",
  "BUSINESS_HOURS_WEEKDAY": "10:00-20:00",
  "BUSINESS_HOURS_WEEKEND": "10:00-19:00",
  "CANCEL_POLICY": "来店2時間前まで無料",
  "REMIND_TIME": "09:00"
}
```

### `/api/data/services.json`
Service and staff configuration:
```json
{
  "services": {
    "カット": {
      "duration": 60,
      "price": 5000
    }
  },
  "staff": {
    "あやか": {
      "color_id": "1",
      "email_env": "STAFF_AYAKA_EMAIL"
    }
  }
}
```

### `/api/data/faq_data.json`
FAQ questions and templates:
```json
{
  "question": "営業時間は？",
  "required_elements": ["BUSINESS_HOURS_WEEKDAY"],
  "answer_template": "平日は{BUSINESS_HOURS_WEEKDAY}です。",
  "category": "基本情報"
}
```

### `/api/data/keywords.json`
Intent detection keywords:
```json
{
  "intent_keywords": {
    "reservation": ["予約", "予約したい"],
    "modify": ["変更", "変更したい"],
    "cancel": ["キャンセル", "キャンセルしたい"]
  }
}
```

## User Flows

### 1. New User Flow
```
User adds bot → FollowEvent → Consent screen → User agrees → Welcome message
```

### 2. Reservation Flow
```
User: "予約したい" → Date selection → Time selection → Service selection → Staff selection → Confirmation → Calendar event created
```

### 3. Modification Flow
```
User: "予約変更したい" → Select reservation → Choose field (date/time/service/staff) → New selection → Confirmation → Calendar updated
```

### 4. FAQ Flow
```
User: "営業時間は？" → RAG search → KB facts → Template processing → Response
```

### 5. Re-reservation Flow
```
User: "複数項目変更したい" → Confirmation → Cancel current → Create new reservation
```

## Troubleshooting

### Common Issues

#### 1. "Error loading KB data: No such file or directory"
**Cause**: File path issues in different environments
**Solution**: 
- Check file exists in `/api/data/`
- Verify case sensitivity (Linux vs Windows)
- Check file permissions

#### 2. "Google Calendar API error"
**Cause**: Authentication or permission issues
**Solution**:
- Verify service account JSON format
- Check calendar sharing with service account
- Ensure Calendar API is enabled

#### 3. "LINE webhook verification failed"
**Cause**: Incorrect webhook URL or signature
**Solution**:
- Verify webhook URL format
- Check LINE_CHANNEL_SECRET
- Ensure HTTPS is used

#### 4. "Reminder system not working"
**Cause**: Scheduler or timezone issues
**Solution**:
- Check REMIND_TIME in kb.json
- Verify timezone settings
- Check cron job configuration

#### 5. "Notifications not sending"
**Cause**: Invalid credentials or webhook URLs
**Solution**:
- Verify Slack webhook URL
- Check LINE Channel Access Token
- Test notification endpoints

### Debug Mode

Enable debug logging by setting:
```python
# In api/index.py
DEBUG = True
```

### Log Analysis

Check Google Sheets for:
- Message logs (Sheet1)
- Reservation data (Reservations sheet)
- User data (Users sheet)

## Maintenance

### Regular Tasks

1. **Monitor Logs**: Check Google Sheets for errors
2. **Update KB Data**: Keep salon information current
3. **Test Notifications**: Verify Slack/LINE notifications work
4. **Check Reminders**: Ensure daily reminders are sent
5. **Review Reservations**: Monitor calendar sync accuracy

### Updates

1. **Code Updates**: Deploy via Git push
2. **Configuration Updates**: Modify JSON files
3. **Environment Variables**: Update in deployment platform
4. **Dependencies**: Update requirements.txt

### Backup

1. **Google Sheets**: Export regularly
2. **Configuration Files**: Version control
3. **Environment Variables**: Document securely
4. **Calendar Data**: Google Calendar backup

### Performance Monitoring

- **Response Times**: Monitor API response times
- **Error Rates**: Track failed requests
- **User Engagement**: Analyze message patterns
- **Reservation Accuracy**: Verify calendar sync

## Support

For technical support:
1. Check logs in Google Sheets
2. Review error messages in deployment logs
3. Test individual components
4. Verify environment variables
5. Check API quotas and limits