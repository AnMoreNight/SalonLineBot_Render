"""
RAG-FAQ system: Extract KB from user message, then use ChatGPT to reply
"""
import json
import os
import re
import openai
from typing import List, Dict, Any, Optional

class RAGFAQ:
    def __init__(self, kb_data_path: str = "api/data/kb.json"):
        # Initialize ChatGPT client
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = openai.OpenAI(api_key=api_key)
            self.api_available = True
        else:
            self.client = None
            self.api_available = False
            print("Warning: OPENAI_API_KEY not set. ChatGPT features will use fallback responses.")
        
        # Load KB data
        self.kb_data = self._load_kb_data(kb_data_path)
        
        # System prompt for ChatGPT
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
- 不明な点は素直に「分かりません」と伝える"""

    def _load_kb_data(self, path: str) -> Dict[str, str]:
        """Load KB data from JSON file and convert to key-value mapping"""
        try:
            # Try multiple possible paths for different deployment environments
            possible_paths = []
            
            if os.path.isabs(path):
                possible_paths.append(path)
            else:
                # Remove 'api/' prefix if present
                clean_path = path.replace('api/', '')
                
                # Try different base directories
                base_dirs = [
                    os.path.dirname(os.path.abspath(__file__)),  # Current module directory
                    os.getcwd(),  # Current working directory
                    os.path.join(os.getcwd(), 'api'),  # api subdirectory of working directory
                ]
                
                for base_dir in base_dirs:
                    possible_paths.append(os.path.join(base_dir, clean_path))
                    # Also try with 'api/' prefix
                    possible_paths.append(os.path.join(base_dir, path))
                    # Try with uppercase KB.json (for Render deployment)
                    if 'kb.json' in clean_path:
                        possible_paths.append(os.path.join(base_dir, clean_path.replace('kb.json', 'KB.json')))
                    if 'kb.json' in path:
                        possible_paths.append(os.path.join(base_dir, path.replace('kb.json', 'KB.json')))
            
            # Try each possible path
            for full_path in possible_paths:
                try:
                    if not os.path.exists(full_path):
                        continue
                    
                    if not os.path.isfile(full_path):
                        continue
                    
                    with open(full_path, 'r', encoding='utf-8') as f:
                        kb_list = json.load(f)
                    
                    # Convert list of dicts to key-value mapping
                    kb_dict = {}
                    for item in kb_list:
                        key = item.get('キー', '')
                        value = item.get('例（置換値）', '')
                        if key and value:
                            kb_dict[key] = value
                    
                    return kb_dict
                except (FileNotFoundError, OSError, json.JSONDecodeError):
                    continue
            
            # If none of the paths worked, return empty dict
            print(f"Warning: Could not load KB data from {path}")
            return {}
            
        except Exception as e:
            print(f"Error loading KB data from {path}: {e}")
            return {}

    def extract_kb_from_message(self, user_message: str) -> Dict[str, str]:
        """
        Extract relevant KB data from user message
        Returns dict of KB key-value pairs that match the user's query
        """
        if not self.kb_data:
            return {}
        
        user_message_lower = user_message.lower()
        extracted_kb = {}
        
        # Simple keyword-based extraction
        keyword_mapping = {
            # Basic info
            '店名': ['SALON_NAME'],
            '名前': ['SALON_NAME'],
            '住所': ['ADDRESS'],
            '場所': ['ADDRESS'],
            '電話': ['PHONE'],
            '連絡先': ['PHONE'],
            
            # Business hours
            '営業時間': ['BUSINESS_HOURS_WEEKDAY', 'BUSINESS_HOURS_WEEKEND'],
            '時間': ['BUSINESS_HOURS_WEEKDAY', 'BUSINESS_HOURS_WEEKEND'],
            '開店': ['BUSINESS_HOURS_WEEKDAY', 'BUSINESS_HOURS_WEEKEND'],
            '閉店': ['BUSINESS_HOURS_WEEKDAY', 'BUSINESS_HOURS_WEEKEND'],
            '定休日': ['HOLIDAY'],
            '休み': ['HOLIDAY'],
            
            # Access
            'アクセス': ['ACCESS_STATION', 'ACCESS_DETAIL'],
            '駅': ['ACCESS_STATION'],
            '最寄り': ['ACCESS_STATION'],
            '駐車場': ['PARKING'],
            'パーキング': ['PARKING'],
            
            # Payment
            '支払い': ['PAYMENTS'],
            '支払': ['PAYMENTS'],
            '決済': ['PAYMENTS'],
            '現金': ['PAYMENTS'],
            'クレジット': ['PAYMENTS'],
            'キャッシュレス': ['PAYMENTS'],
            
            # Booking
            '予約': ['BOOKING_METHOD'],
            'キャンセル': ['CANCEL_POLICY'],
            '取消': ['CANCEL_POLICY'],
            
            # Staff
            'スタイリスト': ['STAFF_AYAKA', 'STAFF_KENTO', 'STAFF_MIKU'],
            '指名': ['STAFF_REQUEST', 'STAFF_REQUEST_FEE'],
            
            # SNS
            'sns': ['SNS'],
            'instagram': ['SNS'],
            'line': ['SNS'],
            
            # Safety
            'アレルギー': ['ALLERGY_CARE'],
            '妊娠': ['PREGNANCY_CARE'],
            '安全': ['ALLERGY_CARE', 'PREGNANCY_CARE'],
            
            # Accessibility
            '子連れ': ['CHILDREN_WELCOME'],
            '子ども': ['CHILDREN_WELCOME'],
            'バリアフリー': ['BARRIER_FREE'],
            '車椅子': ['BARRIER_FREE'],
            'ペット': ['PET_POLICY'],
        }
        
        # Extract keywords from user message
        for keyword, kb_keys in keyword_mapping.items():
            if keyword in user_message_lower:
                for kb_key in kb_keys:
                    if kb_key in self.kb_data:
                        extracted_kb[kb_key] = self.kb_data[kb_key]
        
        return extracted_kb

    def generate_response_with_chatgpt(self, user_message: str, kb_data: Dict[str, str]) -> str:
        """
        Use ChatGPT to generate natural response based on KB data
        """
        if not self.api_available:
            return self._generate_fallback_response(kb_data)
        
        try:
            # Build context from KB data
            context = ""
            if kb_data:
                context = f"\n\n利用可能な事実情報：\n"
                for key, value in kb_data.items():
                    context += f"- {key}: {value}\n"
                context += "\n上記の事実情報を必ず使用して回答してください。"
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.system_prompt + context},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"ChatGPT API error: {e}")
            return self._generate_fallback_response(kb_data)

    def _generate_fallback_response(self, kb_data: Dict[str, str]) -> str:
        """Generate fallback response when ChatGPT is not available"""
        if not kb_data:
            return "申し訳ございませんが、その質問については分かりません。スタッフにお繋ぎします。"
        
        # Create a simple response using KB data
        response_parts = []
        for key, value in kb_data.items():
            response_parts.append(f"{value}です。")
        
        return " ".join(response_parts)

    def process_user_message(self, user_message: str) -> str:
        """
        Main RAG-FAQ flow:
        1. Extract KB data from user message
        2. Use ChatGPT to generate response based on KB data
        """
        # Step 1: Extract KB data from user message
        kb_data = self.extract_kb_from_message(user_message)
        
        # Step 2: Generate response using ChatGPT with KB data
        if kb_data:
            response = self.generate_response_with_chatgpt(user_message, kb_data)
        else:
            # No KB data found - return standard response
            response = "申し訳ございませんが、その質問については分かりません。スタッフにお繋ぎします。"
        
        return response

    def get_kb_facts(self, user_message: str) -> Optional[Dict[str, Any]]:
        """
        Get KB facts for compatibility with existing system
        """
        kb_data = self.extract_kb_from_message(user_message)
        
        if kb_data:
            return {
                'kb_facts': kb_data,
                'category': 'rag_faq',
                'question': user_message,
                'processed_answer': self.process_user_message(user_message)
            }
        
        return None