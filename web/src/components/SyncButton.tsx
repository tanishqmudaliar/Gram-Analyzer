"use client";

import { useState, useEffect, useCallback } from "react";
import { Progress } from "@/components/ui/progress";
import { analyticsApi, SyncStatus, CanSyncResponse } from "@/lib/api";
import { RefreshCw, Check, Clock, AlertCircle } from "lucide-react";

interface AutoSyncProps {
  onSyncComplete?: () => void;
}

function formatTimeRemaining(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);

  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }
  return `${minutes}m`;
}

export function AutoSync({ onSyncComplete }: AutoSyncProps) {
  const [status, setStatus] = useState<SyncStatus | null>(null);
  const [canSyncInfo, setCanSyncInfo] = useState<CanSyncResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [hasTriedAutoSync, setHasTriedAutoSync] = useState(false);

  const checkCanSync = useCallback(async () => {
    try {
      const info = await analyticsApi.canSync();
      setCanSyncInfo(info);
      return info;
    } catch (err) {
      console.error("Failed to check sync status:", err);
      return null;
    }
  }, []);

  const checkSyncStatus = useCallback(async () => {
    try {
      const s = await analyticsApi.getSyncStatus();
      setStatus(s);
      return s;
    } catch (err) {
      console.error("Failed to get sync status:", err);
      return null;
    }
  }, []);

  const startAutoSync = useCallback(async () => {
    setError(null);
    try {
      const result = await analyticsApi.startSync();
      if (result.success) {
        setStatus(result.status);
      } else {
        setError(result.message);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to start sync");
    }
  }, []);

  // Initial check and auto-sync logic
  useEffect(() => {
    const initAutoSync = async () => {
      // First check current sync status
      const currentStatus = await checkSyncStatus();

      // If already syncing, don't do anything
      if (currentStatus?.is_syncing) {
        return;
      }

      // Check if we can sync
      const syncInfo = await checkCanSync();

      // Auto-sync if allowed and haven't tried yet this session
      if (syncInfo?.can_sync && !hasTriedAutoSync) {
        setHasTriedAutoSync(true);
        await startAutoSync();
      }
    };

    initAutoSync();
  }, [checkCanSync, checkSyncStatus, hasTriedAutoSync, startAutoSync]);

  // Poll while syncing
  useEffect(() => {
    if (status?.is_syncing) {
      const interval = setInterval(async () => {
        const s = await checkSyncStatus();

        // If sync just completed, notify parent and refresh can-sync info
        if (s && !s.is_syncing) {
          await checkCanSync();
          onSyncComplete?.();
        }
      }, 2000);
      return () => clearInterval(interval);
    }
  }, [status?.is_syncing, checkSyncStatus, checkCanSync, onSyncComplete]);

  // Update countdown timer
  useEffect(() => {
    if (canSyncInfo && !canSyncInfo.can_sync && canSyncInfo.seconds_until_next_sync) {
      const interval = setInterval(() => {
        setCanSyncInfo(prev => {
          if (!prev || !prev.seconds_until_next_sync) return prev;
          const newSeconds = prev.seconds_until_next_sync - 1;
          if (newSeconds <= 0) {
            // Time's up, check again and potentially auto-sync
            checkCanSync().then(info => {
              if (info?.can_sync) {
                startAutoSync();
              }
            });
            return { ...prev, can_sync: true, seconds_until_next_sync: null };
          }
          return {
            ...prev,
            seconds_until_next_sync: newSeconds,
            hours_until_next_sync: Math.round(newSeconds / 3600 * 10) / 10
          };
        });
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [canSyncInfo?.can_sync, canSyncInfo?.seconds_until_next_sync, checkCanSync, startAutoSync]);

  // Currently syncing
  if (status?.is_syncing) {
    return (
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <RefreshCw className="h-4 w-4 text-pink-500 animate-spin" />
          <span className="text-sm font-medium text-white">Syncing...</span>
        </div>
        <div className="text-sm text-zinc-400">{status.current_task}</div>
        <Progress value={status.progress} className="h-2" />
        <p className="text-xs text-zinc-500">{status.progress}% complete</p>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex items-center gap-2 text-amber-500">
        <AlertCircle className="h-4 w-4" />
        <span className="text-sm">{error}</span>
      </div>
    );
  }

  // Cooldown active
  if (canSyncInfo && !canSyncInfo.can_sync && canSyncInfo.seconds_until_next_sync) {
    return (
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Clock className="h-4 w-4 text-zinc-400" />
          <span className="text-sm text-zinc-400">Next sync available in</span>
        </div>
        <span className="text-sm font-medium text-white">
          {formatTimeRemaining(canSyncInfo.seconds_until_next_sync)}
        </span>
      </div>
    );
  }

  // Sync complete / ready
  if (status?.last_sync || canSyncInfo?.last_sync) {
    const lastSync = status?.last_sync || canSyncInfo?.last_sync;
    return (
      <div className="flex items-center gap-2">
        <Check className="h-4 w-4 text-green-500" />
        <span className="text-sm text-zinc-400">
          Synced {lastSync ? new Date(lastSync).toLocaleString() : "recently"}
        </span>
      </div>
    );
  }

  // Loading state
  return (
    <div className="flex items-center gap-2">
      <RefreshCw className="h-4 w-4 text-zinc-400 animate-spin" />
      <span className="text-sm text-zinc-400">Checking sync status...</span>
    </div>
  );
}

// Keep the old export name for backward compatibility
export const SyncButton = AutoSync;
