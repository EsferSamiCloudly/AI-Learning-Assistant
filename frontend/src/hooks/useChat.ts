"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { chatApi } from "@/lib/api";
import { useChatStore } from "@/store/chatStore";

export function useChat(sessionId: string) {
  const queryClient = useQueryClient();
  const { setActiveSession } = useChatStore();

  const sendMessage = useMutation({
    mutationFn: (content: string) => chatApi.sendMessage(sessionId, content),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["session", sessionId] });
      queryClient.invalidateQueries({ queryKey: ["sessions"] });
    },
  });

  return { sendMessage };
}