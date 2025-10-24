"""
RAG-FAQ system using FAISS for semantic search
Simplified approach with vector similarity search
"""
import json
import os
import numpy as np
import faiss
from typing import Dict, Any, Optional
from sentence_transformers import SentenceTransformer

class RAGFAQ:
    def __init__(self, kb_data_path: str = "api/data/kb.json"):
        self.kb_data = self._load_kb_data(kb_data_path)
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        self.index = None
        self.kb_keys = []
        self._build_faiss_index()
    
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
    
    def _build_faiss_index(self):
        """Build FAISS index for semantic search"""
        if not self.kb_data:
            return
        
        # Prepare texts for embedding
        texts = []
        self.kb_keys = []
        
        for key, data in self.kb_data.items():
            # Create more descriptive text for better semantic matching
            note = data['note']
            value = data['value']
            
            # Create contextual text that includes common query patterns
            if '住所' in note or 'ADDRESS' in key:
                text = f"住所 場所 所在地 {note} {value}"
            elif '営業時間' in note or 'BUSINESS_HOURS' in key:
                text = f"営業時間 時間 開店 閉店 {note} {value}"
            elif '駐車場' in note or 'PARKING' in key:
                text = f"駐車場 パーキング 車 {note} {value}"
            elif '支払い' in note or 'PAYMENTS' in key:
                text = f"支払い 支払 決済 現金 クレジット {note} {value}"
            elif '予約' in note or 'BOOKING' in key:
                text = f"予約 予約方法 予約する {note} {value}"
            elif 'キャンセル' in note or 'CANCEL' in key:
                text = f"キャンセル 取消 取り消し {note} {value}"
            else:
                text = f"{note} {value}"
            
            texts.append(text)
            self.kb_keys.append(key)
        
        # Generate embeddings
        embeddings = self.model.encode(texts)
        
        # Create FAISS index
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        self.index.add(embeddings.astype('float32'))
    
    def search(self, query: str, threshold: float = 0.5) -> Optional[Dict[str, Any]]:
        """
        Search using FAISS semantic similarity
        Returns None if no good match found (KB only approach)
        """
        if not self.index or not self.kb_data:
            return None
        
        # Generate query embedding
        query_embedding = self.model.encode([query])
        faiss.normalize_L2(query_embedding)
        
        # Search for most similar
        scores, indices = self.index.search(query_embedding.astype('float32'), 1)
        
        if len(indices[0]) > 0 and scores[0][0] >= threshold:
            best_idx = indices[0][0]
            best_key = self.kb_keys[best_idx]
            best_score = float(scores[0][0])
            
            kb_data = self.kb_data[best_key]
            response = self._create_response(best_key, kb_data, query)
            
            return {
                'kb_key': best_key,
                'similarity_score': best_score,
                'kb_facts': {best_key: kb_data['value']},
                'category': self._get_category(best_key),
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