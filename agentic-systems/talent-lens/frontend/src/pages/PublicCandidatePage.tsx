import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Loader2, AlertCircle, ExternalLink } from "lucide-react";
import { cn } from "@/lib/utils";
import { api } from "@/utils/api";
import { ScoreBar } from "@/components/ScoreBar";

interface PublicCriterionScore {
  criterion_name: string;
  score: number;
  max_score: number;
  confidence_level: string;
  assessment_status: string;
}

interface PublicAssessment {
  id: string;
  stage: string;
  overall_score: number | null;
  summary: string | null;
  recommendation: string | null;
  criterion_scores: PublicCriterionScore[];
  created_at: string;
}

interface PublicCandidate {
  id: string;
  name: string;
  role: string | null;
  stage: string;
  email: string | null;
  cv_url: string | null;
}

interface PublicData {
  candidate: PublicCandidate;
  assessments: PublicAssessment[];
}

const STAGE_LABELS: Record<string, string> = {
  initial: "Initial",
  screening: "Screening",
  coderpad: "CoderPad",
  technical_interview: "Technical",
  final_interview: "Final",
  decision: "Decision",
};

function scoreColor(score: number | null): string {
  if (score == null) return "text-slate-400";
  if (score >= 4) return "text-emerald-600";
  if (score >= 3) return "text-amber-600";
  return "text-red-600";
}

function recBadge(rec: string | null) {
  if (!rec) return null;
  const lower = rec.toLowerCase();
  let bg = "bg-slate-100 text-slate-700";
  if (lower.includes("strong") && lower.includes("yes")) bg = "bg-emerald-100 text-emerald-800";
  else if (lower.includes("yes") || lower.includes("proceed")) bg = "bg-green-100 text-green-800";
  else if (lower.includes("no") || lower.includes("reject")) bg = "bg-red-100 text-red-800";
  else if (lower.includes("maybe")) bg = "bg-amber-100 text-amber-800";
  return (
    <span className={cn("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold capitalize", bg)}>
      {rec}
    </span>
  );
}

export function PublicCandidatePage() {
  const { token } = useParams<{ token: string }>();
  const [data, setData] = useState<PublicData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    api
      .get<PublicData>(`/shared-links/public/${token}`)
      .then(setData)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [token]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
        <span className="ml-2 text-slate-500">Loading profile...</span>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-4 max-w-md">
          <AlertCircle className="h-5 w-5 text-red-500" />
          <p className="text-sm text-red-700">{error ?? "Profile not found"}</p>
        </div>
      </div>
    );
  }

  const { candidate, assessments } = data;
  const scored = assessments.filter((a) => a.overall_score != null);
  const avgScore = scored.length > 0
    ? scored.reduce((s, a) => s + (a.overall_score ?? 0), 0) / scored.length
    : null;

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">
        {/* Header */}
        <div className="rounded-lg border bg-white p-6 shadow-sm">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-2xl font-bold text-slate-900">{candidate.name}</h1>
              <div className="flex items-center gap-3 mt-1">
                {candidate.role && <span className="text-sm text-slate-500">{candidate.role}</span>}
                {candidate.email && <span className="text-sm text-slate-400">{candidate.email}</span>}
              </div>
              <span className="mt-2 inline-block rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-semibold text-blue-800 capitalize">
                {candidate.stage.replace(/_/g, " ")}
              </span>
            </div>
            <div className="flex items-center gap-2">
              {candidate.cv_url && (
                <a
                  href={candidate.cv_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 rounded-md border px-3 py-1.5 text-sm text-blue-600 hover:bg-blue-50"
                >
                  <ExternalLink className="h-3.5 w-3.5" />
                  View CV
                </a>
              )}
            </div>
          </div>

          {avgScore != null && (
            <div className="mt-4 flex items-center gap-2">
              <span className="text-sm text-slate-500">Overall Score:</span>
              <span className={cn("text-xl font-bold tabular-nums", scoreColor(avgScore))}>
                {avgScore.toFixed(1)}
              </span>
              <span className="text-sm text-slate-400">/5.0</span>
            </div>
          )}
        </div>

        {/* Assessments */}
        {assessments.length === 0 ? (
          <div className="rounded-lg border border-dashed p-8 text-center">
            <p className="text-sm text-slate-500">No assessments available.</p>
          </div>
        ) : (
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-slate-800">Assessment History</h2>
            {assessments.map((a) => (
              <div key={a.id} className="rounded-lg border bg-white shadow-sm overflow-hidden">
                <div className="flex items-center justify-between px-5 py-3 border-b bg-slate-50">
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-semibold text-slate-800">
                      {STAGE_LABELS[a.stage] ?? a.stage}
                    </span>
                    {a.overall_score != null && (
                      <span className={cn("text-sm font-bold tabular-nums", scoreColor(a.overall_score))}>
                        {a.overall_score.toFixed(1)}/5.0
                      </span>
                    )}
                    {recBadge(a.recommendation)}
                  </div>
                  <span className="text-xs text-slate-400">
                    {new Date(a.created_at).toLocaleDateString()}
                  </span>
                </div>
                <div className="px-5 py-4 space-y-3">
                  {a.summary && (
                    <p className="text-sm text-slate-600 leading-relaxed">{a.summary}</p>
                  )}
                  {a.criterion_scores.length > 0 && (
                    <div className="space-y-1.5">
                      {a.criterion_scores
                        .filter((cs) => cs.assessment_status !== "not_assessed")
                        .map((cs) => (
                          <div key={cs.criterion_name} className="flex items-center gap-3">
                            <span className="w-40 text-sm text-slate-700 truncate">{cs.criterion_name}</span>
                            <div className="flex-1">
                              <ScoreBar score={cs.score} maxScore={cs.max_score} />
                            </div>
                          </div>
                        ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="text-center text-xs text-slate-400 py-4">
          Powered by TalentLens
        </div>
      </div>
    </div>
  );
}
