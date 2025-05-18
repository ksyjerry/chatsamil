import openai
from .config import OPENAI_API_KEY, GPT_MODEL
from .models import ChatMessage, ChatRequest, ChatResponse, ImageAnalysisRequest, ImageAnalysisResponse, WebSearchRequest, WebSearchResponse
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
    # 스트리밍 요청이면 스트리밍 응답을 반환
    if request.stream:
        # 비동기 이터레이터 생성
        stream_iterator = await generate_streaming_response(request)
        return stream_iterator
    
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
        
        # 웹 검색 기능 지원 체크
        tools = None
        tool_choice = None
        if request.enable_web_search:
            # 웹 검색을 지원하지 않는 모델의 경우 gpt-4.1로 변경
            if api_model in ["gpt-4o-mini", "gpt-3.5-turbo"]:
                print(f"Warning: Model {api_model} does not support web search. Using gpt-4.1 instead.")
                api_model = "gpt-4.1"
                model = "gpt-4.1"
            
            # 웹 검색 도구 설정
            tools = [{"type": "web_search_preview", 
                     "user_location": {
                         "type": "approximate",
                         "country": "KR",
                         "city": "Seoul",
                         "region": "Seoul",
                         "timezone": "Asia/Seoul"
                     },
                     "search_context_size": "medium"
                     }]
            tool_choice = {"type": "web_search_preview"}  # 웹 검색 도구를 강제로 사용하도록 설정
            print(f"Debug - Web search enabled with model: {api_model}")
            
            # 특정 검색어가 있는 경우 마지막 메시지를 수정
            if request.search_query:
                # 마지막 메시지를 검색어로 변경
                input_messages[-1]["content"] = request.search_query
        
        # API 호출 준비
        api_params = {
            "model": api_model,
            "input": input_messages,
            "temperature": request.temperature,
            "max_output_tokens": request.max_tokens
        }
        
        # 웹 검색 도구가 있으면 추가
        if tools:
            api_params["tools"] = tools
        
        # 도구 선택 설정이 있으면 추가
        if tool_choice:
            api_params["tool_choice"] = tool_choice
        
        # 새로운 응답 API 호출
        response = client.responses.create(**api_params)
        
        # 응답 파싱
        content = ""
        citations = []
        
        # 웹 검색을 사용했다면 웹 검색 호출 ID 확인 (디버깅용)
        if request.enable_web_search:
            web_search_id = None
            for output in response.output:
                if output.type == "web_search_call":
                    web_search_id = output.id
                    print(f"Debug - Web search call ID: {web_search_id}")
                    break
        
        if hasattr(response, 'output_text'):
            content = response.output_text
        else:
            # 각 출력 항목 처리
            for output in response.output:
                # 웹 검색 결과인 경우
                if output.type == "message" and hasattr(output, 'content'):
                    for item in output.content:
                        if hasattr(item, 'text'):
                            content += item.text
                        
                        # 인용 정보 추출
                        if hasattr(item, 'annotations'):
                            for annotation in item.annotations:
                                if annotation.type == "url_citation":
                                    citations.append({
                                        "url": annotation.url,
                                        "title": annotation.title if hasattr(annotation, 'title') else "",
                                        "start_index": annotation.start_index,
                                        "end_index": annotation.end_index
                                    })
        
        # 사용량 정보
        usage = {}
        if hasattr(response, 'usage'):
            usage = {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.total_tokens
            }
        
        # 디버그 정보
        if citations:
            print(f"Debug - Found {len(citations)} citations in response")
        
        return ChatResponse(
            response=content,
            model=model,
            usage=usage,
            citations=citations
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
    
    # OpenAI 클라이언트 초기화
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    
    async def stream_generator():
        try:
            # 지역 변수로 api_model을 복사
            local_api_model = api_model
            
            # 입력 메시지 형식 변환
            input_messages = []
            for msg in request.messages:
                input_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # API 호출 준비
            api_params = {
                "model": local_api_model,
                "input": input_messages,
                "temperature": request.temperature,
                "max_output_tokens": request.max_tokens,
                "stream": True
            }
            
            # 웹 검색 기능 지원 체크
            if request.enable_web_search:
                # 웹 검색을 지원하지 않는 모델의 경우 gpt-4.1로 변경
                if local_api_model in ["gpt-4o-mini", "gpt-3.5-turbo"]:
                    print(f"Warning: Model {local_api_model} does not support web search. Using gpt-4.1 instead.")
                    local_api_model = "gpt-4.1"
                    api_params["model"] = local_api_model
                
                # 웹 검색 도구 설정
                api_params["tools"] = [{"type": "web_search_preview", 
                                       "user_location": {
                                           "type": "approximate",
                                           "country": "KR",
                                           "city": "Seoul",
                                           "region": "Seoul",
                                           "timezone": "Asia/Seoul"
                                       },
                                       "search_context_size": "medium"
                                      }]
                api_params["tool_choice"] = {"type": "web_search_preview"}
                print(f"Debug - Web search enabled with model: {local_api_model}")
                
                # 특정 검색어가 있는 경우 마지막 메시지를 수정
                if request.search_query:
                    # 마지막 메시지를 검색어로 변경
                    input_messages[-1]["content"] = request.search_query
                    api_params["input"] = input_messages
            
            # 새로운 응답 API 호출 (스트리밍)
            stream = client.responses.create(**api_params)
            
            collected_messages = []
            citations = []
            
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
                
                # 인용 정보 처리
                elif hasattr(event, 'type') and event.type == 'response.output_text.annotations':
                    if hasattr(event, 'annotations'):
                        for annotation in event.annotations:
                            if annotation.type == "url_citation":
                                citation = {
                                    "url": annotation.url,
                                    "title": annotation.title if hasattr(annotation, 'title') else "",
                                    "start_index": annotation.start_index,
                                    "end_index": annotation.end_index
                                }
                                citations.append(citation)
                        
                        # 인용 정보가 있으면 전송
                        if citations:
                            yield f"data: {json.dumps({'citations': citations, 'is_streaming': True, 'model': model})}\n\n"
                            # 비동기 작업 양보하기
                            await asyncio.sleep(0)
                
                # 웹 검색 호출 정보 처리
                elif hasattr(event, 'type') and event.type == 'web_search_call':
                    web_search_id = event.id if hasattr(event, 'id') else None
                    if web_search_id:
                        print(f"Debug - Web search call ID in streaming: {web_search_id}")
                
                # 완료 이벤트 처리
                elif hasattr(event, 'type') and event.type == 'response.completed':
                    break
            
            # 스트리밍 완료 신호
            completion_info = {
                'content': '', 
                'is_streaming': False, 
                'model': model, 
                'usage': {'completion_tokens': len(collected_messages)}
            }
            
            # 인용 정보가 있으면 추가
            if citations:
                completion_info['citations'] = citations
                print(f"Debug - Sending {len(citations)} citations in streaming completion")
            
            yield f"data: {json.dumps(completion_info)}\n\n"
            yield f"data: [DONE]\n\n"
            
        except Exception as e:
            # 에러 처리
            error_message = f"Error streaming response: {str(e)}"
            print(f"Streaming error: {str(e)}")
            yield f"data: {json.dumps({'content': error_message, 'is_streaming': False, 'error': str(e), 'model': model})}\n\n"
            yield f"data: [DONE]\n\n"
    
    # 비동기 이터레이터 반환
    return stream_generator()

async def perform_web_search(request: WebSearchRequest) -> WebSearchResponse:
    """
    OpenAI API의 웹 검색 도구를 사용하여 웹 검색을 수행합니다.
    
    Args:
        request: WebSearchRequest 모델의 요청 데이터
    
    Returns:
        WebSearchResponse: 웹 검색 결과
    """
    try:
        # 모델 설정
        model = request.model or "gpt-4.1"  # 웹 검색은 gpt-4.1에서 지원됨
        
        # 모델 ID 매핑 (필요한 경우)
        model_mapping = {
            "gpt-4.1": "gpt-4.1",
            "gpt-4o": "gpt-4o",
            "o4-mini": "gpt-4o-mini",
            "o3": "gpt-3.5-turbo"
        }
        
        # 모델 ID 변환
        api_model = model_mapping.get(model, model)
        
        # web_search 도구가 지원되지 않는 모델인 경우 gpt-4.1로 변경
        if api_model in ["gpt-4o-mini", "gpt-3.5-turbo"]:
            print(f"Warning: Model {api_model} does not support web search. Using gpt-4.1 instead.")
            api_model = "gpt-4.1"
            model = "gpt-4.1"
        
        # OpenAI 클라이언트 초기화
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        # 웹 검색 도구 설정
        web_search_tool = {
            "type": "web_search_preview",
            "search_context_size": request.search_context_size
        }
        
        # 사용자 위치 정보가 있으면 추가
        if request.user_location:
            web_search_tool["user_location"] = {
                "type": "approximate",
                **request.user_location
            }
        else:
            # 기본 한국 위치 정보 추가
            web_search_tool["user_location"] = {
                "type": "approximate",
                "country": "KR",
                "city": "Seoul",
                "region": "Seoul",
                "timezone": "Asia/Seoul"
            }
        
        print(f"Debug - Performing web search with query: {request.query}, model: {api_model}")
        
        # OpenAI API 호출
        response = client.responses.create(
            model=api_model,
            tools=[web_search_tool],
            input=request.query,
            temperature=request.temperature,
            max_output_tokens=request.max_tokens,
            tool_choice={"type": "web_search_preview"}  # 웹 검색 도구를 강제로 사용하도록 설정
        )
        
        # 응답 파싱
        content = ""
        citations = []
        
        # 웹 검색 호출 ID 확인 (디버깅용)
        web_search_id = None
        for output in response.output:
            if output.type == "web_search_call":
                web_search_id = output.id
                print(f"Debug - Web search call ID: {web_search_id}")
                break
        
        if hasattr(response, 'output_text'):
            content = response.output_text
        else:
            # 각 출력 항목 처리
            for output in response.output:
                # 웹 검색 결과인 경우
                if output.type == "message" and hasattr(output, 'content'):
                    for item in output.content:
                        if hasattr(item, 'text'):
                            content += item.text
                        
                        # 인용 정보 추출
                        if hasattr(item, 'annotations'):
                            for annotation in item.annotations:
                                if annotation.type == "url_citation":
                                    citations.append({
                                        "url": annotation.url,
                                        "title": annotation.title if hasattr(annotation, 'title') else "",
                                        "start_index": annotation.start_index,
                                        "end_index": annotation.end_index
                                    })
        
        # 사용량 정보
        usage = {}
        if hasattr(response, 'usage'):
            usage = {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.total_tokens
            }
        
        return WebSearchResponse(
            response=content,
            model=model,
            usage=usage,
            citations=citations
        )
    
    except Exception as e:
        # 에러 처리
        error_message = f"Error performing web search: {str(e)}"
        print(f"Web search error: {str(e)}")
        return WebSearchResponse(
            response=error_message,
            model=model,
            usage={"error": str(e)}
        ) 