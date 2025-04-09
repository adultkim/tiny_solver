from enum import Enum
from pydantic import BaseModel
from typing import Any

class EventType(str, Enum):
    TEXT = "TEXT"
    JOB_TITLE_TEXT = "JOB_TITLE_TEXT"
    JOB_DESCRIPTION_TEXT = "JOB_DESCRIPTION_TEXT"
    REQUIRED_SKILL_TEXT = "REQUIRED_SKILL_TEXT"
    PREFERRED_SKILL_TEXT = "PREFERRED_SKILL_TEXT"
    COMMAND = "COMMAND"

class CommandType(str, Enum):
    ERROR = "ERROR"

class StreamChunk(BaseModel):
    type: EventType
    data: Any
