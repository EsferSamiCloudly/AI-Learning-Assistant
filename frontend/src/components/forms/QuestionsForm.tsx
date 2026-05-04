"use client";

import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { questionsApi, documentApi } from "@/lib/api";
import type { QuestionsResponse } from "@/lib/types";

interface QuestionsFormProps {
  onGenerated?: (qs: QuestionsResponse) => void;
}

export function QuestionsForm({ onGenerated }: QuestionsFormProps) {
  const [sourceType, setSourceType] = useState<"text" | "document">("text");
  const [content, setContent] = useState("");
  const [documentId, setDocumentId] = useState("");
  const [difficulty, setDifficulty] = useState("medium");
  const [count, setCount] = useState(5);
  const [domain, setDomain] = useState("");

  const { data: documents } = useQuery({
    queryKey: ["documents"],
    queryFn: () => documentApi.getDocuments().then((r) => r.data),
  });

  const readyDocs = documents?.filter((d) => d.embed_status === "done") ?? [];

  const mutation = useMutation({
    mutationFn: () =>
      questionsApi.generate({
        content: sourceType === "text" ? content : undefined,
        document_id: sourceType === "document" ? documentId : undefined,
        difficulty,
        count,
        domain: sourceType === "text" ? domain || undefined : undefined,
      }),
    onSuccess: (res) => {
      if (onGenerated) onGenerated(res.data);
    },
  });

  return (
    <div className="flex flex-col gap-4">
      <div className="flex gap-2">
        {["text", "document"].map((t) => (
          <button
            key={t}
            onClick={() => setSourceType(t as "text" | "document")}
            className={`px-3 py-1 rounded text-sm ${
              sourceType === t
                ? "bg-white text-black"
                : "bg-gray-900 text-gray-400 border border-gray-700"
            }`}
          >
            {t === "text" ? "Paste Text" : "From Document"}
          </button>
        ))}
      </div>

      {sourceType === "text" ? (
        <div>
          <label className="text-xs text-gray-400 mb-1 block">Content</label>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Paste your study material here..."
            rows={6}
            className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-gray-500 resize-none"
          />
        </div>
      ) : (
        <div>
          <label className="text-xs text-gray-400 mb-1 block">Select Document</label>
          <select
            value={documentId}
            onChange={(e) => setDocumentId(e.target.value)}
            className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white focus:outline-none"
          >
            <option value="">Select a document...</option>
            {readyDocs.map((d) => (
              <option key={d.id} value={d.id}>{d.filename}</option>
            ))}
          </select>
          {readyDocs.length === 0 && (
            <p className="text-xs text-gray-600 mt-1">No ready documents. Upload a PDF in Chat first.</p>
          )}
        </div>
      )}

      <div className="flex gap-4">
        <div className="flex-1">
          <label className="text-xs text-gray-400 mb-1 block">Difficulty</label>
          <select
            value={difficulty}
            onChange={(e) => setDifficulty(e.target.value)}
            className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white focus:outline-none"
          >
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
          </select>
        </div>
        <div className="flex-1">
          <label className="text-xs text-gray-400 mb-1 block">Count</label>
          <input
            type="number"
            value={count}
            onChange={(e) => setCount(Number(e.target.value))}
            min={1}
            max={20}
            className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white focus:outline-none"
          />
        </div>
      </div>

      {sourceType === "text" && (
        <div>
          <label className="text-xs text-gray-400 mb-1 block">Domain (optional)</label>
          <input
            type="text"
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            placeholder="e.g. Biology, History..."
            className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-gray-500"
          />
        </div>
      )}

      <button
        onClick={() => mutation.mutate()}
        disabled={
          mutation.isPending ||
          (sourceType === "text" && !content.trim()) ||
          (sourceType === "document" && !documentId)
        }
        className="bg-white text-black px-4 py-2 rounded text-sm font-medium hover:bg-gray-200 disabled:opacity-40 disabled:cursor-not-allowed"
      >
        {mutation.isPending ? "Generating..." : "Generate Questions"}
      </button>

      {mutation.isError && (
        <p className="text-red-400 text-sm">Something went wrong. Try again.</p>
      )}
    </div>
  );
}