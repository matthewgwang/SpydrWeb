export default function GovernanceBar() {
  return (
    <div className="flex items-center justify-between px-4 py-2 bg-sentinel-panel border-b border-sentinel-border text-xs">
      <span className="font-bold text-sentinel-accent tracking-wider">
        SENTINEL
      </span>
      <div className="flex gap-6 text-gray-500">
        <span>Events: —</span>
        <span>Alerts: —</span>
        <span>Fast-path: —%</span>
        <span className="text-sentinel-safe">System OK</span>
      </div>
    </div>
  );
}
