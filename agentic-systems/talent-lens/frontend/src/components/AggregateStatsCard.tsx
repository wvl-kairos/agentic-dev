import { TrendingUp, Layers, Mic, Award, MessageSquare } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Assessment } from "@/types/assessment";
import type { Candidate } from "@/types/candidate";

interface AggregateStatsCardProps {
  assessments: Assessment[];
  candidate: Candidate;
}

function scoreColorClass(score: number | null): string {
  if (score == null) return "text-slate-400";
  if (score >= 4) return "text-emerald-600";
  if (score >= 3) return "text-amber-600";
  return "text-red-600";
}

export function AggregateStatsCard({
  assessments,
  candidate: _candidate,
}: AggregateStatsCardProps) {
  const scored = assessments.filter((a) => a.overall_score != null);
  const avgScore =
    scored.length > 0
      ? scored.reduce((sum, a) => sum + (a.overall_score ?? 0), 0) /
        scored.length
      : null;

  const stagesDone = scored.length;
  const totalStages = 5;

  const withTalkRatio = assessments.filter((a) => a.talk_ratio != null);
  const avgTalkRatio =
    withTalkRatio.length > 0
      ? withTalkRatio.reduce((sum, a) => sum + (a.talk_ratio ?? 0), 0) /
        withTalkRatio.length
      : null;

  // Find strongest area: highest-scored criterion across all assessments (exclude not_assessed)
  let strongestArea: string | null = null;
  let highestCriterionScore = -1;
  for (const a of assessments) {
    for (const cs of a.criterion_scores) {
      if (cs.assessment_status === "not_assessed") continue;
      if (cs.score > highestCriterionScore) {
        highestCriterionScore = cs.score;
        strongestArea = cs.criterion_name;
      }
    }
  }

  // Derive communication score from "Soft Skills", "Communication", or "Communication & Presence"
  const commNames = new Set(["soft skills", "communication", "communication & presence"]);
  const commScores: number[] = [];
  for (const a of assessments) {
    for (const cs of a.criterion_scores) {
      if (cs.assessment_status === "not_assessed") continue;
      if (commNames.has(cs.criterion_name.toLowerCase())) {
        commScores.push(cs.score);
      }
    }
  }
  const avgComm =
    commScores.length > 0
      ? commScores.reduce((s, v) => s + v, 0) / commScores.length
      : null;

  const stats = [
    {
      label: "Avg Score",
      value: avgScore != null ? avgScore.toFixed(1) : "--",
      sub: "/ 5.0",
      icon: TrendingUp,
      colorClass: scoreColorClass(avgScore),
    },
    {
      label: "Stages Done",
      value: `${stagesDone}`,
      sub: `/ ${totalStages}`,
      icon: Layers,
      colorClass: "text-slate-700",
    },
    {
      label: "Communication",
      value: avgComm != null ? avgComm.toFixed(1) : "--",
      sub: avgComm != null ? "/ 5.0" : null,
      icon: MessageSquare,
      colorClass: scoreColorClass(avgComm),
    },
    {
      label: "Avg Talk Ratio",
      value: avgTalkRatio != null ? `${Math.round(avgTalkRatio * 100)}%` : "--",
      sub: null,
      icon: Mic,
      colorClass: "text-slate-700",
    },
    {
      label: "Strongest Area",
      value: strongestArea ?? "--",
      sub: null,
      icon: Award,
      colorClass: "text-slate-700",
    },
  ];

  return (
    <div className="grid grid-cols-3 gap-3">
      {stats.map((stat) => (
        <div
          key={stat.label}
          className="flex flex-col rounded-lg border bg-white px-3 py-2.5"
        >
          <div className="flex items-center gap-1.5">
            <stat.icon className="h-3.5 w-3.5 text-slate-400" />
            <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
              {stat.label}
            </span>
          </div>
          <div className="mt-1 flex items-baseline gap-1">
            <span
              className={cn(
                "font-bold tabular-nums truncate",
                stat.colorClass,
                stat.label === "Strongest Area" ? "text-sm" : "text-xl"
              )}
              title={stat.value}
            >
              {stat.value}
            </span>
            {stat.sub && (
              <span className="text-xs text-slate-400">{stat.sub}</span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
