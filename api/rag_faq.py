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
    
    def _load_kb_data(self, path: str) -> Dict[str, str]:
        """Load KB data from JSON file and return simple key-value mapping"""
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
                    possible_paths.append(os.path.join(base_dir, path))
                    # Try with uppercase KB.json (for Render deployment)
                    if 'kb.json' in clean_path:
                        possible_paths.append(os.path.join(base_dir, clean_path.replace('kb.json', 'KB.json')))
                    if 'kb.json' in path:
                        possible_paths.append(os.path.join(base_dir, path.replace('kb.json', 'KB.json')))
            
            # Try each possible path
            for full_path in possible_paths:
                try:
                    if not os.path.exists(full_path) or not os.path.isfile(full_path):
                        continue
                    
                    with open(full_path, 'r', encoding='utf-8') as f:
                        kb_list = json.load(f)
                    
                    # Convert list of dicts to simple key-value mapping
                    kb_dict = {}
                    for item in kb_list:
                        key = item.get('キー', '')
                        value = item.get('値', '')
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
    
    def _build_faiss_index(self):
        """Build FAISS index for semantic search"""
        if not self.kb_data:
            return
        
        # Prepare texts for embedding
        texts = []
        self.kb_keys = []
        
        for key, value in self.kb_data.items():
            # Create contextual text for better semantic matching
            if '住所' in key:
                text = f"住所 場所 所在地 {key} {value}"
            elif '営業時間' in key:
                text = f"営業時間 時間 開店 閉店 {key} {value}"
            elif '駐車場' in key:
                text = f"駐車場 パーキング 車 {key} {value}"
            elif '支払い' in key:
                text = f"支払い 支払 決済 現金 クレジット {key} {value}"
            elif '予約' in key:
                text = f"予約 予約方法 予約する {key} {value}"
            elif 'キャンセル' in key:
                text = f"キャンセル 取消 取り消し {key} {value}"
            elif 'SNS' in key or 'sns' in key.lower():
                text = f"SNS ソーシャル 公式 アカウント LINE Instagram {key} {value}"
            else:
                text = f"{key} {value}"
            
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
        Returns None if no good match found
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
            
            kb_value = self.kb_data[best_key]
            response = self._create_response(best_key, kb_value, query)
            
            return {
                'kb_key': best_key,
                'similarity_score': best_score,
                'kb_facts': {best_key: kb_value},
                'category': self._get_category(best_key),
                'question': query,
                'processed_answer': response
            }
        
        return None

    def _create_response(self, key: str, value: str, query: str) -> str:
        """Create natural Japanese response based on KB data"""
        # Create contextual responses based on the type of information
        if '店名' in key:
            return f"店名は「{value}」です。"
        elif '住所' in key:
            return f"住所は「{value}」です。"
        elif '電話' in key:
            return f"お電話は「{value}」までお願いいたします。"
        elif 'アクセス' in key:
            return f"アクセスは「{value}」です。"
        elif '営業時間' in key:
            return f"営業時間は「{value}」です。"
        elif '定休日' in key:
            return f"定休日は「{value}」です。"
        elif '駐車場' in key:
            return f"駐車場は「{value}」です。"
        elif '支払い' in key:
            return f"支払い方法は「{value}」です。"
        elif 'キャンセル' in key:
            return f"キャンセル規定は「{value}」です。"
        elif 'アレルギー' in key or '妊娠' in key:
            return f"安全のため、{value}。詳細はスタッフにお繋ぎします。"
        elif 'SNS' in key or 'sns' in key.lower():
            return f"SNSアカウントは「{value}」です。"
        else:
            # Generic response for other keys
            return f"{value}です。"
    
    def _get_category(self, key: str) -> str:
        """Get category for KB key"""
        if '店名' in key or '住所' in key or '電話' in key:
            return '基本情報'
        elif 'アクセス' in key or '駐車場' in key:
            return 'アクセス'
        elif '営業時間' in key or '定休日' in key:
            return '営業時間'
        elif '支払い' in key:
            return '支払い'
        elif '予約' in key or 'キャンセル' in key:
            return '予約'
        elif 'アレルギー' in key or '妊娠' in key:
            return '安全'
        elif 'SNS' in key or 'sns' in key.lower():
            return 'SNS'
        else:
            return 'その他'
    
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
        return self.search(user_message, threshold=0.3)