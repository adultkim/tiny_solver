from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict
from type_def import StreamChunk, EventType
import asyncio

class ChatRequest(BaseModel):
    chatSn: int
    content: str
    created_at: Optional[datetime] = None

class ChatResponse(BaseModel):
    chatSn: int
    type: str
    content: str
    created_at: Optional[datetime] = None

class JobPosting(BaseModel):
    text: str
    job_title: str
    job_description: str
    required_skills: str
    preferred_skills: str

# 테스트용 응답 데이터
DEFAULT_CHUNKS = [
    StreamChunk(type=EventType.TEXT, data="재무회계 담당자를 찾고 계시군요!\n정확한 수치 분석과 체계적인 관리로, 안정적인 재무 환경을 만들어갈 분이 필요하겠네요."),
    StreamChunk(type=EventType.JOB_TITLE_TEXT, data="재경본부 신입"),
    StreamChunk(type=EventType.JOB_DESCRIPTION_TEXT, data="자금 조달 및 지출 관리\n단기 및 장기 자금 계획 수립 및 운영\n재무제표 작성 및 분석 지원\n회계 장부 관리 및 일반예산 결산 수행\n내부 감사 및 재무 규정 준수 여부 검토\n"),
    StreamChunk(type=EventType.REQUIRED_SKILL_TEXT, data="회계 및 세무 관련 경력 1년 이상\n회계 관련 학위 또는 자격증 소지자\n회계 소프트웨어 사용 경험 (SAP, ERP 등)\n"),
    StreamChunk(type=EventType.PREFERRED_SKILL_TEXT, data="CPA 자격증 소지자\n세무 및 회계 규정에 대한 이해\n"),
    StreamChunk(type=EventType.TEXT, data="입력창을 눌러 언제든 직접 수정하실 수 있어요.\n편하게 적어주시면, 제가 자연스럽게 다듬어드릴게요."),
]

# 진행 중인 채팅 응답 생성 작업을 추적하기 위한 전역 상태
chat_response_events: Dict[int, asyncio.Event] = {}