"use client";

import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/authStore";
import { authApi } from "@/lib/api";

export function useAuth() {
  const router = useRouter();
  const { accessToken, user, setAccessToken, setUser, clearAuth, isAuthenticated } =
    useAuthStore();

  const login = async (email: string, password: string) => {
    const res = await authApi.login({ email, password });
    setAccessToken(res.data.access_token);
    const meRes = await authApi.getMe();
    setUser(meRes.data);
    router.push("/chat");
  };

  const register = async (
    email: string,
    password: string,
    full_name?: string
  ) => {
    const res = await authApi.register({ email, password, full_name });
    setAccessToken(res.data.access_token);
    const meRes = await authApi.getMe();
    setUser(meRes.data);
    router.push("/chat");
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } finally {
      clearAuth();
      router.push("/login");
    }
  };

  return {
    user,
    accessToken,
    isAuthenticated: isAuthenticated(),
    login,
    register,
    logout,
  };
}