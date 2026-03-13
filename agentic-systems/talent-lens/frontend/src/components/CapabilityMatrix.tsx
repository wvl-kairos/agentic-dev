import { useState } from "react";
import {
  Monitor,
  Server,
  Database,
  Brain,
  BarChart3,
  Cloud,
  Users,
  HeartHandshake,
  Globe,
  Check,
  X,
  Minus,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { Capability } from "@/types/capability";

// ---------------------------------------------------------------------------
// Icon map
// ---------------------------------------------------------------------------

const ICON_MAP: Record<string, React.ElementType> = {
  frontend: Monitor,
  backend: Server,
  "data-engineering": Database,
  "data-science-ml": Brain,
  analytics: BarChart3,
  devops: Cloud,
  leadership: Users,
  "soft-skills": HeartHandshake,
  "cultural-fit": Globe,
};

function CapabilityIcon({ slug }: { slug: string }) {
  const Icon = ICON_MAP[slug] ?? Monitor;
  return <Icon className="h-4 w-4 text-slate-500 flex-shrink-0" />;
}

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface Requirement {
  capability_id: string;
  required_level: number;
  survey_level?: number;
}

interface Score {
  capability_id: string;
  avg_score: number | null;
}

interface CapabilityMatrixProps {
  capabilities: Capability[];
  requirements: Requirement[];
  scores?: Score[];
  editable?: boolean;
  onRequirementChange?: (capability_id: string, level: number) => void;
}

// ---------------------------------------------------------------------------
// Editable Level Selector (for RoleTemplatesPage)
// ---------------------------------------------------------------------------

function EditableSurveyDots({
  cap,
  surveyLevel,
  onRequirementChange,
}: {
  cap: Capability;
  surveyLevel: number;
  onRequirementChange: (capability_id: string, surveyLevel: number) => void;
}) {
  const [hoveredTooltip, setHoveredTooltip] = useState<string | null>(null);

  return (
    <div className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((level) => {
        // Map survey level to capability level for tooltip: ceil(level/2)
        const capLevel = Math.ceil(level / 2);
        const levelData = cap.levels.find((l) => l.level === capLevel);
        const tooltipKey = `${cap.id}-${level}`;
        const isActive = level <= surveyLevel;

        return (
          <div key={level} className="relative">
            <button
              type="button"
              onClick={() => {
                const newLevel = surveyLevel === level ? 0 : level;
                onRequirementChange(cap.id, newLevel);
              }}
              onMouseEnter={() => setHoveredTooltip(tooltipKey)}
              onMouseLeave={() => setHoveredTooltip(null)}
              className={cn(
                "h-4 w-4 rounded-full transition-colors cursor-pointer hover:ring-2 hover:ring-blue-400",
                isActive ? "bg-blue-500" : "bg-slate-200",
                level % 2 === 0 && level < 10 ? "mr-1" : ""
              )}
            />
            {hoveredTooltip === tooltipKey && levelData && (
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 z-10 w-48 rounded-md bg-slate-800 px-3 py-2 text-xs text-white shadow-lg pointer-events-none">
                <p className="font-semibold">
                  {level}/10 → L{capLevel}: {levelData.title}
                </p>
                {levelData.description && (
                  <p className="mt-1 text-slate-300">
                    {levelData.description}
                  </p>
                )}
              </div>
            )}
          </div>
        );
      })}
      {surveyLevel > 0 && (
        <span className="ml-1.5 text-xs font-medium text-blue-600 tabular-nums w-6">
          {surveyLevel}/10
        </span>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Score comparison row (for AssessmentPage)
// ---------------------------------------------------------------------------

function ScoreComparisonRow({
  cap,
  reqLevel,
  capScore,
}: {
  cap: Capability;
  reqLevel: number;
  capScore: number | null;
}) {
  const isRequired = reqLevel > 0;
  const hasScore = capScore != null;

  // Determine status
  let status: "meets" | "close" | "below" | "pending" | "not-required" =
    "not-required";
  if (!isRequired && hasScore) {
    status = "meets"; // bonus skill, always fine
  } else if (isRequired && hasScore) {
    if (capScore >= reqLevel) status = "meets";
    else if (capScore >= reqLevel - 1) status = "close";
    else status = "below";
  } else if (isRequired && !hasScore) {
    status = "pending";
  }

  const barColor = {
    meets: "bg-emerald-500",
    close: "bg-amber-500",
    below: "bg-red-500",
    pending: "bg-slate-200",
    "not-required": "bg-slate-300",
  }[status];

  const statusIcon = {
    meets: <Check className="h-3.5 w-3.5 text-emerald-600" />,
    close: <Minus className="h-3.5 w-3.5 text-amber-600" />,
    below: <X className="h-3.5 w-3.5 text-red-600" />,
    pending: null,
    "not-required": null,
  }[status];

  // Normalized bar: 100% width = required level (or 5 for optional skills)
  const baseline = isRequired ? reqLevel : 5;
  const barPct = hasScore ? Math.min((capScore / baseline) * 100, 100) : 0;

  // Percentage label for how well the candidate meets the requirement
  const fulfillmentPct = isRequired && hasScore
    ? Math.round((capScore / reqLevel) * 100)
    : null;

  return (
    <div className="group py-2 first:pt-0 last:pb-0">
      {/* Row: icon + name + bars + numbers */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 w-44 min-w-[11rem] flex-shrink-0">
          <CapabilityIcon slug={cap.slug} />
          <span
            className="text-sm font-medium text-slate-700 truncate"
            title={cap.name}
          >
            {cap.name}
          </span>
        </div>

        {/* Bar area — normalized: full width = required level */}
        <div className="flex-1 min-w-0">
          <div className="relative h-6 rounded bg-slate-100 overflow-hidden">
            {/* Candidate score bar */}
            {hasScore && (
              <div
                className={cn("h-full rounded transition-all", barColor)}
                style={{ width: `${barPct}%` }}
              />
            )}
          </div>
        </div>

        {/* Numbers + status */}
        <div className="flex items-center gap-2 w-32 flex-shrink-0 justify-end">
          {hasScore ? (
            <span
              className={cn(
                "text-sm font-bold tabular-nums",
                status === "meets"
                  ? "text-emerald-600"
                  : status === "close"
                    ? "text-amber-600"
                    : status === "below"
                      ? "text-red-600"
                      : "text-slate-500"
              )}
            >
              {capScore.toFixed(1)}
            </span>
          ) : (
            <span className="text-xs text-slate-400 italic">
              {isRequired ? "Pending" : ""}
            </span>
          )}

          {isRequired && (
            <span className="text-xs text-slate-400">/ {reqLevel}</span>
          )}

          {fulfillmentPct != null && (
            <span
              className={cn(
                "text-[10px] font-semibold tabular-nums w-8 text-right",
                status === "meets"
                  ? "text-emerald-500"
                  : status === "close"
                    ? "text-amber-500"
                    : "text-red-500"
              )}
            >
              {fulfillmentPct}%
            </span>
          )}

          {statusIcon && (
            <span className="flex-shrink-0">{statusIcon}</span>
          )}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export function CapabilityMatrix({
  capabilities,
  requirements,
  scores,
  editable = false,
  onRequirementChange,
}: CapabilityMatrixProps) {
  const reqMap = new Map(
    requirements.map((r) => [r.capability_id, r.required_level])
  );
  const scoreMap = new Map(
    scores?.map((s) => [s.capability_id, s.avg_score]) ?? []
  );

  const sorted = [...capabilities].sort((a, b) => a.order - b.order);
  const hasAnyScore = scores?.some((s) => s.avg_score != null) ?? false;

  // Build survey-level map from requirements
  const surveyMap = new Map(
    requirements.map((r) => [r.capability_id, r.survey_level ?? r.required_level * 2])
  );

  // ── Editable mode: 10-dot survey scale ──
  if (editable && onRequirementChange) {
    return (
      <div className="space-y-1.5">
        {/* Header */}
        <div className="flex items-center gap-3">
          <div className="w-44 min-w-[11rem]" />
          <div className="flex items-center">
            {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((level) => (
              <span
                key={level}
                className={cn(
                  "flex h-4 w-4 items-center justify-center text-[9px] font-semibold text-slate-400",
                  level % 2 === 0 && level < 10 ? "mr-1.5" : "mr-0.5"
                )}
              >
                {level % 2 === 0 ? level : ""}
              </span>
            ))}
          </div>
        </div>

        {sorted.map((cap) => {
          const currentSurvey = surveyMap.get(cap.id) ?? 0;
          return (
            <div key={cap.id} className="flex items-center gap-3">
              <div className="flex items-center gap-2 w-44 min-w-[11rem]">
                <CapabilityIcon slug={cap.slug} />
                <span
                  className="text-sm font-medium text-slate-700 truncate"
                  title={cap.name}
                >
                  {cap.name}
                </span>
              </div>
              <EditableSurveyDots
                cap={cap}
                surveyLevel={currentSurvey}
                onRequirementChange={onRequirementChange}
              />
            </div>
          );
        })}
      </div>
    );
  }

  // ── Read-only mode: bar comparison (required vs candidate) ──

  // Separate into required and non-required capabilities
  const requiredCaps = sorted.filter(
    (cap) => (reqMap.get(cap.id) ?? 0) > 0
  );
  const optionalCaps = sorted.filter(
    (cap) =>
      (reqMap.get(cap.id) ?? 0) === 0 &&
      (scoreMap.get(cap.id) ?? null) != null
  );

  // ── Template-only view (no scores prop) — clean bars with weight % ──
  if (!scores) {
    if (requiredCaps.length === 0) {
      return (
        <p className="text-xs text-slate-400 italic">
          No capability requirements defined for this role.
        </p>
      );
    }

    // Compute weight percentages that always sum to 100 (largest-remainder method)
    const rawWeights = requiredCaps.map((cap) => {
      const level = reqMap.get(cap.id) ?? 0;
      return Math.max(1, level / 2);
    });
    const totalWeight = rawWeights.reduce((s, w) => s + w, 0);
    const exactPcts = rawWeights.map((w) => (totalWeight > 0 ? (w / totalWeight) * 100 : 0));
    const floored = exactPcts.map(Math.floor);
    let remainder = 100 - floored.reduce((s, v) => s + v, 0);
    const remainders = exactPcts.map((v, i) => ({ i, r: v - (floored[i] ?? 0) }));
    remainders.sort((a, b) => b.r - a.r);
    for (const { i } of remainders) {
      if (remainder <= 0) break;
      floored[i] = (floored[i] ?? 0) + 1;
      remainder--;
    }

    return (
      <div className="divide-y divide-slate-100">
        {requiredCaps.map((cap, idx) => {
          const reqLevel = reqMap.get(cap.id) ?? 0;
          const weightPct = floored[idx];

          return (
            <div key={cap.id} className="flex items-center gap-3 py-2 first:pt-0 last:pb-0">
              <div className="flex items-center gap-2 w-44 min-w-[11rem] flex-shrink-0">
                <CapabilityIcon slug={cap.slug} />
                <span
                  className="text-sm font-medium text-slate-700 truncate"
                  title={cap.name}
                >
                  {cap.name}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <div className="relative h-6 rounded bg-slate-100 overflow-hidden">
                  <div
                    className="h-full rounded bg-blue-400"
                    style={{ width: `${(reqLevel / 5) * 100}%` }}
                  />
                </div>
              </div>
              <div className="w-32 flex-shrink-0 flex items-center justify-end gap-2">
                <span className="text-xs font-medium text-blue-600 tabular-nums">
                  {weightPct}%
                </span>
                <span className="text-xs text-slate-400">
                  L{reqLevel}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Legend */}
      {hasAnyScore && (
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[10px] text-slate-500">
          <span className="flex items-center gap-1.5">
            <span className="inline-block h-2 w-6 rounded bg-emerald-500" />
            Meets / exceeds
          </span>
          <span className="flex items-center gap-1.5">
            <span className="inline-block h-2 w-6 rounded bg-amber-500" />
            Close
          </span>
          <span className="flex items-center gap-1.5">
            <span className="inline-block h-2 w-6 rounded bg-red-500" />
            Below
          </span>
          <span className="text-slate-400">|</span>
          <span>Full bar = meets requirement</span>
        </div>
      )}

      {/* Required capabilities */}
      {requiredCaps.length > 0 && (
        <div className="divide-y divide-slate-100">
          {requiredCaps.map((cap) => (
            <ScoreComparisonRow
              key={cap.id}
              cap={cap}
              reqLevel={reqMap.get(cap.id) ?? 0}
              capScore={scoreMap.get(cap.id) ?? null}
            />
          ))}
        </div>
      )}

      {/* Optional capabilities with scores */}
      {optionalCaps.length > 0 && (
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 mb-2">
            Additional Skills Detected
          </p>
          <div className="divide-y divide-slate-100">
            {optionalCaps.map((cap) => (
              <ScoreComparisonRow
                key={cap.id}
                cap={cap}
                reqLevel={0}
                capScore={scoreMap.get(cap.id) ?? null}
              />
            ))}
          </div>
        </div>
      )}

      {/* No scores yet */}
      {!hasAnyScore && (
        <div>
          {/* Show requirements as simple list */}
          {requiredCaps.length > 0 && (
            <div className="divide-y divide-slate-100">
              {requiredCaps.map((cap) => {
                const reqLevel = reqMap.get(cap.id) ?? 0;
                return (
                  <div key={cap.id} className="flex items-center gap-3 py-2">
                    <div className="flex items-center gap-2 w-44 min-w-[11rem]">
                      <CapabilityIcon slug={cap.slug} />
                      <span className="text-sm font-medium text-slate-700 truncate" title={cap.name}>
                        {cap.name}
                      </span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="relative h-6 rounded bg-slate-100 overflow-hidden">
                        <div
                          className="h-full rounded bg-blue-200"
                          style={{ width: `${(reqLevel / 5) * 100}%` }}
                        />
                      </div>
                    </div>
                    <div className="w-28 flex-shrink-0 text-right">
                      <span className="text-xs text-slate-500">
                        Level {reqLevel} required
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
          <p className="text-xs text-slate-400 italic pt-2">
            Candidate scores will appear after assessments are completed.
          </p>
        </div>
      )}
    </div>
  );
}
