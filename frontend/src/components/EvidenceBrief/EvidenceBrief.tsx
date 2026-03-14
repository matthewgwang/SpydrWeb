import type { EvidenceBrief as BriefType } from "../../types";

interface Props {
  brief: BriefType;
}

export default function EvidenceBrief({ brief }: Props) {
  return (
    <div className="space-y-3 text-sm">
      <h3 className="font-semibold">Evidence Brief</h3>
      <p className="text-gray-300 whitespace-pre-wrap">{brief.narrative}</p>
      {brief.manipulation_indicators.length > 0 && (
        <div>
          <h4 className="text-sentinel-warn font-medium">
            Manipulation Indicators
          </h4>
          <ul className="list-disc list-inside text-gray-400">
            {brief.manipulation_indicators.map((ind, i) => (
              <li key={i}>{ind}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
