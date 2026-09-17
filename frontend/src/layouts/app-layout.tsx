import { Menu } from "lucide-react";
import { useState } from "react";
import { Outlet, useLocation } from "react-router-dom";

import { DashboardControls } from "@/components/dashboard-controls";
import { SidebarNav } from "@/components/sidebar-nav";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { useDashboard } from "@/lib/dashboard-context";
import { formatSource } from "@/lib/format";
import { NAV_ITEMS } from "@/lib/navigation";

function pageTitle(pathname: string): string {
  const match = NAV_ITEMS.find((item) =>
    item.to === "/" ? pathname === "/" : pathname.startsWith(item.to),
  );
  return match?.label ?? "Overview";
}

export function AppLayout() {
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const title = pageTitle(location.pathname);
  const { selectedSource, selectedProject, isLoadingDashboard } = useDashboard();

  return (
    <div className="flex min-h-full bg-background">
      <aside className="sticky top-0 hidden h-screen w-60 shrink-0 border-r border-sidebar-border bg-sidebar md:flex md:flex-col">
        <SidebarNav />
      </aside>

      <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
        <SheetContent side="left" className="w-60 bg-sidebar p-0 sm:max-w-60">
          <SheetHeader className="sr-only">
            <SheetTitle>Navigation</SheetTitle>
          </SheetHeader>
          <SidebarNav onNavigate={() => setMobileOpen(false)} />
        </SheetContent>
      </Sheet>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b bg-background/90 px-4 backdrop-blur-sm">
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            className="md:hidden"
            onClick={() => setMobileOpen(true)}
            aria-label="Open navigation"
          >
            <Menu className="size-4" />
          </Button>

          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium">{title}</p>
            <p className="truncate text-xs text-muted-foreground">
              AI Delivery Dashboard
            </p>
          </div>

          <div className="hidden min-w-0 items-center gap-2 sm:flex">
            <div className="rounded-md border bg-card px-2.5 py-1.5 text-xs text-muted-foreground">
              {selectedSource ? formatSource(selectedSource) : "Source —"}
            </div>
            <div className="max-w-[180px] truncate rounded-md border bg-card px-2.5 py-1.5 text-xs text-muted-foreground">
              {selectedProject || "Project —"}
            </div>
            {isLoadingDashboard ? (
              <span className="text-xs text-muted-foreground">Loading…</span>
            ) : null}
          </div>
        </header>

        <DashboardControls />

        <main className="flex-1 px-4 py-6 md:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
