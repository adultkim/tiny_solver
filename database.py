from tinydb import TinyDB, Query, where, JSONStorage
from models import ChatRequest, ChatResponse
from datetime import datetime

class Database:
    def __init__(self):
            self.db = TinyDB(
                'db.json',
                encoding='utf-8',  
                ensure_ascii=False 
            )
            self.chat_request = self.db.table('chat_request')
            self.chat_response = self.db.table('chat_response')

    def save_chat_request(self, chat_request: ChatRequest) -> int:
        data = chat_request.model_dump()
        data['created_at'] = datetime.now().isoformat()
        
        # 기존 데이터 삭제 후 새로 삽입
        self.chat_request.remove(where('chatSn') == chat_request.chatSn)
        self.chat_request.insert(data)
        return chat_request.chatSn

    def save_chat_response(self, chat_response: ChatResponse) -> int:
        data = chat_response.model_dump()
        data['created_at'] = datetime.now().isoformat()
        return self.chat_response.insert(data)

    def get_chat_responses(self, chat_sn: int) -> list:
        return self.chat_response.search(where('chatSn') == chat_sn)

    def get_chat_request(self, chat_sn: int) -> dict:
        return self.chat_request.get(where('chatSn') == chat_sn)

    def get_all_chat_responses(self) -> list:
        return self.chat_response.all()

# 데이터베이스 인스턴스 생성
db = Database()