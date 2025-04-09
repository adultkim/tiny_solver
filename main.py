from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import asyncio
from datetime import datetime
import random
from typing import Dict, Optional
import logging
import os

from models import ChatRequest, ChatResponse, DEFAULT_CHUNKS, chat_response_events
from database import db
from type_def import StreamChunk

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Solver API Skeleton",
    description="솔버 인터페이스 정의",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def generate_fake_responses(chat_sn: int):
    """8초에 걸쳐 fake 응답 데이터를 생성하고 DB에 저장"""
    try:
        ###################################################
        # 모델을 사용해서 chatResponse를 생성하는 코드로 변경되어야함
        
        # 지연 시간 고의 추가
        await asyncio.sleep(3)

        for chunk in DEFAULT_CHUNKS:
            # DB에 응답 저장
            chat_response = ChatResponse(
                chatSn=chat_sn,
                type=chunk.type,
                content=chunk.data
            )
        ###################################################
         
            await asyncio.get_event_loop().run_in_executor(
                None, 
                db.save_chat_response, 
                chat_response
            )
        
        # 응답 생성 완료를 알림
        if chat_sn in chat_response_events:
            chat_response_events[chat_sn].set()
            
    except Exception as e:
        logger.error(f"Error generating responses for chatSn {chat_sn}: {str(e)}", exc_info=True)
        if chat_sn in chat_response_events:
            del chat_response_events[chat_sn]

@app.post("/api/v1/chats/responses")
async def create_chat_request(chat_request: ChatRequest):
    try:
        # 채팅 요청 저장
        db.save_chat_request(chat_request)
        
        # 응답 생성 시작
        chat_response_events[chat_request.chatSn] = asyncio.Event()
        asyncio.create_task(generate_fake_responses(chat_request.chatSn))
        
        return {"status": "success", "chatSn": chat_request.chatSn}
    except Exception as e:
        logger.error(f"Error in create_chat_request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal Solver Error: {str(e)}"
        )

@app.get("/api/v1/chats/{chat_sn}/responses/stream")
async def stream(chat_sn: int):
    try:
        # 해당 chatSn에 대한 이벤트가 없으면 404 반환
        if chat_sn not in chat_response_events:
            raise HTTPException(
                status_code=404,
                detail="Chat response generation not started"
            )
        
        # 30초 타임아웃으로 응답 생성 완료 대기
        event = chat_response_events[chat_sn]
        try:
            await asyncio.wait_for(event.wait(), timeout=30.0)
        except asyncio.TimeoutError:
            del chat_response_events[chat_sn]
            raise HTTPException(
                status_code=408,
                detail="Response generation timed out"
            )
        
        # 응답 생성이 완료되면 DB에서 응답들을 가져와서 스트리밍
        async def stream_responses():
            responses = db.get_chat_responses(chat_sn)
            for response in responses:
                chunk = StreamChunk(
                    type=response['type'],
                    data=response['content']
                )
                for char in chunk.data:
                    partial_chunk = StreamChunk(
                        type=chunk.type,
                        data=char
                    )
                    yield partial_chunk.model_dump_json() + "\n"
            
            # 스트리밍 완료 후 이벤트 정리
            del chat_response_events[chat_sn]
        
        return StreamingResponse(
            stream_responses(),
            media_type="application/x-ndjson"
        )
        
    except Exception as e:
        if chat_sn in chat_response_events:
            del chat_response_events[chat_sn]
        logger.error(f"Error in stream: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal Solver Error: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    
    # 환경 변수에서 PORT를 가져오고, 없으면 기본값 8000 사용
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port) 
