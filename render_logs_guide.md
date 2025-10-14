# Render Logs Viewing Guide

## Method 1: Render Dashboard (Easiest) ⭐

1. Visit: https://dashboard.render.com/
2. Select your service: `salonLineBot`
3. Click the **"Logs"** tab at the top
4. View real-time logs as you test on LINE

**Features:**
- Real-time streaming
- Search and filter
- Download logs
- Shows all Python `logging` output

---

## Method 2: Render CLI (For Power Users)

### Installation:

```bash
# Windows (PowerShell)
iwr https://render.com/install.ps1 -useb | iex

# Or using npm
npm install -g render-cli
```

### Usage:

```bash
# Login
render login

# View logs (real-time)
render logs --service salonLineBot --tail

# View last 100 lines
render logs --service salonLineBot --num 100
```

---

## Method 3: Send Logs to LINE (For Quick Testing)

Add a helper function to send important logs as LINE messages:

```python
# In api/reservation_flow.py
def _send_debug_message(self, user_id: str, debug_info: str):
    """Send debug information as LINE message (only for testing)"""
    if os.getenv("DEBUG_MODE") == "true":
        # Send debug info to the user
        return f"🔍 DEBUG:\n{debug_info}"
    return None
```

Then in your `.env` on Render, set:
```
DEBUG_MODE=true
```

**Warning:** Only use this for testing, remove before production!

---

## Method 4: External Logging Service

### Option A: LogTail (Free Tier Available)

1. Sign up: https://logtail.com/
2. Get your source token
3. Add to Render environment variables:
   ```
   LOGTAIL_SOURCE_TOKEN=your_token_here
   ```
4. Install in `requirements.txt`:
   ```
   logtail-python
   ```
5. Configure in your code:
   ```python
   from logtail import LogtailHandler
   import logging
   
   handler = LogtailHandler(source_token=os.getenv('LOGTAIL_SOURCE_TOKEN'))
   logger = logging.getLogger()
   logger.addHandler(handler)
   ```

### Option B: Sentry (Error Tracking)

1. Sign up: https://sentry.io/
2. Install: `pip install sentry-sdk`
3. Initialize in `api/index.py`:
   ```python
   import sentry_sdk
   
   sentry_sdk.init(
       dsn=os.getenv("SENTRY_DSN"),
       traces_sample_rate=1.0
   )
   ```

---

## Recommended Setup for Your Use Case

**For Development/Testing:**
1. **Primary:** Use Render Dashboard Logs (Method 1)
2. **Secondary:** Keep logs in code with `logging.info()`
3. **Quick debug:** Add temporary debug messages to LINE (Method 3)

**For Production:**
1. Keep `logging.info()` for important events
2. Use `logging.error()` for errors
3. Monitor via Render Dashboard
4. Optional: Add Sentry for error tracking

---

## Current Logging Best Practices

Your current logs are already well-structured:

```python
logging.info(f"[Modification] Date: {date_str}, Total events: {len(events)}")
logging.info(f"Detected 'reservation' intent for message: '{message_normalized}'")
```

These will appear in Render logs automatically! Just view them in the dashboard.

---

## Quick Test

1. Open Render Dashboard → Logs
2. Send a message on LINE: "予約したい"
3. Watch logs appear in real-time:
   ```
   INFO: Detected 'reservation' intent for message: '予約したい'
   INFO: Starting reservation flow for user: U1234567890
   ```

That's it! 🎉

