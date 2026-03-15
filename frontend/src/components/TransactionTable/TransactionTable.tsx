import { Activity } from "lucide-react";
import type { TransactionFeedItem } from "../../types";

interface Props {
  transactions: TransactionFeedItem[];
  compact?: boolean;
  pinnedId?: string | null;
  recentAlertTxIds?: Set<string>;
  onReasoning: (tx: TransactionFeedItem) => void;
  onReport: (tx: TransactionFeedItem) => void;
}

function riskColor(score: number) {
  if (score >= 0.7) return "bg-s-danger-light text-s-danger border border-s-danger/20";
  if (score >= 0.4) return "bg-s-warn-light text-s-warn border border-s-warn/20";
  return "bg-s-safe-light text-s-safe border border-s-safe/20";
}

function statusColor(status: string) {
  const s = status.toLowerCase();
  if (s === "hold" || s === "refer") return "text-s-danger font-bold";
  if (s === "delay") return "text-s-warn font-bold";
  return "text-s-safe";
}

function statusLabel(status: string) {
  const s = status.toLowerCase();
  if (s === "hold") return "HOLD";
  if (s === "refer") return "REFER";
  if (s === "delay") return "DELAY";
  if (s === "allow") return "ALLOW";
  return status.toUpperCase();
}

function formatTime(ts: string) {
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

function entityLabel(tx: TransactionFeedItem) {
  if (tx.sender_name) return tx.sender_name;
  if (tx.sender_id) return tx.sender_id.slice(0, 12);
  return "—";
}

export default function TransactionTable({
  transactions,
  compact = false,
  pinnedId,
  recentAlertTxIds,
  onReasoning,
  onReport,
}: Props) {
  const riskScore = (tx: TransactionFeedItem) =>
    Math.round(tx.confidence_score * 100);

  const sorted = pinnedId
    ? [
        ...transactions.filter((tx) => tx.id === pinnedId),
        ...transactions.filter((tx) => tx.id !== pinnedId),
      ]
    : transactions;

  if (compact) {
    return (
      <div className="flex flex-col h-full bg-s-panel">
        <div className="panel-header flex items-center gap-2">
          <Activity size={12} className="text-s-accent" />
          <span className="panel-title">Stream</span>
        </div>
        <div className="flex-1 overflow-y-auto">
          {sorted.map((tx) => {
            const isPinned = tx.id === pinnedId;
            const isAlerted = recentAlertTxIds?.has(tx.id) ?? false;
            return (
              <div
                key={tx.id}
                className={`flex items-center justify-between px-2 py-1.5 border-b border-s-border text-[10px] ${
                  isAlerted
                    ? "animate-row-danger"
                    : isPinned
                      ? "bg-s-accent-light border-l-2 border-l-s-accent"
                      : "hover:bg-s-surface"
                }`}
              >
                <div className="flex-1 min-w-0">
                  <div className="font-mono font-medium text-s-text truncate">
                    {tx.id.slice(0, 10)}
                  </div>
                  <span className={`text-[9px] ${statusColor(tx.status)}`}>
                    {statusLabel(tx.status)}
                  </span>
                </div>
                <div className="flex gap-1 shrink-0 ml-1">
                  <button
                    onClick={() => onReasoning(tx)}
                    className="px-1.5 py-0.5 rounded text-[9px] font-medium bg-s-surface border border-s-border text-s-text-secondary hover:bg-s-accent-light hover:text-s-accent transition"
                  >
                    Detail
                  </button>
                  <button
                    onClick={() => onReport(tx)}
                    className="px-1.5 py-0.5 rounded text-[9px] font-medium bg-s-surface border border-s-border text-s-text-secondary hover:bg-s-surface transition"
                  >
                    Report
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 bg-s-panel border border-s-border rounded flex flex-col min-h-0 overflow-hidden">
      <div className="px-3 py-2 border-b border-s-border flex items-center justify-between shrink-0">
        <h2 className="text-[11px] font-semibold text-s-text flex items-center gap-2">
          <Activity size={12} className="text-s-safe animate-pulse" />
          Live Transaction Stream
        </h2>
        <span className="text-[9px] font-mono text-s-text-tertiary">
          {transactions.length} events
        </span>
      </div>

      <div className="flex-1 overflow-auto">
        <table className="w-full text-left border-collapse text-[11px]">
          <thead className="bg-s-panel sticky top-0 z-10">
            <tr>
              <th className="px-3 py-2 font-semibold text-s-text-tertiary uppercase text-[9px] border-b border-s-border">
                Time
              </th>
              <th className="px-3 py-2 font-semibold text-s-text-tertiary uppercase text-[9px] border-b border-s-border">
                TXN ID
              </th>
              <th className="px-3 py-2 font-semibold text-s-text-tertiary uppercase text-[9px] border-b border-s-border">
                Sender
              </th>
              <th className="px-3 py-2 font-semibold text-s-text-tertiary uppercase text-[9px] border-b border-s-border">
                Receiver
              </th>
              <th className="px-3 py-2 font-semibold text-s-text-tertiary uppercase text-[9px] border-b border-s-border">
                Amount
              </th>
              <th className="px-3 py-2 font-semibold text-s-text-tertiary uppercase text-[9px] border-b border-s-border">
                Type
              </th>
              <th className="px-3 py-2 font-semibold text-s-text-tertiary uppercase text-[9px] border-b border-s-border">
                Risk
              </th>
              <th className="px-3 py-2 font-semibold text-s-text-tertiary uppercase text-[9px] border-b border-s-border">
                Status
              </th>
              <th className="px-3 py-2 font-semibold text-s-text-tertiary uppercase text-[9px] border-b border-s-border text-right">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="font-mono">
            {sorted.map((tx) => {
              const score = riskScore(tx);
              const isPinned = tx.id === pinnedId;
              const isAlerted = recentAlertTxIds?.has(tx.id) ?? false;
              return (
                <tr
                  key={tx.id}
                  className={`border-b border-s-border-light transition ${
                    isAlerted
                      ? "animate-row-danger"
                      : isPinned
                        ? "bg-s-accent-light"
                        : "hover:bg-s-surface"
                  }`}
                >
                  <td className="px-3 py-1.5 text-s-text-tertiary">
                    {formatTime(tx.timestamp)}
                  </td>
                  <td className="px-3 py-1.5 text-s-text font-medium">
                    {tx.id.slice(0, 10)}...
                  </td>
                  <td className="px-3 py-1.5 text-s-text-secondary font-sans">
                    {entityLabel(tx)}
                  </td>
                  <td className="px-3 py-1.5 text-s-text-tertiary font-sans">
                    {tx.receiver_name || tx.receiver_id?.slice(0, 12) || "—"}
                  </td>
                  <td className="px-3 py-1.5 text-s-text">
                    ${tx.amount.toLocaleString(undefined, {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })}
                  </td>
                  <td className="px-3 py-1.5 text-s-text-tertiary text-[10px]">
                    {tx.tx_type || tx.type || "—"}
                  </td>
                  <td className="px-3 py-1.5">
                    <span
                      className={`tag text-[9px] ${riskColor(tx.confidence_score)}`}
                    >
                      {score}
                    </span>
                  </td>
                  <td className="px-3 py-1.5">
                    <span className={`text-[10px] ${statusColor(tx.status)}`}>
                      {statusLabel(tx.status)}
                    </span>
                  </td>
                  <td className="px-3 py-1.5 text-right">
                    <div className="flex justify-end gap-1.5">
                      <button
                        onClick={() => onReasoning(tx)}
                        className="px-2 py-1 rounded text-[10px] font-medium font-sans bg-s-panel border border-s-border text-s-text-secondary hover:bg-s-accent-light hover:text-s-accent hover:border-s-accent/30 transition"
                      >
                        Reasoning
                      </button>
                      <button
                        onClick={() => onReport(tx)}
                        className="px-2 py-1 rounded text-[10px] font-medium font-sans bg-s-panel border border-s-border text-s-text-secondary hover:bg-s-surface transition"
                      >
                        Report
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
            {transactions.length === 0 && (
              <tr>
                <td
                  colSpan={9}
                  className="px-3 py-8 text-center text-s-text-tertiary font-sans text-[11px]"
                >
                  Awaiting transaction stream — start the demo to begin
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
