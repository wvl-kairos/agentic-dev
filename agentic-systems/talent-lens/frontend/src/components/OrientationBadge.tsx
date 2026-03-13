import { cn } from "@/lib/utils";

const ORIENTATION_STYLES: Record<string, { label: string; bg: string; text: string }> = {
  frontend: { label: "Frontend", bg: "bg-blue-100", text: "text-blue-700" },
  backend: { label: "Backend", bg: "bg-green-100", text: "text-green-700" },
  fullstack: { label: "Fullstack", bg: "bg-purple-100", text: "text-purple-700" },
  data: { label: "Data", bg: "bg-orange-100", text: "text-orange-700" },
  devops: { label: "DevOps", bg: "bg-cyan-100", text: "text-cyan-700" },
};

export function OrientationBadge({
  orientation,
  size = "md",
}: {
  orientation: string | null;
  size?: "sm" | "md";
}) {
  if (!orientation) return null;
  const style = ORIENTATION_STYLES[orientation] ?? {
    label: orientation,
    bg: "bg-slate-100",
    text: "text-slate-600",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full font-semibold",
        size === "sm" ? "px-2 py-0.5 text-[10px]" : "px-2.5 py-0.5 text-xs",
        style.bg,
        style.text
      )}
    >
      {style.label}
    </span>
  );
}
