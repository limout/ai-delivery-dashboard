import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

type AnalysisSectionProps = {
  title: string;
  items: string[];
  asParagraphs?: boolean;
};

export function AnalysisSection({
  title,
  items,
  asParagraphs = false,
}: AnalysisSectionProps) {
  if (items.length === 0) {
    return null;
  }

  return (
    <Card className="rounded-lg py-5 shadow-none">
      <CardHeader className="px-5">
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent className="px-5">
        {asParagraphs ? (
          <div className="space-y-3">
            {items.map((item, index) => (
              <p key={`${title}-${index}`} className="text-sm leading-relaxed break-words">
                {item}
              </p>
            ))}
          </div>
        ) : (
          <ul className="list-disc space-y-2 pl-5 text-sm leading-relaxed">
            {items.map((item, index) => (
              <li key={`${title}-${index}`} className="break-words">
                {item}
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
