"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { questionsApi } from "@/lib/api";
import { QuestionsForm } from "@/components/forms/QuestionsForm";
import type { QuestionsResponse } from "@/lib/types";
import { Trash2 } from "lucide-react";

export default function QuestionsPage() {
  const queryClient = useQueryClient();
  const [selected, setSelected] = useState<QuestionsResponse | null>(null);
  const [expanded, setExpanded] = useState<number | null>(null);

  const { data: history } = useQuery({
    queryKey: ["questions-history"],
    queryFn: () => questionsApi.getHistory().then((r) => r.data),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => questionsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["questions-history"] });
      setSelected(null);
    },
  });

  return (
    <div className="flex gap-6 h-full">
      {/* History sidebar */}
      <div className="w-52 flex-shrink-0 flex flex-col gap-1">
        <p className="text-xs text-gray-500 uppercase tracking-widest mb-2">History</p>
        {!history?.length && (
          <p className="text-xs text-gray-600">No question sets yet</p>
        )}
        {history?.map((q, i) => (
          <div
            key={q.id}
            className={`group flex items-center justify-between px-2 py-2 rounded text-sm cursor-pointer ${
              selected?.id === q.id
                ? "bg-gray-800 text-white"
                : "text-gray-400 hover:bg-gray-900 hover:text-white"
            }`}
            onClick={() => { setSelected(q); setExpanded(null); }}
          >
            <span className="truncate">{q.difficulty} · {q.count}Q</span>
            <button
              onClick={(ev) => { ev.stopPropagation(); deleteMutation.mutate(q.id); }}
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
                Questions
                <span className="ml-2 text-xs text-gray-500 font-normal bg-gray-800 px-2 py-0.5 rounded">
                  {selected.difficulty} · {selected.count} questions
                </span>
              </h1>
              <button
                onClick={() => setSelected(null)}
                className="text-xs text-gray-500 hover:text-white"
              >
                ← New Set
              </button>
            </div>
            <div className="flex flex-col gap-2">
              {selected.questions.map((q, i) => (
                <div key={i} className="border border-gray-800 rounded bg-gray-900">
                  <button
                    onClick={() => setExpanded(expanded === i ? null : i)}
                    className="w-full text-left px-4 py-3 text-sm text-white flex justify-between items-center"
                  >
                    <span>{i + 1}. {q.question}</span>
                    <span className="text-gray-600 text-xs">{expanded === i ? "▲" : "▼"}</span>
                  </button>
                  {expanded === i && (
                    <div className="px-4 pb-3 text-sm text-gray-400 border-t border-gray-800 pt-2">
                      <span className="text-xs text-gray-600">Answer: </span>
                      {q.expected_answer}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="max-w-2xl">
            <h1 className="text-white text-lg font-medium mb-6">Question Generator</h1>
            <QuestionsForm onGenerated={(qs) => {
              setSelected(qs);
              queryClient.invalidateQueries({ queryKey: ["questions-history"] });
            }} />
          </div>
        )}
      </div>
    </div>
  );
}