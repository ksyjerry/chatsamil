from pydantic import BaseModel, Field
from typing import List, Optional, Union, Dict, Any, Literal


class ChatMessage(BaseModel):
    role: str = "user"
    content: str


class ImageAnalysisRequest(BaseModel):
    image_url: str
    prompt: Optional[str] = "이 이미지에 대해 자세히 설명해주세요."
    model: Optional[str] = None
    max_tokens: Optional[int] = 1000
    detail: Optional[Literal["low", "high", "auto"]] = "auto"


class ImageAnalysisResponse(BaseModel):
    response: str
    model: str
    usage: dict


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000
    stream: Optional[bool] = False
    
    
class ChatResponse(BaseModel):
    response: str
    model: str
    usage: dict
    is_streaming: Optional[bool] = False 