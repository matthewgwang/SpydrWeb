import type { AccountProfile as ProfileType } from "../../types";
import Md from "../Md";

interface Props {
  profile: ProfileType;
  role: "sender" | "receiver";
}

function Stat({ label, value }: { label: string; value: string | number | null | undefined }) {
  if (value == null || value === "") return null;
  return (
    <div className="flex justify-between text-[10px]">
      <span className="text-s-text-tertiary">{label}</span>
      <span className="font-mono text-s-text-secondary">{value}</span>
    </div>
  );
}

export default function AccountProfile({ profile, role }: Props) {
  const vuln = profile.vulnerability;
  const rr = profile.recipient_risk;
  const bl = profile.baseline;

  return (
    <div className="rounded border border-s-border p-2 space-y-1.5 bg-s-panel-alt">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-1.5">
            <span className="text-[11px] font-medium text-s-text">
              {profile.name}
            </span>
            <span className="tag tag-neutral text-[8px]">
              {role === "sender" ? "Sender" : "Receiver"}
            </span>
          </div>
          <div className="text-[9px] text-s-text-tertiary mt-0.5">
            {[
              profile.age ? `${profile.age}y` : null,
              profile.location,
              profile.account_type,
            ]
              .filter(Boolean)
              .join(" · ")}
          </div>
        </div>
        <div className="text-right text-[9px]">
          <div className="text-s-text-tertiary">Confidence</div>
          <div className="font-mono font-medium text-s-text-secondary">
            {Math.round(profile.profile_confidence * 100)}%
          </div>
        </div>
      </div>

      {profile.summary_text && (
        <Md className="text-[10px] text-s-muted leading-relaxed">
          {profile.summary_text}
        </Md>
      )}

      {/* Vulnerability */}
      {vuln && (
        <div className="rounded border border-s-warn/15 bg-s-warn-light p-1.5">
          <div className="flex items-center justify-between text-[10px] mb-0.5">
            <span className="font-medium text-s-warn">Vulnerability</span>
            <span className="font-mono font-medium text-s-warn">
              {Math.round(vuln.score * 100)}%
            </span>
          </div>
          <div className="w-full h-1 bg-white rounded-full overflow-hidden">
            <div
              className="h-full bg-s-warn rounded-full"
              style={{ width: `${vuln.score * 100}%` }}
            />
          </div>
          {vuln.factors.length > 0 && (
            <div className="mt-1 space-y-0.5">
              {vuln.factors.slice(0, 3).map((f, i) => (
                <div key={i} className="text-[9px] text-s-muted flex justify-between">
                  <span>{f.factor}</span>
                  <Md>{f.description}</Md>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Baseline */}
      {bl && (
        <div className="space-y-0.5">
          <div className="text-[9px] text-s-text-tertiary uppercase tracking-wide">
            Baseline
          </div>
          <Stat label="Avg txn" value={`$${bl.avg_amount.toFixed(0)} ± $${bl.std_amount.toFixed(0)}`} />
          <Stat label="Daily freq" value={bl.avg_daily_frequency.toFixed(1)} />
          <Stat label="Bal checks/day" value={bl.balance_check_frequency_daily.toFixed(1)} />
          <Stat label="History" value={`${bl.days_of_history}d`} />
        </div>
      )}

      {/* Recipient Risk */}
      {rr && role === "receiver" && (
        <div className="rounded border border-s-danger/15 bg-s-danger-light p-1.5 space-y-0.5">
          <div className="text-[10px] font-medium text-s-danger">Recipient Risk</div>
          <Stat label="First-time senders (7d)" value={rr.first_time_sender_count_7d} />
          <Stat label="Avg relationship" value={`${rr.avg_relationship_duration_days.toFixed(0)}d`} />
          <Stat label="Recv/send ratio" value={rr.receive_to_send_ratio.toFixed(1)} />
          <Stat label="Inbound vel (24h)" value={rr.inbound_velocity_24h.toFixed(1)} />
          <Stat label="Total inbound (7d)" value={`$${rr.total_inbound_amount_7d.toLocaleString()}`} />
          {rr.is_receive_only && (
            <div className="text-[9px] text-s-danger">Receive-only</div>
          )}
          {rr.connected_to_other_vulnerable_customers && (
            <div className="text-[9px] text-s-danger">Linked to other vulnerable customers</div>
          )}
        </div>
      )}

      {profile.devices.length > 0 && (
        <div className="text-[9px] text-s-text-tertiary">
          Devices: <span className="font-mono">{profile.devices.join(", ")}</span>
        </div>
      )}
    </div>
  );
}
