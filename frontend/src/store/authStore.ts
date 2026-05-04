import { create } from "zustand";
import type { User } from "@/lib/types";

interface AuthStore {
  accessToken: string | null;
  user: User | null;
  setAccessToken: (token: string) => void;
  setUser: (user: User) => void;
  clearAuth: () => void;
  isAuthenticated: () => boolean;
}

export const useAuthStore = create<AuthStore>((set, get) => ({
  accessToken: null,
  user: null,

  setAccessToken: (token) => set({ accessToken: token }),

  setUser: (user) => set({ user }),

  clearAuth: () => set({ accessToken: null, user: null }),

  isAuthenticated: () => get().accessToken !== null,
}));