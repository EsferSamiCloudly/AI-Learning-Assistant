"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useChatHistory } from "@/hooks/useChatHistory";
import { MessageSquare, Trash2 } from "lucide-react";
import { chatApi } from "@/lib/api";
import { useQueryClient } from "@tanstack/react-query";

export function ChatHistorySidebar() {
  const { sessions, isLoading } = useChatHistory();
  const pathname = usePathname();
  const queryClient = useQueryClient();

  const handleDelete = async (e: React.MouseEvent, sessionId: string) => {
    e.preventDefault();
    await chatApi.deleteSession(sessionId);
    queryClient.invalidateQueries({ queryKey: ["sessions"] });
  };

  return (
    <div className="flex flex-col gap-1">
      <p className="text-xs text-gray-500 uppercase tracking-widest mb-2 px-2">
        History
      </p>
      {isLoading && (
        <p className="text-xs text-gray-600 px-2">Loading...</p>
      )}
      {sessions.map((session) => {
        const isActive = pathname === `/chat/${session.id}`;
        return (
          <Link
            key={session.id}
            href={`/chat/${session.id}`}
            className={`flex items-center justify-between px-2 py-2 rounded text-sm group ${
              isActive
                ? "bg-gray-800 text-white"
                : "text-gray-400 hover:bg-gray-900 hover:text-white"
            }`}
          >
            <div className="flex items-center gap-2 truncate">
              <MessageSquare size={14} />
              <span className="truncate">
                {session.title ?? "New Chat"}
              </span>
            </div>
            <button
              onClick={(e) => handleDelete(e, session.id)}
              className="opacity-0 group-hover:opacity-100 text-gray-600 hover:text-red-400"
            >
              <Trash2 size={12} />
            </button>
          </Link>
        );
      })}
      {!isLoading && sessions.length === 0 && (
        <p className="text-xs text-gray-600 px-2">No chats yet</p>
      )}
    </div>
  );
}