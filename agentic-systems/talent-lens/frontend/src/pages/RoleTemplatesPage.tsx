import { useEffect, useMemo, useState } from "react";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  KeyboardSensor,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import type { DragStartEvent, DragEndEvent } from "@dnd-kit/core";
import {
  Loader2,
  AlertCircle,
  Plus,
  Pencil,
  Trash2,
  X,
  Briefcase,
  FileText,
  Copy,
  Check,
  Search,
  ChevronDown,
  ChevronUp,
  ClipboardList,
  Archive,
  RotateCcw,
  Info,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { api } from "@/utils/api";
import { useCapabilities } from "@/hooks/useCapabilities";
import { useRoleTemplates } from "@/hooks/useRoleTemplates";
import { CapabilityMatrix } from "@/components/CapabilityMatrix";
import { TechnologyPalette, TechChipOverlay } from "@/components/TechnologyPalette";
import { TechnologyRequirements } from "@/components/TechnologyRequirements";
import type { TechRequirementDraft } from "@/components/TechnologyRequirements";
import type { RoleTemplate, Technology, TechPriority } from "@/types/capability";

// ---------------------------------------------------------------------------
// Color map for tech badges on cards
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
// Types
// ---------------------------------------------------------------------------

interface SurveyAggregate {
  capability_id: string;
  capability_name: string;
  avg_score: number;
  response_count: number;
}

interface RequirementDraft {
  capability_id: string;
  required_level: number;
  survey_level?: number;
}

interface TemplateDraft {
  name: string;
  description: string;
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string;
  role_type: string;
  requirements: RequirementDraft[];
  technology_requirements: TechRequirementDraft[];
}

// ---------------------------------------------------------------------------
// Template Form (Create / Edit)
// ---------------------------------------------------------------------------

function TemplateForm({
  capabilities,
  initial,
  onSave,
  onCancel,
  saving,
}: {
  capabilities: import("@/types/capability").Capability[];
  initial: TemplateDraft;
  onSave: (draft: TemplateDraft) => void;
  onCancel: () => void;
  saving: boolean;
}) {
  const [name, setName] = useState(initial.name);
  const [description, setDescription] = useState(initial.description);
  const [salaryMin, setSalaryMin] = useState<string>(initial.salary_min?.toString() ?? "");
  const [salaryMax, setSalaryMax] = useState<string>(initial.salary_max?.toString() ?? "");
  const [salaryCurrency, setSalaryCurrency] = useState(initial.salary_currency);
  const [roleType, setRoleType] = useState(initial.role_type);
  const [requirements, setRequirements] = useState<RequirementDraft[]>(
    initial.requirements
  );
  const [techRequirements, setTechRequirements] = useState<TechRequirementDraft[]>(
    initial.technology_requirements
  );

  // Drag state for overlay
  const [activeDrag, setActiveDrag] = useState<{
    techId: string;
    techName: string;
    capSlug: string;
  } | null>(null);

  // DnD sensors
  const pointerSensor = useSensor(PointerSensor, {
    activationConstraint: { distance: 8 },
  });
  const keyboardSensor = useSensor(KeyboardSensor);
  const sensors = useSensors(pointerSensor, keyboardSensor);

  // Flatten all technologies for name lookups
  const allTechnologies = useMemo(
    () => capabilities.flatMap((c) => c.technologies),
    [capabilities]
  );

  // Build a capability-id-to-slug map for overlay
  const capSlugMap = useMemo(() => {
    const map = new Map<string, string>();
    for (const cap of capabilities) {
      for (const tech of cap.technologies) {
        map.set(tech.id, cap.slug);
      }
    }
    return map;
  }, [capabilities]);

  // Set of used tech ids
  const usedTechIds = useMemo(
    () => new Set(techRequirements.map((r) => r.technology_id)),
    [techRequirements]
  );

  // Filter capabilities for tech palette: only show technologies from selected capabilities
  const selectedCapabilityIds = useMemo(
    () => new Set(requirements.filter((r) => r.required_level > 0).map((r) => r.capability_id)),
    [requirements]
  );

  const filteredCapabilities = useMemo(
    () => capabilities.filter((c) => selectedCapabilityIds.has(c.id)),
    [capabilities, selectedCapabilityIds]
  );

  // Add a technology requirement
  const addTech = (techId: string) => {
    if (usedTechIds.has(techId)) return;
    setTechRequirements((prev) => [
      ...prev,
      { technology_id: techId, required_level: 5, priority: "must_have" as TechPriority },
    ]);
  };

  // Remove a technology requirement
  const removeTech = (techId: string) => {
    setTechRequirements((prev) =>
      prev.filter((r) => r.technology_id !== techId)
    );
  };

  // Change level
  const changeTechLevel = (techId: string, level: number) => {
    if (level === 0) {
      removeTech(techId);
      return;
    }
    setTechRequirements((prev) =>
      prev.map((r) =>
        r.technology_id === techId ? { ...r, required_level: level } : r
      )
    );
  };

  // Change priority
  const changeTechPriority = (techId: string, priority: TechPriority) => {
    setTechRequirements((prev) =>
      prev.map((r) =>
        r.technology_id === techId ? { ...r, priority } : r
      )
    );
  };

  const handleRequirementChange = (capId: string, surveyLevel: number) => {
    const requiredLevel = Math.ceil(surveyLevel / 2);
    setRequirements((prev) => {
      const existing = prev.find((r) => r.capability_id === capId);
      if (existing) {
        if (surveyLevel === 0) {
          // Auto-remove orphaned tech requirements when a capability is deselected
          const cap = capabilities.find((c) => c.id === capId);
          if (cap) {
            const capTechIds = new Set(cap.technologies.map((t) => t.id));
            setTechRequirements((tr) => tr.filter((r) => !capTechIds.has(r.technology_id)));
          }
          return prev.filter((r) => r.capability_id !== capId);
        }
        return prev.map((r) =>
          r.capability_id === capId
            ? { ...r, required_level: requiredLevel, survey_level: surveyLevel }
            : r
        );
      }
      if (surveyLevel > 0) {
        return [...prev, { capability_id: capId, required_level: requiredLevel, survey_level: surveyLevel }];
      }
      return prev;
    });
  };

  // DnD handlers
  const handleDragStart = (event: DragStartEvent) => {
    const data = event.active.data.current as
      | { techId: string; techName: string }
      | undefined;
    if (data) {
      setActiveDrag({
        techId: data.techId,
        techName: data.techName,
        capSlug: capSlugMap.get(data.techId) ?? "",
      });
    }
  };

  const handleDragEnd = (event: DragEndEvent) => {
    if (event.over?.id === "tech-drop-zone" && activeDrag) {
      addTech(activeDrag.techId);
    }
    setActiveDrag(null);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave({
      name,
      description,
      salary_min: salaryMin ? parseInt(salaryMin, 10) : null,
      salary_max: salaryMax ? parseInt(salaryMax, 10) : null,
      salary_currency: salaryCurrency,
      role_type: roleType,
      requirements,
      technology_requirements: techRequirements,
    });
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-lg border bg-white p-5 shadow-sm space-y-5"
    >
      {/* Name */}
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1">
          Template Name
        </label>
        <input
          type="text"
          required
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Senior Backend Engineer"
          className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
      </div>

      {/* Description */}
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1">
          Description
        </label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Brief description of this role..."
          rows={6}
          className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 resize-y"
        />
      </div>

      {/* Role Type + Salary */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">
            Role Type
          </label>
          <input
            type="text"
            value={roleType}
            onChange={(e) => setRoleType(e.target.value)}
            placeholder="e.g. Full-time, Contract"
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">
            Salary Range
          </label>
          <div className="flex items-center gap-2">
            <select
              value={salaryCurrency}
              onChange={(e) => setSalaryCurrency(e.target.value)}
              className="rounded-md border border-slate-300 px-2 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="USD">USD</option>
              <option value="EUR">EUR</option>
              <option value="GBP">GBP</option>
              <option value="MXN">MXN</option>
              <option value="BRL">BRL</option>
            </select>
            <input
              type="number"
              value={salaryMin}
              onChange={(e) => setSalaryMin(e.target.value)}
              placeholder="Min"
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <span className="text-slate-400">–</span>
            <input
              type="number"
              value={salaryMax}
              onChange={(e) => setSalaryMax(e.target.value)}
              placeholder="Max"
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Capability requirements */}
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-2">
          Capability Requirements
        </label>
        <p className="text-xs text-slate-400 mb-3">
          Click a dot to set the required level. Click again to remove.
        </p>
        <CapabilityMatrix
          capabilities={capabilities}
          requirements={requirements}
          editable
          onRequirementChange={handleRequirementChange}
        />
      </div>

      {/* Technology Stack (drag-and-drop) */}
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1">
          Technology Stack
        </label>
        <p className="text-xs text-slate-400 mb-3">
          Click or drag technologies to add them
        </p>

        <DndContext
          sensors={sensors}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
        >
          <div className="flex gap-4">
            {/* Palette (left) */}
            <div className="flex-1 min-w-0">
              {filteredCapabilities.length > 0 ? (
                <TechnologyPalette
                  capabilities={filteredCapabilities}
                  usedTechIds={usedTechIds}
                  onAdd={addTech}
                />
              ) : (
                <div className="rounded-lg border border-dashed p-6 text-center">
                  <p className="text-sm text-slate-400">
                    Select capability requirements above to see available technologies
                  </p>
                </div>
              )}
            </div>

            {/* Drop zone (right) */}
            <div className="flex-1 min-w-0">
              <TechnologyRequirements
                requirements={techRequirements}
                allTechnologies={allTechnologies}
                capabilities={capabilities}
                onRemove={removeTech}
                onLevelChange={changeTechLevel}
                onPriorityChange={changeTechPriority}
              />
            </div>
          </div>

          {/* Drag overlay portal */}
          <DragOverlay dropAnimation={null}>
            {activeDrag ? (
              <TechChipOverlay
                name={activeDrag.techName}
                capSlug={activeDrag.capSlug}
              />
            ) : null}
          </DragOverlay>
        </DndContext>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 pt-2">
        <button
          type="submit"
          disabled={saving || !name.trim()}
          className={cn(
            "inline-flex items-center gap-1.5 rounded-md px-4 py-2 text-sm font-medium text-white transition-colors",
            saving || !name.trim()
              ? "bg-slate-300 cursor-not-allowed"
              : "bg-blue-600 hover:bg-blue-700"
          )}
        >
          {saving && <Loader2 className="h-4 w-4 animate-spin" />}
          Save Template
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="inline-flex items-center gap-1.5 rounded-md border px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}

// ---------------------------------------------------------------------------
// Tech Badge for template cards
// ---------------------------------------------------------------------------

const PRIORITY_LABEL: Record<string, { text: string; cls: string }> = {
  must_have: { text: "Must", cls: "text-red-600" },
  should_have: { text: "Should", cls: "text-amber-600" },
  nice_to_have: { text: "Nice", cls: "text-slate-400" },
};

function TechBadge({
  tech,
  level,
  capSlug,
  priority,
}: {
  tech: Technology;
  level: number;
  capSlug: string;
  priority?: string;
}) {
  const colorClass = COLOR_MAP[capSlug] ?? "bg-slate-100 text-slate-600";
  const prio = priority ? PRIORITY_LABEL[priority] : null;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[11px] font-medium",
        colorClass
      )}
    >
      {tech.name}
      <span className="inline-flex items-center gap-0.5">
        {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((n) => (
          <span
            key={n}
            className={cn(
              "h-1 w-1 rounded-full",
              n <= level ? "bg-current opacity-80" : "bg-current opacity-20"
            )}
          />
        ))}
      </span>
      {prio && (
        <span className={cn("text-[9px] font-semibold", prio.cls)}>
          {prio.text}
        </span>
      )}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Template Card
// ---------------------------------------------------------------------------

function TemplateCard({
  template,
  capabilities,
  onEdit,
  onDelete,
  onGenerateJD,
  generatingJD,
  onToggleStatus,
  onCopySurveyUrl,
  surveyCount,
  onApplySurvey,
  applyingSurvey,
  surveyAggregates,
}: {
  template: RoleTemplate;
  capabilities: import("@/types/capability").Capability[];
  onEdit: () => void;
  onDelete: () => void;
  onGenerateJD: () => void;
  generatingJD: boolean;
  onToggleStatus: () => void;
  onCopySurveyUrl: () => void;
  surveyCount: number;
  onApplySurvey: () => void;
  applyingSurvey: boolean;
  surveyAggregates: SurveyAggregate[];
}) {
  const [descExpanded, setDescExpanded] = useState(false);

  const requirements = template.requirements.map((r) => ({
    capability_id: r.capability_id,
    required_level: r.required_level,
  }));

  // Build a tech catalog + slug map from capabilities
  const techMap = useMemo(() => {
    const map = new Map<string, Technology>();
    for (const cap of capabilities) {
      for (const tech of cap.technologies) {
        map.set(tech.id, tech);
      }
    }
    return map;
  }, [capabilities]);

  const capSlugByTechId = useMemo(() => {
    const map = new Map<string, string>();
    for (const cap of capabilities) {
      for (const tech of cap.technologies) {
        map.set(tech.id, cap.slug);
      }
    }
    return map;
  }, [capabilities]);

  // Group tech requirements by parent capability
  const groupedTechReqs = useMemo(() => {
    const groups = new Map<
      string,
      { capName: string; capSlug: string; items: { tech: Technology; level: number; priority: string }[] }
    >();
    for (const tr of template.technology_requirements) {
      const tech = tr.technology
        ? ({ id: tr.technology.id ?? tr.technology_id, name: tr.technology.name, slug: tr.technology.slug, icon: tr.technology.icon ?? null, capability_id: tr.technology.capability_id ?? "", order: tr.technology.order ?? 0 } as Technology)
        : techMap.get(tr.technology_id);
      if (!tech) continue;

      const capSlug = capSlugByTechId.get(tr.technology_id) ?? "";
      const parentCap = capabilities.find((c) => c.slug === capSlug);
      const capName = parentCap?.name ?? "Other";
      const key = capSlug || "other";

      const displayLevel = Math.min(tr.required_level * 2, 10);
      const existing = groups.get(key);
      if (existing) {
        existing.items.push({ tech, level: displayLevel, priority: tr.priority ?? "must_have" });
      } else {
        groups.set(key, {
          capName,
          capSlug,
          items: [{ tech, level: displayLevel, priority: tr.priority ?? "must_have" }],
        });
      }
    }
    return groups;
  }, [template.technology_requirements, techMap, capSlugByTechId, capabilities]);

  return (
    <div className={cn("rounded-lg border bg-white shadow-sm overflow-hidden", template.status === "closed" && "opacity-70")}>
      <div className="flex items-center justify-between border-b px-5 py-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="text-base font-semibold text-slate-800">
              {template.name}
            </h3>
            {template.role_type && (
              <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-500">
                {template.role_type}
              </span>
            )}
            <span className={cn(
              "rounded-full px-2 py-0.5 text-[10px] font-semibold",
              template.status === "open" ? "bg-emerald-100 text-emerald-700" : "bg-slate-200 text-slate-500"
            )}>
              {template.status === "open" ? "Open" : "Closed"}
            </span>
          </div>
          {template.description && (
            <div className="mt-0.5">
              <p className={cn("text-sm text-slate-500", !descExpanded && "line-clamp-2")}>
                {template.description}
              </p>
              {template.description.length > 120 && (
                <button
                  onClick={() => setDescExpanded(!descExpanded)}
                  className="mt-0.5 text-xs text-blue-600 hover:text-blue-700 inline-flex items-center gap-0.5"
                >
                  {descExpanded ? (
                    <>Show less <ChevronUp className="h-3 w-3" /></>
                  ) : (
                    <>Learn more <ChevronDown className="h-3 w-3" /></>
                  )}
                </button>
              )}
            </div>
          )}
          {(template.salary_min || template.salary_max) && (
            <p className="mt-0.5 text-xs text-slate-400">
              {template.salary_currency}{" "}
              {template.salary_min?.toLocaleString() ?? "–"}
              {" – "}
              {template.salary_max?.toLocaleString() ?? "–"}
            </p>
          )}
        </div>
        <div className="flex items-center gap-1 flex-shrink-0 ml-3">
          <button
            onClick={onCopySurveyUrl}
            className="inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium bg-purple-50 text-purple-600 hover:bg-purple-100 transition-colors"
            title="Share this link to collect team input on skill levels. Click 'Apply' to update requirements."
          >
            <ClipboardList className="h-3.5 w-3.5" />
            Survey{surveyCount > 0 && ` (${surveyCount})`}
          </button>
          {surveyCount > 0 && (
            <button
              onClick={onApplySurvey}
              disabled={applyingSurvey}
              className={cn(
                "inline-flex items-center gap-1 rounded-md px-2 py-1.5 text-xs font-medium transition-colors",
                applyingSurvey
                  ? "bg-slate-100 text-slate-400 cursor-not-allowed"
                  : "bg-green-50 text-green-600 hover:bg-green-100"
              )}
              title="Apply survey results to requirements"
            >
              {applyingSurvey ? <Loader2 className="h-3 w-3 animate-spin" /> : <Check className="h-3 w-3" />}
              Apply
            </button>
          )}
          <button
            onClick={onGenerateJD}
            disabled={generatingJD}
            className={cn(
              "inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium transition-colors",
              generatingJD
                ? "bg-slate-100 text-slate-400 cursor-not-allowed"
                : "bg-blue-50 text-blue-600 hover:bg-blue-100"
            )}
            title="Generate job description"
          >
            {generatingJD ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <FileText className="h-3.5 w-3.5" />
            )}
            JD
          </button>
          <button
            onClick={onToggleStatus}
            className={cn(
              "rounded-md p-1.5 transition-colors",
              template.status === "open"
                ? "text-slate-400 hover:bg-amber-50 hover:text-amber-600"
                : "text-slate-400 hover:bg-emerald-50 hover:text-emerald-600"
            )}
            title={template.status === "open" ? "Close role" : "Reopen role"}
          >
            {template.status === "open" ? <Archive className="h-4 w-4" /> : <RotateCcw className="h-4 w-4" />}
          </button>
          <button
            onClick={onEdit}
            className="rounded-md p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors"
            title="Edit template"
          >
            <Pencil className="h-4 w-4" />
          </button>
          <button
            onClick={onDelete}
            className="rounded-md p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-600 transition-colors"
            title="Delete template"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>
      <div className="px-5 py-4 space-y-4">
        {requirements.length > 0 ? (
          <CapabilityMatrix
            capabilities={capabilities}
            requirements={requirements}
          />
        ) : (
          <p className="text-sm text-slate-400">
            No capability requirements set.
          </p>
        )}

        {/* Technology requirement badges */}
        {groupedTechReqs.size > 0 && (
          <div className="space-y-2 pt-2 border-t">
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">
              Technology Stack
            </p>
            {Array.from(groupedTechReqs.entries()).map(([key, group]) => (
              <div key={key} className="space-y-1">
                <p className="text-xs text-slate-400">{group.capName}</p>
                <div className="flex flex-wrap gap-1.5">
                  {group.items.map((item) => (
                    <TechBadge
                      key={item.tech.id}
                      tech={item.tech}
                      level={item.level}
                      capSlug={group.capSlug}
                      priority={item.priority}
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Survey-Informed Requirements */}
        {surveyAggregates.length > 0 && (
          <div className="space-y-2 pt-2 border-t">
            <div className="flex items-center gap-1.5">
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">
                Survey-Informed Requirements
              </p>
              <span title="Scores from team survey responses. Purple = has survey data, check = applied to requirements." className="cursor-help">
                <Info className="h-3 w-3 text-slate-400" />
              </span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {surveyAggregates.map((agg) => {
                const applied = template.requirements.some(
                  (r) => r.capability_id === agg.capability_id && r.survey_level != null
                );
                return (
                  <span
                    key={agg.capability_id}
                    className="inline-flex items-center gap-1 rounded-full bg-purple-50 border border-purple-200 px-2.5 py-0.5 text-xs font-medium text-purple-700"
                    title={`${agg.response_count} response${agg.response_count !== 1 ? "s" : ""}`}
                  >
                    {agg.capability_name}
                    <span className="text-purple-500">{agg.avg_score}/10</span>
                    {applied && <Check className="h-3 w-3 text-green-600" />}
                  </span>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Job Description Types + Modal
// ---------------------------------------------------------------------------

interface JobDescription {
  title: string;
  summary: string;
  company_summary?: string;
  location?: string;
  about_role: string;
  responsibilities: string[];
  required_qualifications: string[];
  preferred_qualifications: string[];
  tech_stack: string[];
  level: string;
}

function EditableList({
  items,
  onChange,
}: {
  items: string[];
  onChange: (items: string[]) => void;
}) {
  return (
    <div className="space-y-1">
      {items.map((item, i) => (
        <div key={i} className="flex items-center gap-1">
          <input
            type="text"
            value={item}
            onChange={(e) => {
              const next = [...items];
              next[i] = e.target.value;
              onChange(next);
            }}
            className="flex-1 rounded-md border border-slate-300 px-2 py-1 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
          <button
            onClick={() => onChange(items.filter((_, j) => j !== i))}
            className="rounded p-0.5 text-slate-400 hover:text-red-500"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      ))}
      <button
        onClick={() => onChange([...items, ""])}
        className="text-xs text-blue-500 hover:text-blue-700"
      >
        + Add item
      </button>
    </div>
  );
}

function JobDescriptionModal({
  jd,
  onClose,
}: {
  jd: JobDescription;
  onClose: () => void;
}) {
  const [copied, setCopied] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editedJd, setEditedJd] = useState<JobDescription>({ ...jd, responsibilities: [...jd.responsibilities], required_qualifications: [...jd.required_qualifications], preferred_qualifications: [...jd.preferred_qualifications], tech_stack: [...jd.tech_stack] });

  const source = isEditing ? editedJd : jd;

  const plainText = [
    `# ${source.title}`,
    `**Level:** ${source.level}`,
    ...(source.location ? [`**Location:** ${source.location}`] : []),
    "",
    ...(source.company_summary ? ["## About UP Labs", source.company_summary, ""] : []),
    source.summary,
    "",
    "## About the Role",
    source.about_role,
    "",
    "## Responsibilities",
    ...source.responsibilities.map((r) => `- ${r}`),
    "",
    "## Required Qualifications",
    ...source.required_qualifications.map((q) => `- ${q}`),
    ...(source.preferred_qualifications.length > 0
      ? [
          "",
          "## Preferred Qualifications",
          ...source.preferred_qualifications.map((q) => `- ${q}`),
        ]
      : []),
    ...(source.tech_stack.length > 0
      ? ["", "## Tech Stack", ...source.tech_stack.map((t) => `- ${t}`)]
      : []),
  ].join("\n");

  const handleCopy = async () => {
    await navigator.clipboard.writeText(plainText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleReset = () => {
    setEditedJd({ ...jd, responsibilities: [...jd.responsibilities], required_qualifications: [...jd.required_qualifications], preferred_qualifications: [...jd.preferred_qualifications], tech_stack: [...jd.tech_stack] });
  };

  const update = (patch: Partial<JobDescription>) =>
    setEditedJd((prev) => ({ ...prev, ...patch }));

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="rounded-lg border bg-white shadow-xl max-w-2xl w-full max-h-[85vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between border-b px-5 py-4">
          <div className="flex items-center gap-2 min-w-0 flex-1">
            <FileText className="h-5 w-5 text-blue-600 flex-shrink-0" />
            {isEditing ? (
              <input
                type="text"
                value={editedJd.title}
                onChange={(e) => update({ title: e.target.value })}
                className="text-lg font-semibold text-slate-900 border-b border-blue-300 bg-transparent focus:outline-none focus:border-blue-500 w-full"
              />
            ) : (
              <h3 className="text-lg font-semibold text-slate-900">{source.title}</h3>
            )}
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            {isEditing && (
              <button
                onClick={handleReset}
                className="inline-flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors"
                title="Reset to original"
              >
                <RotateCcw className="h-3.5 w-3.5" />
                Reset
              </button>
            )}
            <button
              onClick={handleCopy}
              className="inline-flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors"
            >
              {copied ? (
                <Check className="h-3.5 w-3.5 text-green-600" />
              ) : (
                <Copy className="h-3.5 w-3.5" />
              )}
              {copied ? "Copied" : "Copy"}
            </button>
            <button
              onClick={() => setIsEditing(!isEditing)}
              className={cn(
                "inline-flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-sm font-medium transition-colors",
                isEditing ? "bg-blue-50 text-blue-600 border-blue-200" : "text-slate-600 hover:bg-slate-50"
              )}
            >
              <Pencil className="h-3.5 w-3.5" />
              {isEditing ? "Done" : "Edit"}
            </button>
            <button
              onClick={onClose}
              className="rounded-md p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="overflow-y-auto px-5 py-4 space-y-4 text-sm text-slate-700">
          <div className="flex items-center gap-2">
            <span className="rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-700">
              {source.level}
            </span>
            {source.location && (
              <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-600">
                {source.location}
              </span>
            )}
          </div>

          {(source.company_summary || isEditing) && (
            <div className="rounded-md bg-blue-50 p-3 border border-blue-100">
              <h4 className="font-semibold text-blue-800 mb-1 text-xs uppercase tracking-wide">About UP Labs</h4>
              {isEditing ? (
                <textarea
                  value={editedJd.company_summary ?? ""}
                  onChange={(e) => update({ company_summary: e.target.value })}
                  rows={3}
                  className="w-full rounded-md border border-blue-200 bg-white px-2 py-1 text-sm text-blue-700 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 resize-y"
                />
              ) : (
                <p className="text-blue-700 leading-relaxed text-sm">{source.company_summary}</p>
              )}
            </div>
          )}

          {isEditing ? (
            <textarea
              value={editedJd.summary}
              onChange={(e) => update({ summary: e.target.value })}
              rows={3}
              className="w-full rounded-md border border-slate-300 px-2 py-1 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 resize-y"
            />
          ) : (
            <p className="text-slate-600 leading-relaxed">{source.summary}</p>
          )}

          <div>
            <h4 className="font-semibold text-slate-800 mb-1">About the Role</h4>
            {isEditing ? (
              <textarea
                value={editedJd.about_role}
                onChange={(e) => update({ about_role: e.target.value })}
                rows={4}
                className="w-full rounded-md border border-slate-300 px-2 py-1 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 resize-y"
              />
            ) : (
              <p className="leading-relaxed whitespace-pre-line">{source.about_role}</p>
            )}
          </div>

          <div>
            <h4 className="font-semibold text-slate-800 mb-1">Responsibilities</h4>
            {isEditing ? (
              <EditableList
                items={editedJd.responsibilities}
                onChange={(items) => update({ responsibilities: items })}
              />
            ) : source.responsibilities.length > 0 ? (
              <ul className="list-disc list-inside space-y-0.5">
                {source.responsibilities.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            ) : null}
          </div>

          <div>
            <h4 className="font-semibold text-slate-800 mb-1">Required Qualifications</h4>
            {isEditing ? (
              <EditableList
                items={editedJd.required_qualifications}
                onChange={(items) => update({ required_qualifications: items })}
              />
            ) : source.required_qualifications.length > 0 ? (
              <ul className="list-disc list-inside space-y-0.5">
                {source.required_qualifications.map((q, i) => (
                  <li key={i}>{q}</li>
                ))}
              </ul>
            ) : null}
          </div>

          <div>
            <h4 className="font-semibold text-slate-800 mb-1">Preferred Qualifications</h4>
            {isEditing ? (
              <EditableList
                items={editedJd.preferred_qualifications}
                onChange={(items) => update({ preferred_qualifications: items })}
              />
            ) : source.preferred_qualifications.length > 0 ? (
              <ul className="list-disc list-inside space-y-0.5">
                {source.preferred_qualifications.map((q, i) => (
                  <li key={i}>{q}</li>
                ))}
              </ul>
            ) : null}
          </div>

          <div>
            <h4 className="font-semibold text-slate-800 mb-1">Tech Stack</h4>
            {isEditing ? (
              <div className="flex flex-wrap gap-1.5">
                {editedJd.tech_stack.map((t, i) => (
                  <span
                    key={i}
                    className="inline-flex items-center gap-1 rounded-full bg-slate-100 pl-2.5 pr-1 py-0.5 text-xs font-medium text-slate-600"
                  >
                    <input
                      type="text"
                      value={t}
                      onChange={(e) => {
                        const next = [...editedJd.tech_stack];
                        next[i] = e.target.value;
                        update({ tech_stack: next });
                      }}
                      className="bg-transparent border-none outline-none w-20 text-xs"
                    />
                    <button
                      onClick={() => update({ tech_stack: editedJd.tech_stack.filter((_, j) => j !== i) })}
                      className="rounded-full p-0.5 text-slate-400 hover:text-red-500"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </span>
                ))}
                <button
                  onClick={() => update({ tech_stack: [...editedJd.tech_stack, ""] })}
                  className="rounded-full border border-dashed border-slate-300 px-2.5 py-0.5 text-xs text-blue-500 hover:text-blue-700"
                >
                  + Add
                </button>
              </div>
            ) : source.tech_stack.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {source.tech_stack.map((t, i) => (
                  <span
                    key={i}
                    className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-600"
                  >
                    {t}
                  </span>
                ))}
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Delete Confirmation
// ---------------------------------------------------------------------------

function DeleteConfirm({
  templateName,
  onConfirm,
  onCancel,
  deleting,
}: {
  templateName: string;
  onConfirm: () => void;
  onCancel: () => void;
  deleting: boolean;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="rounded-lg border bg-white p-6 shadow-xl max-w-sm w-full mx-4">
        <div className="flex items-start gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-red-100">
            <AlertCircle className="h-5 w-5 text-red-600" />
          </div>
          <div className="flex-1">
            <h4 className="text-sm font-semibold text-slate-900">
              Delete Template
            </h4>
            <p className="mt-1 text-sm text-slate-500">
              Are you sure you want to delete{" "}
              <span className="font-medium text-slate-700">{templateName}</span>
              ? This action cannot be undone.
            </p>
          </div>
          <button
            onClick={onCancel}
            className="text-slate-400 hover:text-slate-600"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="mt-5 flex justify-end gap-2">
          <button
            onClick={onCancel}
            className="rounded-md border px-3 py-1.5 text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={deleting}
            className={cn(
              "inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium text-white transition-colors",
              deleting
                ? "bg-slate-300 cursor-not-allowed"
                : "bg-red-600 hover:bg-red-700"
            )}
          >
            {deleting && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
            Delete
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export function RoleTemplatesPage() {
  const { capabilities, loading: capsLoading, error: capsError } = useCapabilities();
  const { templates, loading: tplLoading, error: tplError, refetch } = useRoleTemplates();

  const [mode, setMode] = useState<"list" | "create" | "edit">("list");
  const [editingTemplate, setEditingTemplate] = useState<RoleTemplate | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<RoleTemplate | null>(null);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [ventureId, setVentureId] = useState<string | null>(null);
  const [generatingJDFor, setGeneratingJDFor] = useState<string | null>(null);
  const [jobDescription, setJobDescription] = useState<JobDescription | null>(null);
  const [searchText, setSearchText] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | "open" | "closed">("open");
  const [surveyCounts, setSurveyCounts] = useState<Record<string, number>>({});
  const [applyingSurveyFor, setApplyingSurveyFor] = useState<string | null>(null);
  const [surveyAggregates, setSurveyAggregates] = useState<Record<string, SurveyAggregate[]>>({});

  // Fetch first venture for creating templates
  useEffect(() => {
    api
      .get<{ id: string }[]>("/ventures/")
      .then((ventures) => {
        const first = ventures[0];
        if (first) {
          setVentureId(first.id);
        }
      })
      .catch(() => {
        // Ignore — will use a fallback
      });
  }, []);

  const loading = capsLoading || tplLoading;
  const error = capsError || tplError;

  // Fetch survey counts for all templates
  // NOTE: all hooks must be before any early returns
  useEffect(() => {
    for (const tpl of templates) {
      api
        .get<{ id: string }[]>(`/surveys/role-template/${tpl.id}`)
        .then((data) => {
          setSurveyCounts((prev) => ({ ...prev, [tpl.id]: data.length }));
        })
        .catch(() => {});
    }
  }, [templates]);

  // Fetch survey aggregates for all templates
  useEffect(() => {
    for (const tpl of templates) {
      api
        .get<SurveyAggregate[]>(`/surveys/role-template/${tpl.id}/aggregate`)
        .then((data) => {
          setSurveyAggregates((prev) => ({ ...prev, [tpl.id]: data }));
        })
        .catch(() => {});
    }
  }, [templates]);

  // Filter templates
  const filteredTemplates = useMemo(() => {
    let list = templates;
    if (statusFilter !== "all") {
      list = list.filter((t) => t.status === statusFilter);
    }
    if (searchText) {
      const q = searchText.toLowerCase();
      list = list.filter((t) => t.name.toLowerCase().includes(q));
    }
    return list;
  }, [templates, statusFilter, searchText]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
        <span className="ml-2 text-slate-500">Loading role templates...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-4">
        <AlertCircle className="h-5 w-5 text-red-500" />
        <p className="text-sm text-red-700">Failed to load data: {error}</p>
      </div>
    );
  }

  const emptyDraft: TemplateDraft = {
    name: "",
    description: "",
    salary_min: null,
    salary_max: null,
    salary_currency: "USD",
    role_type: "",
    requirements: [],
    technology_requirements: [],
  };

  const editDraft: TemplateDraft | null = editingTemplate
    ? {
        name: editingTemplate.name,
        description: editingTemplate.description ?? "",
        salary_min: editingTemplate.salary_min ?? null,
        salary_max: editingTemplate.salary_max ?? null,
        salary_currency: editingTemplate.salary_currency ?? "USD",
        role_type: editingTemplate.role_type ?? "",
        requirements: editingTemplate.requirements.map((r) => ({
          capability_id: r.capability_id,
          required_level: r.required_level,
          survey_level: r.survey_level ?? r.required_level * 2,
        })),
        technology_requirements: editingTemplate.technology_requirements.map(
          (tr) => ({
            technology_id: tr.technology_id,
            required_level: Math.min(tr.required_level * 2, 10),
            priority: (tr.priority ?? "must_have") as TechPriority,
          })
        ),
      }
    : null;

  const handleCreate = async (draft: TemplateDraft) => {
    setSaving(true);
    try {
      await api.post("/role-templates/", {
        venture_id: ventureId,
        name: draft.name,
        description: draft.description || null,
        salary_min: draft.salary_min,
        salary_max: draft.salary_max,
        salary_currency: draft.salary_currency,
        role_type: draft.role_type || null,
        requirements: draft.requirements.map((r) => ({
          capability_id: r.capability_id,
          required_level: r.required_level,
          survey_level: r.survey_level ?? r.required_level * 2,
        })),
        technology_requirements: draft.technology_requirements.map((tr) => ({
          technology_id: tr.technology_id,
          required_level: Math.ceil(tr.required_level / 2),
          priority: tr.priority ?? "must_have",
        })),
      });
      setMode("list");
      refetch();
    } catch (_e) {
      // Error is handled by the API layer; keep form open
    } finally {
      setSaving(false);
    }
  };

  const handleUpdate = async (draft: TemplateDraft) => {
    if (!editingTemplate) return;
    setSaving(true);
    try {
      await api.put(`/role-templates/${editingTemplate.id}`, {
        name: draft.name,
        description: draft.description || null,
        salary_min: draft.salary_min,
        salary_max: draft.salary_max,
        salary_currency: draft.salary_currency,
        role_type: draft.role_type || null,
        requirements: draft.requirements.map((r) => ({
          capability_id: r.capability_id,
          required_level: r.required_level,
          survey_level: r.survey_level ?? r.required_level * 2,
        })),
        technology_requirements: draft.technology_requirements.map((tr) => ({
          technology_id: tr.technology_id,
          required_level: Math.ceil(tr.required_level / 2),
          priority: tr.priority ?? "must_have",
        })),
      });
      setMode("list");
      setEditingTemplate(null);
      refetch();
    } catch (_e) {
      // Keep form open on error
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await api.del(`/role-templates/${deleteTarget.id}`);
      setDeleteTarget(null);
      refetch();
    } catch (_e) {
      // Keep modal open on error
    } finally {
      setDeleting(false);
    }
  };

  const handleToggleStatus = async (tpl: RoleTemplate) => {
    const newStatus = tpl.status === "open" ? "closed" : "open";
    await api.put(`/role-templates/${tpl.id}`, { status: newStatus });
    refetch();
  };

  const handleCopySurveyUrl = (templateId: string) => {
    const url = `${window.location.origin}/survey/${templateId}`;
    navigator.clipboard.writeText(url);
  };

  const handleApplySurvey = async (templateId: string) => {
    setApplyingSurveyFor(templateId);
    try {
      await api.post(`/surveys/role-template/${templateId}/apply`, {});
      refetch();
    } catch (_e) {
      // handled by API layer
    } finally {
      setApplyingSurveyFor(null);
    }
  };

  const handleGenerateJD = async (templateId: string) => {
    setGeneratingJDFor(templateId);
    try {
      const jd = await api.post<JobDescription>(
        `/role-templates/${templateId}/generate-jd`,
        {}
      );
      setJobDescription(jd);
    } catch (_e) {
      // Error handled by API layer
    } finally {
      setGeneratingJDFor(null);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Role Templates</h2>
          <p className="mt-1 text-sm text-slate-500">
            Define capability requirements for engineering roles
          </p>
        </div>
        {mode === "list" && (
          <button
            onClick={() => setMode("create")}
            className="inline-flex items-center gap-1.5 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
          >
            <Plus className="h-4 w-4" />
            Create Template
          </button>
        )}
      </div>

      {/* Search + Status Filter */}
      {mode === "list" && (
        <div className="flex items-center gap-3">
          <div className="relative flex-1 max-w-xs">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              placeholder="Search templates..."
              className="w-full rounded-md border border-slate-300 pl-9 pr-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <div className="flex rounded-md border border-slate-300 overflow-hidden text-sm">
            {(["open", "closed", "all"] as const).map((s) => (
              <button
                key={s}
                onClick={() => setStatusFilter(s)}
                className={cn(
                  "px-3 py-1.5 font-medium capitalize transition-colors",
                  statusFilter === s
                    ? "bg-blue-600 text-white"
                    : "bg-white text-slate-600 hover:bg-slate-50"
                )}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Create form */}
      {mode === "create" && (
        <TemplateForm
          capabilities={capabilities}
          initial={emptyDraft}
          onSave={handleCreate}
          onCancel={() => setMode("list")}
          saving={saving}
        />
      )}

      {/* Edit form */}
      {mode === "edit" && editDraft && (
        <TemplateForm
          capabilities={capabilities}
          initial={editDraft}
          onSave={handleUpdate}
          onCancel={() => {
            setMode("list");
            setEditingTemplate(null);
          }}
          saving={saving}
        />
      )}

      {/* Template list */}
      {mode === "list" && (
        <>
          {filteredTemplates.length === 0 ? (
            <div className="rounded-lg border border-dashed p-8 text-center">
              <Briefcase className="mx-auto h-10 w-10 text-slate-300" />
              <p className="mt-2 text-sm text-slate-500">
                {templates.length === 0
                  ? "No role templates yet. Create one to define capability requirements."
                  : "No templates match your filters."}
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredTemplates.map((tpl) => (
                <TemplateCard
                  key={tpl.id}
                  template={tpl}
                  capabilities={capabilities}
                  onEdit={() => {
                    setEditingTemplate(tpl);
                    setMode("edit");
                  }}
                  onDelete={() => setDeleteTarget(tpl)}
                  onGenerateJD={() => handleGenerateJD(tpl.id)}
                  generatingJD={generatingJDFor === tpl.id}
                  onToggleStatus={() => handleToggleStatus(tpl)}
                  onCopySurveyUrl={() => handleCopySurveyUrl(tpl.id)}
                  surveyCount={surveyCounts[tpl.id] ?? 0}
                  onApplySurvey={() => handleApplySurvey(tpl.id)}
                  applyingSurvey={applyingSurveyFor === tpl.id}
                  surveyAggregates={surveyAggregates[tpl.id] ?? []}
                />
              ))}
            </div>
          )}
        </>
      )}

      {/* Delete confirmation modal */}
      {deleteTarget && (
        <DeleteConfirm
          templateName={deleteTarget.name}
          onConfirm={handleDelete}
          onCancel={() => setDeleteTarget(null)}
          deleting={deleting}
        />
      )}

      {/* Job description modal */}
      {jobDescription && (
        <JobDescriptionModal
          jd={jobDescription}
          onClose={() => setJobDescription(null)}
        />
      )}
    </div>
  );
}
