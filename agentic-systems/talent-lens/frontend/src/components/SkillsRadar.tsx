import { cn } from "@/lib/utils";
import type { CandidateCapabilityScore } from "@/types/capability";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function barColor(
  score: number | null,
  required: number | null
): string {
  if (score == null) return "bg-slate-300";
  if (required != null) {
    if (score >= required) return "bg-emerald-500";
    if (score >= required - 1) return "bg-amber-500";
    return "bg-red-500";
  }
  // No requirement — color by absolute score
  if (score >= 4) return "bg-emerald-500";
  if (score >= 3) return "bg-amber-500";
  return "bg-red-500";
}

function labelColor(
  score: number | null,
  required: number | null
): string {
  if (score == null) return "text-slate-400";
  if (required != null) {
    if (score >= required) return "text-emerald-600";
    if (score >= required - 1) return "text-amber-600";
    return "text-red-600";
  }
  if (score >= 4) return "text-emerald-600";
  if (score >= 3) return "text-amber-600";
  return "text-red-600";
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

interface SkillsRadarProps {
  skills: CandidateCapabilityScore[];
}

export function SkillsRadar({ skills }: SkillsRadarProps) {
  const maxScore = 5;

  return (
    <div className="space-y-3">
      {skills.map((skill) => {
        const score = skill.avg_score;
        const pct = score != null ? Math.min((score / maxScore) * 100, 100) : 0;
        const reqPct =
          skill.required_level != null
            ? Math.min((skill.required_level / maxScore) * 100, 100)
            : null;

        return (
          <div key={skill.capability_id} className="flex items-center gap-3">
            {/* Label */}
            <span className="w-36 min-w-[9rem] text-sm font-medium text-slate-700 truncate text-right">
              {skill.capability_name}
            </span>

            {/* Bar container */}
            <div className="relative flex-1 h-5 rounded-full bg-slate-100 overflow-hidden">
              {/* Score bar */}
              <div
                className={cn(
                  "h-full rounded-full transition-all",
                  barColor(score, skill.required_level)
                )}
                style={{ width: `${pct}%` }}
              />

              {/* Required level marker */}
              {reqPct != null && (
                <div
                  className="absolute top-0 bottom-0 w-0.5 bg-slate-600"
                  style={{ left: `${reqPct}%` }}
                  title={`Required: ${skill.required_level}`}
                />
              )}
            </div>

            {/* Score value */}
            <span
              className={cn(
                "w-10 text-xs font-medium tabular-nums text-right",
                labelColor(score, skill.required_level)
              )}
            >
              {score != null ? score.toFixed(1) : "--"}
            </span>
          </div>
        );
      })}
    </div>
  );
}
