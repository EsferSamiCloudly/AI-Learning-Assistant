"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { summarizeApi } from "@/lib/api";
import { SummarizeForm } from "@/components/forms/SummarizeForm";
import type { SummarizeResponse } from "@/lib/types";
import { Trash2 } from "lucide-react";

export default function SummarizePage() {
  const queryClient = useQueryClient();
  const [selected, setSelected] = useState<SummarizeResponse | null>(null);

  const { data: history } = useQuery({
    queryKey: ["summarize-history"],
    queryFn: () => summarizeApi.getHistory().then((r) => r.data),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => summarizeApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["summarize-history"] });
      setSelected(null);
    },
  });

  return (
    <div className="flex gap-6 h-full">
      {/* History sidebar */}
      <div className="w-52 flex-shrink-0 flex flex-col gap-1">
        <p className="text-xs text-gray-500 uppercase tracking-widest mb-2">History</p>
        {!history?.length && (
          <p className="text-xs text-gray-600">No summaries yet</p>
        )}
        {history?.map((s, i) => (
          <div
            key={s.id}
            className={`group flex items-center justify-between px-2 py-2 rounded text-sm cursor-pointer ${
              selected?.id === s.id
                ? "bg-gray-800 text-white"
                : "text-gray-400 hover:bg-gray-900 hover:text-white"
            }`}
            onClick={() => setSelected(s)}
          >
            <span className="truncate">Summary {history.length - i}</span>
            <button
              onClick={(ev) => { ev.stopPropagation(); deleteMutation.mutate(s.id); }}
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
              <h1 className="text-white text-lg font-medium">
                Summary
                <span className="ml-2 text-xs text-gray-500 font-normal bg-gray-800 px-2 py-0.5 rounded">
                  {selected.mode}
                </span>
              </h1>
              <button
                onClick={() => setSelected(null)}
                className="text-xs text-gray-500 hover:text-white"
              >
                ← New Summary
              </button>
            </div>
            <div className="border border-gray-800 rounded p-4 bg-gray-900 text-sm text-gray-200 whitespace-pre-wrap">
              {selected.content}
            </div>
          </div>
        ) : (
          <div className="max-w-2xl">
            <h1 className="text-white text-lg font-medium mb-6">Summarize</h1>
            <SummarizeForm onSummarized={(summary) => {
              setSelected(summary);
              queryClient.invalidateQueries({ queryKey: ["summarize-history"] });
            }} />
          </div>
        )}
      </div>
    </div>
  );
}