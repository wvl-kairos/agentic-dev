import { useState } from "react";
import { ChevronDown, ChevronUp, Mic, Quote } from "lucide-react";
import { cn } from "@/lib/utils";
import { ScoreBar } from "@/components/ScoreBar";
import type { Assessment, CriterionScore } from "@/types/assessment";

// ---------------------------------------------------------------------------
// Helpers (duplicated from AssessmentPage to avoid circular imports)
// ---------------------------------------------------------------------------

const STAGE_LABELS: Record<string, string> = {
  initial: "Initial Interview with Talent Team",
  screening: "Screening",
  coderpad: "CoderPad",
  technical_interview: "Technical Interview",
  final_interview: "Final Interview",
  decision: "Decision",
};

function scoreColorClass(score: number | null): string {
  if (score == null) return "text-slate-400";
  if (score >= 4) return "text-emerald-600";
  if (score >= 3) return "text-amber-600";
  return "text-red-600";
}

function recommendationBadge(rec: string | null) {
  if (!rec) return null;
  const lower = rec.toLowerCase();
  let bg = "bg-slate-100 text-slate-700";
  if (lower.includes("strong") && lower.includes("yes")) {
    bg = "bg-emerald-100 text-emerald-800";
  } else if (
    lower.includes("yes") ||
    lower.includes("proceed") ||
    lower.includes("advance")
  ) {
    bg = "bg-green-100 text-green-800";
  } else if (lower.includes("no") || lower.includes("reject")) {
    bg = "bg-red-100 text-red-800";
  } else if (lower.includes("maybe") || lower.includes("borderline")) {
    bg = "bg-amber-100 text-amber-800";
  }
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold capitalize",
        bg
      )}
    >
      {rec}
    </span>
  );
}

// ---------------------------------------------------------------------------
// TalkRatioBar (extracted from AssessmentPage)
// ---------------------------------------------------------------------------

function TalkRatioBar({ ratio }: { ratio: number }) {
  const candidatePct = Math.round(ratio * 100);
  const interviewerPct = 100 - candidatePct;

  return (
    <div className="space-y-1.5">
      <div className="flex items-center gap-2 text-xs text-slate-500">
        <Mic className="h-3.5 w-3.5" />
        <span>Talk Ratio</span>
      </div>
      <div className="flex h-4 w-full overflow-hidden rounded-full">
        <div
          className="bg-blue-500 transition-all"
          style={{ width: `${candidatePct}%` }}
        />
        <div
          className="bg-slate-300 transition-all"
          style={{ width: `${interviewerPct}%` }}
        />
      </div>
      <div className="flex justify-between text-xs text-slate-500">
        <span>Candidate {candidatePct}%</span>
        <span>Interviewer {interviewerPct}%</span>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// CriterionRow (extracted from AssessmentPage)
// ---------------------------------------------------------------------------

function CriterionRow({ cs }: { cs: CriterionScore }) {
  const [expanded, setExpanded] = useState(false);
  const hasEvidence = cs.evidence && cs.evidence.length > 0;

  return (
    <div className="border-t border-slate-100 py-3 first:border-t-0">
      <div className="flex items-center gap-3">
        <span className="flex-1 text-sm font-medium text-slate-700">
          {cs.criterion_name}
        </span>
        <div className="w-40">
          <ScoreBar score={cs.score} maxScore={cs.max_score} />
        </div>
        {(hasEvidence || cs.reasoning) && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center text-xs text-slate-400 hover:text-slate-600 transition-colors"
          >
            {expanded ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </button>
        )}
      </div>

      {expanded && (
        <div className="mt-2 ml-0 space-y-2">
          {cs.reasoning && (
            <p className="text-xs text-slate-500 leading-relaxed">
              {cs.reasoning}
            </p>
          )}
          {hasEvidence &&
            cs.evidence.map((ev, i) => (
              <div
                key={i}
                className="flex gap-2 rounded-md bg-slate-50 px-3 py-2"
              >
                <Quote className="mt-0.5 h-3.5 w-3.5 flex-shrink-0 text-slate-400" />
                <div className="text-xs">
                  <p className="italic text-slate-600">"{ev.quote}"</p>
                  {ev.speaker && (
                    <p className="mt-0.5 font-medium text-slate-500">
                      -- {ev.speaker}
                    </p>
                  )}
                  {ev.relevance && (
                    <p className="mt-0.5 text-slate-400">{ev.relevance}</p>
                  )}
                </div>
              </div>
            ))}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// CompactStageCard
// ---------------------------------------------------------------------------

interface CompactStageCardProps {
  assessment: Assessment;
}

export function CompactStageCard({ assessment }: CompactStageCardProps) {
  const [expanded, setExpanded] = useState(false);
  const label = STAGE_LABELS[assessment.stage] ?? assessment.stage;
  const talkPct =
    assessment.talk_ratio != null
      ? `${Math.round(assessment.talk_ratio * 100)}%`
      : null;

  return (
    <div className="rounded-lg border bg-white shadow-sm overflow-hidden">
      {/* Collapsed header row */}
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center gap-3 px-4 py-3 text-left hover:bg-slate-50 transition-colors"
      >
        <span className="text-sm font-semibold text-slate-800 min-w-[140px]">
          {label}
        </span>

        {assessment.overall_score != null && (
          <span
            className={cn(
              "text-sm font-bold tabular-nums",
              scoreColorClass(assessment.overall_score)
            )}
          >
            {assessment.overall_score.toFixed(1)}
            <span className="text-xs font-normal text-slate-400">/5.0</span>
          </span>
        )}

        <div className="flex-1" />

        {recommendationBadge(assessment.recommendation)}

        {talkPct && (
          <span className="flex items-center gap-1 text-xs text-slate-500">
            <Mic className="h-3 w-3" />
            {talkPct}
          </span>
        )}

        {expanded ? (
          <ChevronUp className="h-4 w-4 text-slate-400" />
        ) : (
          <ChevronDown className="h-4 w-4 text-slate-400" />
        )}
      </button>

      {/* Expanded detail */}
      {expanded && (
        <div className="border-t px-4 py-4 space-y-4">
          {assessment.summary && (
            <p className="text-sm leading-relaxed text-slate-600">
              {assessment.summary}
            </p>
          )}

          {assessment.talk_ratio != null && (
            <TalkRatioBar ratio={assessment.talk_ratio} />
          )}

          {assessment.criterion_scores.length > 0 && (
            <div>
              <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
                Criteria Breakdown
              </h4>
              <div>
                {assessment.criterion_scores.map((cs) => (
                  <CriterionRow key={cs.criterion_name} cs={cs} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
