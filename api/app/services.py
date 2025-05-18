import openai
from .config import OPENAI_API_KEY, GPT_MODEL
from .models import ChatMessage, ChatRequest, ChatResponse, ImageAnalysisRequest, ImageAnalysisResponse
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
        
        # 모델 ID 매핑 (필요한 경우)
        model_mapping = {
            "gpt-4.1": "gpt-4.1",
            "gpt-4o": "gpt-4o",
            "o4-mini": "gpt-4o-mini",
            "o3": "gpt-3.5-turbo"
        }
        
        # 모델 ID 변환
        api_model = model_mapping.get(model, model)
        
        # OpenAI API 호출
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        # 입력 메시지 형식 변환
        input_messages = []
        for msg in request.messages:
            input_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # 새로운 응답 API 호출
        response = client.responses.create(
            model=api_model,
            input=input_messages,
            temperature=request.temperature,
            max_output_tokens=request.max_tokens
        )
        
        # 응답 파싱
        content = ""
        if hasattr(response, 'output_text'):
            content = response.output_text
        else:
            # 출력 텍스트를 찾을 수 없는 경우
            for output in response.output:
                if hasattr(output, 'content'):
                    for item in output.content:
                        if hasattr(item, 'text'):
                            content += item.text
        
        # 사용량 정보
        usage = {}
        if hasattr(response, 'usage'):
            usage = {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
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


async def analyze_image(request: ImageAnalysisRequest) -> ImageAnalysisResponse:
    """
    OpenAI API를 사용하여 이미지를 분석합니다.
    
    Args:
        request: ImageAnalysisRequest 모델의 요청 데이터
    
    Returns:
        ImageAnalysisResponse: 이미지 분석 결과
    """
    # 스트리밍 요청이면 스트리밍 처리
    if hasattr(request, 'stream') and request.stream:
        # 별도의 함수를 직접 호출하지 않고, 라우터에서 처리하도록 표시만 함
        # 스트리밍 요청임을 나타내는 값만 반환
        return ImageAnalysisResponse(
            response="Streaming request - handled separately",
            model=request.model or "gpt-4.1",
            is_streaming=True
        )
        
    try:
        # 모델 설정 (기본값: GPT-4.1)
        model = request.model or "gpt-4.1"
        
        # 모델 ID 매핑 (필요한 경우)
        model_mapping = {
            "gpt-4.1": "gpt-4.1",
            "gpt-4o": "gpt-4o",
            "o4-mini": "gpt-4o-mini",
            "o3": "gpt-3.5-turbo"
        }
        
        # 모델 ID 변환
        api_model = model_mapping.get(model, model)
        
        # OpenAI 클라이언트 초기화
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        # 이미지 URL 확인 및 처리
        image_url = request.image_url
        
        print(f"Debug - Model: {model} -> API Model: {api_model}")
        
        # 이미지 URL이 유효한지 확인
        if not image_url:
            raise ValueError("유효한 이미지 URL이 필요합니다.")
        
        # URL이 base64 형식인지 확인하고 처리
        if image_url.startswith('data:image/'):
            print("Debug - Processing base64 image")
            
            # 이미지 형식 확인
            try:
                content_type = image_url.split(';')[0].split(':')[1]
                print(f"Debug - Image content type: {content_type}")
                
                # 지원되는 형식 확인
                if content_type not in ["image/jpeg", "image/png", "image/gif", "image/webp"]:
                    print(f"Warning - Content type {content_type} may not be supported")
            except Exception as e:
                print(f"Debug - Error parsing image content type: {str(e)}")
            
            # Base64 데이터 추출 ("data:image/jpeg;base64," 부분 제거)
            try:
                base64_data = image_url.split(',')[1]
                print(f"Debug - Base64 data length: {len(base64_data)}")
            except Exception as e:
                print(f"Debug - Error extracting base64 data: {str(e)}")
                raise ValueError("이미지 URL 형식이 올바르지 않습니다. 'data:image/xxx;base64,' 형식이어야 합니다.")
        else:
            print(f"Debug - Image URL is not base64 format")
        
        # API 호출을 위한 입력 구성 - 새로운 responses API 형식 사용
        input_content = []
        
        # 대화 컨텍스트가 있으면 추가
        if request.conversation_history:
            for msg in request.conversation_history:
                input_content.append({
                    "role": msg.role,
                    "content": [{
                        "type": "input_text",
                        "text": msg.content
                    }]
                })
                print(f"Debug - Added context message: {msg.role[:100]}")
        
        # 사용자 메시지와 이미지 추가
        input_content.append({
            "role": "user",
            "content": [
                {
                    "type": "input_text", 
                    "text": request.prompt
                },
                {
                    "type": "input_image",
                    "image_url": image_url
                }
            ]
        })
        
        # API 호출 준비
        print(f"Debug - Calling OpenAI API with model: {model} -> {api_model}")
        
        # OpenAI API 호출 (비스트리밍 모드)
        response = client.responses.create(
            model=api_model,
            input=input_content,
            max_output_tokens=request.max_tokens
        )
        
        # 응답 파싱
        content = ""
        if hasattr(response, 'output_text'):
            content = response.output_text
        else:
            # 출력 텍스트를 찾을 수 없는 경우
            for output in response.output:
                if hasattr(output, 'content'):
                    for item in output.content:
                        if hasattr(item, 'text'):
                            content += item.text
        
        # 사용량 정보
        usage = {}
        if hasattr(response, 'usage'):
            usage = {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.total_tokens
            }
        
        # 최종 응답 반환
        return ImageAnalysisResponse(
            response=content,
            model=model,
            usage=usage
        )
        
    except Exception as e:
        # 상세 에러 메시지 로깅
        error_message = f"Error analyzing image: {str(e)}"
        print(f"Image analysis error: {str(e)}")
        
        # 사용자에게 반환할 응답 작성
        return ImageAnalysisResponse(
            response=error_message,
            model=model or "gpt-4.1",
            usage={"error": str(e)}
        )

async def analyze_image_streaming(request: ImageAnalysisRequest):
    """
    이미지를 분석하고 스트리밍 응답을 생성합니다.
    
    Args:
        request: ImageAnalysisRequest 객체
        
    Returns:
        StreamingResponse: 스트리밍 응답 객체
    """
    # 모델 설정 (기본값: GPT-4.1)
    model = request.model or "gpt-4.1"
    
    # 모델 ID 매핑 (필요한 경우)
    model_mapping = {
        "gpt-4.1": "gpt-4.1",
        "gpt-4o": "gpt-4o",
        "o4-mini": "gpt-4o-mini",
        "o3": "gpt-3.5-turbo"
    }
    
    # 모델 ID 변환
    api_model = model_mapping.get(model, model)
    
    # OpenAI 클라이언트 초기화
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    
    # 비동기 이터레이터를 정의합니다
    async def stream_generator():
        try:
            # 이미지 URL 확인 및 처리
            image_url = request.image_url
            
            if not image_url:
                raise ValueError("유효한 이미지 URL이 필요합니다.")
            
            # 이미지 형식 검증
            if image_url.startswith('data:image/'):
                print("Debug - Processing base64 image for streaming")
                try:
                    content_type = image_url.split(';')[0].split(':')[1]
                    print(f"Debug - Image content type: {content_type}")
                except Exception as e:
                    print(f"Debug - Error parsing image content type: {str(e)}")
            
            # API 호출을 위한 입력 구성
            input_content = []
            
            # 대화 컨텍스트가 있으면 추가
            if request.conversation_history:
                for msg in request.conversation_history:
                    input_content.append({
                        "role": msg.role,
                        "content": [{
                            "type": "input_text",
                            "text": msg.content
                        }]
                    })
                    print(f"Debug - Added context message to stream: {msg.role}")
            
            # 사용자 메시지와 이미지 추가
            input_content.append({
                "role": "user",
                "content": [
                    {
                        "type": "input_text", 
                        "text": request.prompt
                    },
                    {
                        "type": "input_image",
                        "image_url": image_url
                    }
                ]
            })
            
            print(f"Debug - Calling streaming OpenAI API with model: {model} -> {api_model}")
            
            # OpenAI API 호출
            stream = client.responses.create(
                model=api_model,
                input=input_content,
                stream=True,
                max_output_tokens=request.max_tokens
            )
            
            collected_messages = []
            
            # 청크 스트리밍
            for event in stream:
                # 응답 타입에 따라 처리
                if hasattr(event, 'type') and event.type == 'response.output_text.delta':
                    delta = event.delta
                    if delta:
                        collected_messages.append(delta)
                        
                        # 각 청크를 JSON으로 반환하고 명시적으로 개행 문자를 포함
                        # text/event-stream 형식으로 변경
                        yield f"data: {json.dumps({'content': delta, 'is_streaming': True, 'model': model})}\n\n"
                        # 비동기 작업 양보하기
                        await asyncio.sleep(0)
                
                # 완료 이벤트 처리
                if hasattr(event, 'type') and event.type == 'response.completed':
                    break
            
            # 스트리밍 완료 신호
            yield f"data: {json.dumps({'content': '', 'is_streaming': False, 'model': model, 'usage': {'completion_tokens': len(collected_messages)}})}\n\n"
            yield f"data: [DONE]\n\n"
            
        except Exception as e:
            # 에러 처리
            error_message = f"Error streaming image analysis: {str(e)}"
            print(f"Image streaming error: {str(e)}")
            yield f"data: {json.dumps({'content': error_message, 'is_streaming': False, 'error': str(e), 'model': model})}\n\n"
            yield f"data: [DONE]\n\n"
    
    # 비동기 이터레이터 반환
    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )


async def generate_streaming_response(request: ChatRequest):
    """
    OpenAI API를 사용하여 스트리밍 응답을 생성하는 비동기 함수.
    
    Args:
        request: ChatRequest 객체
        
    Returns:
        스트리밍 응답 이터레이터
    """
    # 모델 설정
    model = request.model
    
    # 모델 ID 매핑 (필요한 경우)
    model_mapping = {
        "gpt-4.1": "gpt-4.1",
        "gpt-4o": "gpt-4o",
        "o4-mini": "gpt-4o-mini",
        "o3": "gpt-3.5-turbo"
    }
    
    # 모델 ID 변환
    api_model = model_mapping.get(model, model)
    
    # OpenAI 클라이언트 초기화
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    
    async def stream_generator():
        try:
            # 입력 메시지 형식 변환
            input_messages = []
            for msg in request.messages:
                input_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
                
            # 새로운 응답 API 호출 (스트리밍)
            stream = client.responses.create(
                model=api_model,
                input=input_messages,
                temperature=request.temperature,
                max_output_tokens=request.max_tokens,
                stream=True
            )
            
            collected_messages = []
            
            # 청크 스트리밍
            for event in stream:
                # 응답 타입에 따라 처리
                if hasattr(event, 'type') and event.type == 'response.output_text.delta':
                    delta = event.delta
                    if delta:
                        collected_messages.append(delta)
                        
                        # 각 청크를 JSON으로 반환하고 명시적으로 개행 문자를 포함
                        # text/event-stream 형식으로 변경
                        yield f"data: {json.dumps({'content': delta, 'is_streaming': True, 'model': model})}\n\n"
                        # 비동기 작업 양보하기
                        await asyncio.sleep(0)
                
                # 완료 이벤트 처리
                if hasattr(event, 'type') and event.type == 'response.completed':
                    break
            
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