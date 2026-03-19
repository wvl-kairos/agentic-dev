import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Loader2, AlertCircle, User, ChevronRight, Briefcase, Plus, X, Search } from "lucide-react";
import { cn } from "@/lib/utils";
import { useCandidateStore } from "@/stores/candidateStore";
import { useRoleTemplates } from "@/hooks/useRoleTemplates";
import { api } from "@/utils/api";
import type { Candidate, PipelineStage } from "@/types/candidate";
import { OrientationBadge } from "@/components/OrientationBadge";

/** Stage badge styling map. */
const STAGE_BADGE: Record<
  PipelineStage,
  { label: string; bg: string; text: string }
> = {
  initial_interview: { label: "Initial", bg: "bg-teal-100", text: "text-teal-800" },
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
// Add Candidate Modal
// ---------------------------------------------------------------------------

function AddCandidateModal({
  templates,
  onClose,
  onCreated,
}: {
  templates: { id: string; name: string }[];
  onClose: () => void;
  onCreated: () => void;
}) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("");
  const [salaryExpected, setSalaryExpected] = useState("");
  const [roleTemplateId, setRoleTemplateId] = useState("");
  const [recruiterName, setRecruiterName] = useState("");
  const [ventureId, setVentureId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api
      .get<{ id: string }[]>("/ventures/")
      .then((ventures) => {
        if (ventures[0]) setVentureId(ventures[0].id);
      })
      .catch(() => {});
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post("/candidates/", {
        venture_id: ventureId,
        name,
        email: email || undefined,
        role: role || undefined,
        salary_expected: salaryExpected ? parseInt(salaryExpected, 10) : undefined,
        role_template_id: roleTemplateId || undefined,
        recruiter_name: recruiterName || undefined,
      });
      onCreated();
      onClose();
    } catch (_e) {
      // Error handled by API layer; keep modal open
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="rounded-lg border bg-white shadow-xl max-w-md w-full">
        <div className="flex items-center justify-between border-b px-5 py-4">
          <h3 className="text-lg font-semibold text-slate-900">
            Add Candidate
          </h3>
          <button
            onClick={onClose}
            className="rounded-md p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="px-5 py-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Maria Garcia"
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="maria@example.com"
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Role
            </label>
            <input
              type="text"
              value={role}
              onChange={(e) => setRole(e.target.value)}
              placeholder="e.g. Senior Backend Engineer"
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Expected Salary (USD)
            </label>
            <input
              type="number"
              value={salaryExpected}
              onChange={(e) => setSalaryExpected(e.target.value)}
              placeholder="e.g. 80000"
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Role Template
            </label>
            <select
              value={roleTemplateId}
              onChange={(e) => setRoleTemplateId(e.target.value)}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="">None</option>
              {templates.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Recruiter
            </label>
            <input
              type="text"
              value={recruiterName}
              onChange={(e) => setRecruiterName(e.target.value)}
              placeholder="e.g. Clara"
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <div className="flex items-center gap-2 pt-2">
            <button
              type="submit"
              disabled={saving || !name.trim()}
              className={cn(
                "inline-flex items-center gap-1.5 rounded-md px-4 py-2 text-sm font-medium text-white transition-colors",
                saving || !name.trim()
                  ? "bg-slate-300 cursor-not-allowed"
                  : "bg-blue-600 hover:bg-blue-700"
              )}
            >
              {saving && <Loader2 className="h-4 w-4 animate-spin" />}
              Add Candidate
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
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export function CandidatesPage() {
  const { candidates, loading, error, fetchCandidates } = useCandidateStore();
  const { templates, loading: tplLoading } = useRoleTemplates();
  const [showAddModal, setShowAddModal] = useState(false);
  const [searchParams, setSearchParams] = useSearchParams();
  const [searchText, setSearchText] = useState("");

  // Read initial filters from URL params
  const stageFilter = searchParams.get("stage") || "";
  const roleFilter = searchParams.get("role_template_id") || "";
  const recruiterFilter = searchParams.get("recruiter") || "";

  const setStageFilter = (v: string) => {
    const p = new URLSearchParams(searchParams);
    if (v) p.set("stage", v); else p.delete("stage");
    setSearchParams(p, { replace: true });
  };
  const setRoleFilter = (v: string) => {
    const p = new URLSearchParams(searchParams);
    if (v) p.set("role_template_id", v); else p.delete("role_template_id");
    setSearchParams(p, { replace: true });
  };
  const setRecruiterFilter = (v: string) => {
    const p = new URLSearchParams(searchParams);
    if (v) p.set("recruiter", v); else p.delete("recruiter");
    setSearchParams(p, { replace: true });
  };

  useEffect(() => { fetchCandidates(); }, [fetchCandidates]);

  const templateOptions = templates.map((t) => ({ id: t.id, name: t.name }));

  // Unique recruiter names for filter dropdown
  const recruiterNames = useMemo(() => {
    const names = new Set<string>();
    for (const c of candidates) {
      if (c.recruiter_name) names.add(c.recruiter_name);
    }
    return Array.from(names).sort();
  }, [candidates]);

  // Client-side filtering
  const filtered = useMemo(() => {
    let list = candidates;
    if (stageFilter) list = list.filter((c) => c.stage === stageFilter);
    if (roleFilter) list = list.filter((c) => c.role_template_id === roleFilter);
    if (recruiterFilter) list = list.filter((c) => c.recruiter_name === recruiterFilter);
    if (searchText) {
      const q = searchText.toLowerCase();
      list = list.filter(
        (c) =>
          c.name.toLowerCase().includes(q) ||
          (c.email && c.email.toLowerCase().includes(q))
      );
    }
    return list;
  }, [candidates, stageFilter, roleFilter, recruiterFilter, searchText]);

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
            {filtered.length} of {candidates.length} candidate{candidates.length !== 1 && "s"}
          </p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="inline-flex items-center gap-1.5 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
        >
          <Plus className="h-4 w-4" />
          Add Candidate
        </button>
      </div>

      {/* Filter bar */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[200px] max-w-xs">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            placeholder="Search by name or email..."
            className="w-full rounded-md border border-slate-300 pl-9 pr-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>
        <select
          value={stageFilter}
          onChange={(e) => setStageFilter(e.target.value)}
          className="rounded-md border border-slate-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          <option value="">All Stages</option>
          {(Object.keys(STAGE_BADGE) as PipelineStage[]).map((s) => (
            <option key={s} value={s}>{STAGE_BADGE[s].label}</option>
          ))}
        </select>
        <select
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
          className="rounded-md border border-slate-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          <option value="">All Roles</option>
          {templateOptions.map((t) => (
            <option key={t.id} value={t.id}>{t.name}</option>
          ))}
        </select>
        {recruiterNames.length > 0 && (
          <select
            value={recruiterFilter}
            onChange={(e) => setRecruiterFilter(e.target.value)}
            className="rounded-md border border-slate-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="">All Recruiters</option>
            {recruiterNames.map((r) => (
              <option key={r} value={r}>{r}</option>
            ))}
          </select>
        )}
        {(stageFilter || roleFilter || recruiterFilter || searchText) && (
          <button
            onClick={() => {
              setSearchText("");
              setSearchParams({}, { replace: true });
            }}
            className="text-xs text-slate-500 hover:text-slate-700 underline"
          >
            Clear filters
          </button>
        )}
      </div>

      {filtered.length === 0 ? (
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
                  Salary
                </th>
                <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
                  <div className="flex items-center gap-1">
                    <Briefcase className="h-3 w-3" />
                    Role Template
                  </div>
                </th>
                <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Recruiter
                </th>
                <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Orientation
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
              {filtered.map((c) => (
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
                  <td className="px-4 py-3 text-sm text-slate-600 tabular-nums">
                    {c.salary_expected
                      ? `$${c.salary_expected.toLocaleString()}`
                      : <span className="text-slate-300">--</span>}
                  </td>
                  <td className="px-4 py-3 w-48">
                    <RoleTemplateSelector
                      candidate={c}
                      templates={templateOptions}
                      onAssign={handleAssignTemplate}
                    />
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-600">
                    {c.recruiter_name ?? <span className="text-slate-300">--</span>}
                  </td>
                  <td className="px-4 py-3">
                    <OrientationBadge orientation={c.orientation} size="sm" />
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

      {showAddModal && (
        <AddCandidateModal
          templates={templateOptions}
          onClose={() => setShowAddModal(false)}
          onCreated={() => fetchCandidates()}
        />
      )}
    </div>
  );
}
