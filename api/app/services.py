import openai
from .config import OPENAI_API_KEY, GPT_MODEL
from .models import ChatMessage, ChatRequest, ChatResponse
from fastapi.responses import StreamingResponse
import json
import asyncio

# OpenAI 클라이언트 설정
openai.api_key = OPENAI_API_KEY


async def generate_chat_response(request: ChatRequest) -> ChatResponse:
    """
    OpenAI API를 사용하여 채팅 응답을 생성합니다.
    
    Args:
        request: ChatRequest 모델의 요청 데이터
    
    Returns:
        ChatResponse: 생성된 응답
    """
    try:
        # 모델 설정
        model = request.model or GPT_MODEL
        
        # OpenAI API 호출
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=model,
            messages=[{
                "role": msg.role,
                "content": msg.content
            } for msg in request.messages],
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        # 응답 파싱
        content = response.choices[0].message.content
        usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens
        }
        
        return ChatResponse(
            response=content,
            model=model,
            usage=usage
        )
    
    except Exception as e:
        # 에러 처리
        error_message = f"Error generating response: {str(e)}"
        return ChatResponse(
            response=error_message,
            model=model,
            usage={"error": str(e)}
        )


async def generate_streaming_response(request: ChatRequest):
    """
    OpenAI API를 사용하여 스트리밍 채팅 응답을 생성합니다.
    
    Args:
        request: ChatRequest 모델의 요청 데이터
    
    Returns:
        StreamingResponse: 스트리밍 응답
    """
    model = request.model or GPT_MODEL
    
    # 비동기 이터레이터를 정의합니다
    async def stream_generator():
        try:
            # OpenAI API 스트리밍 호출
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            stream = client.chat.completions.create(
                model=model,
                messages=[{
                    "role": msg.role,
                    "content": msg.content
                } for msg in request.messages],
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stream=True
            )
            
            collected_messages = []
            
            # 청크 스트리밍
            for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    collected_messages.append(content)
                    
                    # 각 청크를 JSON으로 반환하고 명시적으로 개행 문자를 포함
                    # text/event-stream 형식으로 변경
                    yield f"data: {json.dumps({'content': content, 'is_streaming': True, 'model': model})}\n\n"
                    # 비동기 작업 양보하기
                    await asyncio.sleep(0)
            
            # 스트리밍 완료 신호
            yield f"data: {json.dumps({'content': '', 'is_streaming': False, 'model': model, 'usage': {'completion_tokens': len(collected_messages)}})}\n\n"
            yield f"data: [DONE]\n\n"
            
        except Exception as e:
            # 에러 처리
            error_message = f"Error streaming response: {str(e)}"
            print(f"Streaming error: {str(e)}")
            yield f"data: {json.dumps({'content': error_message, 'is_streaming': False, 'error': str(e), 'model': model})}\n\n"
            yield f"data: [DONE]\n\n"
    
    # 비동기 이터레이터 반환
    return stream_generator() 