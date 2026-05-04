"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { authApi } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";

export default function ProfilePage() {
  const { user } = useAuth();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const mutation = useMutation({
    mutationFn: () =>
      authApi.updatePassword({
        current_password: currentPassword,
        new_password: newPassword,
      }),
    onSuccess: () => {
      setSuccess("Password updated successfully.");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setError("");
    },
    onError: (err: any) => {
      setError(err?.response?.data?.detail ?? "Something went wrong.");
      setSuccess("");
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (newPassword !== confirmPassword) {
      setError("New passwords do not match.");
      return;
    }
    if (newPassword.length < 6) {
      setError("New password must be at least 6 characters.");
      return;
    }
    mutation.mutate();
  };

  return (
    <div className="max-w-md">
      <h1 className="text-white text-lg font-medium mb-6">Profile</h1>

      {/* User info */}
      <div className="border border-gray-800 rounded p-4 bg-gray-950 mb-6">
        <p className="text-xs text-gray-500 mb-1">Full Name</p>
        <p className="text-sm text-white mb-3">{user?.full_name ?? "—"}</p>
        <p className="text-xs text-gray-500 mb-1">Email</p>
        <p className="text-sm text-white">{user?.email}</p>
      </div>

      {/* Password update */}
      <div className="border border-gray-800 rounded p-4 bg-gray-950">
        <h2 className="text-sm text-white font-medium mb-4">Update Password</h2>

        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <div>
            <label className="text-xs text-gray-400 mb-1 block">
              Current Password
            </label>
            <input
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              placeholder="••••••••"
              required
              className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-gray-500"
            />
          </div>

          <div>
            <label className="text-xs text-gray-400 mb-1 block">
              New Password
            </label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="••••••••"
              required
              className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-gray-500"
            />
          </div>

          <div>
            <label className="text-xs text-gray-400 mb-1 block">
              Confirm New Password
            </label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="••••••••"
              required
              className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-gray-500"
            />
          </div>

          {error && <p className="text-red-400 text-xs">{error}</p>}
          {success && <p className="text-green-400 text-xs">{success}</p>}

          <button
            type="submit"
            disabled={mutation.isPending}
            className="bg-white text-black py-2 rounded text-sm font-medium hover:bg-gray-200 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {mutation.isPending ? "Updating..." : "Update Password"}
          </button>
        </form>
      </div>
    </div>
  );
}