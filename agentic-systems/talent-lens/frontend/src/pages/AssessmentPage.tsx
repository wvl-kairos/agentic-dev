import { useEffect, useRef, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { Loader2, AlertCircle, ArrowLeft, Upload, X, FileText, DollarSign, Link2, Copy, Check, Info, ExternalLink } from "lucide-react";
import { cn } from "@/lib/utils";
import { api } from "@/utils/api";
import type { PipelineStage } from "@/types/candidate";
import type { InterviewType } from "@/types/interview";
import { useAssessments } from "@/hooks/useAssessments";
import { useCapabilities } from "@/hooks/useCapabilities";
import { PipelineStepper } from "@/components/PipelineStepper";
import { FinalDecisionBox } from "@/components/FinalDecisionBox";
import { AggregateStatsCard } from "@/components/AggregateStatsCard";
import { StageScoreTimeline } from "@/components/StageScoreTimeline";
import { CompactStageCard } from "@/components/CompactStageCard";
import { CoverageTracker } from "@/components/CoverageTracker";
import { CapabilityMatrix } from "@/components/CapabilityMatrix";
import { SkillsRadar } from "@/components/SkillsRadar";
import { OrientationBadge } from "@/components/OrientationBadge";
import type { CandidateSkills } from "@/types/capability";

// ---------------------------------------------------------------------------
// Salary Display
// ---------------------------------------------------------------------------

function SalaryDisplay({
  expected,
  rangeMin,
  rangeMax,
  currency,
}: {
  expected: number | null;
  rangeMin: number | null;
  rangeMax: number | null;
  currency: string | null;
}) {
  if (!expected && !rangeMin) return null;
  const fmt = (n: number) => {
    if (n >= 1000) return `${Math.round(n / 1000)}K`;
    return n.toLocaleString();
  };
  const cur = currency ?? "USD";
  const sym = cur === "USD" ? "$" : cur;

  return (
    <div className="flex items-center gap-1.5 text-sm text-slate-500">
      <DollarSign className="h-3.5 w-3.5" />
      {expected ? (
        <span>
          <span className="font-medium text-slate-700">
            {sym}{expected.toLocaleString()}
          </span>
          {rangeMin != null && rangeMax != null && (
            <span className="text-slate-400">
              {" "}(range: {sym}{fmt(rangeMin)}–{sym}{fmt(rangeMax)})
            </span>
          )}
        </span>
      ) : rangeMin != null && rangeMax != null ? (
        <span className="text-slate-400">
          Range: {sym}{fmt(rangeMin)}–{sym}{fmt(rangeMax)}
        </span>
      ) : null}
    </div>
  );
}

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

  // Build Key Strengths: top capabilities with avg_score >= 3.5
  const COLOR_MAP: Record<string, string> = {
    frontend: "bg-blue-100 text-blue-700",
    backend: "bg-green-100 text-green-700",
    "data-engineering": "bg-purple-100 text-purple-700",
    "data-science-ml": "bg-orange-100 text-orange-700",
    analytics: "bg-pink-100 text-pink-700",
    devops: "bg-cyan-100 text-cyan-700",
    leadership: "bg-amber-100 text-amber-700",
  };

  const strengths = skills.capabilities
    .filter((c) => c.avg_score != null && c.avg_score >= 3.5)
    .sort((a, b) => (b.avg_score ?? 0) - (a.avg_score ?? 0))
    .slice(0, 3)
    .map((capScore) => {
      const cap = capabilities.find((c) => c.id === capScore.capability_id);
      const techs = cap?.technologies?.map((t) => t.name) ?? [];
      return {
        name: capScore.capability_name,
        slug: capScore.capability_slug,
        score: capScore.avg_score!,
        technologies: techs.slice(0, 5),
      };
    });

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
      {strengths.length > 0 && (
        <div className="border-t px-5 py-4">
          <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
            Key Strengths
          </h4>
          <div className="flex flex-wrap gap-2">
            {strengths.map((s) => (
              <div
                key={s.slug}
                className={cn(
                  "rounded-lg px-3 py-1.5 text-xs font-medium",
                  COLOR_MAP[s.slug] ?? "bg-slate-100 text-slate-600"
                )}
              >
                <span className="font-semibold">{s.name}</span>
                {s.technologies.length > 0 && (
                  <span className="ml-1 opacity-75">
                    ({s.technologies.join(", ")})
                  </span>
                )}
                <span className="ml-1.5 opacity-60">{s.score.toFixed(1)}/5</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Upload Interview Modal
// ---------------------------------------------------------------------------

const INTERVIEW_TYPES: { value: InterviewType; label: string }[] = [
  { value: "initial", label: "Initial Interview" },
  { value: "screening", label: "Screening" },
  { value: "coderpad", label: "CoderPad" },
  { value: "technical", label: "Technical" },
  { value: "final", label: "Final" },
];

function stageToInterviewType(stage: PipelineStage): InterviewType {
  switch (stage) {
    case "initial_interview":
      return "initial";
    case "screening":
      return "screening";
    case "coderpad":
      return "coderpad";
    case "technical_interview":
      return "technical";
    case "final_interview":
      return "final";
    default:
      return "screening";
  }
}

/** Parse SRT subtitle format — strip sequence numbers, timestamps, and blank lines. */
function parseSRT(text: string): string {
  return text
    .replace(/\r\n/g, "\n")
    .split("\n\n")
    .map((block) => {
      const lines = block.trim().split("\n");
      // Skip sequence number (first line) and timestamp (second line)
      return lines.filter((_, i) => i >= 2).join(" ");
    })
    .filter(Boolean)
    .join("\n");
}

/** Parse WebVTT format — strip header, timestamps, and cue settings. */
function parseVTT(text: string): string {
  return text
    .replace(/\r\n/g, "\n")
    .replace(/^WEBVTT.*\n\n?/, "") // strip header
    .split("\n\n")
    .map((block) => {
      const lines = block.trim().split("\n");
      // Filter out timestamp lines (contain " --> ")
      return lines.filter((l) => !l.includes(" --> ") && !/^\d+$/.test(l.trim())).join(" ");
    })
    .filter(Boolean)
    .join("\n");
}

function UploadInterviewModal({
  candidateId,
  defaultType,
  onClose,
  onUploaded,
}: {
  candidateId: string;
  defaultType: InterviewType;
  onClose: () => void;
  onUploaded: () => void;
}) {
  const [interviewType, setInterviewType] = useState<InterviewType>(defaultType);
  const [transcript, setTranscript] = useState("");
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState<"idle" | "processing">("idle");
  const [fileName, setFileName] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setFileName(file.name);
    const reader = new FileReader();
    reader.onload = () => {
      const raw = reader.result as string;
      const ext = file.name.split(".").pop()?.toLowerCase();
      if (ext === "srt") {
        setTranscript(parseSRT(raw));
      } else if (ext === "vtt") {
        setTranscript(parseVTT(raw));
      } else {
        setTranscript(raw);
      }
    };
    reader.readAsText(file);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post("/interviews/", {
        candidate_id: candidateId,
        interview_type: interviewType,
        transcript,
        source: "manual",
      });
      setStatus("processing");
      setSaving(false);
      // Give the background pipeline a few seconds, then refetch and close
      setTimeout(() => {
        onUploaded();
        onClose();
      }, 4000);
    } catch (_e) {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="rounded-lg border bg-white shadow-xl max-w-lg w-full">
        <div className="flex items-center justify-between border-b px-5 py-4">
          <h3 className="text-lg font-semibold text-slate-900">
            Upload Interview
          </h3>
          <button
            onClick={onClose}
            className="rounded-md p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {status === "processing" ? (
          <div className="flex flex-col items-center justify-center gap-3 px-5 py-10">
            <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
            <p className="text-sm text-slate-600">
              Processing interview... Assessment will appear shortly.
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="px-5 py-4 space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Interview Type
              </label>
              <select
                value={interviewType}
                onChange={(e) => setInterviewType(e.target.value as InterviewType)}
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                {INTERVIEW_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Upload File
              </label>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="inline-flex items-center gap-1.5 rounded-md border border-slate-300 px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-50 transition-colors"
                >
                  <FileText className="h-4 w-4" />
                  Choose .txt / .srt / .vtt
                </button>
                {fileName && (
                  <span className="text-xs text-slate-500 truncate max-w-[200px]">
                    {fileName}
                  </span>
                )}
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".txt,.srt,.vtt"
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Transcript <span className="text-red-500">*</span>
              </label>
              <textarea
                required
                value={transcript}
                onChange={(e) => setTranscript(e.target.value)}
                placeholder="Paste the interview transcript here..."
                rows={12}
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 resize-y"
              />
            </div>
            <div className="flex items-center gap-2 pt-2">
              <button
                type="submit"
                disabled={saving || !transcript.trim()}
                className={cn(
                  "inline-flex items-center gap-1.5 rounded-md px-4 py-2 text-sm font-medium text-white transition-colors",
                  saving || !transcript.trim()
                    ? "bg-slate-300 cursor-not-allowed"
                    : "bg-blue-600 hover:bg-blue-700"
                )}
              >
                {saving && <Loader2 className="h-4 w-4 animate-spin" />}
                Upload
              </button>
              <button
                type="button"
                onClick={onClose}
                className="inline-flex items-center gap-1.5 rounded-md border px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
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
  const { assessments, candidate, loading, error, refetch } = useAssessments(id!);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [cvUrl, setCvUrl] = useState("");
  const [showCvInput, setShowCvInput] = useState(false);
  const [savingCv, setSavingCv] = useState(false);
  const [shareLink, setShareLink] = useState<string | null>(null);
  const [creatingLink, setCreatingLink] = useState(false);
  const [copied, setCopied] = useState(false);
  const [showScoreInfo, setShowScoreInfo] = useState(false);

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

  // Map interview-type stages (from assessments) to pipeline stages (for stepper)
  const interviewToPipeline: Record<string, string> = {
    initial: "initial_interview",
    screening: "screening",
    coderpad: "coderpad",
    technical: "technical_interview",
    final: "final_interview",
  };
  const completedStages = assessments.map(
    (a) => interviewToPipeline[a.stage] ?? a.stage
  );

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
          {/* Candidate name / role / email / salary + upload button */}
          <div className="mb-4 flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-bold text-slate-900">
                  {candidate.name}
                </h2>
                <OrientationBadge orientation={candidate.orientation} />
              </div>
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
              <div className="mt-1">
                <SalaryDisplay
                  expected={candidate.salary_expected}
                  rangeMin={candidate.role_salary_min}
                  rangeMax={candidate.role_salary_max}
                  currency={candidate.role_salary_currency}
                />
              </div>
            </div>
            <div className="flex items-center gap-2">
              {/* CV URL */}
              {candidate.cv_url ? (
                <a
                  href={candidate.cv_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 rounded-md border px-2.5 py-1.5 text-xs font-medium text-blue-600 hover:bg-blue-50 transition-colors"
                >
                  <ExternalLink className="h-3.5 w-3.5" />
                  View CV
                </a>
              ) : showCvInput ? (
                <div className="flex items-center gap-1">
                  <input
                    type="url"
                    value={cvUrl}
                    onChange={(e) => setCvUrl(e.target.value)}
                    placeholder="Paste CV URL..."
                    className="rounded-md border border-slate-300 px-2 py-1 text-xs w-48 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                  <button
                    onClick={async () => {
                      if (!cvUrl) return;
                      setSavingCv(true);
                      try {
                        await api.patch(`/candidates/${candidate.id}`, { cv_url: cvUrl });
                        refetch();
                        setShowCvInput(false);
                      } finally {
                        setSavingCv(false);
                      }
                    }}
                    disabled={savingCv || !cvUrl}
                    className="rounded-md bg-blue-600 px-2 py-1 text-xs text-white hover:bg-blue-700 disabled:bg-slate-300"
                  >
                    {savingCv ? <Loader2 className="h-3 w-3 animate-spin" /> : "Save"}
                  </button>
                  <button onClick={() => setShowCvInput(false)} className="text-slate-400 hover:text-slate-600">
                    <X className="h-3.5 w-3.5" />
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => setShowCvInput(true)}
                  className="inline-flex items-center gap-1 rounded-md border px-2.5 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50 transition-colors"
                >
                  <FileText className="h-3.5 w-3.5" />
                  Upload CV
                </button>
              )}

              {/* Share Profile */}
              {shareLink ? (
                <div className="flex items-center gap-1">
                  <input
                    readOnly
                    value={shareLink}
                    className="rounded-md border border-slate-300 px-2 py-1 text-xs w-48 bg-slate-50"
                  />
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(shareLink);
                      setCopied(true);
                      setTimeout(() => setCopied(false), 2000);
                    }}
                    className="rounded-md border px-2 py-1 text-xs text-slate-600 hover:bg-slate-50"
                  >
                    {copied ? <Check className="h-3 w-3 text-green-600" /> : <Copy className="h-3 w-3" />}
                  </button>
                  <button onClick={() => setShareLink(null)} className="text-slate-400 hover:text-slate-600">
                    <X className="h-3.5 w-3.5" />
                  </button>
                </div>
              ) : (
                <button
                  onClick={async () => {
                    setCreatingLink(true);
                    try {
                      const resp = await api.post<{ token: string }>("/shared-links/", {
                        candidate_id: candidate.id,
                      });
                      setShareLink(`${window.location.origin}/shared/${resp.token}`);
                    } finally {
                      setCreatingLink(false);
                    }
                  }}
                  disabled={creatingLink}
                  className="inline-flex items-center gap-1 rounded-md border px-2.5 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50 transition-colors"
                >
                  {creatingLink ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Link2 className="h-3.5 w-3.5" />}
                  Share Profile
                </button>
              )}

              <button
                onClick={() => setShowUploadModal(true)}
                className="inline-flex items-center gap-1.5 rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
              >
                <Upload className="h-4 w-4" />
                Upload Interview
              </button>
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

          {/* Score methodology */}
          <div className="mt-3">
            <button
              onClick={() => setShowScoreInfo(!showScoreInfo)}
              className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-slate-600 transition-colors"
            >
              <Info className="h-3.5 w-3.5" />
              How are scores calculated?
            </button>
            {showScoreInfo && (
              <div className="mt-2 rounded-md bg-slate-50 border border-slate-200 p-3 text-xs text-slate-600 space-y-1.5">
                <p><strong>Scoring Scale:</strong> Each criterion is scored 1-5 by Claude based on interview evidence.</p>
                <p><strong>Confidence Multipliers:</strong> Demonstrated (1.0x) = directly shown in interview. Mentioned (0.6x) = discussed but not demonstrated. Claimed (0.3x) = self-reported without evidence.</p>
                <p><strong>Overall Score:</strong> Weighted average of assessed criteria. Not-assessed criteria are excluded from the average.</p>
                <p><strong>Coverage Ratio:</strong> (Assessed criteria / Total required criteria). Higher coverage = more reliable overall score.</p>
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

      {/* Coverage Tracker */}
      {id && <CoverageTracker candidateId={id} />}

      {/* Skills Matrix */}
      {id && <SkillsMatrixSection candidateId={id} />}

      {showUploadModal && candidate && (
        <UploadInterviewModal
          candidateId={candidate.id}
          defaultType={stageToInterviewType(candidate.stage)}
          onClose={() => setShowUploadModal(false)}
          onUploaded={() => refetch()}
        />
      )}
    </div>
  );
}
