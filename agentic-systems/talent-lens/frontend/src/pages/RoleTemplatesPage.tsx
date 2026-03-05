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
} from "lucide-react";
import { cn } from "@/lib/utils";
import { api } from "@/utils/api";
import { useCapabilities } from "@/hooks/useCapabilities";
import { useRoleTemplates } from "@/hooks/useRoleTemplates";
import { CapabilityMatrix } from "@/components/CapabilityMatrix";
import { TechnologyPalette, TechChipOverlay } from "@/components/TechnologyPalette";
import { TechnologyRequirements } from "@/components/TechnologyRequirements";
import type { TechRequirementDraft } from "@/components/TechnologyRequirements";
import type { RoleTemplate, Technology } from "@/types/capability";

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

interface RequirementDraft {
  capability_id: string;
  required_level: number;
}

interface TemplateDraft {
  name: string;
  description: string;
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

  // Add a technology requirement
  const addTech = (techId: string) => {
    if (usedTechIds.has(techId)) return;
    setTechRequirements((prev) => [
      ...prev,
      { technology_id: techId, required_level: 3 },
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

  const handleRequirementChange = (capId: string, level: number) => {
    setRequirements((prev) => {
      const existing = prev.find((r) => r.capability_id === capId);
      if (existing) {
        if (level === 0) {
          return prev.filter((r) => r.capability_id !== capId);
        }
        return prev.map((r) =>
          r.capability_id === capId ? { ...r, required_level: level } : r
        );
      }
      if (level > 0) {
        return [...prev, { capability_id: capId, required_level: level }];
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
          rows={2}
          className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none"
        />
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
              <TechnologyPalette
                capabilities={capabilities}
                usedTechIds={usedTechIds}
                onAdd={addTech}
              />
            </div>

            {/* Drop zone (right) */}
            <div className="flex-1 min-w-0">
              <TechnologyRequirements
                requirements={techRequirements}
                allTechnologies={allTechnologies}
                capabilities={capabilities}
                onRemove={removeTech}
                onLevelChange={changeTechLevel}
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

function TechBadge({
  tech,
  level,
  capSlug,
}: {
  tech: Technology;
  level: number;
  capSlug: string;
}) {
  const colorClass = COLOR_MAP[capSlug] ?? "bg-slate-100 text-slate-600";

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[11px] font-medium",
        colorClass
      )}
    >
      {tech.name}
      <span className="inline-flex items-center gap-0.5">
        {[1, 2, 3, 4, 5].map((n) => (
          <span
            key={n}
            className={cn(
              "h-1.5 w-1.5 rounded-full",
              n <= level ? "bg-current opacity-80" : "bg-current opacity-20"
            )}
          />
        ))}
      </span>
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
}: {
  template: RoleTemplate;
  capabilities: import("@/types/capability").Capability[];
  onEdit: () => void;
  onDelete: () => void;
}) {
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
      { capName: string; capSlug: string; items: { tech: Technology; level: number }[] }
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

      const existing = groups.get(key);
      if (existing) {
        existing.items.push({ tech, level: tr.required_level });
      } else {
        groups.set(key, {
          capName,
          capSlug,
          items: [{ tech, level: tr.required_level }],
        });
      }
    }
    return groups;
  }, [template.technology_requirements, techMap, capSlugByTechId, capabilities]);

  return (
    <div className="rounded-lg border bg-white shadow-sm overflow-hidden">
      <div className="flex items-center justify-between border-b px-5 py-4">
        <div>
          <h3 className="text-base font-semibold text-slate-800">
            {template.name}
          </h3>
          {template.description && (
            <p className="mt-0.5 text-sm text-slate-500">
              {template.description}
            </p>
          )}
        </div>
        <div className="flex items-center gap-1">
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
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
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
    requirements: [],
    technology_requirements: [],
  };

  const editDraft: TemplateDraft | null = editingTemplate
    ? {
        name: editingTemplate.name,
        description: editingTemplate.description ?? "",
        requirements: editingTemplate.requirements.map((r) => ({
          capability_id: r.capability_id,
          required_level: r.required_level,
        })),
        technology_requirements: editingTemplate.technology_requirements.map(
          (tr) => ({
            technology_id: tr.technology_id,
            required_level: tr.required_level,
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
        requirements: draft.requirements,
        technology_requirements: draft.technology_requirements,
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
        requirements: draft.requirements,
        technology_requirements: draft.technology_requirements,
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
          {templates.length === 0 ? (
            <div className="rounded-lg border border-dashed p-8 text-center">
              <Briefcase className="mx-auto h-10 w-10 text-slate-300" />
              <p className="mt-2 text-sm text-slate-500">
                No role templates yet. Create one to define capability
                requirements.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {templates.map((tpl) => (
                <TemplateCard
                  key={tpl.id}
                  template={tpl}
                  capabilities={capabilities}
                  onEdit={() => {
                    setEditingTemplate(tpl);
                    setMode("edit");
                  }}
                  onDelete={() => setDeleteTarget(tpl)}
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
    </div>
  );
}
