"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";
import { api } from "@/lib/api";
import { Instagram, Loader2 } from "lucide-react";

export default function Home() {
  const router = useRouter();
  const { isAuthenticated, accessToken, logout } = useAuthStore();
  const [hasChecked, setHasChecked] = useState(false);

  useEffect(() => {
    const checkAndRedirect = async () => {
      // Wait a tick for zustand to rehydrate from localStorage
      await new Promise(resolve => setTimeout(resolve, 100));

      if (isAuthenticated && accessToken) {
        try {
          // Verify token is still valid
          await api.get("/analytics/sync/status");
          router.push("/dashboard");
          return;
        } catch (err) {
          // Token invalid, clear and redirect to login
          logout();
        }
      }
      setHasChecked(true);
      router.push("/login");
    };

    checkAndRedirect();
  }, [isAuthenticated, accessToken, router, logout]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-zinc-950 via-zinc-900 to-zinc-950">
      <div className="text-center">
        <div className="mx-auto w-20 h-20 bg-gradient-to-br from-pink-500 to-purple-600 rounded-2xl flex items-center justify-center mb-6 pulse-glow">
          <Instagram className="w-10 h-10 text-white" />
        </div>
        <h1 className="text-3xl font-bold mb-2">
          <span className="gradient-text">GramAnalyzer</span>
        </h1>
        <div className="flex items-center justify-center gap-2 text-zinc-400">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span>Loading...</span>
        </div>
      </div>
    </div>
  );
}
