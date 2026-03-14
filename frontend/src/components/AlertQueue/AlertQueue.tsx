import type { AlertBundle } from "../../types";

interface Props {
  bundles: AlertBundle[];
}

export default function AlertQueue({ bundles }: Props) {
  return (
    <div className="space-y-2 text-sm">
      <h3 className="font-semibold text-sentinel-danger">Alert Queue</h3>
      {bundles.length === 0 && (
        <p className="text-gray-600 text-xs">No active alerts</p>
      )}
      {bundles.map((b) => (
        <div
          key={b.bundle_id}
          className="bg-sentinel-panel border border-sentinel-danger/30 rounded p-2"
        >
          <div className="font-medium">
            {b.primary_fraud_type} &middot; {b.case_reports.length} case(s)
          </div>
          <div className="text-gray-500 text-xs">
            Accounts: {b.related_account_ids.join(", ")}
          </div>
        </div>
      ))}
    </div>
  );
}
