import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { Loader2, AlertCircle, ArrowLeft } from "lucide-react";
import { api } from "@/utils/api";
import { useAssessments } from "@/hooks/useAssessments";
import { useCapabilities } from "@/hooks/useCapabilities";
import { PipelineStepper } from "@/components/PipelineStepper";
import { FinalDecisionBox } from "@/components/FinalDecisionBox";
import { AggregateStatsCard } from "@/components/AggregateStatsCard";
import { StageScoreTimeline } from "@/components/StageScoreTimeline";
import { CompactStageCard } from "@/components/CompactStageCard";
import { CapabilityMatrix } from "@/components/CapabilityMatrix";
import { SkillsRadar } from "@/components/SkillsRadar";
import type { CandidateSkills } from "@/types/capability";

// ---------------------------------------------------------------------------
// Skills Matrix Section (unchanged)
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
        <p className="text-sm text-red-700">
          Failed to load assessment: {error}
        </p>
      </div>
    );
  }

  const completedStages = assessments.map((a) => a.stage);

  const scoredAssessments = assessments.filter(
    (a) => a.overall_score != null
  );
  const avgScore =
    scoredAssessments.length > 0
      ? scoredAssessments.reduce(
          (sum, a) => sum + (a.overall_score ?? 0),
          0
        ) / scoredAssessments.length
      : null;

  // Latest recommendation for the decision box
  const lastIdx = assessments.length - 1;
  const latestRecommendation =
    lastIdx >= 0 ? assessments[lastIdx]!.recommendation : null;

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

      {/* Top section: Candidate info + Decision + Stats */}
      {candidate && (
        <div className="rounded-lg border bg-white p-5 shadow-sm">
          {/* Candidate name / role / email */}
          <div className="mb-4">
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

          {/* Decision box + Aggregate stats side by side */}
          <div className="flex gap-4">
            <FinalDecisionBox
              stage={candidate.stage}
              recommendation={latestRecommendation}
              avgScore={avgScore}
            />
            <div className="flex-1">
              <AggregateStatsCard
                assessments={assessments}
                candidate={candidate}
              />
            </div>
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

      {/* Stage Score Timeline */}
      {assessments.length > 0 && (
        <StageScoreTimeline assessments={assessments} />
      )}

      {/* Stage Details (compact accordion cards) */}
      {assessments.length === 0 ? (
        <div className="rounded-lg border border-dashed p-8 text-center">
          <p className="text-sm text-slate-500">
            No assessments have been completed for this candidate yet.
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Stage Details
          </h3>
          {assessments.map((a) => (
            <CompactStageCard key={a.id} assessment={a} />
          ))}
        </div>
      )}

      {/* Skills Matrix */}
      {id && <SkillsMatrixSection candidateId={id} />}
    </div>
  );
}
