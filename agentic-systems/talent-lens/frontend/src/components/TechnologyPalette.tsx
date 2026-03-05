import { useState } from "react";
import { useDraggable } from "@dnd-kit/core";
import {
  Monitor,
  Server,
  Database,
  Brain,
  BarChart3,
  Cloud,
  Users,
  Search,
  GripVertical,
  ChevronDown,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { Capability, Technology } from "@/types/capability";

// ---------------------------------------------------------------------------
// Icon + color maps (consistent with CapabilityMatrix)
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
// Draggable Tech Chip
// ---------------------------------------------------------------------------

function DraggableTechChip({
  tech,
  capSlug,
  used,
  onAdd,
}: {
  tech: Technology;
  capSlug: string;
  used: boolean;
  onAdd: (techId: string) => void;
}) {
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
    id: `tech-${tech.id}`,
    data: { techId: tech.id, techName: tech.name },
    disabled: used,
  });

  const colorClass = COLOR_MAP[capSlug] ?? "bg-slate-100 text-slate-700";

  return (
    <button
      ref={setNodeRef}
      type="button"
      onClick={() => {
        if (!used) onAdd(tech.id);
      }}
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium transition-colors select-none",
        colorClass,
        used && "opacity-40 pointer-events-none",
        isDragging && "opacity-50",
        !used && "cursor-grab hover:ring-2 hover:ring-blue-300 active:cursor-grabbing"
      )}
      {...listeners}
      {...attributes}
    >
      <GripVertical className="h-3 w-3 opacity-50" />
      {tech.name}
    </button>
  );
}

// ---------------------------------------------------------------------------
// Palette chip (non-draggable, used in DragOverlay)
// ---------------------------------------------------------------------------

export function TechChipOverlay({
  name,
  capSlug,
}: {
  name: string;
  capSlug?: string;
}) {
  const colorClass = COLOR_MAP[capSlug ?? ""] ?? "bg-slate-100 text-slate-700";
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium shadow-lg ring-2 ring-blue-400",
        colorClass
      )}
    >
      <GripVertical className="h-3 w-3 opacity-50" />
      {name}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Collapsible Capability Group
// ---------------------------------------------------------------------------

function CapabilityGroup({
  capability,
  usedTechIds,
  onAdd,
  filterText,
}: {
  capability: Capability;
  usedTechIds: Set<string>;
  onAdd: (techId: string) => void;
  filterText: string;
}) {
  const [expanded, setExpanded] = useState(true);
  const Icon = ICON_MAP[capability.slug] ?? Monitor;

  const filteredTechs = capability.technologies.filter((t) =>
    t.name.toLowerCase().includes(filterText.toLowerCase())
  );

  if (filteredTechs.length === 0) return null;

  return (
    <div>
      <button
        type="button"
        onClick={() => setExpanded((prev) => !prev)}
        className="flex items-center gap-2 w-full py-1.5 px-1 rounded hover:bg-slate-50 transition-colors"
      >
        {expanded ? (
          <ChevronDown className="h-3.5 w-3.5 text-slate-400" />
        ) : (
          <ChevronRight className="h-3.5 w-3.5 text-slate-400" />
        )}
        <Icon className="h-4 w-4 text-slate-500" />
        <span className="text-sm font-medium text-slate-700">
          {capability.name}
        </span>
        <span className="text-xs text-slate-400 ml-auto">
          {filteredTechs.length}
        </span>
      </button>

      {expanded && (
        <div className="flex flex-wrap gap-1.5 pl-7 pt-1 pb-2">
          {filteredTechs.map((tech) => (
            <DraggableTechChip
              key={tech.id}
              tech={tech}
              capSlug={capability.slug}
              used={usedTechIds.has(tech.id)}
              onAdd={onAdd}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// TechnologyPalette
// ---------------------------------------------------------------------------

interface TechnologyPaletteProps {
  capabilities: Capability[];
  usedTechIds: Set<string>;
  onAdd: (techId: string) => void;
}

export function TechnologyPalette({
  capabilities,
  usedTechIds,
  onAdd,
}: TechnologyPaletteProps) {
  const [search, setSearch] = useState("");

  const sorted = [...capabilities].sort((a, b) => a.order - b.order);

  return (
    <div className="rounded-lg border bg-white">
      {/* Search */}
      <div className="relative px-3 pt-3 pb-2">
        <Search className="absolute left-5.5 top-5.5 h-4 w-4 text-slate-400 pointer-events-none" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search technologies..."
          className="w-full rounded-md border border-slate-300 pl-8 pr-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
      </div>

      {/* Groups */}
      <div className="max-h-80 overflow-y-auto px-3 pb-3 space-y-0.5">
        {sorted.map((cap) => (
          <CapabilityGroup
            key={cap.id}
            capability={cap}
            usedTechIds={usedTechIds}
            onAdd={onAdd}
            filterText={search}
          />
        ))}
      </div>
    </div>
  );
}
