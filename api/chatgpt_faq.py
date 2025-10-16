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
        self.system_prompt = """あなたは美容室「サロンAI」の親切なスタッフです。

重要なルール：
1. 提供されたKB事実を必ず使用して回答してください
2. KB事実がある場合は、それを基に具体的で有用な回答をしてください
3. 推測や憶測は禁止ですが、KB事実は積極的に活用してください
4. 医療・薬剤に関する質問は人手誘導してください
5. 数値の推測は禁止です

回答スタイル：
- 丁寧で親しみやすい口調
- KB事実を自然な日本語で説明
- KB事実がある場合は具体的な情報を提供
- 不明な点は素直に「分かりません」と伝える
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
                # Create a simple response using KB facts
                response_parts = []
                for key, value in facts_dict.items():
                    if key == 'SNS':
                        response_parts.append(f"はい、{value}をご覧ください。")
                    elif key == 'SALON_NAME':
                        response_parts.append(f"店名は{value}です。")
                    elif key == 'PHONE':
                        response_parts.append(f"お電話は{value}までお願いいたします。")
                    elif key == 'ADDRESS':
                        response_parts.append(f"住所は{value}です。")
                    elif key == 'ACCESS_STATION':
                        response_parts.append(f"最寄りは{value}です。")
                    elif key == 'PARKING':
                        response_parts.append(f"駐車場は{value}です。")
                    elif key == 'HOLIDAY':
                        response_parts.append(f"定休日は{value}です。")
                    elif key == 'BUSINESS_HOURS_WEEKDAY':
                        response_parts.append(f"平日の営業時間は{value}です。")
                    elif key == 'BUSINESS_HOURS_WEEKEND':
                        response_parts.append(f"土日祝の営業時間は{value}です。")
                    elif key == 'PAYMENTS':
                        response_parts.append(f"支払い方法は{value}です。")
                    elif key == 'CANCEL_POLICY':
                        response_parts.append(f"キャンセル規定は{value}です。")
                    else:
                        response_parts.append(f"{key}: {value}")
                
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
