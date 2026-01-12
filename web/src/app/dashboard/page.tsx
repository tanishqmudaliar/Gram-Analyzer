/* eslint-disable @next/next/no-img-element */
"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { ThemeToggle } from "@/components/ThemeToggle";
import { useAuthStore } from "@/store/auth";
import {
  analyticsApi,
  DetailedAnalytics,
  SyncStatus,
  getProfilePicUrl,
} from "@/lib/api";
import {
  Users,
  UserMinus,
  UserPlus,
  Heart,
  LogOut,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Sparkles,
  Clock,
} from "lucide-react";
import { VirtualUserList } from "@/components/VirtualUserList";

function UserAvatar({
  igUserId,
  username,
}: {
  igUserId?: string;
  username?: string;
}) {
  const [imgError, setImgError] = useState(false);
  const initials = username?.slice(0, 2).toUpperCase() || "??";

  // Use our backend proxy for profile pictures
  const profilePicUrl = igUserId ? getProfilePicUrl(igUserId) : null;

  return (
    <div className="w-10 h-10 rounded-full bg-linear-to-br from-purple-500 via-pink-500 to-orange-400 p-0.5">
      <div className="w-full h-full rounded-full bg-background flex items-center justify-center overflow-hidden">
        {profilePicUrl && !imgError ? (
          <img
            src={profilePicUrl}
            alt={username || "User"}
            className="w-full h-full object-cover rounded-full"
            onError={() => setImgError(true)}
          />
        ) : (
          <span className="text-sm font-bold gradient-text">{initials}</span>
        )}
      </div>
    </div>
  );
}

type TabType =
  | "followers"
  | "following"
  | "not-following-back"
  | "you-dont-follow"
  | "mutual"
  | "new"
  | "lost";

const TABS: {
  id: TabType;
  label: string;
  icon: React.ElementType;
  color: string;
}[] = [
  {
    id: "followers",
    label: "Followers",
    icon: Users,
    color: "from-blue-500 to-cyan-500",
  },
  {
    id: "following",
    label: "Following",
    icon: Heart,
    color: "from-pink-500 to-rose-500",
  },
  {
    id: "not-following-back",
    label: "Don't Follow Back",
    icon: UserMinus,
    color: "from-red-500 to-orange-500",
  },
  {
    id: "you-dont-follow",
    label: "You Don't Follow",
    icon: UserPlus,
    color: "from-amber-500 to-yellow-500",
  },
  {
    id: "mutual",
    label: "Mutuals",
    icon: Sparkles,
    color: "from-purple-500 to-pink-500",
  },
  {
    id: "new",
    label: "New Followers",
    icon: TrendingUp,
    color: "from-green-500 to-emerald-500",
  },
  {
    id: "lost",
    label: "Lost",
    icon: TrendingDown,
    color: "from-slate-500 to-zinc-500",
  },
];

export default function DashboardPage() {
  const router = useRouter();
  const { user, isAuthenticated, logout } = useAuthStore();
  const [analytics, setAnalytics] = useState<DetailedAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<TabType>("followers");
  const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [syncError, setSyncError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/login");
      return;
    }
    fetchAnalytics();
    checkSyncStatus();
  }, [isAuthenticated, router]);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (syncing) {
      interval = setInterval(async () => {
        const status = await analyticsApi.getSyncStatus();
        setSyncStatus(status);

        // Check for error in current_task
        if (
          status.current_task?.includes("error") ||
          status.current_task?.includes("restricted") ||
          status.current_task?.includes("expired")
        ) {
          setSyncError(status.current_task);
          setSyncing(false);
        } else if (!status.is_syncing) {
          setSyncing(false);
          setSyncError(null);
          fetchAnalytics();
        }
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [syncing]);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const data = await analyticsApi.getDetailed();
      setAnalytics(data);
    } catch (err) {
      console.error("Failed to fetch analytics:", err);
    } finally {
      setLoading(false);
    }
  };

  const checkSyncStatus = async () => {
    try {
      const status = await analyticsApi.getSyncStatus();
      setSyncStatus(status);
      if (status.is_syncing) {
        setSyncing(true);
      }
    } catch (err) {
      console.error("Failed to check sync status:", err);
    }
  };

  const handleSync = async () => {
    try {
      setSyncing(true);
      await analyticsApi.startSync();
    } catch (err) {
      console.error("Failed to start sync:", err);
      setSyncing(false);
    }
  };

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  const getTabData = () => {
    if (!analytics) return [];
    switch (activeTab) {
      case "followers":
        return analytics.followers;
      case "following":
        return analytics.following;
      case "not-following-back":
        return analytics.not_following_back;
      case "you-dont-follow":
        return analytics.not_followed_back;
      case "mutual":
        return analytics.mutual_friends;
      case "new":
        return analytics.new_followers;
      case "lost":
        return analytics.lost_followers;
      default:
        return [];
    }
  };

  const getTabCount = (tabId: TabType) => {
    if (!analytics) return 0;
    switch (tabId) {
      case "followers":
        return analytics.followers.length;
      case "following":
        return analytics.following.length;
      case "not-following-back":
        return analytics.not_following_back.length;
      case "you-dont-follow":
        return analytics.not_followed_back.length;
      case "mutual":
        return analytics.mutual_friends.length;
      case "new":
        return analytics.new_followers.length;
      case "lost":
        return analytics.lost_followers.length;
      default:
        return 0;
    }
  };

  const getEmptyMessage = () => {
    switch (activeTab) {
      case "followers":
        return "No followers yet";
      case "following":
        return "Not following anyone";
      case "not-following-back":
        return "Everyone follows you back!";
      case "you-dont-follow":
        return "You follow everyone back!";
      case "mutual":
        return "No mutual friends";
      case "new":
        return "No new followers since last sync";
      case "lost":
        return "No one unfollowed you";
      default:
        return "No data";
    }
  };

  if (!isAuthenticated) return null;

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-xl">
        <div className="container mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <UserAvatar
                igUserId={user?.ig_user_id}
                username={user?.username}
              />
              <div>
                <h1 className="font-semibold text-foreground">
                  @{user?.username}
                </h1>
                <p className="text-xs text-muted-foreground">
                  {user?.full_name}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <ThemeToggle />
              <Button
                variant="ghost"
                size="icon"
                className="rounded-full"
                onClick={handleLogout}
              >
                <LogOut className="h-5 w-5" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6 max-w-4xl">
        {/* Sync Card */}
        <Card className="mb-6 overflow-hidden border-border">
          <CardContent className="p-4">
            {syncing ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <RefreshCw className="h-4 w-4 animate-spin text-purple-500" />
                    <span className="text-sm font-medium">
                      {syncStatus?.current_task}
                    </span>
                  </div>
                  <span className="text-sm text-muted-foreground">
                    {syncStatus?.progress}%
                  </span>
                </div>
                <Progress value={syncStatus?.progress || 0} className="h-2" />
                {syncError && (
                  <div className="mt-3 p-3 rounded-lg bg-red-500/10 border border-red-500/30">
                    <p className="text-sm text-red-500">{syncError}</p>
                  </div>
                )}
                {/* ADD THIS:  Estimated time remaining */}
                {syncStatus?.progress && syncStatus.progress < 100 && (
                  <p className="text-xs text-muted-foreground text-center">
                    This may take a few minutes for large accounts
                  </p>
                )}
              </div>
            ) : (
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-full bg-purple-500/10">
                    <Clock className="h-4 w-4 text-purple-500" />
                  </div>
                  <div>
                    <p className="text-sm font-medium">
                      {analytics?.overview.last_sync
                        ? `Last synced ${new Date(
                            analytics.overview.last_sync
                          ).toLocaleDateString()}`
                        : "Never synced"}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Sync to update your analytics
                    </p>
                  </div>
                </div>
                <Button
                  onClick={handleSync}
                  className="bg-linear-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white border-0"
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Sync Now
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Stats Grid */}
        {analytics && (
          <div className="grid grid-cols-4 gap-3 mb-6">
            <div className="text-center p-3 rounded-2xl bg-card border border-border">
              <p className="text-2xl font-bold text-foreground">
                {analytics.overview.total_followers}
              </p>
              <p className="text-xs text-muted-foreground">Followers</p>
            </div>
            <div className="text-center p-3 rounded-2xl bg-card border border-border">
              <p className="text-2xl font-bold text-foreground">
                {analytics.overview.total_following}
              </p>
              <p className="text-xs text-muted-foreground">Following</p>
            </div>
            <div className="text-center p-3 rounded-2xl bg-card border border-border">
              <p className="text-2xl font-bold text-foreground">
                {analytics.overview.mutual_friends}
              </p>
              <p className="text-xs text-muted-foreground">Mutuals</p>
            </div>
            <div className="text-center p-3 rounded-2xl bg-card border border-border">
              <p className="text-2xl font-bold text-red-500">
                {analytics.overview.not_following_back}
              </p>
              <p className="text-xs text-muted-foreground">Don&apos;t Follow</p>
            </div>
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <RefreshCw className="h-8 w-8 text-purple-500 animate-spin" />
          </div>
        ) : analytics ? (
          <>
            {/* Tab Pills */}
            <div className="flex gap-2 overflow-x-auto pb-4 mb-4 scrollbar-hide">
              {TABS.map((tab) => {
                const Icon = tab.icon;
                const count = getTabCount(tab.id);
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all ${
                      isActive
                        ? `bg-linear-to-r ${tab.color} text-white shadow-lg`
                        : "bg-card border border-border text-foreground hover:bg-accent"
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                    {tab.label}
                    <span
                      className={`px-1.5 py-0.5 rounded-full text-xs ${
                        isActive ? "bg-white/20" : "bg-muted"
                      }`}
                    >
                      {count}
                    </span>
                  </button>
                );
              })}
            </div>

            {/* User List */}
            <Card className="border-border">
              <CardContent className="p-4">
                {loading ? (
                  <div className="flex items-center justify-center py-12">
                    <RefreshCw className="h-6 w-6 text-purple-500 animate-spin" />
                  </div>
                ) : (
                  <VirtualUserList
                    users={getTabData()}
                    emptyMessage={getEmptyMessage()}
                  />
                )}
              </CardContent>
            </Card>
          </>
        ) : null}
      </main>
    </div>
  );
}
