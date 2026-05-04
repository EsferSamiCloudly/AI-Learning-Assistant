import { useAuthStore } from "@/store/authStore";

export function getAccessToken(): string | null {
  return useAuthStore.getState().accessToken;
}

export function setAccessToken(token: string): void {
  useAuthStore.getState().setAccessToken(token);
}

export function clearAuth(): void {
  useAuthStore.getState().clearAuth();
}

export function isAuthenticated(): boolean {
  return useAuthStore.getState().accessToken !== null;
}