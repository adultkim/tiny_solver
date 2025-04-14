from fastapi import FastAPI, HTTPException, Depends, Header, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
import logging
import os
import requests
from uuid import uuid4
from models import ChatRequest, DEFAULT_JOB_DESCRIPTIONS, DEFAULT_MATCHING_TALENT, ChatResponseJson, JobDescriptionResponse, ChatSessionLog, EventType, Chunk, ChatValidRequest, ChatValidResponse, InputType
from pydantic import BaseModel, Field
from typing import List, Union, Optional, Any
from enum import Enum
import re

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

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Solver API Docs",
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
        swagger_favicon_url="/static/favicon.ico",
        init_script="/static/swagger-ui-init.js"  # ← 여기에 js 삽입
    )

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# async def verify_api_key(x_api_key: str = Header(None)):
#     if x_api_key != API_KEY:
#         raise HTTPException(
#             status_code=401,
#             detail="Invalid API Key"
#         )
#     return x_api_key

# 요청/응답 모델 정의
class SolverChatRefineRq(BaseModel):
    inputType : InputType
    content: List[str]  

class SolverChatRefineRs(BaseModel):
    content: List[str]

@app.post("/api/v1/chats/refine")
async def refine_chat(request: SolverChatRefineRq) -> SolverChatRefineRs:
    try:
        # 각 항목을 다듬는 예시 처리
        refined = [f"[다듬다듬] {item}" for item in request.content]
        return SolverChatRefineRs(content=refined)
    except Exception as e:
        logger.error(f"Error in refine_chat: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal Solver Error: {str(e)}"
        )

@app.post("/api/v1/chats/validate")
async def validte_chat(
    chat_valid_request: ChatValidRequest,
    # api_key: str = Depends(verify_api_key)
):
    try:
        return ChatValidResponse(validYn=True)
    except Exception as e:
        logger.error(f"Error in create_chat_request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal Solver Error: {str(e)}"
        )


@app.post("/api/v1/chats/responses")
async def create_chat_request(
    chat_request: ChatRequest,
    # api_key: str = Depends(verify_api_key)
):
    try:
        return ChatResponseJson(
            chatSn=chat_request.chatSn,
            subDomain=chat_request.subDomain,
            chunkRsList=DEFAULT_JOB_DESCRIPTIONS
        )
    except Exception as e:
        logger.error(f"Error in create_chat_request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal Solver Error: {str(e)}"
        )


# @app.post("/api/v1/chats/responses")
# async def create_chat_request(
#     chat_request: ChatRequest,
# # api_key: str = Depends(verify_api_key)
# ):
#     try:
#         response = call_matching_solver(chat_request.chatSn, chat_request.content)
#         return convert_solver_response_to_chunks(response)
#     except Exception as e:
#         logger.error(f"Error in create_chat_request: {str(e)}", exc_info=True)
#         raise HTTPException(
#             status_code=500,
#             detail=f"Internal Solver Error: {str(e)}"
#         )


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

# @app.post("/api/solver/chats/responses")
# async def create_chat_request(
#     chat_request: ChatRequest,
# # api_key: str = Depends(verify_api_key)
# ):
#     try:
#         response = call_matching_solver(chat_request.chatSn, chat_request.content)
#         return response
#     except Exception as e:
#         logger.error(f"Error in create_chat_request: {str(e)}", exc_info=True)
#         raise HTTPException(
#             status_code=500,
#             detail=f"Internal Solver Error: {str(e)}"
#         )


def sanitize_text(text: str) -> str:
    if not text:
        return text
    # BMP 범위 (0x0000 ~ 0xFFFF)만 허용 (utf8에서 문제 없는 문자들)
    return re.sub(r'[^\u0000-\uFFFF]', '', text)


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



class JobDescriptionServiceDto(BaseModel):
    chatSn: int
    jobDescriptionSn: int
    title: str
    subDomain: str
    descriptions: List[str]
    requiredSkills: List[str]
    preferredSkills: List[str]

class RecommendedTalentsRs(BaseModel):
    chatSn: int
    jobDescriptionSn: int
    chunkRsList: List[Chunk]
    subDomain: str

@app.post("/api/v1/chats/job-descriptions/recommended-talents")
async def get_recommended_talents(
    job_description: JobDescriptionServiceDto,
    # api_key: str = Depends(verify_api_key)
):
    try:
        # TODO: 실제 추천 로직 구현
        # 임시로 더미 데이터 반환
        return RecommendedTalentsRs(
            chatSN=job_description.chatSn,
            jobDescriptionSn=job_description.jobDescriptionSn,
            subDomain=job_description.subDomain,
            chunkRsList=DEFAULT_MATCHING_TALENT
        )
    except Exception as e:
        logger.error(f"Error in get_recommended_talents: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal Solver Error: {str(e)}"
        )

class ChatFilterType(str, Enum):
    EDUCATION = "EDUCATION"
    LICENSE = "LICENSE"
    SKILL = "SKILL"
    EXAMINATION = "EXAMINATION"
    CAREER = "CAREER"

class CareerConditionType(str, Enum):
    OVER = "OVER"
    UNDER = "UNDER"

class ExaminationFilterDetailRs(BaseModel):
    examinationCode: int
    score: Optional[float] = None
    gradeCode: Optional[str] = None

class CareerFilterDetailRs(BaseModel):
    jobTitleCode: int
    careerMonths: int
    careerConditionType: CareerConditionType

class EducationFilterRs(BaseModel):
    majorCodes: List[int]

class LicenseFilterRs(BaseModel):
    licenseCodes: List[int]

class SkillFilterRs(BaseModel):
    skillCodes: List[int]

class ExaminationFilterRs(BaseModel):
    examinationList: List[ExaminationFilterDetailRs]

class CareerFilterRs(BaseModel):
    careerList: List[CareerFilterDetailRs]

class JobDescriptionFiltersRq(BaseModel):
    chatSn: int
    jobDescriptionSn: int
    subDomain: str
    descriptions: List[str]
    requiredSkills: List[str]
    preferredSkills: List[str]
    requiredSkills: List[str]

class FilterResult(BaseModel):
    type: ChatFilterType
    summary: str
    filterValue: Union[EducationFilterRs, LicenseFilterRs, SkillFilterRs, ExaminationFilterRs, CareerFilterRs]

class JobDescriptionFiltersRs(BaseModel):
    chatSn: int
    jobDescriptionSn: int
    subDomain: str
    filters: List[FilterResult]

def get_next_filter(requiredSkills: List[str], subDomain: str, jobDescriptionSn: int) -> JobDescriptionFiltersRs:
    # 필터 타입과 해당 필터 값을 생성하는 함수 정의
    filter_types = [
        (ChatFilterType.SKILL, lambda: SkillFilterRs(skillCodes=[2, 4, 6])),
        (ChatFilterType.EDUCATION, lambda: EducationFilterRs(majorCodes=[1, 2, 3])),
        (ChatFilterType.LICENSE, lambda: LicenseFilterRs(licenseCodes=[1, 2, 3])),
        (ChatFilterType.EXAMINATION, lambda: ExaminationFilterRs(examinationList=[
            ExaminationFilterDetailRs(examinationCode=1, score=800.0, gradeCode=None),
            ExaminationFilterDetailRs(examinationCode=2, score=None, gradeCode="IH")
        ])),
        (ChatFilterType.CAREER, lambda: CareerFilterRs(careerList=[
            CareerFilterDetailRs(jobTitleCode="1", careerMonths=24, careerConditionType=CareerConditionType.UNDER),
            CareerFilterDetailRs(jobTitleCode="2", careerMonths=12, careerConditionType=CareerConditionType.OVER)
        ]))
    ]

    skill_summary = ", ".join(requiredSkills)
    summaries = {
        ChatFilterType.SKILL: f"{skill_summary} 개발자 포지션에 대한 기술 스킬 필터입니다.",
        ChatFilterType.EDUCATION: f"{skill_summary} 개발자 포지션에 대한 교육 필터입니다.",
        ChatFilterType.LICENSE: f"{skill_summary} 개발자 포지션에 대한 자격증 필터입니다.",
        ChatFilterType.EXAMINATION: f"{skill_summary} 개발자 포지션에 대한 시험 필터입니다.",
        ChatFilterType.CAREER: f"{skill_summary} 개발자 포지션에 대한 경력 필터입니다."
    }

    # 모든 필터 타입에 대한 결과를 생성
    filter_results = [
        FilterResult(
            type=filter_type,
            summary=summaries[filter_type],
            filterValue=filter_value_func()
        )
        for filter_type, filter_value_func in filter_types
    ]

    return JobDescriptionFiltersRs(
        jobDescriptionSn=jobDescriptionSn,
        subDomain=subDomain,
        filters=filter_results
    )

@app.post("/api/v1/chats/job-descriptions/filter")
async def get_job_description_filters(
    job_description_filter: JobDescriptionFiltersRq,
    # api_key: str = Depends(verify_api_key)
):
    try:
        return get_next_filter(job_description_filter.requiredSkills, job_description_filter.subDomain, job_description_filter.jobDescriptionSn)
    except Exception as e:
        logger.error(f"Error in get_job_description_filters: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal Solver Error: {str(e)}"
        )



if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
