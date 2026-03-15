import type { EvidenceBrief as BriefType } from "../../types";
import Md from "../Md";

interface Props {
  brief: BriefType;
}

export default function EvidenceBrief({ brief }: Props) {
  return (
    <div className="space-y-3 text-sm">
      <h3 className="font-semibold text-s-text">Evidence Brief</h3>
      <Md className="text-s-text-secondary">{brief.narrative}</Md>
      {brief.manipulation_indicators.length > 0 && (
        <div>
          <h4 className="text-s-warn font-medium text-[11px]">
            Manipulation Indicators
          </h4>
          <ul className="list-disc list-inside text-s-muted text-[11px]">
            {brief.manipulation_indicators.map((ind, i) => (
              <li key={i}><Md>{ind}</Md></li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
