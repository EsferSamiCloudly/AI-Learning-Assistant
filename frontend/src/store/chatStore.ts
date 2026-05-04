import { create } from "zustand";

interface ChatStore {
  activeSessionId: string | null;
  streamingMessage: string;
  setActiveSession: (id: string | null) => void;
  appendStreamChunk: (chunk: string) => void;
  clearStream: () => void;
}

export const useChatStore = create<ChatStore>((set) => ({
  activeSessionId: null,
  streamingMessage: "",

  setActiveSession: (id) => set({ activeSessionId: id }),

  appendStreamChunk: (chunk) =>
    set((state) => ({ streamingMessage: state.streamingMessage + chunk })),

  clearStream: () => set({ streamingMessage: "" }),
}));