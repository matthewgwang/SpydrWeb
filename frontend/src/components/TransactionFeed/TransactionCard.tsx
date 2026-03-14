import type { TransactionFeedItem } from "../../types";

const STATUS_COLORS: Record<string, string> = {
  cleared: "border-sentinel-safe",
  flagged: "border-sentinel-danger",
  pending: "border-sentinel-warn",
};

interface Props {
  tx: TransactionFeedItem;
}

export default function TransactionCard({ tx }: Props) {
  const borderColor = STATUS_COLORS[tx.status] ?? "border-sentinel-border";

  return (
    <div
      className={`border-l-4 ${borderColor} bg-sentinel-panel rounded p-2 text-xs`}
    >
      <div className="flex justify-between">
        <span className="font-medium">{tx.sender_name}</span>
        <span className="text-gray-400">${tx.amount.toFixed(2)}</span>
      </div>
      <div className="text-gray-500">
        &rarr; {tx.receiver_name} &middot; {tx.type}
      </div>
    </div>
  );
}
