from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, List
import asyncio
from enum import Enum
from pydantic import BaseModel
from typing import Any

class EventType(str, Enum):
    TEXT = "TEXT"
    JOB_TITLE_TEXT = "JOB_TITLE_TEXT"
    JOB_DESCRIPTION_TEXT = "JOB_DESCRIPTION_TEXT"
    REQUIRED_SKILL_TEXT = "REQUIRED_SKILL_TEXT"
    PREFERRED_SKILL_TEXT = "PREFERRED_SKILL_TEXT"
    MATCHING_TALENT = "MATCHING_TALENT"
    ERROR = "ERROR"

class InputType(str, Enum):
    INIT_REQUEST = "INIT_REQUEST"
    TITLE = "TITLE"
    DESCRIPTION = "DESCRIPTION"
    REQUIRED_SKILL = "REQUIRED_SKILL"
    PREFERRED_SKILL = "PREFERRED_SKILL"


class Chunk(BaseModel):
    type: str
    data: object

class JobDescriptionServiceDto(BaseModel):
    sn: int
    title: str
    descriptions: List[str]
    requiredSkills: List[str]
    preferredSkills: List[str]

class JobDto(BaseModel):
    jobGroupCode: int
    jobGroupName: str
    jobDefinition: str

class TalentsRecommendRs(BaseModel):
    chatSn: int
    jobDescriptionSn: int
    jobGroupCode: int
    chunkRsList: List[Chunk]
    businessNumber: str    

class ChatValidRequest(BaseModel):
    jobDescription: Optional[JobDescriptionServiceDto] = None  
    inputType : InputType
    content: List[str]

class ChatRequest(BaseModel):
    chatSn: int
    businessNumber : str
    content: str

class ChatResponse(BaseModel):
    chatSn: int
    type: str
    content: str

class JobPosting(BaseModel):
    text: str
    job_title: str
    job_description: str
    required_skills: str
    preferred_skills: str

class ChatValidResponse(BaseModel):
    isValidYn : bool
    comment: str

class ChatResponseJson(BaseModel):
    businessNumber : str
    chatSn: int
    chunkRsList: List[Chunk]

class ChatSessionLog(BaseModel):
    chat: List[Any]
    cost: float


class JobDescriptionResponse(BaseModel):
    chatSn : int
    chatSessionId: str
    chatResponse: str
    jobDesc: dict
    chatSessionLog: ChatSessionLog

# 테스트용 응답 데이터
DEFAULT_JOB_DESCRIPTIONS = [
    Chunk(type=EventType.TEXT, data="재무회계 담당자를 찾고 계시군요!"),
    Chunk(type=EventType.TEXT, data="정확한 수치 분석과 체계적인 관리로, 안정적인 재무 환경을 만들어갈 분이 필요하겠네요."),
    Chunk(type=EventType.JOB_TITLE_TEXT, data="재경본부 신입"),
    Chunk(type=EventType.JOB_DESCRIPTION_TEXT, data="자금 조달 및 지출 관리"),
    Chunk(type=EventType.JOB_DESCRIPTION_TEXT, data="단기 및 장기 자금 계획 수립 및 운영"),
    Chunk(type=EventType.JOB_DESCRIPTION_TEXT, data="재무제표 작성 및 분석 지원"),
    Chunk(type=EventType.JOB_DESCRIPTION_TEXT, data="회계 장부 관리 및 일반예산 결산 수행"),
    Chunk(type=EventType.JOB_DESCRIPTION_TEXT, data="내부 감사 및 재무 규정 준수 여부 검토"),
    Chunk(type=EventType.REQUIRED_SKILL_TEXT, data="회계 및 세무 관련 경력 1년 이상"),
    Chunk(type=EventType.REQUIRED_SKILL_TEXT, data="회계 관련 학위 또는 자격증 소지자"),
    Chunk(type=EventType.REQUIRED_SKILL_TEXT, data="회계 소프트웨어 사용 경험 (SAP, ERP 등)"),
    Chunk(type=EventType.PREFERRED_SKILL_TEXT, data="CPA 자격증 소지자"),
    Chunk(type=EventType.PREFERRED_SKILL_TEXT, data="세무 및 회계 규정에 대한 이해"),
    Chunk(type=EventType.TEXT, data="입력창을 눌러 언제든 직접 수정하실 수 있어요."),
    Chunk(type=EventType.TEXT, data="편하게 적어주시면, 제가 자연스럽게 다듬어드릴게요."),
]

DEFAULT_MATCHING_TALENT = [
    Chunk(type=EventType.MATCHING_TALENT, data=["cano721", "zkdlto", "jjs0621", "wldb20", "lyj0508"])
]
# 진행 중인 채팅 응답 생성 작업을 추적하기 위한 전역 상태
chat_response_events: Dict[int, asyncio.Event] = {}