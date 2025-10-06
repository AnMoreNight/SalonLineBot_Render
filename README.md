# Salon Line Bot

A LINE bot for salon reservations with AI-powered FAQ responses using RAG (Retrieval-Augmented Generation) and ChatGPT integration.

## Features

- LINE Bot integration for customer interactions
- AI-powered FAQ responses using RAG and ChatGPT
- Google Calendar integration for reservations
- Reservation flow management
- Natural language processing for customer queries

## Deployment on Render

### Prerequisites

1. GitHub repository with this code
2. Render account
3. LINE Bot credentials (Channel Access Token and Channel Secret)
4. OpenAI API key
5. Google Calendar API credentials

### Deployment Steps

1. **Connect to GitHub:**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" and select "Web Service"
   - Connect your GitHub account and select this repository

2. **Configure the Service:**
   - **Name**: salon-line-bot (or your preferred name)
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python -m uvicorn api.index:app --host 0.0.0.0 --port $PORT`

3. **Set Environment Variables:**
   Add the following environment variables in the Render dashboard:
   - `LINE_CHANNEL_ACCESS_TOKEN`: Your LINE Bot Channel Access Token
   - `LINE_CHANNEL_SECRET`: Your LINE Bot Channel Secret
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `GOOGLE_CREDENTIALS`: Your Google Calendar API credentials (JSON format)

4. **Deploy:**
   - Click "Create Web Service"
   - Render will automatically build and deploy your application

5. **Configure LINE Webhook:**
   - Once deployed, copy your Render service URL
   - In LINE Developers Console, set your webhook URL to: `https://your-service-name.onrender.com/api/callback`

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Bot Channel Access Token | Yes |
| `LINE_CHANNEL_SECRET` | LINE Bot Channel Secret | Yes |
| `OPENAI_API_KEY` | OpenAI API key for ChatGPT integration | Yes |
| `GOOGLE_CREDENTIALS` | Google Calendar API credentials (JSON) | Yes |

### Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables in a `.env` file:
   ```
   LINE_CHANNEL_ACCESS_TOKEN=your_token_here
   LINE_CHANNEL_SECRET=your_secret_here
   OPENAI_API_KEY=your_openai_key_here
   GOOGLE_CREDENTIALS=your_google_credentials_json
   ```

3. Run the application:
   ```bash
   python -m uvicorn api.index:app --reload
   ```

### Project Structure

```
salonLineBot/
├── api/
│   ├── index.py              # Main FastAPI application
│   ├── asgi.py              # ASGI configuration (legacy)
│   ├── chatgpt_faq.py       # ChatGPT FAQ integration
│   ├── rag_faq.py           # RAG FAQ system
│   ├── reservation_flow.py  # Reservation management
│   ├── google_calendar.py   # Google Calendar integration
│   └── data/
│       ├── faq_data.json    # FAQ data
│       └── KB.json         # Knowledge base
├── requirements.txt         # Python dependencies
├── render.yaml             # Render deployment configuration
├── Procfile               # Process file for Render
└── README.md              # This file
```

### API Endpoints

- `GET /`: Health check endpoint
- `POST /api/callback`: LINE Bot webhook endpoint

### Notes

- The application uses FastAPI with Uvicorn for the ASGI server
- RAG system provides intelligent FAQ responses based on knowledge base
- ChatGPT integration enhances natural language responses
- Google Calendar integration handles reservation scheduling
- The bot supports both FAQ queries and reservation management flows
