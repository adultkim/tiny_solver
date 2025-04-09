from openai import AsyncOpenAI
from typing import AsyncGenerator
from type_def import StreamChunk, EventType
import json

class OpenAIClient:
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
        
    async def generate_streaming_response(self, prompt: str) -> AsyncGenerator[StreamChunk, None]:
        """
        OpenAI API를 통해 스트리밍 응답을 생성하고 이벤트 타입에 따라 분류합니다.
        """
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[{"role": "user", "content": prompt}],
                stream=True,
                temperature=0.7,
                max_tokens=1000
            )
            
            current_type = EventType.TEXT
            current_content = ""
            
            async for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    current_content += content
                    
                    # 특정 키워드나 패턴을 감지하여 이벤트 타입 변경
                    if "직무 제목:" in current_content:
                        if current_type != EventType.JOB_TITLE_TEXT:
                            if current_content.strip():
                                yield StreamChunk(type=current_type, data=current_content.strip())
                            current_type = EventType.JOB_TITLE_TEXT
                            current_content = ""
                    elif "직무 설명:" in current_content:
                        if current_type != EventType.JOB_DESCRIPTION_TEXT:
                            if current_content.strip():
                                yield StreamChunk(type=current_type, data=current_content.strip())
                            current_type = EventType.JOB_DESCRIPTION_TEXT
                            current_content = ""
                    elif "필수 스킬:" in current_content:
                        if current_type != EventType.REQUIRED_SKILL_TEXT:
                            if current_content.strip():
                                yield StreamChunk(type=current_type, data=current_content.strip())
                            current_type = EventType.REQUIRED_SKILL_TEXT
                            current_content = ""
                    elif "우대 스킬:" in current_content:
                        if current_type != EventType.PREFERRED_SKILL_TEXT:
                            if current_content.strip():
                                yield StreamChunk(type=current_type, data=current_content.strip())
                            current_type = EventType.PREFERRED_SKILL_TEXT
                            current_content = ""
            
            # 마지막 청크 전송
            if current_content.strip():
                yield StreamChunk(type=current_type, data=current_content.strip())
                
        except Exception as e:
            yield StreamChunk(type=EventType.COMMAND, data=json.dumps({"type": "ERROR", "message": str(e)})) 