import { NavLink } from "react-router-dom";

import { Separator } from "@/components/ui/separator";
import { CLIENT_NAME } from "@/lib/client-name";
import { NAV_ITEMS } from "@/lib/navigation";
import { cn } from "@/lib/utils";

type SidebarNavProps = {
  onNavigate?: () => void;
};

export function SidebarNav({ onNavigate }: SidebarNavProps) {
  return (
    <div className="flex h-full flex-col">
      <div className="px-5 py-4">
        <p className="text-[11px] font-medium tracking-[0.14em] text-muted-foreground">
          {CLIENT_NAME}
        </p>
        <h1 className="mt-1 text-[15px] leading-5 font-semibold tracking-tight">
          AI Delivery Dashboard
        </h1>
      </div>
      <Separator />
      <nav className="flex flex-1 flex-col gap-1 p-3">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              onClick={onNavigate}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-2.5 rounded-md px-2.5 py-2 text-sm transition-colors",
                  isActive
                    ? "bg-sidebar-accent font-medium text-foreground shadow-[inset_2px_0_0_0_var(--foreground)]"
                    : "text-muted-foreground hover:bg-sidebar-accent/70 hover:text-foreground",
                )
              }
            >
              <Icon className="size-4 shrink-0" />
              {item.label}
            </NavLink>
          );
        })}
      </nav>
    </div>
  );
}
