import { useMemo } from "react";
import type { AlertFeedItem, TransactionFeedItem } from "../../types";
import TransactionCard from "./TransactionCard";

interface Props {
  transactions: TransactionFeedItem[];
  alerts: AlertFeedItem[];
  onAlertSelect: (reportId: string) => void;
}

export interface FeedEntry {
  id: string;
  timestamp: string;
  senderName: string;
  senderId: string;
  receiverName: string;
  receiverId: string;
  amount: number;
  type: string;
  status: "cleared" | "flagged" | "amber" | "pending";
  confidenceScore: number;
  exploitationTactic?: string;
  alertSummary?: string;
  reportId?: string;
}

export default function TransactionFeed({
  transactions,
  alerts,
  onAlertSelect,
}: Props) {
  const feedEntries = useMemo<FeedEntry[]>(() => {
    const alertMap = new Map<string, AlertFeedItem>();
    for (const a of alerts) {
      alertMap.set(a.transaction_id, a);
    }

    return transactions.map((tx) => {
      const alert = alertMap.get(tx.id);
      const status: FeedEntry["status"] = alert
        ? alert.confidence_score >= 0.8
          ? "flagged"
          : "amber"
        : tx.status === "flagged"
          ? "flagged"
          : tx.status === "pending"
            ? "pending"
            : "cleared";

      return {
        id: tx.id,
        timestamp: tx.timestamp,
        senderName: tx.sender_name,
        senderId: tx.sender_id,
        receiverName: tx.receiver_name,
        receiverId: tx.receiver_id,
        amount: tx.amount,
        type: tx.type,
        status,
        confidenceScore: alert?.confidence_score ?? tx.confidence_score,
        exploitationTactic: alert?.exploitation_tactic,
        alertSummary: alert?.summary,
        reportId: alert?.id,
      };
    });
  }, [transactions, alerts]);

  return (
    <div className="flex flex-col h-full">
      <div className="panel-header">
        <h2 className="panel-title">Live Feed</h2>
        <p className="panel-subtitle">Real-time event stream</p>
      </div>

      <div className="flex-1 overflow-y-auto p-1.5 space-y-px">
        {feedEntries.length === 0 && (
          <div className="flex items-center justify-center h-20 text-s-text-tertiary text-[11px]">
            Waiting for events...
          </div>
        )}
        {feedEntries.map((entry) => (
          <TransactionCard
            key={entry.id}
            entry={entry}
            onClick={
              entry.reportId
                ? () => onAlertSelect(entry.reportId!)
                : undefined
            }
          />
        ))}
      </div>
    </div>
  );
}
