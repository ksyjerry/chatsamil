import { Avatar } from "@/components/ui/avatar";
import { User, Bot, Copy, Check } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import rehypeHighlight from "rehype-highlight";
import React, { useState, useRef, useCallback, ReactNode } from "react";

interface Message {
  id: number;
  role: "user" | "system";
  content: string;
  imageUrl?: string;
}

interface ChatMessageProps {
  message: Message;
  isStreaming?: boolean;
  showImage?: boolean;
}

// 커스텀 컴포넌트 인터페이스
interface PreProps {
  children?: ReactNode;
  className?: string;
  [key: string]: any;
}

export function ChatMessage({
  message,
  isStreaming = false,
  showImage = false,
}: ChatMessageProps) {
  const isUser = message.role === "user";
  const [copiedMap, setCopiedMap] = useState<Record<string, boolean>>({});

  // 코드 복사 함수
  const copyToClipboard = useCallback((text: string, id: string) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopiedMap((prev) => ({ ...prev, [id]: true }));
      setTimeout(() => {
        setCopiedMap((prev) => ({ ...prev, [id]: false }));
      }, 2000);
    });
  }, []);

  // 코드 내용을 추출하는 함수
  const extractCodeText = useCallback((node: any): string => {
    if (!node) return "";

    // 문자열인 경우 바로 반환
    if (typeof node === "string") return node;

    // props와 children이 있는 객체인 경우 재귀적으로 처리
    if (typeof node === "object") {
      // props.children이 있는 경우
      if ("props" in node && node.props && node.props.children) {
        const children = node.props.children;

        // children이 배열인 경우
        if (Array.isArray(children)) {
          return children.map(extractCodeText).join("");
        }

        // children이 객체나 문자열인 경우
        return extractCodeText(children);
      }
    }

    return "";
  }, []);

  // pre 요소를 커스텀 컴포넌트로 대체
  const PreBlock = useCallback(
    ({ children, ...props }: PreProps) => {
      const preRef = useRef<HTMLPreElement>(null);
      const codeId = `code-${Math.random().toString(36).substr(2, 9)}`;

      // 코드 텍스트 추출
      const codeText = extractCodeText(children);
      const isCopied = copiedMap[codeId] || false;

      return (
        <div className="code-block-wrapper">
          <button
            className={`code-copy-button ${isCopied ? "copied" : ""}`}
            onClick={() => copyToClipboard(codeText, codeId)}
            aria-label="코드 복사"
            title="코드 복사"
          >
            <span className="flex items-center gap-1">
              {isCopied ? (
                <>
                  <Check size={14} />
                  <span className="text-xs">복사됨</span>
                </>
              ) : (
                <>
                  <Copy size={14} />
                  <span className="text-xs">복사</span>
                </>
              )}
            </span>
          </button>
          <pre ref={preRef} {...props}>
            {children}
          </pre>
        </div>
      );
    },
    [copiedMap, copyToClipboard, extractCodeText]
  );

  return (
    <div className={`flex gap-4 ${isUser ? "flex-row-reverse" : ""}`}>
      <Avatar
        className={`flex items-center justify-center flex-shrink-0 ${
          isUser ? "bg-orange-500" : "bg-gray-700"
        }`}
      >
        {isUser ? (
          <User className="h-5 w-5 text-white" />
        ) : (
          <Bot className="h-5 w-5 text-white" />
        )}
      </Avatar>
      <div
        className={`flex-1 flex items-center ${
          isUser ? "justify-end" : "justify-start"
        }`}
      >
        {isUser ? (
          <div className="text-gray-700 dark:text-foreground whitespace-pre-line text-right">
            {message.imageUrl && showImage && (
              <div
                className={`mb-2 ${isUser ? "ml-auto" : "mr-auto"} max-w-xs`}
              >
                <img
                  src={message.imageUrl}
                  alt="Uploaded image"
                  className="rounded-lg object-contain max-h-64 border border-gray-200 dark:border-gray-700 shadow-sm"
                />
              </div>
            )}
            {message.content}
          </div>
        ) : (
          <div
            className={`text-gray-700 dark:text-foreground prose dark:prose-invert 
            prose-headings:font-semibold
            prose-a:text-orange-500 dark:prose-a:text-orange-400
            prose-a:hover:text-orange-600 dark:prose-a:hover:text-orange-300
            prose-p:my-2
            prose-li:my-0.5
            prose-pre:bg-gray-100 dark:prose-pre:bg-gray-800 prose-pre:border prose-pre:border-gray-200 dark:prose-pre:border-gray-700
            prose-pre:shadow-sm
            max-w-none ${isUser ? "text-right" : "text-left"}`}
          >
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeRaw, rehypeHighlight]}
              components={{
                pre: PreBlock,
              }}
            >
              {message.content}
            </ReactMarkdown>
            {isStreaming && <span className="animate-pulse">▌</span>}
          </div>
        )}
      </div>
    </div>
  );
}
