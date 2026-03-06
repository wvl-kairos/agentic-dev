import { cn } from "@/lib/utils";
import type { Assessment } from "@/types/assessment";

const STAGES = [
  { key: "screening", label: "Screen" },
  { key: "coderpad", label: "Coder" },
  { key: "technical_interview", label: "Tech" },
  { key: "final_interview", label: "Final" },
] as const;

function barColor(score: number): string {
  if (score >= 4) return "bg-emerald-500";
  if (score >= 3) return "bg-amber-500";
  return "bg-red-500";
}

interface StageScoreTimelineProps {
  assessments: Assessment[];
}

export function StageScoreTimeline({ assessments }: StageScoreTimelineProps) {
  const scoreMap = new Map(
    assessments
      .filter((a) => a.overall_score != null)
      .map((a) => [a.stage, a.overall_score!])
  );

  return (
    <div className="rounded-lg border bg-white px-5 py-4">
      <h4 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
        Stage Score Timeline
      </h4>
      <div className="flex items-end gap-3">
        {STAGES.map(({ key, label }) => {
          const score = scoreMap.get(key);
          const hasScore = score != null;
          const barHeight = hasScore ? Math.round((score / 5) * 64) : 0;

          return (
            <div
              key={key}
              className="flex flex-1 flex-col items-center gap-1"
            >
              {/* Bar container */}
              <div className="flex h-16 w-full items-end justify-center">
                {hasScore ? (
                  <div
                    className={cn(
                      "w-full max-w-[40px] rounded-t transition-all",
                      barColor(score)
                    )}
                    style={{ height: `${barHeight}px` }}
                  />
                ) : (
                  <div className="h-16 w-full max-w-[40px] rounded-t border-2 border-dashed border-slate-200" />
                )}
              </div>
              {/* Score */}
              <span
                className={cn(
                  "text-sm font-bold tabular-nums",
                  hasScore ? "text-slate-700" : "text-slate-300"
                )}
              >
                {hasScore ? score.toFixed(1) : "--"}
              </span>
              {/* Label */}
              <span className="text-[10px] font-medium text-slate-400">
                {label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
