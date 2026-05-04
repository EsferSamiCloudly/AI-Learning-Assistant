import axios, { AxiosInstance } from "axios";
import { useAuthStore } from "@/store/authStore";
import type {
  TokenResponse,
  User,
  ChatSession,
  SessionDetail,
  ChatMessage,
  Document,
  EssayResponse,
  QuestionsResponse,
  EvaluateResponse,
  SummarizeResponse,
  TaskStatus,
} from "@/lib/types";

const api: AxiosInstance = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  withCredentials: true,
});

// Request interceptor — attach access token
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor — refresh token on 401
let isRefreshing = false;

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry && !isRefreshing) {
      original._retry = true;
      isRefreshing = true;
      try {
        const res = await api.post<TokenResponse>("/auth/refresh");
        useAuthStore.getState().setAccessToken(res.data.access_token);
        original.headers.Authorization = `Bearer ${res.data.access_token}`;
        return api(original);
      } catch {
        useAuthStore.getState().clearAuth();
        window.location.href = "/login";
      } finally {
        isRefreshing = false;
      }
    }
    return Promise.reject(error);
  }
);

// ─── Auth ────────────────────────────────────────────────────────────────────
export const authApi = {
  register: (data: { email: string; password: string; full_name?: string }) =>
    api.post<TokenResponse>("/auth/register", data),

  login: (data: { email: string; password: string }) =>
    api.post<TokenResponse>("/auth/login", data),

  refresh: () =>
    api.post<TokenResponse>("/auth/refresh"),

  logout: () =>
    api.post("/auth/logout"),

  getMe: () =>
    api.get<User>("/users/me"),

  updateMe: (data: { full_name?: string }) =>
    api.patch<User>("/users/me", data),

  updatePassword: (data: { current_password: string; new_password: string }) =>
    api.patch("/users/me/password", data),
};

// ─── Chat ────────────────────────────────────────────────────────────────────
export const chatApi = {
  getSessions: () =>
    api.get<ChatSession[]>("/chat/sessions"),

  createSession: (data: { document_id?: string; mode: string }) =>
    api.post<ChatSession>("/chat/sessions", data),

  getSession: (sessionId: string) =>
    api.get<SessionDetail>(`/chat/sessions/${sessionId}`),

  deleteSession: (sessionId: string) =>
    api.delete(`/chat/sessions/${sessionId}`),

  sendMessage: (sessionId: string, content: string) =>
    api.post<ChatMessage>(`/chat/sessions/${sessionId}/message`, { content }),
};

// ─── Documents ───────────────────────────────────────────────────────────────
export const documentApi = {
  upload: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post<Document>("/documents/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  getDocuments: () =>
    api.get<Document[]>("/documents/"),
};

// ─── Essay ───────────────────────────────────────────────────────────────────
export const essayApi = {
  generate: (data: {
    topic: string;
    tone: string;
    length: string;
    include_outline: boolean;
  }) => api.post<EssayResponse>("/essay/generate", data),

  getHistory: () =>
    api.get<EssayResponse[]>("/essay/history"),

  getOne: (id: string) =>
    api.get<EssayResponse>(`/essay/history/${id}`),

  delete: (id: string) =>
    api.delete(`/essay/history/${id}`),
};

// ─── Summarize ───────────────────────────────────────────────────────────────
export const summarizeApi = {
  summarizeText: (data: { content: string; mode: string }) =>
    api.post<SummarizeResponse>("/summarize/text", data),

  summarizeDocument: (data: { document_id: string; mode: string }) =>
    api.post<SummarizeResponse>("/summarize/document", data),

  getHistory: () =>
    api.get<SummarizeResponse[]>("/summarize/history"),

  getOne: (id: string) =>
    api.get<SummarizeResponse>(`/summarize/history/${id}`),

  delete: (id: string) =>
    api.delete(`/summarize/history/${id}`),
};

// ─── Questions ───────────────────────────────────────────────────────────────
export const questionsApi = {
  generate: (data: {
    content?: string;
    document_id?: string;
    difficulty: string;
    count: number;
    domain?: string;
  }) => api.post<QuestionsResponse>("/questions/generate", data),

  getHistory: () =>
    api.get<QuestionsResponse[]>("/questions/history"),

  getOne: (id: string) =>
    api.get<QuestionsResponse>(`/questions/history/${id}`),

  delete: (id: string) =>
    api.delete(`/questions/history/${id}`),
};

// ─── Evaluate ────────────────────────────────────────────────────────────────
export const evaluateApi = {
  evaluate: (data: {
    pairs: Array<{
      question: string;
      student_answer: string;
      reference_answer?: string;
    }>;
    reference_content?: string;
    document_id?: string;
    mode: string;
  }) => api.post<EvaluateResponse>("/evaluate/answers", data),

  getHistory: () =>
    api.get<EvaluateResponse[]>("/evaluate/history"),

  getOne: (id: string) =>
    api.get<EvaluateResponse>(`/evaluate/history/${id}`),

  delete: (id: string) =>
    api.delete(`/evaluate/history/${id}`),
};

// ─── Tasks ───────────────────────────────────────────────────────────────────
export const taskApi = {
  getStatus: (taskId: string) =>
    api.get<TaskStatus>(`/tasks/${taskId}`),
};

export default api;