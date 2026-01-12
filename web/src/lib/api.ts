import axios, { AxiosError } from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    "Content-Type": "application/json",
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      if (typeof window !== "undefined") {
        localStorage.removeItem("access_token");
        localStorage.removeItem("user");
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

// Types
export interface UserProfile {
  ig_user_id: string;
  username: string;
  full_name?: string;
  profile_pic_url?: string;
  follower_count?: number;
  following_count?: number;
  media_count?: number;
  is_private?: boolean;
  is_verified?: boolean;
  biography?: string;
}

export interface InstagramUser {
  ig_id: string;
  username: string;
  full_name?: string;
  profile_pic_url?: string;
  is_verified: boolean;
  is_private: boolean;
}

export interface AnalyticsOverview {
  total_followers: number;
  total_following: number;
  not_following_back: number;
  not_followed_back: number;
  mutual_friends: number;
  new_followers: number;
  lost_followers: number;
  last_sync?: string;
}

export interface DetailedAnalytics {
  overview: AnalyticsOverview;
  followers: InstagramUser[];
  following: InstagramUser[];
  not_following_back: InstagramUser[];
  not_followed_back: InstagramUser[];
  mutual_friends: InstagramUser[];
  new_followers: InstagramUser[];
  lost_followers: InstagramUser[];
}

export interface SyncStatus {
  is_syncing: boolean;
  progress: number;
  current_task: string;
  last_sync?: string;
}

export interface ImageCacheStatus {
  is_caching: boolean;
  total: number;
  completed: number;
  failed: number;
  current_user?: string;
  started_at?: string;
}

export interface CanSyncResponse {
  can_sync: boolean;
  seconds_until_next_sync: number | null;
  hours_until_next_sync: number | null;
  last_sync: string | null;
  cooldown_hours: number;
}

export interface AuthResponse {
  success: boolean;
  message: string;
  requires_challenge?: boolean;
  challenge_type?: "sms" | "email";
  session_id?: string;
  access_token?: string;
  user?: UserProfile;
}

// Auth API
export const authApi = {
  login: async (username: string, password: string): Promise<AuthResponse> => {
    const { data } = await api.post<AuthResponse>("/auth/login", {
      username,
      password,
    });
    return data;
  },

  verify2FA: async (
    sessionId: string,
    code: string,
    username: string,
    password: string
  ): Promise<AuthResponse> => {
    const { data } = await api.post<AuthResponse>("/auth/verify-2fa", {
      session_id: sessionId,
      code,
      username,
      password,
    });
    return data;
  },

  verifyChallenge: async (
    sessionId: string,
    code: string,
    challengeType: "sms" | "email"
  ): Promise<AuthResponse> => {
    const { data } = await api.post<AuthResponse>("/auth/verify-challenge", {
      session_id: sessionId,
      code,
      challenge_type: challengeType,
    });
    return data;
  },

  logout: async () => {
    await api.post("/auth/logout");
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
  },
};

// Analytics API
export const analyticsApi = {
  getOverview: async (): Promise<AnalyticsOverview> => {
    const { data } = await api.get<AnalyticsOverview>("/analytics/overview");
    return data;
  },

  getDetailed: async (): Promise<DetailedAnalytics> => {
    const { data } = await api.get<DetailedAnalytics>("/analytics/detailed");
    return data;
  },

  getNotFollowingBack: async (
    limit = 50,
    offset = 0
  ): Promise<InstagramUser[]> => {
    const { data } = await api.get<InstagramUser[]>(
      `/analytics/not-following-back?limit=${limit}&offset=${offset}`
    );
    return data;
  },

  getNotFollowedBack: async (
    limit = 50,
    offset = 0
  ): Promise<InstagramUser[]> => {
    const { data } = await api.get<InstagramUser[]>(
      `/analytics/not-followed-back?limit=${limit}&offset=${offset}`
    );
    return data;
  },

  getMutual: async (limit = 50, offset = 0): Promise<InstagramUser[]> => {
    const { data } = await api.get<InstagramUser[]>(
      `/analytics/mutual?limit=${limit}&offset=${offset}`
    );
    return data;
  },

  getNewFollowers: async (): Promise<InstagramUser[]> => {
    const { data } = await api.get<InstagramUser[]>("/analytics/new-followers");
    return data;
  },

  getLostFollowers: async (): Promise<InstagramUser[]> => {
    const { data } = await api.get<InstagramUser[]>(
      "/analytics/lost-followers"
    );
    return data;
  },

  startSync: async (): Promise<{
    success: boolean;
    message: string;
    status: SyncStatus;
  }> => {
    const { data } = await api.post("/analytics/sync");
    return data;
  },

  getSyncStatus: async (): Promise<SyncStatus> => {
    const { data } = await api.get<SyncStatus>("/analytics/sync/status");
    return data;
  },

  canSync: async (): Promise<CanSyncResponse> => {
    const { data } = await api.get<CanSyncResponse>("/analytics/can-sync");
    return data;
  },

  getProfile: async (): Promise<UserProfile> => {
    const { data } = await api.get<UserProfile>("/analytics/profile");
    return data;
  },

  getImageCacheStatus: async (): Promise<ImageCacheStatus> => {
    const { data } = await api.get<ImageCacheStatus>(
      "/analytics/image-cache/status"
    );
    return data;
  },

  hasCachedPic: async (igUserId: string): Promise<boolean> => {
    const { data } = await api.get<{ has_cached_pic: boolean }>(
      `/analytics/has-cached-pic/${igUserId}`
    );
    return data.has_cached_pic;
  },
};

// Helper to get profile picture URL (cached or fallback to original)
export const getProfilePicUrl = (igUserId: string): string => {
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  return `${API_URL}/api/analytics/profile-pic/${igUserId}`;
};
