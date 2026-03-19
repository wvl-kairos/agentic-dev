import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Loader2, AlertCircle, Check } from "lucide-react";
import { cn } from "@/lib/utils";
import { api } from "@/utils/api";
import type { RoleTemplate, Capability } from "@/types/capability";

export function SurveyPage() {
  const { roleTemplateId } = useParams<{ roleTemplateId: string }>();
  const [template, setTemplate] = useState<RoleTemplate | null>(null);
  const [capabilities, setCapabilities] = useState<Capability[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [respondentName, setRespondentName] = useState("");
  const [respondentEmail, setRespondentEmail] = useState("");
  const [scores, setScores] = useState<Record<string, number>>({});
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    if (!roleTemplateId) return;
    setLoading(true);
    Promise.all([
      api.get<RoleTemplate>(`/role-templates/${roleTemplateId}`),
      api.get<Capability[]>("/capabilities/"),
    ])
      .then(([tpl, caps]) => {
        setTemplate(tpl);
        setCapabilities(caps);
        // Initialize scores from template requirements
        const initial: Record<string, number> = {};
        for (const req of tpl.requirements) {
          initial[req.capability_id] = 5; // default to middle
        }
        setScores(initial);
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [roleTemplateId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!roleTemplateId) return;
    setSubmitting(true);
    try {
      await api.post(`/surveys/role-template/${roleTemplateId}`, {
        respondent_name: respondentName,
        respondent_email: respondentEmail || null,
        answers: Object.entries(scores).map(([capability_id, score]) => ({
          capability_id,
          score,
        })),
      });
      setSubmitted(true);
    } catch (_e) {
      // handled by API layer
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
        <span className="ml-2 text-slate-500">Loading survey...</span>
      </div>
    );
  }

  if (error || !template) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-4 max-w-md">
          <AlertCircle className="h-5 w-5 text-red-500" />
          <p className="text-sm text-red-700">{error ?? "Survey not found"}</p>
        </div>
      </div>
    );
  }

  if (submitted) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="rounded-lg border bg-white p-8 shadow-sm max-w-md text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100">
            <Check className="h-6 w-6 text-emerald-600" />
          </div>
          <h2 className="text-xl font-bold text-slate-900">Thank you!</h2>
          <p className="mt-2 text-sm text-slate-500">
            Your survey response for <strong>{template.name}</strong> has been submitted.
          </p>
        </div>
      </div>
    );
  }

  // Get capabilities that are required by this template
  const requiredCapIds = new Set(template.requirements.map((r) => r.capability_id));
  const requiredCaps = capabilities.filter((c) => requiredCapIds.has(c.id));

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-2xl mx-auto px-4 py-8">
        <div className="rounded-lg border bg-white p-6 shadow-sm">
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-slate-900">Capabilities Survey</h1>
            <p className="mt-1 text-sm text-slate-500">
              Rate the required skill level (1-10) for each capability in the <strong>{template.name}</strong> role.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Respondent info */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Your Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={respondentName}
                  onChange={(e) => setRespondentName(e.target.value)}
                  placeholder="e.g. Clara"
                  className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Email
                </label>
                <input
                  type="email"
                  value={respondentEmail}
                  onChange={(e) => setRespondentEmail(e.target.value)}
                  placeholder="Optional"
                  className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Capability sliders */}
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wider">
                Required Skill Levels
              </h3>
              {requiredCaps.map((cap) => {
                const score = scores[cap.id] ?? 5;
                return (
                  <div key={cap.id} className="rounded-lg border bg-slate-50 p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <span className="text-sm font-medium text-slate-800">{cap.name}</span>
                        {cap.description && (
                          <p className="text-xs text-slate-400 mt-0.5">{cap.description}</p>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={cn(
                          "text-lg font-bold tabular-nums min-w-[2.5rem] text-center",
                          score >= 7 ? "text-emerald-600" : score >= 4 ? "text-amber-600" : "text-red-600"
                        )}>
                          {score}
                        </span>
                        <span className="text-xs text-slate-400">/10</span>
                      </div>
                    </div>
                    <input
                      type="range"
                      min={1}
                      max={10}
                      value={score}
                      onChange={(e) =>
                        setScores((prev) => ({
                          ...prev,
                          [cap.id]: parseInt(e.target.value, 10),
                        }))
                      }
                      className="w-full h-2 rounded-lg appearance-none cursor-pointer bg-slate-200 accent-blue-600"
                    />
                    <div className="flex justify-between mt-1 text-[10px] text-slate-400">
                      <span>1 - Basic</span>
                      <span>5 - Intermediate</span>
                      <span>10 - Expert</span>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Submit */}
            <div className="flex items-center gap-2 pt-2">
              <button
                type="submit"
                disabled={submitting || !respondentName.trim()}
                className={cn(
                  "inline-flex items-center gap-1.5 rounded-md px-4 py-2 text-sm font-medium text-white transition-colors",
                  submitting || !respondentName.trim()
                    ? "bg-slate-300 cursor-not-allowed"
                    : "bg-blue-600 hover:bg-blue-700"
                )}
              >
                {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
                Submit Survey
              </button>
            </div>
          </form>
        </div>

        <div className="text-center text-xs text-slate-400 py-4 mt-4">
          Powered by TalentLens
        </div>
      </div>
    </div>
  );
}
