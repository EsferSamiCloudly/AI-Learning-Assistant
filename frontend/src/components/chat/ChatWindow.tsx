"use client";

import { useEffect, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { chatApi } from "@/lib/api";
import { MessageBubble } from "./MessageBubble";
import { ChatInput } from "./ChatInput";
import { useChat } from "@/hooks/useChat";
import { FileText } from "lucide-react";

interface ChatWindowProps {
  sessionId: string;
}

export function ChatWindow({ sessionId }: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const { sendMessage } = useChat(sessionId);

  const { data, isLoading } = useQuery({
    queryKey: ["session", sessionId],
    queryFn: () => chatApi.getSession(sessionId).then((r) => r.data),
  });

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [data?.messages]);

  const handleSend = (content: string) => {
    sendMessage.mutate(content);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500 text-sm">
        Loading...
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Chat header — shows mode and document name */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-800 bg-black">
        {data?.session.mode === "pdf" ? (
          <>
            <FileText size={14} className="text-gray-400" />
            <span className="text-xs text-gray-400">
              Chatting with document
            </span>
            <span className="text-xs text-white font-medium bg-gray-800 px-2 py-0.5 rounded">
              PDF loaded ✓
            </span>
          </>
        ) : (
          <span className="text-xs text-gray-500">General Knowledge Mode</span>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4">
        {data?.messages.length === 0 && (
          <p className="text-center text-gray-600 text-sm mt-8">
            {data?.session.mode === "pdf"
              ? "Ask anything about your document."
              : "Ask me anything."}
          </p>
        )}
        {data?.messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        {sendMessage.isPending && (
          <div className="flex justify-start mb-4">
            <div className="bg-gray-900 border border-gray-800 rounded px-4 py-3 text-sm text-gray-500">
              Thinking...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="px-4 pb-4">
        <ChatInput
          onSend={handleSend}
          disabled={sendMessage.isPending}
        />
      </div>
    </div>
  );
}