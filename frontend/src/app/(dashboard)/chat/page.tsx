"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { chatApi, documentApi, taskApi } from "@/lib/api";

export default function ChatPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [mode, setMode] = useState<"general" | "pdf">("general");
  const [selectedDoc, setSelectedDoc] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState("");

  const { data: documents } = useQuery({
    queryKey: ["documents"],
    queryFn: () => documentApi.getDocuments().then((r) => r.data),
  });

  const readyDocs = documents?.filter((d) => d.embed_status === "done") ?? [];

  const createSession = useMutation({
    mutationFn: () =>
      chatApi.createSession({
        mode,
        document_id: mode === "pdf" ? selectedDoc : undefined,
      }),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ["sessions"] });
      router.push(`/chat/${res.data.id}`);
    },
  });

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadStatus("Uploading...");

    try {
      const res = await documentApi.upload(file);
      const taskId = res.data.celery_task_id;
      const docId = res.data.id;

      setUploadStatus("Processing PDF...");

      // Poll task status
      const poll = setInterval(async () => {
        const statusRes = await taskApi.getStatus(taskId);
        if (statusRes.data.status === "SUCCESS") {
          clearInterval(poll);
          setUploadStatus("Ready!");
          setSelectedDoc(docId);
          queryClient.invalidateQueries({ queryKey: ["documents"] });
          setUploading(false);
        } else if (statusRes.data.status === "FAILURE") {
          clearInterval(poll);
          setUploadStatus("Processing failed. Try again.");
          setUploading(false);
        }
      }, 2000);
    } catch {
      setUploadStatus("Upload failed. Try again.");
      setUploading(false);
    }
  };

  return (
    <div className="max-w-lg">
      <h1 className="text-white text-lg font-medium mb-6">New Chat</h1>

      <div className="flex flex-col gap-4">
        <div>
          <label className="text-xs text-gray-400 mb-2 block">Mode</label>
          <div className="flex gap-2">
            {["general", "pdf"].map((m) => (
              <button
                key={m}
                onClick={() => setMode(m as "general" | "pdf")}
                className={`px-4 py-2 rounded text-sm ${
                  mode === m
                    ? "bg-white text-black"
                    : "bg-gray-900 text-gray-400 border border-gray-700"
                }`}
              >
                {m === "general" ? "General Knowledge" : "With PDF"}
              </button>
            ))}
          </div>
        </div>

        {mode === "pdf" && (
          <div className="flex flex-col gap-3">
            <div>
              <label className="text-xs text-gray-400 mb-2 block">
                Upload PDF
              </label>
              <input
                type="file"
                accept=".pdf"
                onChange={handleFileUpload}
                disabled={uploading}
                className="text-sm text-gray-400 file:mr-3 file:py-1 file:px-3 file:rounded file:border-0 file:bg-gray-800 file:text-white hover:file:bg-gray-700 disabled:opacity-50"
              />
              {uploadStatus && (
                <p className="text-xs text-gray-500 mt-1">{uploadStatus}</p>
              )}
            </div>

            {readyDocs.length > 0 && (
              <div>
                <label className="text-xs text-gray-400 mb-1 block">
                  Or select existing document
                </label>
                <select
                  value={selectedDoc}
                  onChange={(e) => setSelectedDoc(e.target.value)}
                  className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white focus:outline-none"
                >
                  <option value="">Select...</option>
                  {readyDocs.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.filename}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>
        )}

        <button
          onClick={() => createSession.mutate()}
          disabled={
            createSession.isPending ||
            (mode === "pdf" && !selectedDoc)
          }
          className="bg-white text-black px-4 py-2 rounded text-sm font-medium hover:bg-gray-200 disabled:opacity-40 disabled:cursor-not-allowed w-fit"
        >
          {createSession.isPending ? "Starting..." : "Start Chat"}
        </button>
      </div>
    </div>
  );
}