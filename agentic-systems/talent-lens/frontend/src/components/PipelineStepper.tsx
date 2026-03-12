import { Check } from "lucide-react";
import { cn } from "@/lib/utils";
import type { PipelineStage } from "@/types/candidate";

/** Ordered pipeline stages for the stepper (excludes terminal states). */
const PIPELINE_STAGES: { key: PipelineStage; label: string }[] = [
  { key: "initial_interview", label: "Initial" },
  { key: "screening", label: "Screening" },
  { key: "coderpad", label: "CoderPad" },
  { key: "technical_interview", label: "Technical" },
  { key: "final_interview", label: "Final" },
  { key: "decision", label: "Decision" },
];

interface PipelineStepperProps {
  currentStage: PipelineStage;
  /** Stages that have completed assessments */
  completedStages?: PipelineStage[];
}

export function PipelineStepper({
  currentStage,
  completedStages = [],
}: PipelineStepperProps) {
  const isTerminal = currentStage === "hired" || currentStage === "rejected";

  // Find current index; for terminal states, all pipeline stages are "done"
  const currentIdx = isTerminal
    ? PIPELINE_STAGES.length
    : PIPELINE_STAGES.findIndex((s) => s.key === currentStage);

  return (
    <div className="w-full">
      <div className="flex items-center justify-between">
        {PIPELINE_STAGES.map((stage, idx) => {
          const isCompleted = completedStages.includes(stage.key);
          const isCurrent = !isTerminal && idx === currentIdx;

          return (
            <div key={stage.key} className="flex items-center flex-1 last:flex-none">
              {/* Circle + label */}
              <div className="flex flex-col items-center">
                <div
                  className={cn(
                    "flex h-9 w-9 items-center justify-center rounded-full border-2 text-sm font-medium transition-colors",
                    isCompleted &&
                      "border-emerald-500 bg-emerald-500 text-white",
                    isCurrent &&
                      "border-blue-600 bg-blue-600 text-white shadow-md shadow-blue-200",
                    !isCompleted &&
                      !isCurrent &&
                      "border-slate-300 bg-white text-slate-400"
                  )}
                >
                  {isCompleted ? (
                    <Check className="h-4 w-4" />
                  ) : (
                    <span>{idx + 1}</span>
                  )}
                </div>
                <span
                  className={cn(
                    "mt-1.5 text-xs font-medium",
                    isCurrent && "text-blue-700",
                    isCompleted && "text-emerald-700",
                    !isCurrent && !isCompleted && "text-slate-400"
                  )}
                >
                  {stage.label}
                </span>
              </div>

              {/* Connecting line (skip after last) */}
              {idx < PIPELINE_STAGES.length - 1 && (
                <div
                  className={cn(
                    "flex-1 h-0.5 mx-2 mt-[-1rem]",
                    isCompleted ? "bg-emerald-500" : "bg-slate-200"
                  )}
                />
              )}
            </div>
          );
        })}
      </div>

      {/* Terminal badge */}
      {isTerminal && (
        <div className="mt-4 flex justify-center">
          <span
            className={cn(
              "inline-flex items-center gap-1.5 rounded-full px-4 py-1.5 text-sm font-semibold",
              currentStage === "hired" &&
                "bg-emerald-100 text-emerald-800",
              currentStage === "rejected" &&
                "bg-red-100 text-red-800"
            )}
          >
            {currentStage === "hired" ? "Hired" : "Rejected"}
          </span>
        </div>
      )}
    </div>
  );
}
