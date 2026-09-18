import type { DeliveryBriefing } from "@/lib/delivery-briefing";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

type ExecutiveBriefingProps = {
  briefing: DeliveryBriefing;
};

export function ExecutiveBriefing({ briefing }: ExecutiveBriefingProps) {
  return (
    <Card className="rounded-lg shadow-none">
      <CardHeader className="gap-2">
        <CardDescription className="text-[11px] tracking-wide uppercase">
          Executive delivery briefing
        </CardDescription>
        <CardTitle className="text-lg leading-snug font-semibold tracking-tight">
          {briefing.headline}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <p className="mb-2 text-xs font-medium tracking-wide text-muted-foreground uppercase">
            Supporting facts
          </p>
          <ul className="list-disc space-y-1.5 pl-5 text-sm leading-relaxed">
            {briefing.facts.map((fact) => (
              <li key={fact} className="break-words">
                {fact}
              </li>
            ))}
          </ul>
        </div>
        <div>
          <p className="mb-1.5 text-xs font-medium tracking-wide text-muted-foreground uppercase">
            What to discuss
          </p>
          <p className="text-sm leading-relaxed">{briefing.discussion}</p>
        </div>
      </CardContent>
    </Card>
  );
}
