import type { ReactNode } from "react";

import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

export function PageShell({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "mx-auto flex min-w-0 max-w-6xl flex-col gap-6",
        className,
      )}
    >
      {children}
    </div>
  );
}

export function PageHeader({
  kicker,
  title,
  description,
}: {
  kicker?: string | null;
  title: string;
  description?: ReactNode;
}) {
  return (
    <header className="space-y-1">
      {kicker ? (
        <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
          {kicker}
        </p>
      ) : null}
      <h2 className="text-xl font-semibold tracking-tight">{title}</h2>
      {description ? (
        <p className="max-w-2xl text-sm text-muted-foreground">{description}</p>
      ) : null}
    </header>
  );
}

export function PageEmpty({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <PageShell>
      <PageHeader title={title} description={children} />
    </PageShell>
  );
}

export function PageLoading() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-8 w-56" />
      <div className="grid gap-3 sm:grid-cols-2">
        <Skeleton className="h-36 w-full" />
        <Skeleton className="h-36 w-full" />
      </div>
      <Skeleton className="h-40 w-full" />
    </div>
  );
}

export function PageMessage({ children }: { children: ReactNode }) {
  return (
    <p className="rounded-lg border border-dashed px-4 py-8 text-sm text-muted-foreground">
      {children}
    </p>
  );
}
