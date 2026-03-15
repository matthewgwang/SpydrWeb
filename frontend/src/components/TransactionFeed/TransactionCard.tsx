import { Check, AlertTriangle, Circle } from "lucide-react";
import type { FeedEntry } from "./TransactionFeed";
import Md from "../Md";

interface Props {
  entry: FeedEntry;
  onClick?: () => void;
}

const STATUS_CONFIG = {
  cleared: {
    border: "border-transparent",
    bg: "hover:bg-s-surface/50",
    label: "Clear",
    color: "text-s-safe",
    Icon: Check,
  },
  flagged: {
    border: "border-s-danger/30",
    bg: "bg-s-danger-light hover:bg-red-50",
    label: "Flagged",
    color: "text-s-danger",
    Icon: AlertTriangle,
  },
  amber: {
    border: "border-s-warn/30",
    bg: "bg-s-warn-light hover:bg-amber-50",
    label: "Review",
    color: "text-s-warn",
    Icon: AlertTriangle,
  },
  pending: {
    border: "border-transparent",
    bg: "hover:bg-s-surface/50",
    label: "Pending",
    color: "text-s-text-tertiary",
    Icon: Circle,
  },
} as const;

function formatTime(ts: string): string {
  try {
    return new Date(ts).toLocaleTimeString("en-US", {
      hour12: false,
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return ts;
  }
}

export default function TransactionCard({ entry, onClick }: Props) {
  const cfg = STATUS_CONFIG[entry.status];
  const Icon = cfg.Icon;

  return (
    <div
      className={`
        border-l-2 ${cfg.border} ${cfg.bg}
        rounded-r px-2.5 py-1.5 text-[11px] transition
        ${onClick ? "cursor-pointer" : ""}
      `}
      onClick={onClick}
    >
      <div className="flex items-center justify-between mb-0.5">
        <span className="font-mono text-[10px] text-s-text-tertiary">
          {formatTime(entry.timestamp)}
        </span>
        <span className={`flex items-center gap-0.5 text-[10px] font-medium ${cfg.color}`}>
          <Icon size={9} />
          {cfg.label}
        </span>
      </div>

      <div className="flex items-baseline justify-between">
        <span className="text-s-text-secondary font-medium">
          {entry.senderId.slice(-4)} → {entry.receiverId.slice(-4)}
        </span>
        <span className="font-mono text-s-text-secondary">
          ${entry.amount.toLocaleString()}
        </span>
      </div>

      {entry.exploitationTactic && (
        <span className="tag tag-danger mt-0.5 text-[9px]">
          {entry.exploitationTactic.replace(/_/g, " ")}
        </span>
      )}

      {entry.alertSummary && (
        <div className="text-[10px] text-s-muted mt-0.5 line-clamp-1">
          <Md>{entry.alertSummary}</Md>
        </div>
      )}
    </div>
  );
}
