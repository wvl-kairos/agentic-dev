import { useState } from "react";
import { Loader2, X, ChevronDown, ChevronRight, Clock, Lightbulb, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import { api } from "@/utils/api";
import type { InterviewGuide, InterviewGuideQuestion } from "@/types/capability";

const STAGES = [
  { value: "initial", label: "Initial Interview" },
  { value: "screening", label: "Screening" },
  { value: "coderpad", label: "CoderPad" },
  { value: "technical", label: "Technical Deep-Dive" },
  { value: "final", label: "Final Interview" },
] as const;

const DIFFICULTY_COLORS: Record<string, string> = {
  easy: "bg-green-100 text-green-700",
  medium: "bg-yellow-100 text-yellow-700",
  hard: "bg-red-100 text-red-700",
};

function QuestionCard({ question }: { question: InterviewGuideQuestion }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="rounded-lg border bg-white">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-start gap-3 px-4 py-3 text-left hover:bg-slate-50 transition-colors"
      >
        <div className="mt-0.5 text-slate-400">
          {expanded ? (
            <ChevronDown className="h-4 w-4" />
          ) : (
            <ChevronRight className="h-4 w-4" />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-bold text-slate-400">
              Q{question.number}
            </span>
            <span
              className={cn(
                "rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase",
                DIFFICULTY_COLORS[question.difficulty] ?? "bg-slate-100 text-slate-600"
              )}
            >
              {question.difficulty}
            </span>
            <span className="flex items-center gap-0.5 text-[10px] text-slate-400">
              <Clock className="h-3 w-3" />
              {question.expected_duration_minutes}m
            </span>
          </div>
          <p className="text-sm text-slate-800 leading-relaxed">
            {question.question}
          </p>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {question.evaluates.capabilities.map((cap) => (
              <span
                key={cap}
                className="rounded-full bg-blue-50 px-2 py-0.5 text-[10px] font-medium text-blue-700"
              >
                {cap}
              </span>
            ))}
            {question.evaluates.technologies.map((tech) => (
              <span
                key={tech}
                className="rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-medium text-emerald-700"
              >
                {tech}
              </span>
            ))}
          </div>
        </div>
      </button>

      {expanded && (
        <div className="border-t px-4 py-3 space-y-3">
          <div>
            <h5 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
              What Good Looks Like
            </h5>
            <p className="text-sm text-slate-600 leading-relaxed">
              {question.what_good_looks_like}
            </p>
          </div>
          {question.follow_ups.length > 0 && (
            <div>
              <h5 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                Follow-up Probes
              </h5>
              <ul className="space-y-1.5">
                {question.follow_ups.map((fu, i) => (
                  <li key={i} className="text-sm">
                    <span className="text-slate-800">{fu.probe}</span>
                    <span className="ml-1.5 text-[10px] text-slate-400">
                      Targets: {fu.targets}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function InterviewGuidePanel({
  roleTemplateId,
  defaultStage,
  onClose,
}: {
  roleTemplateId: string;
  defaultStage: string;
  onClose: () => void;
}) {
  const [stage, setStage] = useState(defaultStage);
  const [guide, setGuide] = useState<InterviewGuide | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    setGuide(null);
    try {
      const data = await api.post<InterviewGuide>(
        `/role-templates/${roleTemplateId}/generate-interview-guide?stage=${stage}`,
        {}
      );
      setGuide(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to generate guide");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="rounded-lg border bg-white shadow-xl max-w-2xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between border-b px-5 py-4 shrink-0">
          <h3 className="flex items-center gap-2 text-lg font-semibold text-slate-900">
            <Sparkles className="h-5 w-5 text-blue-500" />
            AI Interview Guide
          </h3>
          <button
            onClick={onClose}
            className="rounded-md p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-3 border-b px-5 py-3 shrink-0">
          <select
            value={stage}
            onChange={(e) => setStage(e.target.value)}
            className="rounded-md border border-slate-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            {STAGES.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
          <button
            onClick={handleGenerate}
            disabled={loading}
            className={cn(
              "inline-flex items-center gap-1.5 rounded-md px-4 py-1.5 text-sm font-medium text-white transition-colors",
              loading
                ? "bg-slate-300 cursor-not-allowed"
                : "bg-blue-600 hover:bg-blue-700"
            )}
          >
            {loading && <Loader2 className="h-4 w-4 animate-spin" />}
            {guide ? "Regenerate" : "Generate"}
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-5 py-4">
          {loading && (
            <div className="flex flex-col items-center justify-center gap-3 py-12">
              <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
              <p className="text-sm text-slate-500">
                Generating interview guide...
              </p>
            </div>
          )}

          {error && !loading && (
            <div className="rounded-md bg-red-50 border border-red-200 p-3 text-sm text-red-700">
              {error}
            </div>
          )}

          {guide && !loading && (
            <div className="space-y-4">
              {/* Summary */}
              <div className="flex items-center gap-4 text-sm text-slate-500">
                <span>
                  <span className="font-medium text-slate-700">{guide.role_name}</span>
                  {" "}&middot; {guide.stage_name}
                </span>
                {guide.estimated_duration_minutes > 0 && (
                  <span className="flex items-center gap-1">
                    <Clock className="h-3.5 w-3.5" />
                    ~{guide.estimated_duration_minutes} min total
                  </span>
                )}
              </div>

              {/* Question cards */}
              <div className="space-y-2">
                {guide.questions.map((q) => (
                  <QuestionCard key={q.number} question={q} />
                ))}
              </div>

              {/* Interviewer Tips */}
              {guide.interviewer_tips.length > 0 && (
                <div className="rounded-lg border bg-amber-50 px-4 py-3">
                  <h4 className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-amber-700 mb-2">
                    <Lightbulb className="h-3.5 w-3.5" />
                    Interviewer Tips
                  </h4>
                  <ul className="space-y-1">
                    {guide.interviewer_tips.map((tip, i) => (
                      <li key={i} className="text-sm text-amber-900">
                        {tip}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {!guide && !loading && !error && (
            <div className="flex flex-col items-center justify-center gap-2 py-12 text-slate-400">
              <p className="text-sm">
                Select a stage and click Generate to create an interview guide.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
