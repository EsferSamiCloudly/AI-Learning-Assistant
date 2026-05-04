"use client";

import { use } from "react";
import { ChatWindow } from "@/components/chat/ChatWindow";

export default function SessionPage({
  params,
}: {
  params: Promise<{ sessionId: string }>;
}) {
  const { sessionId } = use(params);
  return (
    <div className="h-full flex flex-col">
      <ChatWindow sessionId={sessionId} />
    </div>
  );
}