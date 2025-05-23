import logging
import os
import re
from enum import Enum
from typing import List, Union, Optional
from uuid import uuid4

import requests
from fastapi import FastAPI, Request
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from models import SolverApiResponse, ChatRequest, DEFAULT_JOB_DESCRIPTIONS, DEFAULT_MATCHING_TALENT, ChatResponseJson, \
    JobDescriptionResponse, ChatSessionLog, EventType, Chunk, ChatValidRequest, ChatValidResponse, InputType, \
    JobDescriptionServiceDto, TalentsRecommendRs, JobDto

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


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error for request {request.url}:\n{exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
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
    chatSn: Optional[int] = None
    businessNumber: str
    jobDescription: JobDescriptionServiceDto
    inputType: InputType
    content: List[str]


class SolverChatRefineRs(BaseModel):
    content: List[str]


@app.post("/api/v1/chats/refine")
async def refine_chat(request: SolverChatRefineRq) -> SolverApiResponse[SolverChatRefineRs]:
    try:
        # 각 항목을 다듬는 예시 처리
        refined = [f"[다듬다듬] {item}" for item in request.content]
        return SolverApiResponse(success=True, data=SolverChatRefineRs(content=refined))
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
        return SolverApiResponse(success=True, data=ChatValidResponse(
            isValidYn=True,
            comment='부적절한 단어 "싸움잘하는 사람"이 포함되어 있습니다.'
        ))
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
        return SolverApiResponse(success=True, data=ChatResponseJson(
            chatSn=chat_request.chatSn,
            businessNumber=chat_request.businessNumber,
            chunkRsList=DEFAULT_JOB_DESCRIPTIONS
        ))
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


class TalentsRecommendRq(BaseModel):
    chatSn: int
    businessNumber: str
    jobs: List[JobDto]
    jobDescription: JobDescriptionServiceDto


@app.post("/api/v1/chats/job-descriptions/recommended-talents")
async def get_recommended_talents(
        talentsRq: TalentsRecommendRq,
        # api_key: str = Depends(verify_api_key)
):
    try:
        # TODO: 실제 추천 로직 구현
        # 임시로 더미 데이터 반환
        return SolverApiResponse(success=True, data=TalentsRecommendRs(
            chatSn=talentsRq.chatSn,
            jobDescriptionSn=talentsRq.jobDescription.sn,
            businessNumber=talentsRq.businessNumber,
            jobGroupCode=1,
            chunkRsList=DEFAULT_MATCHING_TALENT
        ))
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


class EducationLevelType(str, Enum):
    HIGHSCHOOL = "HIGHSCHOOL"
    ASSOCIATE = "ASSOCIATE"
    BACHELOR = "BACHELOR"
    MASTER = "MASTER"
    DOCTOR = "DOCTOR"

class SkillLevel(str, Enum):
    BASIC = "BASIC"
    BEGINNER = "BEGINNER"
    MIDDLE = "MIDDLE"
    ADVANCED = "ADVANCED"
    PROFESSIONAL = "PROFESSIONAL"

class EducationFilterDetailRs(BaseModel):
    majorCode: int
    educationLevel: EducationLevelType

class SkillFilterDetailRs(BaseModel):
    skillCode: int
    skillLevel: SkillLevel

class ExaminationFilterDetailRs(BaseModel):
    examinationCode: int
    score: Optional[int] = None
    gradeCode: Optional[str] = None


class CareerFilterDetailRs(BaseModel):
    jobTitleCode: int
    careerMonths: int
    careerConditionType: CareerConditionType


class EducationFilterRs(BaseModel):
    educationList: List[EducationFilterDetailRs]


class LicenseFilterRs(BaseModel):
    licenseCodes: List[int]


class SkillFilterRs(BaseModel):
    skillList: List[SkillFilterDetailRs]


class ExaminationFilterRs(BaseModel):
    examinationList: List[ExaminationFilterDetailRs]


class CareerFilterRs(BaseModel):
    careerList: List[CareerFilterDetailRs]


class JobDescriptionFiltersRq(BaseModel):
    chatSn: int
    jobDescription: JobDescriptionServiceDto
    businessNumber: str


class FilterResult(BaseModel):
    type: ChatFilterType
    summary: str
    userQuery: str
    filterValue: Union[EducationFilterRs, LicenseFilterRs, SkillFilterRs, ExaminationFilterRs, CareerFilterRs]


class FilterUpdateResult(BaseModel):
    type: ChatFilterType
    summary: str
    filterValue: Union[EducationFilterRs, LicenseFilterRs, SkillFilterRs, ExaminationFilterRs, CareerFilterRs]


class JobDescriptionFiltersRs(BaseModel):
    chatSn: int
    jobDescriptionSn: int
    businessNumber: str
    filters: List[FilterResult]


def get_next_filter(chatSn: int, jobDescription: JobDescriptionServiceDto,
                    businessNumber: str) -> JobDescriptionFiltersRs:
    # 필터 타입과 해당 필터 값을 생성하는 함수 정의
    filter_types = [
        (ChatFilterType.SKILL, lambda: SkillFilterRs(skillList=[
            SkillFilterDetailRs(skillCode=2, skillLevel=SkillLevel.BASIC),
            SkillFilterDetailRs(skillCode=4, skillLevel=SkillLevel.BEGINNER),
            SkillFilterDetailRs(skillCode=6, skillLevel=SkillLevel.MIDDLE),
        ])),
        (ChatFilterType.EDUCATION, lambda: EducationFilterRs(educationList=[
            EducationFilterDetailRs(majorCode=1010101, educationLevel=EducationLevelType.BACHELOR),
            EducationFilterDetailRs(majorCode=1010201, educationLevel=EducationLevelType.BACHELOR),
            EducationFilterDetailRs(majorCode=1010301, educationLevel=EducationLevelType.BACHELOR),
        ])),
        (ChatFilterType.LICENSE, lambda: LicenseFilterRs(licenseCodes=[10001, 10002, 10003])),
        (ChatFilterType.EXAMINATION, lambda: ExaminationFilterRs(examinationList=[
            ExaminationFilterDetailRs(examinationCode=1, score=100, gradeCode=None),
            ExaminationFilterDetailRs(examinationCode=2, score=None, gradeCode="A1")
        ])),
        (ChatFilterType.CAREER, lambda: CareerFilterRs(careerList=[
            CareerFilterDetailRs(jobTitleCode="1", careerMonths=60, careerConditionType=CareerConditionType.UNDER),
            CareerFilterDetailRs(jobTitleCode="2", careerMonths=1, careerConditionType=CareerConditionType.OVER)
        ]))
    ]

    skill_summary = ", ".join(jobDescription.requiredSkills)
    summaries = {
        ChatFilterType.SKILL: f"{skill_summary} 개발자 포지션에 대한 기술 스킬 필터입니다.",
        ChatFilterType.EDUCATION: f"{skill_summary} 개발자 포지션에 대한 교육 필터입니다.",
        ChatFilterType.LICENSE: f"{skill_summary} 개발자 포지션에 대한 자격증 필터입니다.",
        ChatFilterType.EXAMINATION: f"{skill_summary} 개발자 포지션에 대한 시험 필터입니다.",
        ChatFilterType.CAREER: f"{skill_summary} 개발자 포지션에 대한 경력 필터입니다."
    }

    userQueries = {
        ChatFilterType.SKILL: "자격 요건1",
        ChatFilterType.EDUCATION: "자격 요건2",
        ChatFilterType.LICENSE: "자격 요건3",
        ChatFilterType.EXAMINATION: "자격 요건4",
        ChatFilterType.CAREER: "자격 요건5"
    }

    # 모든 필터 타입에 대한 결과를 생성
    filter_results = [
        FilterResult(
            type=filter_type,
            summary=summaries[filter_type],
            userQuery=userQueries[filter_type],
            filterValue=filter_value_func()
        )
        for filter_type, filter_value_func in filter_types
    ]

    return JobDescriptionFiltersRs(
        chatSn=chatSn,
        jobDescriptionSn=jobDescription.sn,
        businessNumber=businessNumber,
        filters=filter_results
    )


@app.post("/api/v1/chats/job-descriptions/filter")
async def get_job_description_filters(
        job_description_filter: JobDescriptionFiltersRq,
        # api_key: str = Depends(verify_api_key)
):
    try:
        result = get_next_filter(
            job_description_filter.chatSn,
            job_description_filter.jobDescription,
            job_description_filter.businessNumber)
        return SolverApiResponse(success=True, data=result)
    except Exception as e:
        logger.error(f"Error in get_job_description_filters: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal Solver Error: {str(e)}"
        )


class FilterActionType(str, Enum):
    ADD = "ADD"
    MODIFY = "MODIFY"
    DELETE = "DELETE"


class ActionFilterResult(BaseModel):
    filterSn: int
    type: ChatFilterType
    summary: str
    filterValue: Union[EducationFilterRs, LicenseFilterRs, SkillFilterRs, ExaminationFilterRs, CareerFilterRs]


class FilterActionRequest(BaseModel):
    chatSn: int
    jobDescriptionSn: int
    filters: List[ActionFilterResult]
    keyword: str


class FilterActionResponse(BaseModel):
    actionType: FilterActionType
    filterSn: Optional[int] = None
    filterResult: Optional[FilterResult] = None


class FilterUpdateActionResponse(BaseModel):
    actionType: FilterActionType
    filterSn: Optional[int] = None
    filterResult: Optional[FilterUpdateResult] = None


@app.post("/api/v1/chats/filters")
async def process_filter_action(
        request: FilterActionRequest
):
    try:
        if not request.filters:
            raise HTTPException(
                status_code=400,
                detail="필터 목록이 비어있습니다."
            )

        # 키워드에 "삭제"가 포함된 경우
        if "삭제" in request.keyword:
            # 삭제 케이스
            return SolverApiResponse(success=True, data=FilterUpdateActionResponse(
                actionType=FilterActionType.DELETE,
                filterSn=request.filters[0].filterSn
            ))
        # 키워드에 "변경"이 포함된 경우
        elif "변경" in request.keyword:
            # 수정 케이스
            modified_filter = FilterUpdateResult(
                type=ChatFilterType.SKILL,
                summary=f"Python 개발자 포지션에 대한 수정된 필터입니다.",
                filterValue=SkillFilterRs(skillList=[
                    SkillFilterDetailRs(skillCode=2, skillLevel=SkillLevel.BASIC),
                    SkillFilterDetailRs(skillCode=4, skillLevel=SkillLevel.BEGINNER),
                    SkillFilterDetailRs(skillCode=6, skillLevel=SkillLevel.MIDDLE),
                ])
            )

            filterSn = request.filters[0].filterSn

            return SolverApiResponse(success=True, data=FilterUpdateActionResponse(
                actionType=FilterActionType.MODIFY,
                filterSn=filterSn,
                filterResult=modified_filter
            ))
        # 그 외 케이스
        else:
            # 추가 케이스
            new_filter = FilterUpdateResult(
                type=ChatFilterType.SKILL,
                summary=f"Python 개발자 포지션에 대한 새로운 필터입니다.",
                filterValue=SkillFilterRs(skillList=[
                    SkillFilterDetailRs(skillCode=2, skillLevel=SkillLevel.BASIC),
                    SkillFilterDetailRs(skillCode=4, skillLevel=SkillLevel.BEGINNER),
                    SkillFilterDetailRs(skillCode=6, skillLevel=SkillLevel.MIDDLE),
                ])
            )

            return SolverApiResponse(success=True, data=FilterUpdateActionResponse(
                actionType=FilterActionType.ADD,
                filterResult=new_filter))

    except Exception as e:
        logger.error(f"Error in process_filter_action: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal Solver Error: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
