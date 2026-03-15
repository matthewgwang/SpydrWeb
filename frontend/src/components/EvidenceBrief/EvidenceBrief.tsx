import type { EvidenceBrief as BriefType } from "../../types";

interface Props {
  brief: BriefType;
}

export default function EvidenceBrief({ brief }: Props) {
  return (
    <div className="space-y-3 text-sm">
      <h3 className="font-semibold text-s-text">Evidence Brief</h3>
      <p className="text-s-text-secondary whitespace-pre-wrap">{brief.narrative}</p>
      {brief.manipulation_indicators.length > 0 && (
        <div>
          <h4 className="text-s-warn font-medium text-[11px]">
            Manipulation Indicators
          </h4>
          <ul className="list-disc list-inside text-s-muted text-[11px]">
            {brief.manipulation_indicators.map((ind, i) => (
              <li key={i}>{ind}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
