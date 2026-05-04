"use client";

import { useQuery } from "@tanstack/react-query";
import { chatApi } from "@/lib/api";

export function useChatHistory() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["sessions"],
    queryFn: () => chatApi.getSessions().then((r) => r.data),
    refetchOnWindowFocus: false,
  });

  return {
    sessions: data ?? [],
    isLoading,
    error,
  };
}