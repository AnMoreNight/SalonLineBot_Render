# SalonAI LINE Bot

A comprehensive LINE bot for salon reservations with AI-powered FAQ responses, Google Calendar integration, and automated reminder system.

## 📚 Documentation

### English Documentation

**[📖 Complete English Documentation](README_EN.md)**

- Full setup and deployment guide
- Feature documentation
- API reference
- Troubleshooting guide

### Japanese Documentation

**[📖 完全な日本語ドキュメント](README_JP.md)**

- セットアップとデプロイメントガイド
- 機能ドキュメント
- APIリファレンス
- トラブルシューティングガイド

## 🚀 Quick Start

### Prerequisites

- LINE Developer Account
- Google Cloud Platform Account
- OpenAI Account (optionai)
- Render Account (or any cloud platform)

### Environment Variables

```env
LINE_CHANNEL_ACCESS_TOKEN=your_line_token
LINE_CHANNEL_SECRET=your_line_secret
GOOGLE_SERVICE_ACCOUNT_JSON={"type": "service_account", ...}
GOOGLE_SHEET_ID=your_sheet_id
OPENAI_API_KEY=your_openai_key
SLACK_WEBHOOK_URL=your_slack_webhook
NOTIFICATION_METHOD=slack/line/both
```

### Deployment

1. Clone repository
2. Set environment variables
3. Deploy to Render/Heroku/Railway
4. Configure LINE webhook URL

## ✨ Key Features

- **🤖 AI-Powered FAQ**: RAG + ChatGPT integration
- **📅 Reservation Management**: Create, modify, cancel with Google Calendar sync
- **🔔 Multi-Platform Notifications**: Slack and LINE notifications
- **⏰ Automated Reminders**: Daily reminder system
- **📊 Comprehensive Logging**: Google Sheets integration
- **👥 User Management**: Consent tracking and session management

## 📁 Project Structure

```
salonLineBot/
├── api/
│   ├── index.py                    # Main FastAPI application
│   ├── reservation_flow.py         # Reservation management
│   ├── google_calendar.py          # Google Calendar integration
│   ├── google_sheets_logger.py     # Google Sheets logging
│   ├── rag_faq.py                  # RAG FAQ system
│   ├── chatgpt_faq.py              # ChatGPT integration
│   ├── notification_manager.py     # Unified notifications
│   ├── reminder_system.py          # Automated reminders
│   ├── user_consent_manager.py     # User consent management
│   └── data/
│       ├── kb.json                 # Knowledge base
│       ├── faq_data.json           # FAQ data
│       ├── services.json           # Services and staff
│       └── keywords.json           # Intent keywords
├── requirements.txt                # Python dependencies
├── Procfile                        # Process configuration
├── README_EN.md                    # English documentation
├── README_JP.md                    # Japanese documentation
└── README.md                       # This file
```

## 🔗 API Endpoints

- `GET /` - Health check
- `POST /api/callback` - LINE Bot webhook
- `POST /api/run-reminders` - Trigger reminders
- `GET /api/reminder-status` - Check reminder status

## 📞 Support

For detailed setup instructions, troubleshooting, and maintenance guides, please refer to the complete documentation:

- **[English Documentation](README_EN.md)** - Comprehensive setup and deployment guide
- **[Japanese Documentation](README_JP.md)** - 完全なセットアップとデプロイメントガイド
