"""
RAG-FAQ system that only uses KB data as the source of truth
Direct KB-based approach without FAQ dependency
"""
import json
import os
import re
from typing import List, Dict, Any, Optional

class RAGFAQ:
    def __init__(self, kb_data_path: str = "api/data/kb.json"):
        self.kb_data = self._load_kb_data(kb_data_path)
        self.kb_index = self._build_kb_index()
    
    
    def _load_kb_data(self, path: str) -> Dict[str, Dict[str, str]]:
        """Load KB data from JSON file and return full structure"""
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
                    
                    # Convert list of dicts to key-based mapping with full data
                    kb_dict = {}
                    for item in kb_list:
                        key = item.get('キー', '')
                        value = item.get('例（置換値）', '')
                        note = item.get('備考', '')
                        if key and value:
                            kb_dict[key] = {
                                'value': value,
                                'note': note
                            }
                    
                    return kb_dict
                except (FileNotFoundError, OSError, json.JSONDecodeError):
                    continue
            
            # If none of the paths worked, return empty dict
            print(f"Warning: Could not load KB data from {path}")
            return {}
            
        except Exception as e:
            print(f"Error loading KB data from {path}: {e}")
            return {}
    
    def _build_kb_index(self) -> Dict[str, List[str]]:
        """Build keyword index for KB data based on Japanese notes"""
        kb_index = {}
        
        for key, data in self.kb_data.items():
            note = data.get('note', '').lower()
            value = data.get('value', '').lower()
            
            # Extract keywords from Japanese note and value
            keywords = self._extract_keywords(note + ' ' + value)
            
            # Add English key as keyword too
            keywords.append(key.lower())
            
            kb_index[key] = keywords
        
        return kb_index
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text for matching"""
        # Less aggressive stop words - keep important particles
        stop_words = ['です', 'ます', 'か', 'の', 'を', 'に', 'で', 'と']
        
        # Simple keyword extraction
        words = re.findall(r'[a-zA-Z\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]+', text)
        keywords = [word for word in words if len(word) > 1 and word not in stop_words]
        
        # Add synonym expansion
        expanded_keywords = self._expand_synonyms(keywords)
        
        return expanded_keywords
    
    def _expand_synonyms(self, keywords: List[str]) -> List[str]:
        """Expand keywords with synonyms"""
        synonyms = {
            '料金': ['値段', '価格', '費用', '代金'],
            '予約': ['予約する', '予約方法', '予約の仕方'],
            '時間': ['営業時間', '開店時間', '閉店時間'],
            '駅': ['最寄り駅', '駅'],
            '店': ['お店', '店', 'サロン'],
            '名前': ['店名', '名前'],
            '住所': ['場所', '所在地'],
            '電話': ['電話番号', '連絡先'],
            '駐車場': ['パーキング', '駐車'],
            '休み': ['定休日', '休業日'],
            'カット': ['ヘアカット', 'カット'],
            'カラー': ['ヘアカラー', 'カラー'],
            'パーマ': ['ヘアパーマ', 'パーマ'],
            'キャンセル': ['キャンセル料', 'キャンセル料金', 'キャンセル費用', '取消', '取り消し'],
            '料': ['料金', '費用', '代金'],
            '支払い': ['支払', '支払方法', '支払い方法', '決済'],
            '方法': ['仕方', 'やり方', '手順']
        }
        
        expanded = set(keywords)
        
        # Check for synonyms in each keyword (including partial matches)
        for keyword in keywords:
            # Direct synonym match
            if keyword in synonyms:
                expanded.update(synonyms[keyword])
            
            # Check for partial matches (e.g., "料金は" contains "料金")
            for base_word, synonym_list in synonyms.items():
                if base_word in keyword:
                    expanded.update(synonym_list)
                    expanded.add(base_word)  # Add the base word too
        
        return list(expanded)
    
    def search(self, query: str, threshold: float = 0.2) -> Optional[Dict[str, Any]]:
        """
        Search for KB facts using Japanese query to English key mapping
        Returns None if no good match found (KB only approach)
        """
        if not self.kb_data or not self.kb_index:
            return None
        
        query_lower = query.lower()
        query_keywords = self._extract_keywords(query_lower)
        
        best_match_key = None
        best_score = 0
        
        # Search through KB index
        for key, keywords in self.kb_index.items():
            # Calculate keyword overlap score
            overlap = len(set(query_keywords) & set(keywords))
            
            # Use min length to avoid penalizing short queries
            min_length = min(len(query_keywords), len(keywords))
            
            if min_length > 0:
                score = overlap / min_length
                
                # Bonus for direct text matches in note or value
                kb_data = self.kb_data[key]
                note = kb_data.get('note', '').lower()
                value = kb_data.get('value', '').lower()
                
                # Check if query keywords appear in note or value
                if any(keyword in note for keyword in query_keywords):
                    score += 0.3
                if any(keyword in value for keyword in query_keywords):
                    score += 0.2
                
                # Check for dangerous queries (medical, pricing, etc.)
                if self._is_dangerous_query(query_lower):
                    score *= 0.1  # Heavy penalty for dangerous queries
                
                if score > best_score:
                    best_score = score
                    best_match_key = key
        
        # Only return if similarity is above threshold
        if best_match_key and best_score >= threshold:
            kb_data = self.kb_data[best_match_key]
            
            # Create response based on KB data
            response = self._create_response(best_match_key, kb_data, query)
            
            return {
                'kb_key': best_match_key,
                'similarity_score': float(best_score),
                'kb_facts': {best_match_key: kb_data['value']},
                'category': self._get_category(best_match_key),
                'question': query,
                'processed_answer': response
            }
        
        return None

    def _create_response(self, key: str, kb_data: Dict[str, str], query: str) -> str:
        """Create natural Japanese response based on KB data"""
        value = kb_data['value']
        note = kb_data['note']
        
        # Create contextual responses based on the type of information
        if key in ['SALON_NAME']:
            return f"店名は「{value}」です。"
        elif key in ['ADDRESS']:
            return f"住所は「{value}」です。"
        elif key in ['PHONE']:
            return f"お電話は「{value}」までお願いいたします。"
        elif key in ['ACCESS_STATION']:
            return f"最寄りは「{value}」です。"
        elif key in ['BUSINESS_HOURS_WEEKDAY', 'BUSINESS_HOURS_WEEKEND']:
            return f"営業時間は「{value}」です。"
        elif key in ['HOLIDAY']:
            return f"定休日は「{value}」です。"
        elif key in ['PARKING']:
            return f"駐車場は「{value}」です。"
        elif key in ['PAYMENTS']:
            return f"支払い方法は「{value}」です。"
        elif key in ['CANCEL_POLICY']:
            return f"キャンセル規定は「{value}」です。"
        elif key in ['ALLERGY_CARE', 'PREGNANCY_CARE']:
            return f"安全のため、{value}。詳細はスタッフにお繋ぎします。"
        else:
            # Generic response for other keys
            return f"{value}です。"
    
    def _get_category(self, key: str) -> str:
        """Get category for KB key"""
        category_map = {
            'SALON_NAME': '基本情報',
            'ADDRESS': '基本情報', 
            'PHONE': '基本情報',
            'ACCESS_STATION': 'アクセス',
            'BUSINESS_HOURS_WEEKDAY': '営業時間',
            'BUSINESS_HOURS_WEEKEND': '営業時間',
            'HOLIDAY': '営業時間',
            'PARKING': 'アクセス',
            'PAYMENTS': '支払い',
            'CANCEL_POLICY': '予約',
            'ALLERGY_CARE': '安全',
            'PREGNANCY_CARE': '安全'
        }
        return category_map.get(key, 'その他')
    
    def _is_dangerous_query(self, query: str) -> bool:
        """Check if query is in dangerous areas that need human guidance"""
        dangerous_keywords = [
            "薬", "薬剤", "治療", "診断", "病気", "症状", "副作用",
            "アレルギー", "妊娠", "授乳", "医療", "医師", "病院",
            "競合", "他店", "安く", "値下げ", "割引"
        ]
        
        return any(keyword in query for keyword in dangerous_keywords)

    def get_kb_facts(self, user_message: str) -> Optional[Dict[str, Any]]:
        """
        Get KB facts only - for use by ChatGPT
        Returns None if not found in KB
        """
        return self.search(user_message)
