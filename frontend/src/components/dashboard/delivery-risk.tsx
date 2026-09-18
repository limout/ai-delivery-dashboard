import type { DeliveryConcern } from "@/lib/delivery-briefing";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

type DeliveryRiskProps = {
  concerns: DeliveryConcern[];
  dataInsufficient: boolean;
};

export function DeliveryRisk({
  concerns,
  dataInsufficient,
}: DeliveryRiskProps) {
  return (
    <Card className="rounded-lg shadow-none">
      <CardHeader>
        <CardTitle className="text-base">Delivery risk</CardTitle>
        <CardDescription>
          Concerns supported by the currently measurable delivery metrics.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {dataInsufficient ? (
          <p className="text-sm text-muted-foreground">
            Delivery risk cannot be assessed until more complete metric data is
            available.
          </p>
        ) : concerns.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No delivery concern is indicated by the currently measurable
            metrics.
          </p>
        ) : (
          <ul className="space-y-3">
            {concerns.map((concern) => (
              <li key={concern.id} className="space-y-1">
                <p className="text-sm font-medium">{concern.title}</p>
                <p className="text-sm leading-relaxed text-muted-foreground">
                  {concern.detail}
                </p>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
