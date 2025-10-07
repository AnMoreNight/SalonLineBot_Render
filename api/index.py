import os
import logging
import time
from fastapi import FastAPI, Request, Header, HTTPException
from dotenv import load_dotenv
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from api.rag_faq import RAGFAQ
from api.chatgpt_faq import ChatGPTFAQ
from api.reservation_flow import ReservationFlow
from api.google_sheets_logger import GoogleSheetsLogger

load_dotenv()

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_CHANNEL_SECRET:
    raise RuntimeError("Missing LINE credentials in environment variables.")

configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Initialize AI modules
rag_faq = RAGFAQ()
chatgpt_faq = ChatGPTFAQ()
reservation_flow = ReservationFlow()
sheets_logger = GoogleSheetsLogger()

# Set LINE configuration for reservation flow
reservation_flow.set_line_configuration(configuration)

app = FastAPI()


@app.get("/")
async def health():
    return {"status": "ok"}

@app.post("/api/callback")
async def callback(request: Request, x_line_signature: str = Header(None)):
    body = await request.body()
    body_str = body.decode("utf-8")

    try:
        handler.handle(body_str, x_line_signature)
    except InvalidSignatureError as e:
        logging.error(f"Signature error: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logging.error(f"Webhook handle error: {e}")
        raise HTTPException(status_code=401, detail=str(e))
    return "OK"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event: MessageEvent):
    start_time = time.time()
    message_text = event.message.text.strip()
    user_id = event.source.user_id
    reply = ""
    kb_category = None
    action_type = "message"
    reservation_data = None
    user_name = ""
    
    # Get user display name
    try:
        with ApiClient(configuration) as api_client:
            profile = MessagingApi(api_client).get_profile(user_id)
            user_name = profile.display_name
    except Exception as e:
        logging.warning(f"Could not fetch user profile for {user_id}: {e}")
        user_name = "Unknown"

    try:
        # Special ping-pong test
        if message_text == "ping":
            reply = "pong"
            action_type = "ping"
        else:
            # 1. Try reservation flow first (highest priority)
            reservation_reply = reservation_flow.get_response(user_id, message_text)
            if reservation_reply:
                reply = reservation_reply
                action_type = "reservation"
                # Try to get reservation data if available
                if hasattr(reservation_flow, 'user_states') and user_id in reservation_flow.user_states:
                    reservation_data = reservation_flow.user_states[user_id].get('data', {})
            else:
                # 2. Integrated RAG-FAQ + ChatGPT workflow
                # Step 1: Search KB for facts
                kb_facts = rag_faq.get_kb_facts(message_text)
                
                if kb_facts:
                    # Step 2: Use KB facts with ChatGPT for natural language response
                    reply = chatgpt_faq.get_response(message_text, kb_facts)
                    kb_category = kb_facts.get('category', 'unknown')
                    action_type = "faq"
                    
                    # Log successful KB hit
                    logging.info(f"KB hit for user {user_id}: {message_text} -> {kb_category}")
                else:
                    # Step 3: No KB facts found - return standard "分かりません" response
                    reply = "申し訳ございませんが、その質問については分かりません。スタッフにお繋ぎします。"
                    action_type = "unknown"
                    
                    # Log KB miss for future enhancement
                    logging.warning(f"KB miss for user {user_id}: {message_text}")

        # Reply
        try:
            with ApiClient(configuration) as api_client:
                MessagingApi(api_client).reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=reply)]
                    )
                )
        except Exception as e:
            logging.error(f"LINE reply error: {e}")
            # Log error to sheets
            sheets_logger.log_error(
                user_id=user_id,
                error_message=str(e),
                user_name=user_name,
                user_message=message_text,
                bot_response="Error occurred"
            )
            return

    except Exception as e:
        logging.error(f"Message handling error: {e}")
        reply = "申し訳ございませんが、エラーが発生しました。"
        action_type = "error"
        # Log error to sheets
        sheets_logger.log_error(
            user_id=user_id,
            error_message=str(e),
            user_name=user_name,
            user_message=message_text,
            bot_response=reply
        )
        return

    # Log successful interaction to Google Sheets
    processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
    
    if action_type == "reservation":
        sheets_logger.log_reservation_action(
            user_id=user_id,
            action=action_type,
            user_name=user_name,
            reservation_data=reservation_data,
            user_message=message_text,
            bot_response=reply
        )
    elif action_type == "faq":
        sheets_logger.log_faq_interaction(
            user_id=user_id,
            user_message=message_text,
            bot_response=reply,
            user_name=user_name,
            kb_category=kb_category,
            processing_time=processing_time
        )
    else:
        sheets_logger.log_message(
            user_id=user_id,
            user_message=message_text,
            bot_response=reply,
            user_name=user_name,
            message_type="text",
            action_type=action_type,
            processing_time=processing_time
        )

