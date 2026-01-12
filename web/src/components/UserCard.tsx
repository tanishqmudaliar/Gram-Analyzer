/* eslint-disable @next/next/no-img-element */
"use client";

import { useState } from "react";
import { InstagramUser, getProfilePicUrl } from "@/lib/api";
import { BadgeCheck, Lock, ExternalLink } from "lucide-react";

interface UserCardProps {
  user: InstagramUser;
  action?: React.ReactNode;
}

export function UserCard({ user, action }: UserCardProps) {
  const [imgError, setImgError] = useState(false);

  const openProfile = () => {
    window.open(`https://instagram.com/${user.username}`, "_blank");
  };

  // Get initials for avatar fallback
  const getInitials = () => {
    if (user.full_name) {
      return user.full_name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .slice(0, 2)
        .toUpperCase();
    }
    return user.username.slice(0, 2).toUpperCase();
  };

  // Use our backend proxy for profile pictures
  const profilePicUrl = getProfilePicUrl(user.ig_id);

  return (
    <div className="flex items-center justify-between p-3 rounded-xl hover:bg-accent/50 transition-all duration-200 group">
      <div
        className="flex items-center gap-3 cursor-pointer flex-1 min-w-0"
        onClick={openProfile}
      >
        {/* Avatar with gradient border */}
        <div className="relative">
          <div className="w-11 h-11 rounded-full bg-linear-to-br from-purple-500 via-pink-500 to-orange-400 p-0.5">
            <div className="w-full h-full rounded-full bg-card flex items-center justify-center overflow-hidden">
              {!imgError ? (
                <img
                  src={profilePicUrl}
                  alt={user.username}
                  className="w-full h-full object-cover rounded-full"
                  onError={() => setImgError(true)}
                />
              ) : (
                <span className="text-sm font-semibold bg-linear-to-br from-purple-500 to-pink-500 bg-clip-text text-transparent">
                  {getInitials()}
                </span>
              )}
            </div>
          </div>
          {user.is_verified && (
            <div className="absolute -bottom-0.5 -right-0.5 bg-card rounded-full p-0.5">
              <BadgeCheck className="h-4 w-4 text-blue-500 fill-blue-500" />
            </div>
          )}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5">
            <p className="font-medium text-foreground truncate group-hover:text-purple-500 transition-colors">
              {user.username}
            </p>
            {user.is_private && (
              <Lock className="h-3 w-3 text-muted-foreground shrink-0" />
            )}
          </div>
          {user.full_name && (
            <p className="text-sm text-muted-foreground truncate">
              {user.full_name}
            </p>
          )}
        </div>

        <ExternalLink className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
      </div>
      {action && <div className="shrink-0 ml-2">{action}</div>}
    </div>
  );
}

interface UserListProps {
  users: InstagramUser[];
  emptyMessage?: string;
  renderAction?: (user: InstagramUser) => React.ReactNode;
}

export function UserList({
  users,
  emptyMessage = "No users to display",
  renderAction,
}: UserListProps) {
  if (users.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
        <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
          <span className="text-2xl">:/</span>
        </div>
        <p className="text-sm">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="space-y-1">
      {users.map((user) => (
        <UserCard key={user.ig_id} user={user} action={renderAction?.(user)} />
      ))}
    </div>
  );
}
