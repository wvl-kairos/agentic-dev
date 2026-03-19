import { cn } from "@/lib/utils";
import type { ConfidenceLevel, AssessmentStatus } from "@/types/assessment";

export const CONFIDENCE_STYLES: Record<ConfidenceLevel, { label: string; className: string }> = {
  demonstrated: { label: "Demonstrated", className: "bg-emerald-100 text-emerald-700" },
  mentioned: { label: "Mentioned", className: "bg-amber-100 text-amber-700" },
  claimed: { label: "Claimed", className: "bg-red-100 text-red-700" },
  not_assessed: { label: "Not Assessed", className: "bg-slate-100 text-slate-500" },
};

export function ConfidenceBadge({ level }: { level?: ConfidenceLevel }) {
  if (!level) return null;
  const style = CONFIDENCE_STYLES[level];
  return (
    <span className={cn("inline-flex items-center rounded-full px-1.5 py-0.5 text-[10px] font-semibold", style.className)}>
      {style.label}
    </span>
  );
}

export function AssessmentStatusBadge({ status }: { status?: AssessmentStatus }) {
  if (!status || status === "assessed_positive" || status === "assessed_negative") return null;
  return (
    <span className="inline-flex items-center rounded-full bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold text-slate-500">
      Not Assessed
    </span>
  );
}
