import { CheckCircle2, XCircle, Clock } from "lucide-react";
import { cn } from "@/lib/utils";
import type { PipelineStage } from "@/types/candidate";

const STAGE_DISPLAY: Record<string, string> = {
  screening: "Screening",
  coderpad: "CoderPad",
  technical_interview: "Technical Interview",
  final_interview: "Final Interview",
  decision: "Decision",
};

interface FinalDecisionBoxProps {
  stage: PipelineStage;
  recommendation: string | null;
  avgScore: number | null;
}

export function FinalDecisionBox({
  stage,
  recommendation: _recommendation,
  avgScore: _avgScore,
}: FinalDecisionBoxProps) {
  if (stage === "hired") {
    return (
      <div
        className={cn(
          "flex h-40 w-44 flex-col items-center justify-center rounded-lg border-2",
          "border-emerald-300 bg-emerald-50"
        )}
      >
        <CheckCircle2 className="h-10 w-10 text-emerald-600" />
        <span className="mt-2 text-lg font-bold text-emerald-700">
          APPROVED
        </span>
        <span className="text-xs text-emerald-500">Final Decision</span>
      </div>
    );
  }

  if (stage === "rejected") {
    return (
      <div
        className={cn(
          "flex h-40 w-44 flex-col items-center justify-center rounded-lg border-2",
          "border-red-300 bg-red-50"
        )}
      >
        <XCircle className="h-10 w-10 text-red-600" />
        <span className="mt-2 text-lg font-bold text-red-700">REJECTED</span>
        <span className="text-xs text-red-500">Final Decision</span>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "flex h-40 w-44 flex-col items-center justify-center rounded-lg border-2",
        "border-slate-200 bg-slate-50"
      )}
    >
      <Clock className="h-10 w-10 text-slate-400" />
      <span className="mt-2 text-lg font-bold text-slate-600">PENDING</span>
      <span className="text-xs text-slate-400">
        {STAGE_DISPLAY[stage] ?? stage}
      </span>
    </div>
  );
}
