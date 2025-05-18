from pydantic import BaseModel, Field
from typing import List, Optional, Union, Dict, Any, Literal


class ChatMessage(BaseModel):
    role: str = "user"
    content: str


class ImageAnalysisRequest(BaseModel):
    """
    이미지 분석 요청 모델
    """
    image_url: Optional[str] = None
    prompt: str
    model: Optional[str] = None
    max_tokens: int = 1000
    detail: str = "auto"
    stream: bool = False
    conversation_history: Optional[List[ChatMessage]] = None


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