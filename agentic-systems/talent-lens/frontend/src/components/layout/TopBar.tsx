import { Menu } from "lucide-react";
import { useUIStore } from "@/stores/uiStore";

export function TopBar() {
  const toggleSidebar = useUIStore((s) => s.toggleSidebar);

  return (
    <header className="flex h-14 items-center border-b px-4">
      <button onClick={toggleSidebar} className="mr-4 p-1 hover:bg-muted rounded">
        <Menu className="h-5 w-5" />
      </button>
      <h1 className="text-lg font-semibold">TalentLens</h1>
    </header>
  );
}
