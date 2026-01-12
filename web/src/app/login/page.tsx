"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { ThemeToggle } from "@/components/ThemeToggle";
import { authApi, AuthResponse, api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { Instagram, Eye, EyeOff, Loader2, Mail, Phone } from "lucide-react";

type LoginStep = "credentials" | "2fa" | "challenge";

export default function LoginPage() {
  const router = useRouter();
  const { setAuth, isAuthenticated, accessToken, logout } = useAuthStore();
  const [checkingAuth, setCheckingAuth] = useState(true);

  // Check if user is already authenticated on mount
  useEffect(() => {
    const verifyExistingSession = async () => {
      if (isAuthenticated && accessToken) {
        try {
          // Verify the token is still valid by making a test API call
          await api.get("/analytics/sync/status");
          // Token is valid, redirect to dashboard
          router.push("/dashboard");
          return;
        } catch (err) {
          // Token is invalid, clear auth state
          logout();
        }
      }
      setCheckingAuth(false);
    };

    verifyExistingSession();
  }, [isAuthenticated, accessToken, router, logout]);

  const [step, setStep] = useState<LoginStep>("credentials");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [verificationCode, setVerificationCode] = useState("");
  const [sessionId, setSessionId] = useState("");
  const [challengeType, setChallengeType] = useState<"sms" | "email">("email");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response = await authApi.login(username, password);
      handleAuthResponse(response);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Login failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleVerification = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      let response: AuthResponse;

      if (step === "2fa") {
        response = await authApi.verify2FA(
          sessionId,
          verificationCode,
          username,
          password
        );
      } else {
        response = await authApi.verifyChallenge(
          sessionId,
          verificationCode,
          challengeType
        );
      }

      handleAuthResponse(response);
    } catch (err: any) {
      setError(
        err.response?.data?.detail || "Verification failed. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleAuthResponse = (response: AuthResponse) => {
    if (response.success && response.access_token && response.user) {
      setAuth(response.user, response.access_token);
      router.push("/dashboard");
    } else if (response.requires_challenge) {
      setSessionId(response.session_id || "");
      if (response.challenge_type) {
        setChallengeType(response.challenge_type);
      }
      setStep(response.message?.includes("Two-factor") ? "2fa" : "challenge");
    }
  };

  // Show loading while checking existing auth
  if (checkingAuth) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-purple-500" />
          <p className="text-muted-foreground">Checking session...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-background relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-500/20 dark:bg-purple-500/10 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-pink-500/20 dark:bg-pink-500/10 rounded-full blur-3xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-linear-to-r from-purple-500/10 to-pink-500/10 rounded-full blur-3xl" />
      </div>

      {/* Theme toggle */}
      <div className="absolute top-4 right-4">
        <ThemeToggle />
      </div>

      <Card className="w-full max-w-md relative z-10 border-border bg-card/80 backdrop-blur-xl">
        <CardHeader className="text-center">
          <div className="mx-auto w-16 h-16 bg-linear-to-br from-purple-500 via-pink-500 to-orange-400 rounded-2xl flex items-center justify-center mb-4 shadow-lg shadow-purple-500/25">
            <Instagram className="w-8 h-8 text-white" />
          </div>
          <CardTitle className="text-2xl font-bold">
            <span className="bg-linear-to-r from-purple-500 via-pink-500 to-orange-400 bg-clip-text text-transparent">
              GramAnalyzer
            </span>
          </CardTitle>
          <CardDescription className="text-muted-foreground">
            {step === "credentials" && "Sign in with your Instagram account"}
            {step === "2fa" && "Enter your two-factor authentication code"}
            {step === "challenge" &&
              `Enter the code sent to your ${challengeType}`}
          </CardDescription>
        </CardHeader>

        <CardContent>
          {step === "credentials" && (
            <form onSubmit={handleLogin} className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">
                  Username
                </label>
                <Input
                  type="text"
                  placeholder="Enter your Instagram username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  autoComplete="username"
                  className="bg-background border-border"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">
                  Password
                </label>
                <div className="relative">
                  <Input
                    type={showPassword ? "text" : "password"}
                    placeholder="Enter your password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    autoComplete="current-password"
                    className="pr-10 bg-background border-border"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {showPassword ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </button>
                </div>
              </div>

              {error && (
                <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-500 dark:text-red-400 text-sm">
                  {error}
                </div>
              )}

              <Button
                type="submit"
                className="w-full bg-linear-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white border-0 shadow-lg shadow-purple-500/25"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Signing in...
                  </>
                ) : (
                  "Sign in"
                )}
              </Button>

              <p className="text-xs text-muted-foreground text-center mt-4">
                Your credentials are sent directly to Instagram.
                <br />
                We never store your password.
              </p>
            </form>
          )}

          {(step === "2fa" || step === "challenge") && (
            <form onSubmit={handleVerification} className="space-y-4">
              <div className="flex justify-center mb-4">
                <div className="p-4 rounded-full bg-muted">
                  {challengeType === "email" ? (
                    <Mail className="h-8 w-8 text-purple-500" />
                  ) : (
                    <Phone className="h-8 w-8 text-purple-500" />
                  )}
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">
                  Verification Code
                </label>
                <Input
                  type="text"
                  placeholder="Enter 6-digit code"
                  value={verificationCode}
                  onChange={(e) =>
                    setVerificationCode(
                      e.target.value.replace(/\D/g, "").slice(0, 6)
                    )
                  }
                  required
                  autoComplete="one-time-code"
                  className="text-center text-2xl tracking-widest bg-background border-border"
                  maxLength={6}
                />
              </div>

              {error && (
                <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-500 dark:text-red-400 text-sm">
                  {error}
                </div>
              )}

              <Button
                type="submit"
                className="w-full bg-linear-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white border-0"
                disabled={loading || verificationCode.length < 6}
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Verifying...
                  </>
                ) : (
                  "Verify"
                )}
              </Button>

              <Button
                type="button"
                variant="ghost"
                className="w-full"
                onClick={() => {
                  setStep("credentials");
                  setVerificationCode("");
                  setError("");
                }}
              >
                Back to login
              </Button>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
