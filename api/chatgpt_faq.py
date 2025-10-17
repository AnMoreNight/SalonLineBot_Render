"""
ChatGPT-powered FAQ system for natural language responses using KB facts
"""
import os
import openai
from typing import Optional

class ChatGPTFAQ:
    def __init__(self):
        # Initialize client only if API key is available
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = openai.OpenAI(api_key=api_key)
            self.api_available = True
        else:
            self.client = None
            self.api_available = False
            print("Warning: OPENAI_API_KEY not set. ChatGPT features will use fallback responses.")
        self.system_prompt = """あなたは美容室「SalonAI 表参道店」の親切で知識豊富なスタッフです。

【重要なルール】
1. 提供されたKB事実を必ず使用して回答してください
2. KB事実がある場合は、それを基に具体的で有用な回答をしてください
3. 推測や憶測は禁止ですが、KB事実は積極的に活用してください
4. 医療・薬剤に関する質問は人手誘導してください
5. 数値の推測は禁止です
6. 複数のKB事実がある場合は、関連する情報を組み合わせて包括的な回答をしてください

【回答スタイル】
- 丁寧で親しみやすい口調
- KB事実を自然な日本語で説明
- KB事実がある場合は具体的な情報を提供
- 関連する追加情報があれば積極的に提供
- 不明な点は素直に「分かりません」と伝える

【利用可能な情報カテゴリ】
- 基本情報（店名、住所、電話、アクセス）
- 営業時間・定休日・混雑情報
- 予約システム・変更・キャンセル規定
- 支払い方法・領収書・価格表示
- スタイリスト情報・指名料
- クーポン・特典・ポイントシステム
- 安全・ポリシー（アレルギー、妊娠中対応）
- アクセス詳細・バリアフリー・子連れ対応
- 仕上がり保証・来店間隔・持ち込み薬剤

【回答例】
- 支払い方法の質問 → 支払い方法 + 領収書発行 + 価格表示の情報を組み合わせ
- アクセスの質問 → 最寄り駅 + 詳細な道順 + 駐車場情報を組み合わせ
- 営業時間の質問 → 平日・土日祝 + 定休日 + 混雑目安を組み合わせ
"""
    
    def get_response(self, user_message: str, kb_facts: Optional[dict] = None) -> str:
        """
        Get ChatGPT-powered natural language response using KB facts
        """
        try:
            # Check for dangerous queries first
            if self._is_dangerous_query(user_message):
                return "申し訳ございませんが、その質問については分かりません。スタッフにお繋ぎします。"
            
            # If API is not available, use fallback immediately
            if not self.api_available:
                return self._generate_fallback_response(kb_facts)
            
            # Build context from KB facts
            context = ""
            if kb_facts:
                # Handle both direct kb_facts and nested structure
                facts_dict = kb_facts.get('kb_facts', kb_facts) if isinstance(kb_facts, dict) else {}
                
                if facts_dict:
                    context = f"\n\n利用可能な事実情報：\n"
                    for key, value in facts_dict.items():
                        context += f"- {key}: {value}\n"
                    context += "\n上記の事実情報を必ず使用して回答してください。"
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.system_prompt + context},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=500,
                temperature=0.3  # Lower temperature for more consistent responses
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"ChatGPT API error: {e}")
            # Fallback: if we have KB facts, provide a simple response
            return self._generate_fallback_response(kb_facts)
    
    def _generate_fallback_response(self, kb_facts: Optional[dict] = None) -> str:
        """Generate a fallback response using KB facts when ChatGPT API is not available"""
        if kb_facts:
            facts_dict = kb_facts.get('kb_facts', kb_facts) if isinstance(kb_facts, dict) else {}
            if facts_dict:
                # Create a comprehensive response using KB facts
                response_parts = []
                
                # Group related information for better responses
                basic_info = []
                business_hours = []
                payment_info = []
                access_info = []
                staff_info = []
                policy_info = []
                
                for key, value in facts_dict.items():
                    # Basic information
                    if key == 'SALON_NAME':
                        basic_info.append(f"店名は{value}です。")
                    elif key == 'ADDRESS':
                        basic_info.append(f"住所は{value}です。")
                    elif key == 'PHONE':
                        basic_info.append(f"お電話は{value}までお願いいたします。")
                    elif key == 'SNS':
                        basic_info.append(f"SNSアカウントは{value}です。")
                    
                    # Business hours
                    elif key == 'BUSINESS_HOURS_WEEKDAY':
                        business_hours.append(f"平日の営業時間は{value}です。")
                    elif key == 'BUSINESS_HOURS_WEEKEND':
                        business_hours.append(f"土日祝の営業時間は{value}です。")
                    elif key == 'HOLIDAY':
                        business_hours.append(f"定休日は{value}です。")
                    elif key == 'BUSY_TIMES':
                        business_hours.append(f"混雑目安は{value}です。")
                    elif key == 'SAME_DAY_BOOKING':
                        business_hours.append(f"当日予約は{value}です。")
                    
                    # Payment information
                    elif key == 'PAYMENTS':
                        payment_info.append(f"支払い方法は{value}です。")
                    elif key == 'RECEIPT_ISSUE':
                        payment_info.append(f"領収書は{value}です。")
                    elif key == 'PRICE_INCLUDE_TAX':
                        payment_info.append(f"価格は{value}です。")
                    elif key == 'COUPON_COMBINATION':
                        payment_info.append(f"クーポン併用は{value}です。")
                    elif key == 'NEW_CUSTOMER_COUPON':
                        payment_info.append(f"新規クーポンは{value}です。")
                    elif key == 'POINT_SYSTEM':
                        payment_info.append(f"ポイントシステムは{value}です。")
                    
                    # Access information
                    elif key == 'ACCESS_STATION':
                        access_info.append(f"最寄り駅は{value}です。")
                    elif key == 'ACCESS_DETAIL':
                        access_info.append(f"詳細なアクセス方法は{value}です。")
                    elif key == 'PARKING':
                        access_info.append(f"駐車場は{value}です。")
                    elif key == 'BARRIER_FREE':
                        access_info.append(f"バリアフリー対応は{value}です。")
                    elif key == 'CHILDREN_WELCOME':
                        access_info.append(f"子連れ対応は{value}です。")
                    elif key == 'PET_POLICY':
                        access_info.append(f"ペット対応は{value}です。")
                    elif key == 'LOST_DIRECTION_HELP':
                        access_info.append(f"道に迷った場合は{value}です。")
                    
                    # Staff information
                    elif key in ['STAFF_AYAKA', 'STAFF_KENTO', 'STAFF_MIKU']:
                        staff_info.append(f"{value}です。")
                    elif key == 'STAFF_REQUEST_FEE':
                        staff_info.append(f"指名料は{value}です。")
                    elif key == 'PHOTO_REFERENCE':
                        staff_info.append(f"写真持ち込みは{value}です。")
                    
                    # Policy information
                    elif key == 'CANCEL_POLICY':
                        policy_info.append(f"キャンセル規定は{value}です。")
                    elif key == 'ALLERGY_CARE':
                        policy_info.append(f"アレルギー対応は{value}です。")
                    elif key == 'PREGNANCY_CARE':
                        policy_info.append(f"妊娠中対応は{value}です。")
                    elif key == 'SATISFACTION_GUARANTEE':
                        policy_info.append(f"仕上がり保証は{value}です。")
                    elif key == 'VISIT_INTERVAL':
                        policy_info.append(f"来店間隔は{value}です。")
                    elif key == 'BRING_OWN_PRODUCTS':
                        policy_info.append(f"持ち込み薬剤は{value}です。")
                    
                    # Booking information
                    elif key == 'BOOKING_METHOD':
                        policy_info.append(f"予約方法は{value}です。")
                    elif key == 'CHANGE_POLICY':
                        policy_info.append(f"変更ポリシーは{value}です。")
                    elif key == 'NOTIFICATION_SYSTEM':
                        policy_info.append(f"通知システムは{value}です。")
                    
                    # Other information
                    else:
                        # For any other keys, include them as general information
                        response_parts.append(f"{value}です。")
                
                # Combine information by category for better organization
                if basic_info:
                    response_parts.extend(basic_info)
                if business_hours:
                    response_parts.extend(business_hours)
                if payment_info:
                    response_parts.extend(payment_info)
                if access_info:
                    response_parts.extend(access_info)
                if staff_info:
                    response_parts.extend(staff_info)
                if policy_info:
                    response_parts.extend(policy_info)
                
                if response_parts:
                    return " ".join(response_parts)
        
        return "申し訳ございませんが、現在システムの調子が悪いようです。しばらくしてから再度お試しください。"
    
    def _is_dangerous_query(self, message: str) -> bool:
        """Check if query is in dangerous areas that need human guidance"""
        dangerous_keywords = [
            "薬", "薬剤", "治療", "診断", "病気", "症状", "副作用",
            "アレルギー", "妊娠", "授乳", "医療", "医師", "病院"
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in dangerous_keywords)
