import { useEffect, useState } from "react";
import { ChevronDown, ChevronUp, Mic, Quote, ExternalLink, FileText, Loader2, Info, Circle } from "lucide-react";
import { cn } from "@/lib/utils";
import { ScoreBar } from "@/components/ScoreBar";
import { ConfidenceBadge, AssessmentStatusBadge } from "@/components/assessment-badges";
import type { Assessment, CriterionScore } from "@/types/assessment";
import type { InterviewDetail } from "@/types/interview";
import { api } from "@/utils/api";

// ---------------------------------------------------------------------------
// Coverage helpers
// ---------------------------------------------------------------------------

function isNotAssessed(cs: CriterionScore): boolean {
  return cs.assessment_status === "not_assessed"
    || cs.confidence_level === "not_assessed";
}

// ---------------------------------------------------------------------------
// Helpers (duplicated from AssessmentPage to avoid circular imports)
// ---------------------------------------------------------------------------

const STAGE_LABELS: Record<string, string> = {
  initial: "Initial Interview with Talent Team",
  screening: "Screening",
  coderpad: "CoderPad",
  technical: "Technical Interview",
  technical_interview: "Technical Interview",
  final: "Final Interview",
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
// TranscriptViewer — lazy-fetches transcript on demand
// ---------------------------------------------------------------------------

function TranscriptViewer({ interviewId }: { interviewId: string }) {
  const [transcript, setTranscript] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<InterviewDetail>(`/interviews/${interviewId}`)
      .then((data) => setTranscript(data.transcript))
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [interviewId]);

  if (loading) {
    return (
      <div className="flex items-center gap-2 py-4">
        <Loader2 className="h-4 w-4 animate-spin text-slate-400" />
        <span className="text-xs text-slate-500">Loading transcript...</span>
      </div>
    );
  }

  if (error || !transcript) {
    return (
      <p className="py-2 text-xs text-slate-400">
        {error ?? "No transcript available."}
      </p>
    );
  }

  return (
    <div className="max-h-80 overflow-y-auto rounded-md bg-slate-50 px-3 py-2">
      <pre className="whitespace-pre-wrap text-xs text-slate-600 leading-relaxed font-sans">
        {transcript}
      </pre>
    </div>
  );
}

// ---------------------------------------------------------------------------
// CriterionRow (extracted from AssessmentPage)
// ---------------------------------------------------------------------------

function CriterionRow({ cs }: { cs: CriterionScore }) {
  const [expanded, setExpanded] = useState(false);
  const hasEvidence = cs.evidence && cs.evidence.length > 0;
  const notAssessed = isNotAssessed(cs);

  return (
    <div className={cn("border-t border-slate-100 py-3 first:border-t-0", notAssessed && "opacity-50")}>
      <div className="flex items-center gap-3">
        <span className="flex-1 text-sm font-medium text-slate-700 flex items-center gap-1.5">
          {cs.criterion_name}
          <ConfidenceBadge level={cs.confidence_level} />
          <AssessmentStatusBadge status={cs.assessment_status} />
        </span>
        {notAssessed ? (
          <span className="w-40 text-xs text-slate-400 text-right">Not Assessed</span>
        ) : (
          <div className="w-40">
            <ScoreBar score={cs.score} maxScore={cs.max_score} />
          </div>
        )}
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
  const [showTranscript, setShowTranscript] = useState(false);
  const [showScoring, setShowScoring] = useState(false);
  const label = STAGE_LABELS[assessment.stage] ?? assessment.stage;
  const talkPct =
    assessment.talk_ratio != null
      ? `${Math.round(assessment.talk_ratio * 100)}%`
      : null;

  // Coverage computation
  const totalCriteria = assessment.criterion_scores.length;
  const assessedCriteria = assessment.criterion_scores.filter(
    (cs) => !isNotAssessed(cs)
  );
  const notAssessedCriteria = assessment.criterion_scores.filter(isNotAssessed);
  const assessedCount = assessedCriteria.length;
  const coveragePct = totalCriteria > 0 ? Math.round((assessedCount / totalCriteria) * 100) : 0;
  const hasGaps = notAssessedCriteria.length > 0;

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

        {/* Coverage pill — only shown when there are gaps */}
        {hasGaps && totalCriteria > 0 && (
          <span
            className={cn(
              "inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-semibold tabular-nums",
              coveragePct >= 70
                ? "bg-amber-100 text-amber-700"
                : "bg-red-100 text-red-700"
            )}
          >
            {assessedCount}/{totalCriteria}
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
          {/* Action links: Recording + Transcript */}
          <div className="flex items-center gap-3">
            {assessment.recording_url && (
              <a
                href={assessment.recording_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-xs font-medium text-blue-600 hover:text-blue-700 transition-colors"
              >
                <ExternalLink className="h-3.5 w-3.5" />
                Recording
              </a>
            )}
            {assessment.interview_id && (
              <button
                type="button"
                onClick={() => setShowTranscript(!showTranscript)}
                className="inline-flex items-center gap-1 text-xs font-medium text-blue-600 hover:text-blue-700 transition-colors"
              >
                <FileText className="h-3.5 w-3.5" />
                {showTranscript ? "Hide Transcript" : "View Transcript"}
              </button>
            )}
          </div>

          {/* Inline transcript viewer */}
          {showTranscript && assessment.interview_id && (
            <TranscriptViewer interviewId={assessment.interview_id} />
          )}

          {assessment.summary && (
            <p className="text-sm leading-relaxed text-slate-600">
              {assessment.summary}
            </p>
          )}

          {assessment.talk_ratio != null && (
            <TalkRatioBar ratio={assessment.talk_ratio} />
          )}

          {/* Coverage bar — shown when there are criteria */}
          {totalCriteria > 0 && (
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-slate-500">
                  Assessed: {assessedCount}/{totalCriteria} criteria
                </span>
                <span className="text-xs font-medium text-slate-500 tabular-nums">
                  {coveragePct}%
                </span>
              </div>
              <div className="flex h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
                <div
                  className={cn(
                    "transition-all rounded-full",
                    coveragePct === 100
                      ? "bg-emerald-500"
                      : coveragePct >= 70
                        ? "bg-amber-500"
                        : "bg-red-400"
                  )}
                  style={{ width: `${coveragePct}%` }}
                />
              </div>
            </div>
          )}

          {/* Assessed criteria */}
          {assessedCriteria.length > 0 && (
            <div>
              <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
                Criteria Breakdown
              </h4>
              <div>
                {assessedCriteria.map((cs) => (
                  <CriterionRow key={cs.criterion_name} cs={cs} />
                ))}
              </div>
            </div>
          )}

          {/* Not-assessed criteria */}
          {notAssessedCriteria.length > 0 && (
            <div>
              <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
                Not Evaluated ({notAssessedCriteria.length})
              </h4>
              <div className="space-y-1.5">
                {notAssessedCriteria.map((cs) => (
                  <div
                    key={cs.criterion_name}
                    className="flex items-center gap-2 text-sm text-slate-400"
                  >
                    <Circle className="h-3 w-3 flex-shrink-0" />
                    <span>{cs.criterion_name}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Scoring explanation */}
          <div className="border-t pt-3">
            <button
              onClick={() => setShowScoring(!showScoring)}
              className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-slate-600 transition-colors"
            >
              <Info className="h-3 w-3" />
              {showScoring ? "Hide scoring details" : "How is this scored?"}
            </button>
            {showScoring && (
              <div className="mt-2 rounded-md bg-slate-50 p-2.5 text-xs text-slate-500 space-y-1">
                <p>Each criterion is scored 1-5 based on interview evidence by Claude.</p>
                <p>Confidence: <strong>Demonstrated</strong> (1.0x) &gt; <strong>Mentioned</strong> (0.6x) &gt; <strong>Claimed</strong> (0.3x). <strong>Not Assessed</strong> = not evaluated.</p>
                <p>Overall = weighted average of assessed criteria (not-assessed excluded).</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
