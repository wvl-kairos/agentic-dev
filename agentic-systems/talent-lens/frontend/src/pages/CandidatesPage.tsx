import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Loader2, AlertCircle, User, ChevronRight, Briefcase } from "lucide-react";
import { cn } from "@/lib/utils";
import { useCandidateStore } from "@/stores/candidateStore";
import { useRoleTemplates } from "@/hooks/useRoleTemplates";
import { api } from "@/utils/api";
import type { Candidate, PipelineStage } from "@/types/candidate";

/** Stage badge styling map. */
const STAGE_BADGE: Record<
  PipelineStage,
  { label: string; bg: string; text: string }
> = {
  screening: { label: "Screening", bg: "bg-blue-100", text: "text-blue-800" },
  coderpad: { label: "CoderPad", bg: "bg-purple-100", text: "text-purple-800" },
  technical_interview: {
    label: "Technical",
    bg: "bg-amber-100",
    text: "text-amber-800",
  },
  final_interview: {
    label: "Final Interview",
    bg: "bg-orange-100",
    text: "text-orange-800",
  },
  decision: { label: "Decision", bg: "bg-slate-100", text: "text-slate-800" },
  hired: { label: "Hired", bg: "bg-emerald-100", text: "text-emerald-800" },
  rejected: { label: "Rejected", bg: "bg-red-100", text: "text-red-800" },
};

function StageBadge({ stage }: { stage: PipelineStage }) {
  const meta = STAGE_BADGE[stage] ?? {
    label: stage,
    bg: "bg-slate-100",
    text: "text-slate-600",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold",
        meta.bg,
        meta.text
      )}
    >
      {meta.label}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Role Template Selector (inline dropdown)
// ---------------------------------------------------------------------------

function RoleTemplateSelector({
  candidate,
  templates,
  onAssign,
}: {
  candidate: Candidate;
  templates: { id: string; name: string }[];
  onAssign: (candidateId: string, templateId: string | null) => Promise<void>;
}) {
  const [saving, setSaving] = useState(false);

  const handleChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value || null;
    setSaving(true);
    try {
      await onAssign(candidate.id, value);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="relative">
      <select
        value={candidate.role_template_id ?? ""}
        onChange={handleChange}
        disabled={saving}
        className={cn(
          "w-full rounded-md border border-slate-200 bg-white px-2 py-1 text-xs transition-colors",
          "focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500",
          saving && "opacity-50 cursor-not-allowed",
          !candidate.role_template_id && "text-slate-400"
        )}
      >
        <option value="">No template</option>
        {templates.map((t) => (
          <option key={t.id} value={t.id}>
            {t.name}
          </option>
        ))}
      </select>
      {saving && (
        <Loader2 className="absolute right-6 top-1.5 h-3 w-3 animate-spin text-slate-400" />
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export function CandidatesPage() {
  const { candidates, loading, error, fetchCandidates } = useCandidateStore();
  const { templates, loading: tplLoading } = useRoleTemplates();

  useEffect(() => { fetchCandidates(); }, [fetchCandidates]);

  const templateOptions = templates.map((t) => ({ id: t.id, name: t.name }));

  const handleAssignTemplate = async (
    candidateId: string,
    templateId: string | null
  ) => {
    await api.patch(`/candidates/${candidateId}`, {
      role_template_id: templateId,
    });
    await fetchCandidates();
  };

  if (loading || tplLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
        <span className="ml-2 text-slate-500">Loading candidates...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-4">
        <AlertCircle className="h-5 w-5 text-red-500" />
        <p className="text-sm text-red-700">Failed to load candidates: {error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Candidates</h2>
          <p className="mt-1 text-sm text-slate-500">
            {candidates.length} candidate{candidates.length !== 1 && "s"} in
            the pipeline
          </p>
        </div>
      </div>

      {candidates.length === 0 ? (
        <div className="rounded-lg border border-dashed p-8 text-center">
          <User className="mx-auto h-10 w-10 text-slate-300" />
          <p className="mt-2 text-sm text-slate-500">
            No candidates yet. Add a candidate to get started.
          </p>
        </div>
      ) : (
        /* Table layout */
        <div className="overflow-hidden rounded-lg border bg-white shadow-sm">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b bg-slate-50">
                <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Candidate
                </th>
                <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Role
                </th>
                <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
                  <div className="flex items-center gap-1">
                    <Briefcase className="h-3 w-3" />
                    Role Template
                  </div>
                </th>
                <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Stage
                </th>
                <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Added
                </th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y">
              {candidates.map((c) => (
                <tr
                  key={c.id}
                  className="group transition-colors hover:bg-slate-50"
                >
                  <td className="px-4 py-3">
                    <Link
                      to={`/assessment/${c.id}`}
                      className="flex items-center gap-3"
                    >
                      <div className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-200 text-sm font-semibold text-slate-600">
                        {c.name
                          .split(" ")
                          .map((n) => n[0])
                          .join("")
                          .slice(0, 2)
                          .toUpperCase()}
                      </div>
                      <div>
                        <p className="font-medium text-slate-900 group-hover:text-blue-700">
                          {c.name}
                        </p>
                        {c.email && (
                          <p className="text-xs text-slate-400">{c.email}</p>
                        )}
                      </div>
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-600">
                    {c.role ?? <span className="text-slate-300">--</span>}
                  </td>
                  <td className="px-4 py-3 w-48">
                    <RoleTemplateSelector
                      candidate={c}
                      templates={templateOptions}
                      onAssign={handleAssignTemplate}
                    />
                  </td>
                  <td className="px-4 py-3">
                    <StageBadge stage={c.stage} />
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-500">
                    {new Date(c.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Link
                      to={`/assessment/${c.id}`}
                      className="inline-flex items-center text-sm text-slate-400 hover:text-blue-600"
                    >
                      View
                      <ChevronRight className="ml-0.5 h-4 w-4" />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
