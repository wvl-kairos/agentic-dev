import { useState } from "react";
import {
  Monitor,
  Server,
  Database,
  Brain,
  BarChart3,
  Cloud,
  Users,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { Capability } from "@/types/capability";

// ---------------------------------------------------------------------------
// Icon map – maps capability slugs to lucide icons
// ---------------------------------------------------------------------------

const ICON_MAP: Record<string, React.ElementType> = {
  frontend: Monitor,
  backend: Server,
  "data-engineering": Database,
  "data-science-ml": Brain,
  analytics: BarChart3,
  devops: Cloud,
  leadership: Users,
};

function CapabilityIcon({ slug }: { slug: string }) {
  const Icon = ICON_MAP[slug] ?? Monitor;
  return <Icon className="h-4 w-4 text-slate-500" />;
}

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface Requirement {
  capability_id: string;
  required_level: number;
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
// Helpers
// ---------------------------------------------------------------------------

function scoreColor(score: number, required: number): string {
  if (score >= required) return "bg-emerald-500";
  if (score >= required - 1) return "bg-amber-500";
  return "bg-red-500";
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function CapabilityMatrix({
  capabilities,
  requirements,
  scores,
  editable = false,
  onRequirementChange,
}: CapabilityMatrixProps) {
  const [hoveredTooltip, setHoveredTooltip] = useState<string | null>(null);

  const reqMap = new Map(requirements.map((r) => [r.capability_id, r.required_level]));
  const scoreMap = new Map(scores?.map((s) => [s.capability_id, s.avg_score]) ?? []);

  const sorted = [...capabilities].sort((a, b) => a.order - b.order);

  return (
    <div className="space-y-1.5">
      {sorted.map((cap) => {
        const reqLevel = reqMap.get(cap.id) ?? 0;
        const capScore = scoreMap.get(cap.id) ?? null;

        return (
          <div key={cap.id} className="flex items-center gap-3">
            {/* Capability label */}
            <div className="flex items-center gap-2 w-40 min-w-[10rem]">
              <CapabilityIcon slug={cap.slug} />
              <span className="text-sm font-medium text-slate-700 truncate">
                {cap.name}
              </span>
            </div>

            {/* Level dots */}
            <div className="flex items-center gap-1.5">
              {[1, 2, 3, 4, 5].map((level) => {
                const levelData = cap.levels.find((l) => l.level === level);
                const tooltipKey = `${cap.id}-${level}`;
                const isRequired = level <= reqLevel;
                const isScored = capScore != null && level <= Math.round(capScore);

                // Determine the dot color
                let dotColor = "bg-slate-200";
                if (scores && capScore != null && isScored) {
                  dotColor = scoreColor(capScore, reqLevel);
                } else if (!scores && isRequired) {
                  dotColor = "bg-blue-500";
                } else if (scores && isRequired && !isScored) {
                  // Required but not scored — show as outlined blue
                  dotColor = "ring-2 ring-blue-300 bg-white";
                }

                return (
                  <div key={level} className="relative">
                    <button
                      type="button"
                      disabled={!editable}
                      onClick={() => {
                        if (editable && onRequirementChange) {
                          // Toggle: clicking the current level resets to 0
                          const newLevel = reqLevel === level ? 0 : level;
                          onRequirementChange(cap.id, newLevel);
                        }
                      }}
                      onMouseEnter={() => setHoveredTooltip(tooltipKey)}
                      onMouseLeave={() => setHoveredTooltip(null)}
                      className={cn(
                        "h-5 w-5 rounded-full transition-colors",
                        dotColor,
                        editable && "cursor-pointer hover:ring-2 hover:ring-blue-400",
                        !editable && "cursor-default"
                      )}
                    />
                    {/* Tooltip */}
                    {hoveredTooltip === tooltipKey && levelData && (
                      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 z-10 w-48 rounded-md bg-slate-800 px-3 py-2 text-xs text-white shadow-lg pointer-events-none">
                        <p className="font-semibold">
                          Level {level}: {levelData.title}
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
            </div>

            {/* Score number when scores are provided */}
            {scores && (
              <span className="text-xs text-slate-500 tabular-nums w-10 text-right">
                {capScore != null ? capScore.toFixed(1) : "--"}
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
}
