import { Avatar } from "@/components/ui/avatar";
import { User, Bot } from "lucide-react";

interface Message {
  id: number;
  role: "user" | "system";
  content: string;
}

interface ChatMessageProps {
  message: Message;
  isStreaming?: boolean;
}

export function ChatMessage({
  message,
  isStreaming = false,
}: ChatMessageProps) {
  const isUser = message.role === "user";

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
      <div className={`flex-1 ${isUser ? "text-right" : ""}`}>
        <div className="text-gray-700 dark:text-foreground whitespace-pre-line">
          {message.content}
          {isStreaming && <span className="animate-pulse">▌</span>}
        </div>
      </div>
    </div>
  );
}
