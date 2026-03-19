import { useState } from "react";
import { ChevronDown, ChevronUp, Users, Code2, Monitor, Award, MessageSquare } from "lucide-react";
import { cn } from "@/lib/utils";
import { ScoreBar } from "@/components/ScoreBar";
import { ConfidenceBadge, AssessmentStatusBadge } from "@/components/assessment-badges";
import type { Assessment, CriterionScore } from "@/types/assessment";

// ---------------------------------------------------------------------------
// Stage metadata
// ---------------------------------------------------------------------------

interface StageMeta {
  label: string;
  subtitle: string;
  accent: string; // border color class
  icon: React.ComponentType<{ className?: string }>;
}

const STAGE_META: Record<string, StageMeta> = {
  initial: {
    label: "Initial Interview",
    subtitle: "Talent Team Conversation",
    accent: "border-l-blue-500",
    icon: Users,
  },
  screening: {
    label: "Screening",
    subtitle: "Technical Screening",
    accent: "border-l-indigo-500",
    icon: MessageSquare,
  },
  coderpad: {
    label: "CoderPad",
    subtitle: "Live Coding Assessment",
    accent: "border-l-violet-500",
    icon: Code2,
  },
  technical: {
    label: "Technical Interview",
    subtitle: "Deep Technical Evaluation",
    accent: "border-l-emerald-500",
    icon: Monitor,
  },
  final: {
    label: "Final Interview",
    subtitle: "Leadership & Culture Fit",
    accent: "border-l-amber-500",
    icon: Award,
  },
};

const DEFAULT_META: StageMeta = {
  label: "Interview",
  subtitle: "Evaluation",
  accent: "border-l-slate-400",
  icon: MessageSquare,
};

// ---------------------------------------------------------------------------
// SimpleCriterionRow — lightweight row without evidence drill-down
// ---------------------------------------------------------------------------

function SimpleCriterionRow({ cs }: { cs: CriterionScore }) {
  const isNotAssessed = cs.assessment_status === "not_assessed";

  return (
    <div className={cn("flex items-center gap-3 py-2 first:pt-0 last:pb-0", isNotAssessed && "opacity-50")}>
      {/* Status icon */}
      {isNotAssessed ? (
        <span className="text-slate-300 text-sm">-</span>
      ) : cs.score >= 4 ? (
        <span className="text-emerald-500 text-sm">&#10003;</span>
      ) : cs.score >= 3 ? (
        <span className="text-amber-500 text-sm">&#9651;</span>
      ) : (
        <span className="text-red-400 text-sm">&#10005;</span>
      )}

      {/* Criterion name + badges */}
      <span className="flex-1 text-sm text-slate-700 flex items-center gap-1.5 min-w-0">
        <span className="truncate">{cs.criterion_name}</span>
        <ConfidenceBadge level={cs.confidence_level} />
        <AssessmentStatusBadge status={cs.assessment_status} />
      </span>

      {/* Score bar or N/A */}
      {isNotAssessed ? (
        <span className="w-32 text-xs text-slate-400 text-right">N/A</span>
      ) : (
        <div className="w-32">
          <ScoreBar score={cs.score} maxScore={cs.max_score} />
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// StageEvaluationCard
// ---------------------------------------------------------------------------

function StageEvaluationCard({ assessment }: { assessment: Assessment }) {
  const [expanded, setExpanded] = useState(false);
  const meta = STAGE_META[assessment.stage] ?? DEFAULT_META;
  const Icon = meta.icon;

  const totalCriteria = assessment.criterion_scores.length;
  const assessedCriteria = assessment.criterion_scores.filter(
    (cs) => cs.assessment_status !== "not_assessed"
  ).length;
  const coveragePct = totalCriteria > 0 ? Math.round((assessedCriteria / totalCriteria) * 100) : 0;

  return (
    <div className={cn("rounded-lg border border-l-4 bg-white shadow-sm overflow-hidden", meta.accent)}>
      {/* Header */}
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center gap-3 px-4 py-3.5 text-left hover:bg-slate-50/50 transition-colors"
      >
        <Icon className="h-4.5 w-4.5 text-slate-500 flex-shrink-0" />

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-slate-800">
              {meta.label}
            </span>
            <span className="inline-flex items-center rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-500">
              {totalCriteria} criteria
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">{meta.subtitle}</p>
        </div>

        {assessment.overall_score != null && (
          <span
            className={cn(
              "text-sm font-bold tabular-nums",
              assessment.overall_score >= 4
                ? "text-emerald-600"
                : assessment.overall_score >= 3
                  ? "text-amber-600"
                  : "text-red-600"
            )}
          >
            {assessment.overall_score.toFixed(1)}
            <span className="text-xs font-normal text-slate-400">/5</span>
          </span>
        )}

        {expanded ? (
          <ChevronUp className="h-4 w-4 text-slate-400 flex-shrink-0" />
        ) : (
          <ChevronDown className="h-4 w-4 text-slate-400 flex-shrink-0" />
        )}
      </button>

      {/* Expanded body */}
      {expanded && totalCriteria > 0 && (
        <div className="border-t px-4 py-3 space-y-3">
          {/* Mini coverage bar */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-slate-500">
                Assessed: {assessedCriteria}/{totalCriteria} criteria
              </span>
              <span className="text-xs font-medium text-slate-500 tabular-nums">
                {coveragePct}%
              </span>
            </div>
            <div className="flex h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
              <div
                className={cn(
                  "transition-all rounded-full",
                  coveragePct >= 70 ? "bg-emerald-500" : "bg-amber-500"
                )}
                style={{ width: `${coveragePct}%` }}
              />
            </div>
          </div>

          {/* Criterion rows */}
          <div className="divide-y divide-slate-100">
            {assessment.criterion_scores.map((cs) => (
              <SimpleCriterionRow key={cs.criterion_name} cs={cs} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// StageEvaluationSummary — container
// ---------------------------------------------------------------------------

interface StageEvaluationSummaryProps {
  assessments: Assessment[];
}

export function StageEvaluationSummary({ assessments }: StageEvaluationSummaryProps) {
  if (assessments.length === 0) return null;

  return (
    <div className="space-y-2">
      <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
        Evaluation Summary
      </h3>
      {assessments.map((a) => (
        <StageEvaluationCard key={a.id} assessment={a} />
      ))}
    </div>
  );
}
