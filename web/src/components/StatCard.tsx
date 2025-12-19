"use client";

import { Card } from "@/components/ui/card";
import { formatNumber } from "@/lib/utils";
import { LucideIcon } from "lucide-react";

interface StatCardProps {
  title: string;
  value: number;
  icon: LucideIcon;
  trend?: "up" | "down" | "neutral";
  trendValue?: number;
  color?: "pink" | "purple" | "blue" | "green" | "red" | "yellow";
  onClick?: () => void;
}

const colorClasses = {
  pink: "from-pink-500/20 to-pink-500/5 border-pink-500/30",
  purple: "from-purple-500/20 to-purple-500/5 border-purple-500/30",
  blue: "from-blue-500/20 to-blue-500/5 border-blue-500/30",
  green: "from-green-500/20 to-green-500/5 border-green-500/30",
  red: "from-red-500/20 to-red-500/5 border-red-500/30",
  yellow: "from-yellow-500/20 to-yellow-500/5 border-yellow-500/30",
};

const iconColorClasses = {
  pink: "text-pink-500",
  purple: "text-purple-500",
  blue: "text-blue-500",
  green: "text-green-500",
  red: "text-red-500",
  yellow: "text-yellow-500",
};

export function StatCard({
  title,
  value,
  icon: Icon,
  trend,
  trendValue,
  color = "pink",
  onClick,
}: StatCardProps) {
  return (
    <Card
      className={`bg-gradient-to-br ${colorClasses[color]} p-4 cursor-pointer hover:scale-[1.02] transition-transform`}
      onClick={onClick}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-zinc-400">{title}</p>
          <p className="text-2xl font-bold text-white mt-1">
            {formatNumber(value)}
          </p>
          {trend && trendValue !== undefined && (
            <p
              className={`text-xs mt-1 ${
                trend === "up"
                  ? "text-green-500"
                  : trend === "down"
                  ? "text-red-500"
                  : "text-zinc-500"
              }`}
            >
              {trend === "up" ? "+" : trend === "down" ? "-" : ""}
              {trendValue} since last sync
            </p>
          )}
        </div>
        <div className={`p-2 rounded-lg bg-zinc-900/50`}>
          <Icon className={`h-5 w-5 ${iconColorClasses[color]}`} />
        </div>
      </div>
    </Card>
  );
}
