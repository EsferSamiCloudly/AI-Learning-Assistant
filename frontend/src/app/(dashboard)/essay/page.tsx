"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { essayApi } from "@/lib/api";
import { EssayForm } from "@/components/forms/EssayForm";
import type { EssayResponse } from "@/lib/types";
import ReactMarkdown from "react-markdown";
import { Trash2 } from "lucide-react";

export default function EssayPage() {
  const queryClient = useQueryClient();
  const [selected, setSelected] = useState<EssayResponse | null>(null);

  const { data: history } = useQuery({
    queryKey: ["essay-history"],
    queryFn: () => essayApi.getHistory().then((r) => r.data),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => essayApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["essay-history"] });
      setSelected(null);
    },
  });

  return (
    <div className="flex gap-6 h-full">
      {/* History sidebar */}
      <div className="w-52 flex-shrink-0 flex flex-col gap-1">
        <p className="text-xs text-gray-500 uppercase tracking-widest mb-2">History</p>
        {!history?.length && (
          <p className="text-xs text-gray-600">No essays yet</p>
        )}
        {history?.map((e) => (
          <div
            key={e.id}
            className={`group flex items-center justify-between px-2 py-2 rounded text-sm cursor-pointer ${
              selected?.id === e.id
                ? "bg-gray-800 text-white"
                : "text-gray-400 hover:bg-gray-900 hover:text-white"
            }`}
            onClick={() => setSelected(e)}
          >
            <span className="truncate">{e.topic}</span>
            <button
              onClick={(ev) => { ev.stopPropagation(); deleteMutation.mutate(e.id); }}
              className="opacity-0 group-hover:opacity-100 text-gray-600 hover:text-red-400 ml-1"
            >
              <Trash2 size={12} />
            </button>
          </div>
        ))}
      </div>

      {/* Main content */}
      <div className="flex-1 overflow-y-auto">
        {selected ? (
          <div className="max-w-2xl">
            <div className="flex items-center justify-between mb-4">
              <h1 className="text-white text-lg font-medium">{selected.topic}</h1>
              <button
                onClick={() => setSelected(null)}
                className="text-xs text-gray-500 hover:text-white"
              >
                ← New Essay
              </button>
            </div>
            <div className="border border-gray-800 rounded p-4 bg-gray-900 text-sm text-gray-200 prose prose-invert max-w-none">
              <ReactMarkdown>{selected.content}</ReactMarkdown>
            </div>
          </div>
        ) : (
          <div className="max-w-2xl">
            <h1 className="text-white text-lg font-medium mb-6">Essay Writer</h1>
            <EssayForm onGenerated={(essay) => {
              setSelected(essay);
              queryClient.invalidateQueries({ queryKey: ["essay-history"] });
            }} />
          </div>
        )}
      </div>
    </div>
  );
}