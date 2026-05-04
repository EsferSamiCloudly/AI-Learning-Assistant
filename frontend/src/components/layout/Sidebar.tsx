"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  MessageSquare,
  FileText,
  AlignLeft,
  HelpCircle,
  CheckSquare,
  PlusCircle,
  User,
} from "lucide-react";
import { ChatHistorySidebar } from "@/components/chat/ChatHistorySidebar";

const navItems = [
  { href: "/chat", label: "Chat", icon: MessageSquare },
  { href: "/essay", label: "Essay Writer", icon: FileText },
  { href: "/summarize", label: "Summarize", icon: AlignLeft },
  { href: "/questions", label: "Questions", icon: HelpCircle },
  { href: "/evaluate", label: "Evaluate", icon: CheckSquare },
  { href: "/profile", label: "Profile", icon: User },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="w-56 bg-black border-r border-gray-800 flex flex-col h-full">
      {/* Nav links */}
      <div className="p-3 border-b border-gray-800">
        {navItems.map(({ href, label, icon: Icon }) => {
          const isActive = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-2 px-2 py-2 rounded text-sm mb-1 ${
                isActive
                  ? "bg-gray-800 text-white"
                  : "text-gray.500 hover:bg-gray-900 hover:text-white"
              }`}
            >
              <Icon size={15} />
              {label}
            </Link>
          );
        })}
      </div>

      {/* New chat button */}
      <div className="p-3 border-b border-gray-800">
        <Link
          href="/chat"
          className="flex items-center gap-2 px-2 py-2 rounded text-sm text-gray-500 hover:bg-gray-900 hover:text-white w-full"
        >
          <PlusCircle size={15} />
          New Chat
        </Link>
      </div>

      {/* Chat history */}
      <div className="flex-1 overflow-y-auto p-3">
        <ChatHistorySidebar />
      </div>
    </div>
  );
}