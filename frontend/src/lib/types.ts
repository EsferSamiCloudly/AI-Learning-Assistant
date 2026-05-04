// Auth
export interface User {
  id: string;
  email: string;
  full_name: string | null;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

// Chat
export interface ChatSession {
  id: string;
  title: string | null;
  mode: "pdf" | "general";
  document_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface SessionDetail {
  session: ChatSession;
  messages: ChatMessage[];
}

// Document
export interface Document {
  id: string;
  filename: string;
  embed_status: "pending" | "processing" | "done" | "failed";
  celery_task_id: string;
  created_at: string;
}

// Essay
export interface EssayResponse {
  id: string;
  topic: string;
  content: string;
}

// Questions
export interface Question {
  question: string;
  expected_answer: string;
  difficulty: string;
}

export interface QuestionsResponse {
  id: string;
  questions: Question[];
  difficulty: string;
  count: number;
}

// Evaluate
export interface AnswerResult {
  question: string;
  student_answer: string;
  score: number;
  feedback: string;
}

export interface EvaluateResponse {
  id: string;
  mode: string;
  results: AnswerResult[];
  total_score: number;
}

// Summarize
export interface SummarizeResponse {
  id: string;
  content: string;
  mode: string;
}

// Task
export interface TaskStatus {
  task_id: string;
  status: "PENDING" | "STARTED" | "SUCCESS" | "FAILURE";
  result: unknown | null;
}