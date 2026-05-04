"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { evaluateApi } from "@/lib/api";
import { EvaluateForm } from "@/components/forms/EvaluateForm";
import type { EvaluateResponse } from "@/lib/types";
import { Trash2 } from "lucide-react";

export default function EvaluatePage() {
  const queryClient = useQueryClient();
  const [selected, setSelected] = useState<EvaluateResponse | null>(null);

  const { data: history } = useQuery({
    queryKey: ["evaluate-history"],
    queryFn: () => evaluateApi.getHistory().then((r) => r.data),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => evaluateApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["evaluate-history"] });
      setSelected(null);
    },
  });

  return (
    <div className="flex gap-6 h-full">
      {/* History sidebar */}
      <div className="w-52 flex-shrink-0 flex flex-col gap-1">
        <p className="text-xs text-gray-500 uppercase tracking-widest mb-2">History</p>
        {!history?.length && (
          <p className="text-xs text-gray-600">No evaluations yet</p>
        )}
        {history?.map((e, i) => (
          <div
            key={e.id}
            className={`group flex items-center justify-between px-2 py-2 rounded text-sm cursor-pointer ${
              selected?.id === e.id
                ? "bg-gray-800 text-white"
                : "text-gray-400 hover:bg-gray-900 hover:text-white"
            }`}
            onClick={() => setSelected(e)}
          >
            <span className="truncate">{e.mode} · {e.total_score.toFixed(1)}/10</span>
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
              <h1 className="text-white text-lg font-medium">
                Evaluation
                <span className="ml-2 text-xs text-gray-500 font-normal bg-gray-800 px-2 py-0.5 rounded">
                  Total: {selected.total_score.toFixed(1)}/10
                </span>
              </h1>
              <button
                onClick={() => setSelected(null)}
                className="text-xs text-gray-500 hover:text-white"
              >
                ← New Evaluation
              </button>
            </div>
            <div className="flex flex-col gap-3">
              {selected.results.map((r, i) => (
                <div key={i} className="border border-gray-800 rounded p-3 bg-gray-900">
                  <p className="text-sm text-white mb-1">{r.question}</p>
                  <p className="text-xs text-gray-500 mb-2">Your answer: {r.student_answer}</p>
                  <div className="flex items-center justify-between">
                    <p className="text-xs text-gray-400">{r.feedback}</p>
                    <span className={`text-xs font-medium ml-2 ${
                      r.score >= 7 ? "text-green-400" : r.score >= 4 ? "text-yellow-400" : "text-red-400"
                    }`}>
                      {r.score.toFixed(1)}/10
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="max-w-2xl">
            <h1 className="text-white text-lg font-medium mb-6">Answer Evaluation</h1>
            <EvaluateForm onEvaluated={(result) => {
              setSelected(result);
              queryClient.invalidateQueries({ queryKey: ["evaluate-history"] });
            }} />
          </div>
        )}
      </div>
    </div>
  );
}