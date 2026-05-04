"use client";

import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { evaluateApi, documentApi } from "@/lib/api";
import type { EvaluateResponse } from "@/lib/types";

interface EvaluateFormProps {
  onEvaluated?: (result: EvaluateResponse) => void;
}

interface QAPair {
  question: string;
  student_answer: string;
  reference_answer: string;
}

export function EvaluateForm({ onEvaluated }: EvaluateFormProps) {
  const [mode, setMode] = useState<"single" | "exam">("single");
  const [pairs, setPairs] = useState<QAPair[]>([
    { question: "", student_answer: "", reference_answer: "" },
  ]);
  const [referenceType, setReferenceType] = useState<"none" | "text" | "document">("none");
  const [referenceContent, setReferenceContent] = useState("");
  const [documentId, setDocumentId] = useState("");

  const { data: documents } = useQuery({
    queryKey: ["documents"],
    queryFn: () => documentApi.getDocuments().then((r) => r.data),
  });

  const readyDocs = documents?.filter((d) => d.embed_status === "done") ?? [];

  const mutation = useMutation({
    mutationFn: () =>
      evaluateApi.evaluate({
        pairs,
        reference_content: referenceType === "text" ? referenceContent : undefined,
        document_id: referenceType === "document" ? documentId : undefined,
        mode,
      }),
    onSuccess: (res) => {
      if (onEvaluated) onEvaluated(res.data);
    },
  });

  const addPair = () =>
    setPairs([...pairs, { question: "", student_answer: "", reference_answer: "" }]);

  const removePair = (i: number) =>
    setPairs(pairs.filter((_, idx) => idx !== i));

  const updatePair = (i: number, field: keyof QAPair, value: string) => {
    const updated = [...pairs];
    updated[i][field] = value;
    setPairs(updated);
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex gap-2">
        {["single", "exam"].map((m) => (
          <button
            key={m}
            onClick={() => {
              setMode(m as "single" | "exam");
              setPairs([{ question: "", student_answer: "", reference_answer: "" }]);
            }}
            className={`px-3 py-1 rounded text-sm ${
              mode === m
                ? "bg-white text-black"
                : "bg-gray-900 text-gray-400 border border-gray-700"
            }`}
          >
            {m === "single" ? "Single" : "Exam Mode"}
          </button>
        ))}
      </div>

      {pairs.map((pair, i) => (
        <div key={i} className="border border-gray-800 rounded p-3 flex flex-col gap-2">
          {mode === "exam" && (
            <div className="flex justify-between items-center">
              <span className="text-xs text-gray-500">Question {i + 1}</span>
              {pairs.length > 1 && (
                <button onClick={() => removePair(i)} className="text-xs text-red-400 hover:text-red-300">
                  Remove
                </button>
              )}
            </div>
          )}
          <input
            type="text"
            value={pair.question}
            onChange={(e) => updatePair(i, "question", e.target.value)}
            placeholder="Question"
            className="w-full bg-gray-950 border border-gray-700 rounded px-3 py-2 text-sm text-white focus:outline-none"
          />
          <textarea
            value={pair.student_answer}
            onChange={(e) => updatePair(i, "student_answer", e.target.value)}
            placeholder="Student answer"
            rows={2}
            className="w-full bg-gray-950 border border-gray-700 rounded px-3 py-2 text-sm text-white focus:outline-none resize-none"
          />
          <input
            type="text"
            value={pair.reference_answer}
            onChange={(e) => updatePair(i, "reference_answer", e.target.value)}
            placeholder="Reference answer (optional)"
            className="w-full bg-gray-950 border border-gray-700 rounded px-3 py-2 text-sm text-white focus:outline-none"
          />
        </div>
      ))}

      {mode === "exam" && (
        <button
          onClick={addPair}
          className="text-sm text-gray-500 hover:text-white border border-gray-800 rounded px-3 py-2"
        >
          + Add Question
        </button>
      )}

      <div className="border border-gray-800 rounded p-3 flex flex-col gap-3">
        <p className="text-xs text-gray-400">Reference Source (optional)</p>
        <div className="flex gap-2">
          {["none", "text", "document"].map((t) => (
            <button
              key={t}
              onClick={() => setReferenceType(t as "none" | "text" | "document")}
              className={`px-3 py-1 rounded text-xs ${
                referenceType === t
                  ? "bg-white text-black"
                  : "bg-gray-900 text-gray-400 border border-gray-700"
              }`}
            >
              {t === "none" ? "None" : t === "text" ? "Paste Text" : "From Document"}
            </button>
          ))}
        </div>
        {referenceType === "text" && (
          <textarea
            value={referenceContent}
            onChange={(e) => setReferenceContent(e.target.value)}
            placeholder="Paste reference material here..."
            rows={4}
            className="w-full bg-gray-950 border border-gray-700 rounded px-3 py-2 text-sm text-white focus:outline-none resize-none"
          />
        )}
        {referenceType === "document" && (
          <select
            value={documentId}
            onChange={(e) => setDocumentId(e.target.value)}
            className="w-full bg-gray-950 border border-gray-700 rounded px-3 py-2 text-sm text-white focus:outline-none"
          >
            <option value="">Select a document...</option>
            {readyDocs.map((d) => (
              <option key={d.id} value={d.id}>{d.filename}</option>
            ))}
          </select>
        )}
      </div>

      <button
        onClick={() => mutation.mutate()}
        disabled={mutation.isPending || !pairs[0].question.trim()}
        className="bg-white text-black px-4 py-2 rounded text-sm font-medium hover:bg-gray-200 disabled:opacity-40 disabled:cursor-not-allowed"
      >
        {mutation.isPending ? "Evaluating..." : "Evaluate"}
      </button>

      {mutation.isError && (
        <p className="text-red-400 text-sm">Something went wrong. Try again.</p>
      )}
    </div>
  );
}