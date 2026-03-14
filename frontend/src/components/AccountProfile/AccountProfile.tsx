import type { AccountProfile as ProfileType } from "../../types";

interface Props {
  profile: ProfileType;
}

export default function AccountProfile({ profile }: Props) {
  return (
    <div className="space-y-3 text-sm">
      <h3 className="font-semibold text-lg">{profile.name}</h3>
      <p className="text-gray-400">
        {profile.age ? `${profile.age}y` : ""}
        {profile.location ? ` · ${profile.location}` : ""}
      </p>
      {profile.summary_text && (
        <p className="text-gray-300">{profile.summary_text}</p>
      )}
      {profile.vulnerability && (
        <div className="text-sentinel-warn">
          Vulnerability: {(profile.vulnerability.score * 100).toFixed(0)}%
        </div>
      )}
    </div>
  );
}
