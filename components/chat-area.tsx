"use client";

import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Send, User, ChevronDown } from "lucide-react";
import { ChatMessage } from "@/components/chat-message";
import { useMobile } from "@/hooks/use-mobile";
import { ThemeToggle } from "@/components/theme-toggle";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface ChatAreaProps {
  onMenuClick: () => void;
  sidebarOpen: boolean;
  sidebarCollapsed?: boolean;
}

// 모델 타입 정의
type Model = {
  id: string;
  name: string;
};

// Message 타입 정의
interface Message {
  id: number;
  role: "user" | "system";
  content: string;
}

// API URL 설정
const API_URL = "http://localhost:8000/api";

export function ChatArea({
  onMenuClick,
  sidebarOpen,
  sidebarCollapsed,
}: ChatAreaProps) {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    { id: 1, role: "system", content: "How can I help you today?" },
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const isMobile = useMobile();
  const [streamingMessage, setStreamingMessage] = useState<string>("");
  const [isStreaming, setIsStreaming] = useState(false);

  // 메시지 컨테이너 참조 생성
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  // 스크롤을 맨 아래로 이동시키는 함수
  const scrollToBottom = (behavior: ScrollBehavior = "smooth") => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior, block: "start" });
    }
  };

  // 메시지가 추가되거나 업데이트될 때마다 스크롤 조정
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 스트리밍 상태가 변경될 때 스크롤 조정
  useEffect(() => {
    if (isStreaming) {
      const interval = setInterval(() => {
        if (chatContainerRef.current) {
          const isNearBottom =
            chatContainerRef.current.scrollHeight -
              chatContainerRef.current.scrollTop -
              chatContainerRef.current.clientHeight <
            100;

          if (isNearBottom) {
            scrollToBottom("auto");
          }
        }
      }, 100);

      return () => clearInterval(interval);
    }
  }, [isStreaming]);

  // 사용 가능한 모델 목록
  const [models, setModels] = useState<Model[]>([
    { id: "gpt-4.1", name: "GPT4.1" },
    { id: "gpt-4-1106-preview", name: "GPT-4 Turbo" },
    { id: "gpt-4", name: "GPT-4" },
  ]);

  // 선택된 모델 상태
  const [selectedModel, setSelectedModel] = useState<Model>({
    id: "gpt-4.1",
    name: "GPT4.1",
  });

  // 모델 목록 가져오기
  useEffect(() => {
    const fetchModels = async () => {
      try {
        const response = await fetch(`${API_URL}/models`);
        if (!response.ok) {
          throw new Error("모델 목록을 가져오는데 실패했습니다.");
        }
        const data = await response.json();
        setModels(data.models);
        // 기본 모델 설정
        if (data.models.length > 0) {
          setSelectedModel(data.models[0]);
        }
      } catch (err) {
        console.error("모델 목록 에러:", err);
        // 기본 모델 목록 유지
      }
    };

    fetchModels();
  }, []);

  // 메시지 전송
  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: messages.length + 1,
      role: "user",
      content: input,
    };

    // 메시지 목록에 사용자 메시지 추가
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);
    setError(null);
    setStreamingMessage("");

    // 사용자 메시지가 추가된 후 스크롤 조정 (즉시)
    setTimeout(() => scrollToBottom("auto"), 50);

    const newMessageId = messages.length + 2;

    try {
      // API 호출 데이터 준비
      const requestData = {
        messages: [
          ...messages.map((msg) => ({ role: msg.role, content: msg.content })),
          { role: userMessage.role, content: userMessage.content },
        ],
        model: selectedModel.id,
        temperature: 0.7,
        max_tokens: 1000,
        stream: true,
      };

      // 빈 메시지로 시스템 응답 추가
      const initialMessage: Message = {
        id: newMessageId,
        role: "system",
        content: "",
      };
      setMessages((prev) => [...prev, initialMessage]);
      setIsStreaming(true);

      // POST 요청으로 스트리밍 데이터 가져오기
      const response = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        throw new Error("API 요청에 실패했습니다.");
      }

      if (!response.body) {
        throw new Error("응답 본문이 없습니다.");
      }

      // 응답 스트림 처리
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullContent = "";
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        // 텍스트 디코딩
        const chunk = decoder.decode(value, { stream: true });
        buffer += chunk;

        // 이벤트 스트림 형식 처리 (data: {...}\n\n)
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.trim() === "") continue;
          if (line.includes("[DONE]")) {
            setIsStreaming(false);
            continue;
          }

          try {
            // "data: " 접두사 제거
            const jsonStr = line.replace(/^data: /, "").trim();
            if (!jsonStr) continue;

            const data = JSON.parse(jsonStr);

            if (data.content) {
              fullContent += data.content;

              // 실시간으로 메시지 업데이트
              setMessages((currentMessages) =>
                currentMessages.map((msg) =>
                  msg.id === newMessageId
                    ? { ...msg, content: fullContent }
                    : msg
                )
              );
            }

            if (data.is_streaming === false) {
              setIsStreaming(false);
            }
          } catch (e) {
            console.error("JSON 파싱 오류:", e, line);
          }
        }
      }
    } catch (err) {
      console.error("API 에러:", err);
      setError(
        err instanceof Error ? err.message : "알 수 없는 오류가 발생했습니다."
      );
      setIsStreaming(false);
    } finally {
      setIsLoading(false);
    }
  };

  // 엔터 키로 메시지 전송
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="h-full flex flex-col bg-white dark:bg-background">
      {/* Header */}
      <header className="border-b border-gray-200 dark:border-border p-3 flex items-center justify-between bg-white dark:bg-background">
        <div className="flex items-center">
          {/* 모델 선택 드롭다운 */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="outline"
                className="flex items-center gap-2 h-9 border-orange-200 hover:border-orange-300 dark:border-orange-800 dark:hover:border-orange-700"
              >
                <span>{selectedModel.name}</span>
                <ChevronDown size={16} />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start">
              {models.map((model) => (
                <DropdownMenuItem
                  key={model.id}
                  onClick={() => setSelectedModel(model)}
                  className={
                    selectedModel.id === model.id
                      ? "bg-orange-100 dark:bg-orange-900/50 font-medium text-orange-700 dark:text-orange-300"
                      : ""
                  }
                >
                  {model.name}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>

          <h2 className="font-semibold ml-3">Current Chat</h2>
        </div>

        <div className="flex items-center gap-2">
          <ThemeToggle />
          <Button
            variant="ghost"
            size="icon"
            className="h-10 w-10 rounded-full bg-gray-100 hover:bg-gray-200 dark:bg-secondary dark:hover:bg-secondary/80"
          >
            <User size={20} />
            <span className="sr-only">Login</span>
          </Button>
        </div>
      </header>

      {/* Chat messages */}
      <div
        ref={chatContainerRef}
        className="flex-1 overflow-auto p-4 space-y-6 bg-white dark:bg-background"
      >
        {messages.map((message) => (
          <ChatMessage
            key={message.id}
            message={message}
            isStreaming={isStreaming && message.id === messages.length}
          />
        ))}
        {isLoading && !isStreaming && (
          <div className="text-center py-2">
            <span className="text-sm text-gray-500 dark:text-gray-400">
              AI가 응답 중입니다...
            </span>
          </div>
        )}
        {error && (
          <div className="text-center py-2">
            <span className="text-sm text-red-500">{error}</span>
          </div>
        )}
        {/* 스크롤 위치를 조정하기 위한 참조 요소 */}
        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="border-t border-gray-200 dark:border-border p-4 bg-white dark:bg-background">
        <div className="flex gap-2 max-w-3xl mx-auto">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your message..."
            className="flex-1 border-gray-200 dark:bg-secondary dark:border-secondary focus-visible:ring-orange-500 focus-visible:border-orange-500"
            disabled={isLoading}
          />
          <Button
            type="submit"
            size="icon"
            onClick={sendMessage}
            disabled={isLoading}
            className="bg-orange-500 hover:bg-orange-600 text-white"
          >
            <Send size={18} />
            <span className="sr-only">Send</span>
          </Button>
        </div>
        <p className="text-xs text-center text-gray-500 dark:text-muted-foreground mt-2">
          AI may produce inaccurate information about people, places, or facts.
        </p>
      </div>
    </div>
  );
}
