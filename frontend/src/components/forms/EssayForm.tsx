"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { essayApi } from "@/lib/api";
import type { EssayResponse } from "@/lib/types";

interface EssayFormProps {
  onGenerated?: (essay: EssayResponse) => void;
}

export function EssayForm({ onGenerated }: EssayFormProps) {
  const [topic, setTopic] = useState("");
  const [tone, setTone] = useState("academic");
  const [length, setLength] = useState("medium");
  const [includeOutline, setIncludeOutline] = useState(false);

  const mutation = useMutation({
    mutationFn: () =>
      essayApi.generate({ topic, tone, length, include_outline: includeOutline }),
    onSuccess: (res) => {
      if (onGenerated) onGenerated(res.data);
    },
  });

  return (
    <div className="flex flex-col gap-4">
      <div>
        <label className="text-xs text-gray-400 mb-1 block">Topic</label>
        <input
          type="text"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="e.g. The impact of AI on education"
          className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-gray-500"
        />
      </div>

      <div className="flex gap-4">
        <div className="flex-1">
          <label className="text-xs text-gray-400 mb-1 block">Tone</label>
          <select
            value={tone}
            onChange={(e) => setTone(e.target.value)}
            className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white focus:outline-none"
          >
            <option value="academic">Academic</option>
            <option value="casual">Casual</option>
            <option value="professional">Professional</option>
          </select>
        </div>
        <div className="flex-1">
          <label className="text-xs text-gray-400 mb-1 block">Length</label>
          <select
            value={length}
            onChange={(e) => setLength(e.target.value)}
            className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white focus:outline-none"
          >
            <option value="short">Short</option>
            <option value="medium">Medium</option>
            <option value="long">Long</option>
          </select>
        </div>
      </div>

      <label className="flex items-center gap-2 text-sm text-gray-400 cursor-pointer">
        <input
          type="checkbox"
          checked={includeOutline}
          onChange={(e) => setIncludeOutline(e.target.checked)}
          className="accent-white"
        />
        Include outline
      </label>

      <button
        onClick={() => mutation.mutate()}
        disabled={!topic.trim() || mutation.isPending}
        className="bg-white text-black px-4 py-2 rounded text-sm font-medium hover:bg-gray-200 disabled:opacity-40 disabled:cursor-not-allowed"
      >
        {mutation.isPending ? "Generating..." : "Generate Essay"}
      </button>

      {mutation.isError && (
        <p className="text-red-400 text-sm">Something went wrong. Try again.</p>
      )}
    </div>
  );
}