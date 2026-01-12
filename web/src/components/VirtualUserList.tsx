"use client";

import { useRef } from "react";
import { useVirtualizer } from "@tanstack/react-virtual";
import { UserCard } from "./UserCard";
import { InstagramUser } from "@/lib/api";

interface VirtualUserListProps {
  users: InstagramUser[];
  emptyMessage?: string;
}

export function VirtualUserList({
  users,
  emptyMessage = "No users",
}: VirtualUserListProps) {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: users.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 72, // Approximate height of UserCard
    overscan: 10,
  });

  if (users.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        {emptyMessage}
      </div>
    );
  }

  return (
    <div ref={parentRef} className="h-[500px] overflow-auto">
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          width: "100%",
          position: "relative",
        }}
      >
        {virtualizer.getVirtualItems().map((virtualItem) => (
          <div
            key={virtualItem.key}
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              width: "100%",
              height: `${virtualItem.size}px`,
              transform: `translateY(${virtualItem.start}px)`,
            }}
          >
            <UserCard user={users[virtualItem.index]} />
          </div>
        ))}
      </div>
    </div>
  );
}
