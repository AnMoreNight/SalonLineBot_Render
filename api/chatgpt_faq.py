"""
ChatGPT-powered FAQ system for natural language responses using KB facts
"""
import os
from openai import OpenAI
from typing import Optional

class ChatGPTFAQ:
    def __init__(self):
        # Initialize client only if API key is available
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = OpenAI(api_key=api_key)
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
            
            # Check if we have a processed answer from RAG FAQ (template-based response)
            
            
            # If API is not available, use fallback immediately
            if not self.api_available:
                return self._generate_fallback_response()
            
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
            
            response = self.clinet.responses.create(
                model="gpt-4-turbo",
                instructions = "You are a helpful assistant that can answer questions about the salon.",
                input=self.system_prompt + context + "\n\n" + user_message
            )
            
            return response.output_text.strip()
            
        except Exception as e:
            print(f"ChatGPT API error: {e}")
            # Fallback: if we have KB facts, provide a simple response
            return self._generate_fallback_response()
    
    def _generate_fallback_response(self) -> str:
        """Generate a fallback response using KB facts when ChatGPT API is not available"""
        
        return "申し訳ございませんが、現在システムの調子が悪いようです。しばらくしてから再度お試しください。"
    
    def _is_dangerous_query(self, message: str) -> bool:
        """Check if query is in dangerous areas that need human guidance"""
        dangerous_keywords = [
            "薬", "薬剤", "治療", "診断", "病気", "症状", "副作用",
            "アレルギー", "妊娠", "授乳", "医療", "医師", "病院"
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in dangerous_keywords)
