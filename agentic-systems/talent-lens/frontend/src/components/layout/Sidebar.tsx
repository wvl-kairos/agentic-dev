import { Link, useLocation } from "react-router-dom";
import { LayoutDashboard, Users, Video, Briefcase } from "lucide-react";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/stores/uiStore";

const navItems = [
  { label: "Dashboard", path: "/", icon: LayoutDashboard },
  { label: "Candidates", path: "/candidates", icon: Users },
  { label: "Interviews", path: "/interviews", icon: Video },
  { label: "Roles", path: "/role-templates", icon: Briefcase },
];

export function Sidebar() {
  const location = useLocation();
  const open = useUIStore((s) => s.sidebarOpen);

  if (!open) return null;

  return (
    <aside className="w-56 border-r bg-muted/40 p-4">
      <nav className="space-y-1">
        {navItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={cn(
              "flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors",
              location.pathname === item.path
                ? "bg-primary text-primary-foreground"
                : "hover:bg-muted"
            )}
          >
            <item.icon className="h-4 w-4" />
            {item.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
