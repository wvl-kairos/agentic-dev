import { useDroppable } from "@dnd-kit/core";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Capability, Technology, TechPriority } from "@/types/capability";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface TechRequirementDraft {
  technology_id: string;
  required_level: number;
  priority: TechPriority;
}

interface TechnologyRequirementsProps {
  requirements: TechRequirementDraft[];
  allTechnologies: Technology[];
  capabilities: Capability[];
  onRemove: (techId: string) => void;
  onLevelChange: (techId: string, level: number) => void;
  onPriorityChange: (techId: string, priority: TechPriority) => void;
}

const PRIORITY_OPTIONS: { value: TechPriority; label: string; color: string }[] = [
  { value: "must_have", label: "Must", color: "bg-red-100 text-red-700 border-red-200" },
  { value: "should_have", label: "Should", color: "bg-amber-100 text-amber-700 border-amber-200" },
  { value: "nice_to_have", label: "Nice", color: "bg-slate-100 text-slate-600 border-slate-200" },
];

// ---------------------------------------------------------------------------
// Color map (consistent with palette)
// ---------------------------------------------------------------------------

const COLOR_MAP: Record<string, string> = {
  frontend: "bg-blue-100 text-blue-700",
  backend: "bg-green-100 text-green-700",
  "data-engineering": "bg-purple-100 text-purple-700",
  "data-science-ml": "bg-orange-100 text-orange-700",
  analytics: "bg-pink-100 text-pink-700",
  devops: "bg-cyan-100 text-cyan-700",
  leadership: "bg-amber-100 text-amber-700",
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function findTech(
  allTechnologies: Technology[],
  techId: string
): Technology | undefined {
  return allTechnologies.find((t) => t.id === techId);
}

function findParentCapability(
  capabilities: Capability[],
  capabilityId: string
): Capability | undefined {
  return capabilities.find((c) => c.id === capabilityId);
}

// ---------------------------------------------------------------------------
// Level Dots
// ---------------------------------------------------------------------------

function LevelDots({
  level,
  onChange,
}: {
  level: number;
  onChange: (level: number) => void;
}) {
  return (
    <div className="flex items-center gap-1">
      {[1, 2, 3, 4, 5].map((n) => (
        <button
          key={n}
          type="button"
          onClick={() => onChange(n === level ? 0 : n)}
          className={cn(
            "h-4 w-4 rounded-full transition-colors cursor-pointer hover:ring-2 hover:ring-blue-400",
            n <= level ? "bg-blue-500" : "bg-slate-200"
          )}
          title={`Level ${n}`}
        />
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Requirement Row
// ---------------------------------------------------------------------------

function PrioritySelector({
  value,
  onChange,
}: {
  value: TechPriority;
  onChange: (priority: TechPriority) => void;
}) {
  return (
    <div className="flex items-center rounded-full border border-slate-200 overflow-hidden">
      {PRIORITY_OPTIONS.map((opt) => (
        <button
          key={opt.value}
          type="button"
          onClick={() => onChange(opt.value)}
          className={cn(
            "px-2 py-0.5 text-[10px] font-medium transition-colors",
            value === opt.value ? opt.color : "bg-white text-slate-400 hover:bg-slate-50"
          )}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}

function RequirementRow({
  req,
  allTechnologies,
  capabilities,
  onRemove,
  onLevelChange,
  onPriorityChange,
}: {
  req: TechRequirementDraft;
  allTechnologies: Technology[];
  capabilities: Capability[];
  onRemove: (techId: string) => void;
  onLevelChange: (techId: string, level: number) => void;
  onPriorityChange: (techId: string, priority: TechPriority) => void;
}) {
  const tech = findTech(allTechnologies, req.technology_id);
  const parentCap = tech
    ? findParentCapability(capabilities, tech.capability_id)
    : undefined;
  const capColor = parentCap
    ? (COLOR_MAP[parentCap.slug] ?? "bg-slate-100 text-slate-600")
    : "bg-slate-100 text-slate-600";

  return (
    <div className="flex items-center gap-3 rounded-md border bg-white px-3 py-2">
      {/* Tech name */}
      <span className="text-sm font-semibold text-slate-800 min-w-0 truncate">
        {tech?.name ?? "Unknown"}
      </span>

      {/* Capability badge */}
      {parentCap && (
        <span
          className={cn(
            "shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium",
            capColor
          )}
        >
          {parentCap.name}
        </span>
      )}

      {/* Spacer */}
      <div className="flex-1" />

      {/* Priority selector */}
      <PrioritySelector
        value={req.priority}
        onChange={(p) => onPriorityChange(req.technology_id, p)}
      />

      {/* Level dots */}
      <LevelDots
        level={req.required_level}
        onChange={(level) => onLevelChange(req.technology_id, level)}
      />

      {/* Remove */}
      <button
        type="button"
        onClick={() => onRemove(req.technology_id)}
        className="shrink-0 rounded-md p-1 text-slate-400 hover:bg-red-50 hover:text-red-600 transition-colors"
        title="Remove technology"
      >
        <X className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// TechnologyRequirements
// ---------------------------------------------------------------------------

export function TechnologyRequirements({
  requirements,
  allTechnologies,
  capabilities,
  onRemove,
  onLevelChange,
  onPriorityChange,
}: TechnologyRequirementsProps) {
  const { setNodeRef, isOver } = useDroppable({ id: "tech-drop-zone" });

  return (
    <div
      ref={setNodeRef}
      className={cn(
        "rounded-lg border-2 border-dashed min-h-[12rem] p-3 transition-colors",
        isOver
          ? "border-blue-400 bg-blue-50/50"
          : "border-slate-300 bg-slate-50/50"
      )}
    >
      {requirements.length === 0 ? (
        <div className="flex items-center justify-center h-full min-h-[10rem] text-sm text-slate-400">
          Drag technologies here or click in the palette
        </div>
      ) : (
        <div className="space-y-2">
          {requirements.map((req) => (
            <RequirementRow
              key={req.technology_id}
              req={req}
              allTechnologies={allTechnologies}
              capabilities={capabilities}
              onRemove={onRemove}
              onLevelChange={onLevelChange}
              onPriorityChange={onPriorityChange}
            />
          ))}
        </div>
      )}
    </div>
  );
}
