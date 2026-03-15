export default function GovernanceBar() {
  return (
    <div className="flex items-center justify-between px-4 py-2 bg-s-panel border-b border-s-border text-xs">
      <span className="font-semibold text-s-accent tracking-wider">
        SPYDRWEB
      </span>
      <div className="flex gap-6 text-s-text-tertiary">
        <span>Events: —</span>
        <span>Alerts: —</span>
        <span>Fast-path: —%</span>
        <span className="text-s-safe">System OK</span>
      </div>
    </div>
  );
}
