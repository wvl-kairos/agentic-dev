import { useEffect, useState } from "react";
import { AlertTriangle, CheckCircle2, XCircle, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import type { CoverageReport } from "@/types/assessment";
import { api } from "@/utils/api";

const STAGE_LABELS: Record<string, string> = {
  initial: "Initial",
  screening: "Screening",
  coderpad: "CoderPad",
  technical: "Technical",
  final: "Final",
};

interface CoverageTrackerProps {
  candidateId: string;
}

export function CoverageTracker({ candidateId }: CoverageTrackerProps) {
  const [coverage, setCoverage] = useState<CoverageReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    api
      .get<CoverageReport>(`/candidates/${candidateId}/coverage`)
      .then((data) => setCoverage(data))
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [candidateId]);

  if (loading) {
    return (
      <div className="rounded-lg border bg-white p-5 shadow-sm">
        <div className="flex items-center justify-center h-16">
          <Loader2 className="h-5 w-5 animate-spin text-slate-400" />
          <span className="ml-2 text-sm text-slate-500">Loading coverage...</span>
        </div>
      </div>
    );
  }

  if (error || !coverage || coverage.total_required === 0) {
    return null; // silently hide if no data
  }

  const pct = Math.round(coverage.coverage_ratio * 100);
  const isLow = pct < 70;

  return (
    <div className="rounded-lg border bg-white shadow-sm overflow-hidden">
      {/* Header with progress bar */}
      <div className="px-5 py-4 border-b">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-semibold text-slate-800">
            Coverage Tracker
          </h3>
          <span className="text-sm font-bold tabular-nums text-slate-700">
            {pct}%{" "}
            <span className="text-xs font-normal text-slate-400">
              ({coverage.assessed_count}/{coverage.total_required})
            </span>
          </span>
        </div>
        <div className="flex h-2.5 w-full overflow-hidden rounded-full bg-slate-100">
          <div
            className={cn(
              "transition-all rounded-full",
              isLow ? "bg-amber-500" : "bg-emerald-500"
            )}
            style={{ width: `${pct}%` }}
          />
        </div>
        {isLow && (
          <div className="mt-2 flex items-center gap-1.5 text-xs text-amber-600">
            <AlertTriangle className="h-3.5 w-3.5" />
            Coverage below 70% — some skills not yet evaluated
          </div>
        )}
      </div>

      {/* Criteria checklist */}
      <div className="px-5 py-3 divide-y divide-slate-50">
        {coverage.criteria.map((c) => {
          const isAssessed = c.status !== "not_assessed";
          const isPositive = c.status === "assessed_positive";
          return (
            <div
              key={c.criterion_name}
              className={cn(
                "flex items-center gap-3 py-2.5",
                !isAssessed && "opacity-50"
              )}
            >
              {/* Status icon */}
              {isPositive ? (
                <CheckCircle2 className="h-4 w-4 text-emerald-500 flex-shrink-0" />
              ) : isAssessed ? (
                <AlertTriangle className="h-4 w-4 text-amber-500 flex-shrink-0" />
              ) : (
                <XCircle className="h-4 w-4 text-red-400 flex-shrink-0" />
              )}

              {/* Criterion name */}
              <span className="flex-1 text-sm text-slate-700 truncate">
                {c.criterion_name}
              </span>

              {/* Stages where assessed */}
              <span className="text-xs text-slate-400 truncate max-w-[140px]">
                {c.stages.length > 0
                  ? c.stages.map((s) => STAGE_LABELS[s] ?? s).join(", ")
                  : "--"}
              </span>

              {/* Score or Not Assessed */}
              {isAssessed && c.best_score != null ? (
                <span
                  className={cn(
                    "text-sm font-semibold tabular-nums min-w-[36px] text-right",
                    c.best_score / c.max_score >= 0.7
                      ? "text-emerald-600"
                      : c.best_score / c.max_score >= 0.5
                        ? "text-amber-600"
                        : "text-red-600"
                  )}
                >
                  {c.best_score}/{c.max_score}
                </span>
              ) : (
                <span className="text-xs text-slate-400 min-w-[36px] text-right">
                  N/A
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
