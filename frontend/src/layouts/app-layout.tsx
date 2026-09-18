import { Menu } from "lucide-react";
import { useState } from "react";
import { Outlet, useLocation } from "react-router-dom";

import { DashboardControls } from "@/components/dashboard-controls";
import { InnerProjectBar } from "@/components/inner-project-bar";
import { SidebarNav } from "@/components/sidebar-nav";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
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
  const isOverview =
    location.pathname === "/" || location.pathname === "";
  const isMetrics = location.pathname.startsWith("/metrics");

  return (
    <div className="flex min-h-full bg-background">
      <aside className="sticky top-0 hidden h-screen w-56 shrink-0 border-r border-sidebar-border bg-sidebar md:flex md:flex-col">
        <SidebarNav />
      </aside>

      <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
        <SheetContent side="left" className="w-56 bg-sidebar p-0 sm:max-w-56">
          <SheetHeader className="sr-only">
            <SheetTitle>Navigation</SheetTitle>
          </SheetHeader>
          <SidebarNav onNavigate={() => setMobileOpen(false)} />
        </SheetContent>
      </Sheet>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex h-12 items-center gap-3 border-b bg-background/90 px-4 backdrop-blur-sm md:px-8">
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

          <div className="min-w-0">
            <p className="truncate text-sm font-medium">{title}</p>
          </div>
        </header>

        {isOverview ? (
          <DashboardControls />
        ) : isMetrics ? null : (
          <InnerProjectBar />
        )}

        <main className="min-w-0 flex-1 px-4 py-5 md:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
