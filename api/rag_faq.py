"""
RAG-FAQ system that only uses KB data as the source of truth
Lightweight version for Vercel deployment
"""
import json
import os
import re
from typing import List, Dict, Any, Optional

class RAGFAQ:
    def __init__(self, faq_data_path: str = "api/data/faq_data.json", kb_data_path: str = "api/data/kb.json"):
        self.faq_data = self._load_faq_data(faq_data_path)
        self.kb_data = self._load_kb_data(kb_data_path)
        self._build_keyword_index()
    
    def _load_faq_data(self, path: str) -> List[Dict[str, Any]]:
        """Load FAQ data from JSON file"""
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
            
            # Try each possible path
            for full_path in possible_paths:
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except (FileNotFoundError, OSError):
                    continue
            
            # If none of the paths worked, raise an error
            raise FileNotFoundError(f"Could not find FAQ data file. Tried paths: {possible_paths}")
            
        except Exception as e:
            print(f"Error loading FAQ data from {path}: {e}")
            return []
    
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
            
            # Debug: Print all attempted paths and their status
            print(f"DEBUG: Attempting to load KB data from {path}")
            for full_path in possible_paths:
                exists = os.path.exists(full_path)
                is_file = os.path.isfile(full_path) if exists else False
                print(f"DEBUG: Path: {full_path} - Exists: {exists}, IsFile: {is_file}")
            
            # Try each possible path
            for full_path in possible_paths:
                try:
                    if not os.path.exists(full_path):
                        print(f"DEBUG: Path does not exist: {full_path}")
                        continue
                    
                    if not os.path.isfile(full_path):
                        print(f"DEBUG: Path is not a file: {full_path}")
                        continue
                    
                    print(f"DEBUG: Attempting to open: {full_path}")
                    with open(full_path, 'r', encoding='utf-8') as f:
                        kb_list = json.load(f)
                    
                    print(f"DEBUG: Successfully loaded KB data from: {full_path}")
                    
                    # Convert list of dicts to key-value mapping
                    kb_dict = {}
                    for item in kb_list:
                        key = item.get('キー', '')
                        value = item.get('例（置換値）', '')
                        if key and value:
                            kb_dict[key] = value
                    
                    return kb_dict
                except (FileNotFoundError, OSError) as e:
                    print(f"DEBUG: Failed to load from {full_path}: {e}")
                    continue
                except json.JSONDecodeError as e:
                    print(f"DEBUG: JSON decode error from {full_path}: {e}")
                    continue
            
            # If none of the paths worked, raise an error
            raise FileNotFoundError(f"Could not find KB data file. Tried paths: {possible_paths}")
            
        except Exception as e:
            print(f"Error loading KB data from {path}: {e}")
            return {}
    
    def _build_keyword_index(self):
        """Build lightweight keyword index for FAQ questions"""
        if not self.faq_data:
            return
        
        self.keyword_index = []
        for item in self.faq_data:
            question = item.get('question', '').lower()
            answer_template = item.get('answer_template', '').lower()
            
            # Extract keywords from question and answer
            keywords = self._extract_keywords(question + ' ' + answer_template)
            
            self.keyword_index.append({
                'item': item,
                'keywords': keywords,
                'question': question,
                'answer_template': answer_template,
                'category': item.get('category', '')
            })
    
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
        Search for KB facts using lightweight keyword matching
        Returns None if no good match found (KB only approach)
        """
        if not self.faq_data or not hasattr(self, 'keyword_index'):
            return None
        
        query_lower = query.lower()
        query_keywords = self._extract_keywords(query_lower)
        
        best_match = None
        best_score = 0
        
        for index_item in self.keyword_index:
            # Skip questions in "答えないテスト" category unless it's an exact match
            if index_item.get('category') == '（答えないテスト）':
                # Only allow exact matches for dangerous questions
                if query_lower.strip('？?') != index_item['question'].lower().strip('？?'):
                    continue
            
            # Calculate improved keyword overlap score
            overlap = len(set(query_keywords) & set(index_item['keywords']))
            
            # Use min length instead of union to avoid penalizing short queries
            min_length = min(len(query_keywords), len(index_item['keywords']))
            
            if min_length > 0:
                score = overlap / min_length
                
                # Check for exact question match first
                is_exact_match = query_lower.strip('？?') == index_item['question'].lower().strip('？?')
                
                if is_exact_match:
                    score = 1.0
                else:
                    # Bonus for direct text matches (only for non-exact matches)
                    if any(keyword in index_item['question'] for keyword in query_keywords):
                        score += 0.3
                
                # Penalty for dangerous categories (only if not exact match)
                if index_item.get('category') == '（答えないテスト）' and not is_exact_match:
                    score *= 0.1  # Heavy penalty for non-exact matches
                
                if score > best_score:
                    best_score = score
                    best_match = index_item
        
        # Only return if similarity is above threshold
        if best_match and best_score >= threshold:
            faq_item = best_match['item']
            
            # Extract KB facts (replace placeholders with actual data)
            kb_facts = self._extract_kb_facts(faq_item)
            
            return {
                'faq_item': faq_item,
                'similarity_score': float(best_score),
                'kb_facts': kb_facts,
                'category': faq_item.get('category', ''),
                'question': faq_item.get('question', '')
            }
        
        return None

    def _extract_kb_facts(self, faq_item: Dict[str, Any]) -> Dict[str, str]:
        """Extract KB facts from FAQ item with actual salon data"""
        answer_template = faq_item.get('answer_template', '')
        
        # Replace placeholders with actual KB data
        kb_facts = {}
        for key, value in self.kb_data.items():
            if f'{{{key}}}' in answer_template:
                kb_facts[key] = value
        
        return kb_facts

    def get_kb_facts(self, user_message: str) -> Optional[Dict[str, Any]]:
        """
        Get KB facts only - for use by ChatGPT
        Returns None if not found in KB
        """
        return self.search(user_message)
