import {
  Users,
  UserCheck,
  UserX,
  BarChart3,
  Clock,
  Loader2,
  AlertCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useDashboard } from "@/hooks/useDashboard";
import type { PipelineStage } from "@/types/candidate";

/** Label and color for each pipeline stage card. */
const STAGE_META: Record<PipelineStage, { label: string; bg: string; text: string }> = {
  initial_interview: { label: "Initial", bg: "bg-teal-50", text: "text-teal-700" },
  screening: { label: "Screening", bg: "bg-blue-50", text: "text-blue-700" },
  coderpad: { label: "CoderPad", bg: "bg-purple-50", text: "text-purple-700" },
  technical_interview: {
    label: "Technical",
    bg: "bg-amber-50",
    text: "text-amber-700",
  },
  final_interview: {
    label: "Final Interview",
    bg: "bg-orange-50",
    text: "text-orange-700",
  },
  decision: { label: "Decision", bg: "bg-slate-50", text: "text-slate-700" },
  hired: { label: "Hired", bg: "bg-emerald-50", text: "text-emerald-700" },
  rejected: { label: "Rejected", bg: "bg-red-50", text: "text-red-700" },
};

interface StatCardProps {
  label: string;
  value: string | number;
  icon: React.ElementType;
  accent?: string;
}

function StatCard({ label, value, icon: Icon, accent = "text-slate-700" }: StatCardProps) {
  return (
    <div className="rounded-lg border bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-slate-500">{label}</p>
          <p className={cn("mt-1 text-2xl font-bold tabular-nums", accent)}>
            {value}
          </p>
        </div>
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-100">
          <Icon className="h-5 w-5 text-slate-600" />
        </div>
      </div>
    </div>
  );
}

export function DashboardPage() {
  const { metrics, loading, error } = useDashboard();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
        <span className="ml-2 text-slate-500">Loading dashboard...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-4">
        <AlertCircle className="h-5 w-5 text-red-500" />
        <p className="text-sm text-red-700">Failed to load dashboard: {error}</p>
      </div>
    );
  }

  const { totalCandidates, stageCounts, avgScore } = metrics;

  // Active = everyone not in a terminal state
  const activeCandidates =
    totalCandidates - (stageCounts.hired || 0) - (stageCounts.rejected || 0);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-slate-900">Dashboard</h2>
        <p className="mt-1 text-sm text-slate-500">
          Pipeline overview and hiring metrics
        </p>
      </div>

      {/* Top-level stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Total Candidates"
          value={totalCandidates}
          icon={Users}
        />
        <StatCard
          label="Active in Pipeline"
          value={activeCandidates}
          icon={Clock}
          accent="text-blue-700"
        />
        <StatCard
          label="Hired"
          value={stageCounts.hired}
          icon={UserCheck}
          accent="text-emerald-700"
        />
        <StatCard
          label="Avg Score"
          value={avgScore != null ? avgScore.toFixed(1) : "--"}
          icon={BarChart3}
          accent={
            avgScore != null
              ? avgScore >= 4
                ? "text-emerald-700"
                : avgScore >= 3
                  ? "text-amber-700"
                  : "text-red-700"
              : "text-slate-400"
          }
        />
      </div>

      {/* Stage breakdown */}
      <div>
        <h3 className="mb-3 text-lg font-semibold text-slate-800">
          Candidates by Stage
        </h3>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {(Object.keys(STAGE_META) as PipelineStage[]).map((stage) => {
            const meta = STAGE_META[stage];
            const count = stageCounts[stage] || 0;
            return (
              <div
                key={stage}
                className={cn(
                  "flex items-center justify-between rounded-lg border px-4 py-3",
                  meta.bg
                )}
              >
                <span className={cn("text-sm font-medium", meta.text)}>
                  {meta.label}
                </span>
                <span
                  className={cn(
                    "text-xl font-bold tabular-nums",
                    meta.text
                  )}
                >
                  {count}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Pipeline funnel bar */}
      {totalCandidates > 0 && (
        <div>
          <h3 className="mb-3 text-lg font-semibold text-slate-800">
            Pipeline Funnel
          </h3>
          <div className="space-y-2">
            {(Object.keys(STAGE_META) as PipelineStage[]).map((stage) => {
              const meta = STAGE_META[stage];
              const count = stageCounts[stage] || 0;
              const pct = Math.round((count / totalCandidates) * 100);
              return (
                <div key={stage} className="flex items-center gap-3">
                  <span className="w-28 text-sm font-medium text-slate-600 text-right">
                    {meta.label}
                  </span>
                  <div className="flex-1 h-5 rounded-full bg-slate-100 overflow-hidden">
                    <div
                      className={cn(
                        "h-full rounded-full transition-all",
                        stage === "hired"
                          ? "bg-emerald-500"
                          : stage === "rejected"
                            ? "bg-red-400"
                            : "bg-blue-500"
                      )}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <span className="w-12 text-sm font-medium text-slate-500 tabular-nums">
                    {count}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {totalCandidates === 0 && (
        <div className="rounded-lg border border-dashed p-8 text-center">
          <UserX className="mx-auto h-10 w-10 text-slate-300" />
          <p className="mt-2 text-sm text-slate-500">
            No candidates yet. Start by adding candidates to the pipeline.
          </p>
        </div>
      )}
    </div>
  );
}
