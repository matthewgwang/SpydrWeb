import type { TransactionFeedItem, AlertFeedItem } from "../../types";

interface Props {
  transactions: TransactionFeedItem[];
  alerts: AlertFeedItem[];
}

export default function StatsCards({ transactions, alerts }: Props) {
  const flaggedCount = alerts.length;
  const totalEvents = transactions.length;

  const holdCount = transactions.filter(
    (tx) => tx.status === "hold" || tx.status === "refer",
  ).length;

  return (
    <div className="grid grid-cols-4 gap-2 shrink-0">
      {/* Card 1: Total Events */}
      <div className="bg-s-panel rounded border border-s-border px-3 py-2">
        <div className="text-[9px] text-s-text-tertiary uppercase tracking-wide">
          Total Scanned
        </div>
        <div className="text-lg font-bold font-mono text-s-text mt-0.5">
          {totalEvents.toLocaleString()}
        </div>
        <div className="text-[9px] text-s-muted mt-0.5">events in stream</div>
      </div>

      {/* Card 2: Alerts */}
      <div className="bg-s-panel rounded border border-s-border px-3 py-2">
        <div className="text-[9px] text-s-text-tertiary uppercase tracking-wide">
          Active Alerts
        </div>
        <div className="text-lg font-bold font-mono text-s-danger mt-0.5">
          {flaggedCount}
        </div>
        <div className="text-[9px] text-s-muted mt-0.5">flagged transactions</div>
      </div>

      {/* Card 3: Blocked */}
      <div className="bg-s-panel rounded border border-s-border px-3 py-2">
        <div className="text-[9px] text-s-text-tertiary uppercase tracking-wide">
          Transactions Blocked
        </div>
        <div className="text-lg font-bold font-mono text-s-warn mt-0.5">
          {holdCount}
        </div>
        <div className="text-[9px] text-s-muted mt-0.5">held or referred</div>
      </div>

      {/* Card 4: Pipeline Status */}
      <div className="bg-s-panel rounded border border-s-border px-3 py-2">
        <div className="text-[9px] text-s-text-tertiary uppercase tracking-wide">
          Pipeline Status
        </div>
        <div className="flex items-center gap-1.5 mt-0.5">
          <span className="w-1.5 h-1.5 rounded-full bg-s-safe animate-pulse" />
          <span className="text-lg font-bold font-mono text-s-safe">Online</span>
        </div>
        <div className="text-[9px] text-s-muted mt-0.5">5-layer detection active</div>
      </div>
    </div>
  );
}
