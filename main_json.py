from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
import requests
from uuid import uuid4
from models import ChatRequest, DEFAULT_CHUNKS, ChatResponseJson, JobDescriptionResponse, ChatSessionLog, EventType, Chunk

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API 키 설정
API_KEY = os.getenv("MATCHING_SOLVER_API_KEY", "matching-solver-api-key")
MATCHING_SOLVER_BASE_URL = "https://match-solver-api.jobda.kr-dv-jainwon.com"

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

async def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API Key"
        )
    return x_api_key

# @app.post("/api/v1/chats/responses")
# async def create_chat_request(
#     chat_request: ChatRequest,
#     api_key: str = Depends(verify_api_key)
# ):
#     try:
#         return ChatResponseJson(
#             chatSn=chat_request.chatSn,
#             chunkRsList=DEFAULT_CHUNKS
#         )
#     except Exception as e:
#         logger.error(f"Error in create_chat_request: {str(e)}", exc_info=True)
#         raise HTTPException(
#             status_code=500,
#             detail=f"Internal Solver Error: {str(e)}"
#         )


@app.post("/api/v1/chats/responses")
async def create_chat_request(
    chat_request: ChatRequest,
    api_key: str = Depends(verify_api_key)
):
    try:
        response = call_matching_solver(chat_request.chatSn, chat_request.content)
        return convert_solver_response_to_chunks(response)
    except Exception as e:
        logger.error(f"Error in create_chat_request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal Solver Error: {str(e)}"
        )





def post_request_function(url, header, body):
    try:
        response = requests.post(url, headers=header, json=body)
        response.raise_for_status()
        return response
    except Exception as e:
        logger.error(f"API 호출 오류: {url} | {e}")
        raise

def call_matching_solver(chat_sn: int, content: str) -> ChatResponseJson:
    session_id = str(uuid4())
    body = {
        "chatSessionId": session_id,
        "jobDesc": {},
        "userInput": content
    }
    url = f"{MATCHING_SOLVER_BASE_URL}/api/v1/jobdescription-generation-chat"
    res = post_request_function(url, header=None, body=body)
    json_data = res.json()["data"]
    # json_data['chat_sn']
    return JobDescriptionResponse(
        chatSn=chat_sn,
        chatSessionId=json_data["chatSessionId"],
        chatResponse=json_data["chatResponse"],
        jobDesc=json_data["jobDesc"],
        chatSessionLog=ChatSessionLog(
            chat=json_data["chatSessionLogModel"]["chat"],
            cost=json_data["chatSessionLogModel"]["cost"]
        )
    )

@app.post("/api/solver/chats/responses")
async def create_chat_request(
    chat_request: ChatRequest,
    api_key: str = Depends(verify_api_key)
):
    try:
        response = call_matching_solver(chat_request.chatSn, chat_request.content)
        return response
    except Exception as e:
        logger.error(f"Error in create_chat_request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal Solver Error: {str(e)}"
        )



def convert_solver_response_to_chunks(response: JobDescriptionResponse) -> ChatResponseJson:
    try:
        job_desc = response.jobDesc
        chat_sn = response.chatSn

        chunks = [
            Chunk(type=EventType.TEXT, data=response.chatResponse)
        ]

        if job_desc.get("jobTitle"):
            chunks.append(Chunk(
                type=EventType.JOB_TITLE_TEXT,
                data=job_desc["jobTitle"]
            ))

        if job_desc.get("mainResponsibilities"):
            chunks.append(Chunk(
                type=EventType.JOB_DESCRIPTION_TEXT,
                data="\n".join(job_desc["mainResponsibilities"])
            ))

        if job_desc.get("qualifications"):
            chunks.append(Chunk(
                type=EventType.REQUIRED_SKILL_TEXT,
                data="\n".join(job_desc["qualifications"])
            ))

        chunks.append(Chunk(
            type=EventType.PREFERRED_SKILL_TEXT,
            data="\n".join(["CPA 자격증 소지자", "세무 및 회계 규정에 대한 이해"])
        ))
        chunks.append(Chunk(
            type=EventType.TEXT,
            data="입력창을 눌러 언제든 직접 수정하실 수 있어요.\n편하게 적어주시면, 제가 자연스럽게 다듬어드릴게요."
        ))

        return ChatResponseJson(chatSn=chat_sn, chunkRsList=chunks)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chunk 변환 실패: {str(e)}"
        )







if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
