/* eslint-disable jsx-a11y/alt-text */
"use client";

import { useState, useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { ThemeToggle } from "@/components/ThemeToggle";
import { Trash2, Download, Pause, Play, Image } from "lucide-react";
import { analyticsApi, ImageCacheStatus } from "@/lib/api";

export default function LogsPage() {
  const [logs, setLogs] = useState<string[]>([]);
  const [connected, setConnected] = useState(false);
  const [paused, setPaused] = useState(false);
  const [imageCacheStatus, setImageCacheStatus] =
    useState<ImageCacheStatus | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const logsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const WS_URL = API_URL.replace(/^http/, "ws");
    const ws = new WebSocket(`${WS_URL}/ws/logs`);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
    };

    ws.onmessage = (event) => {
      if (!paused) {
        setLogs((prev) => [...prev, event.data]);
      }
    };

    ws.onclose = () => {
      setConnected(false);
    };

    ws.onerror = () => {
      setConnected(false);
    };

    return () => {
      ws.close();
    };
  }, [paused]);

  // Poll for image cache status
  useEffect(() => {
    const fetchImageCacheStatus = async () => {
      try {
        const status = await analyticsApi.getImageCacheStatus();
        setImageCacheStatus(status);
      } catch (err) {
        // Ignore errors - API might not be available
      }
    };

    fetchImageCacheStatus();
    const interval = setInterval(fetchImageCacheStatus, 2000);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    // Auto-scroll to bottom
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  const clearLogs = () => setLogs([]);

  const downloadLogs = () => {
    const blob = new Blob([logs.join("\n")], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `logs-${new Date().toISOString()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const formatLog = (log: string) => {
    // Color code different log types
    if (log.includes("[IG RAW]")) {
      try {
        const jsonStart = log.indexOf("{");
        const prefix = log.substring(0, jsonStart);
        const json = JSON.parse(log.substring(jsonStart));
        return (
          <div className="text-xs">
            <span className="text-purple-500">{prefix}</span>
            <pre className="text-green-500 ml-4 whitespace-pre-wrap">
              {JSON.stringify(json, null, 2)}
            </pre>
          </div>
        );
      } catch {
        return <span className="text-purple-500">{log}</span>;
      }
    }
    if (log.includes("[IMG CACHE]"))
      return <span className="text-amber-500">{log}</span>;
    if (log.includes("[SYNC]"))
      return <span className="text-blue-500">{log}</span>;
    if (log.includes("[SYNC ERROR]") || log.includes("[IG ERROR]"))
      return <span className="text-red-500">{log}</span>;
    if (log.includes("[IG]"))
      return <span className="text-cyan-500">{log}</span>;
    return <span className="text-foreground">{log}</span>;
  };

  const imageCacheProgress = imageCacheStatus?.total
    ? Math.round((imageCacheStatus.completed / imageCacheStatus.total) * 100)
    : 0;

  return (
    <div className="min-h-screen bg-background p-4">
      <div className="flex flex-col gap-4 h-[calc(100vh-2rem)]">
        {/* Image Cache Status Card */}
        {imageCacheStatus &&
          (imageCacheStatus.is_caching || imageCacheStatus.total > 0) && (
            <Card className="shrink-0">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-full bg-amber-500/10">
                    <Image className="h-5 w-5 text-amber-500" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium">
                        {imageCacheStatus.is_caching
                          ? `Caching profile pictures... @${
                              imageCacheStatus.current_user || "..."
                            }`
                          : "Profile pictures cached"}
                      </span>
                      <span className="text-sm text-muted-foreground">
                        {imageCacheStatus.completed}/{imageCacheStatus.total}
                        {imageCacheStatus.failed > 0 && (
                          <span className="text-red-500 ml-2">
                            ({imageCacheStatus.failed} failed)
                          </span>
                        )}
                      </span>
                    </div>
                    <Progress value={imageCacheProgress} className="h-2" />
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

        {/* Logs Card */}
        <Card className="flex-1 min-h-0">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <CardTitle>Live API Logs</CardTitle>
                <span
                  className={`px-2 py-0.5 rounded text-xs ${
                    connected
                      ? "bg-green-500/20 text-green-500"
                      : "bg-red-500/20 text-red-500"
                  }`}
                >
                  {connected ? "Connected" : "Disconnected"}
                </span>
              </div>
              <div className="flex gap-2">
                <ThemeToggle />
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPaused(!paused)}
                >
                  {paused ? (
                    <Play className="h-4 w-4" />
                  ) : (
                    <Pause className="h-4 w-4" />
                  )}
                </Button>
                <Button variant="outline" size="sm" onClick={clearLogs}>
                  <Trash2 className="h-4 w-4" />
                </Button>
                <Button variant="outline" size="sm" onClick={downloadLogs}>
                  <Download className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent className="h-[calc(100%-4rem)] overflow-hidden">
            <div className="h-full overflow-y-auto bg-muted rounded-lg p-4 font-mono text-sm">
              {logs.length === 0 ? (
                <p className="text-muted-foreground">
                  Waiting for logs... Try syncing your account.
                </p>
              ) : (
                logs.map((log, i) => (
                  <div key={i} className="py-1 border-b border-border">
                    {formatLog(log)}
                  </div>
                ))
              )}
              <div ref={logsEndRef} />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
