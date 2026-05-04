"use client";

import { useAuth } from "@/hooks/useAuth";
import { LogOut } from "lucide-react";

export function Navbar() {
  const { user, logout } = useAuth();

  return (
    <div className="h-12 border-b border-gray-800 flex items-center justify-between px-4">
      <span className="text-sm font-medium text-white">
        AI Learning Assistant
      </span>
      <div className="flex items-center gap-3">
        {user && (
          <span className="text-xs text-gray-500">
            {user.full_name ?? user.email}
          </span>
        )}
        <button
          onClick={logout}
          className="text-gray-500 hover:text-white transition-colors"
          title="Logout"
        >
          <LogOut size={16} />
        </button>
      </div>
    </div>
  );
}