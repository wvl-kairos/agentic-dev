import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import {
  Loader2,
  AlertCircle,
  ArrowLeft,
  ChevronDown,
  ChevronUp,
  Quote,
  Mic,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { api } from "@/utils/api";
import { useAssessments } from "@/hooks/useAssessments";
import { useCapabilities } from "@/hooks/useCapabilities";
import { PipelineStepper } from "@/components/PipelineStepper";
import { ScoreBar } from "@/components/ScoreBar";
import { CapabilityMatrix } from "@/components/CapabilityMatrix";
import { SkillsRadar } from "@/components/SkillsRadar";
import type { Assessment, CriterionScore } from "@/types/assessment";
import type { CandidateSkills } from "@/types/capability";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const STAGE_LABELS: Record<string, string> = {
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

function scoreBgClass(score: number | null): string {
  if (score == null) return "bg-slate-100";
  if (score >= 4) return "bg-emerald-50 border-emerald-200";
  if (score >= 3) return "bg-amber-50 border-amber-200";
  return "bg-red-50 border-red-200";
}

function recommendationBadge(rec: string | null) {
  if (!rec) return null;
  const lower = rec.toLowerCase();
  let bg = "bg-slate-100 text-slate-700";
  if (lower.includes("strong") && lower.includes("yes")) {
    bg = "bg-emerald-100 text-emerald-800";
  } else if (lower.includes("yes") || lower.includes("proceed") || lower.includes("advance")) {
    bg = "bg-green-100 text-green-800";
  } else if (lower.includes("no") || lower.includes("reject")) {
    bg = "bg-red-100 text-red-800";
  } else if (lower.includes("maybe") || lower.includes("borderline")) {
    bg = "bg-amber-100 text-amber-800";
  }
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold capitalize",
        bg
      )}
    >
      {rec}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Talk Ratio Bar
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
// Expandable Criterion Row
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
// Assessment Card (per-stage)
// ---------------------------------------------------------------------------

function AssessmentCard({ assessment }: { assessment: Assessment }) {
  const label = STAGE_LABELS[assessment.stage] ?? assessment.stage;

  return (
    <div className="rounded-lg border bg-white shadow-sm overflow-hidden">
      {/* Card header */}
      <div
        className={cn(
          "flex items-center justify-between border-b px-5 py-4",
          scoreBgClass(assessment.overall_score)
        )}
      >
        <h3 className="text-base font-semibold text-slate-800">{label}</h3>
        <div className="flex items-center gap-3">
          {recommendationBadge(assessment.recommendation)}
          {assessment.overall_score != null && (
            <span
              className={cn(
                "text-2xl font-bold tabular-nums",
                scoreColorClass(assessment.overall_score)
              )}
            >
              {assessment.overall_score.toFixed(1)}
              <span className="text-sm font-normal text-slate-400">/5.0</span>
            </span>
          )}
        </div>
      </div>

      <div className="px-5 py-4 space-y-4">
        {/* Summary */}
        {assessment.summary && (
          <p className="text-sm leading-relaxed text-slate-600">
            {assessment.summary}
          </p>
        )}

        {/* Talk ratio */}
        {assessment.talk_ratio != null && (
          <TalkRatioBar ratio={assessment.talk_ratio} />
        )}

        {/* Criterion scores */}
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
    </div>
  );
}

// ---------------------------------------------------------------------------
// Skills Matrix Section
// ---------------------------------------------------------------------------

function SkillsMatrixSection({ candidateId }: { candidateId: string }) {
  const { capabilities, loading: capsLoading } = useCapabilities();
  const [skills, setSkills] = useState<CandidateSkills | null>(null);
  const [skillsLoading, setSkillsLoading] = useState(true);
  const [skillsError, setSkillsError] = useState<string | null>(null);

  useEffect(() => {
    setSkillsLoading(true);
    setSkillsError(null);

    api
      .get<CandidateSkills>(`/candidates/${candidateId}/skills`)
      .then((data) => setSkills(data))
      .catch((e: Error) => setSkillsError(e.message))
      .finally(() => setSkillsLoading(false));
  }, [candidateId]);

  if (skillsLoading || capsLoading) {
    return (
      <div className="rounded-lg border bg-white p-5 shadow-sm">
        <div className="flex items-center justify-center h-24">
          <Loader2 className="h-5 w-5 animate-spin text-slate-400" />
          <span className="ml-2 text-sm text-slate-500">Loading skills...</span>
        </div>
      </div>
    );
  }

  if (skillsError || !skills) {
    return (
      <div className="rounded-lg border bg-white p-5 shadow-sm">
        <div className="flex items-center gap-2">
          <AlertCircle className="h-4 w-4 text-slate-400" />
          <p className="text-sm text-slate-500">
            Skills data not available yet.
          </p>
        </div>
      </div>
    );
  }

  if (skills.capabilities.length === 0) {
    return null;
  }

  const hasRoleTemplate = skills.role_template != null;

  return (
    <div className="rounded-lg border bg-white shadow-sm overflow-hidden">
      <div className="border-b px-5 py-4">
        <h3 className="text-base font-semibold text-slate-800">
          Skills Matrix
        </h3>
        {hasRoleTemplate && skills.role_template && (
          <p className="mt-0.5 text-sm text-slate-500">
            Compared against{" "}
            <span className="font-medium text-slate-600">
              {skills.role_template.name}
            </span>{" "}
            requirements
          </p>
        )}
      </div>
      <div className="px-5 py-4">
        {hasRoleTemplate && capabilities.length > 0 ? (
          <CapabilityMatrix
            capabilities={capabilities}
            requirements={
              skills.role_template!.requirements.map((r) => ({
                capability_id: r.capability_id,
                required_level: r.required_level,
              }))
            }
            scores={skills.capabilities.map((c) => ({
              capability_id: c.capability_id,
              avg_score: c.avg_score,
            }))}
          />
        ) : (
          <SkillsRadar skills={skills.capabilities} />
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export function AssessmentPage() {
  const { id } = useParams<{ id: string }>();
  const { assessments, candidate, loading, error } = useAssessments(id!);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
        <span className="ml-2 text-slate-500">Loading assessment...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-4">
        <AlertCircle className="h-5 w-5 text-red-500" />
        <p className="text-sm text-red-700">Failed to load assessment: {error}</p>
      </div>
    );
  }

  // Determine which stages have assessments
  const completedStages = assessments.map((a) => a.stage);

  // Compute a composite score across all assessments
  const scoredAssessments = assessments.filter((a) => a.overall_score != null);
  const avgScore =
    scoredAssessments.length > 0
      ? scoredAssessments.reduce((sum, a) => sum + (a.overall_score ?? 0), 0) /
        scoredAssessments.length
      : null;

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Back link */}
      <Link
        to="/candidates"
        className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700 transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Candidates
      </Link>

      {/* Candidate info header */}
      {candidate && (
        <div className="rounded-lg border bg-white p-5 shadow-sm">
          <div className="flex items-center gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-slate-200 text-lg font-bold text-slate-600">
              {candidate.name
                .split(" ")
                .map((n) => n[0])
                .join("")
                .slice(0, 2)
                .toUpperCase()}
            </div>
            <div className="flex-1">
              <h2 className="text-xl font-bold text-slate-900">
                {candidate.name}
              </h2>
              <div className="flex items-center gap-3 mt-0.5">
                {candidate.role && (
                  <span className="text-sm text-slate-500">
                    {candidate.role}
                  </span>
                )}
                {candidate.email && (
                  <span className="text-sm text-slate-400">
                    {candidate.email}
                  </span>
                )}
              </div>
            </div>
            {avgScore != null && (
              <div className="text-right">
                <p className="text-xs font-medium uppercase tracking-wider text-slate-400">
                  Avg Score
                </p>
                <p
                  className={cn(
                    "text-3xl font-bold tabular-nums",
                    scoreColorClass(avgScore)
                  )}
                >
                  {avgScore.toFixed(1)}
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Pipeline stepper */}
      {candidate && (
        <div className="rounded-lg border bg-white p-5 shadow-sm">
          <PipelineStepper
            currentStage={candidate.stage}
            completedStages={completedStages as any}
          />
        </div>
      )}

      {/* Assessment cards */}
      {assessments.length === 0 ? (
        <div className="rounded-lg border border-dashed p-8 text-center">
          <p className="text-sm text-slate-500">
            No assessments have been completed for this candidate yet.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {assessments.map((a) => (
            <AssessmentCard key={a.id} assessment={a} />
          ))}
        </div>
      )}

      {/* Skills Matrix */}
      {id && <SkillsMatrixSection candidateId={id} />}
    </div>
  );
}
