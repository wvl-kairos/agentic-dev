import { cn } from "@/lib/utils";

interface ScoreBarProps {
  score: number;
  maxScore: number;
  /** Show the numeric label to the right of the bar */
  showLabel?: boolean;
  /** Height class override (default h-2) */
  height?: string;
}

function scoreColor(score: number): string {
  if (score >= 4) return "bg-emerald-500";
  if (score >= 3) return "bg-amber-500";
  return "bg-red-500";
}

export function ScoreBar({
  score,
  maxScore,
  showLabel = true,
  height = "h-2",
}: ScoreBarProps) {
  const pct = maxScore > 0 ? Math.min((score / maxScore) * 100, 100) : 0;

  return (
    <div className="flex items-center gap-2">
      <div
        className={cn(
          "flex-1 rounded-full bg-slate-200 overflow-hidden",
          height
        )}
      >
        <div
          className={cn("h-full rounded-full transition-all", scoreColor(score))}
          style={{ width: `${pct}%` }}
        />
      </div>
      {showLabel && (
        <span className="text-xs font-medium text-slate-600 tabular-nums whitespace-nowrap">
          {score}/{maxScore}
        </span>
      )}
    </div>
  );
}
