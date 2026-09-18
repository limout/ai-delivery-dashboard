import { getMetricQuality } from "@/lib/metric-quality";
import type {
  HistoricalMetricsResponse,
  MetricResult,
  WorkItem,
} from "@/types/api";

export type DeliveryConcern = {
  id: string;
  title: string;
  detail: string;
};

export type DeliveryBriefing = {
  headline: string;
  facts: string[];
  discussion: string;
  concerns: DeliveryConcern[];
  dataInsufficient: boolean;
};

const COMMITMENT_MEDIUM = 70;
const COMMITMENT_HIGH = 50;
const WIP_THROUGHPUT_RATIO = 2;

function numericValue(
  metrics: Record<string, MetricResult> | null,
  name: string,
): number | null {
  const metric = metrics?.[name];
  if (!metric || metric.value === null || !Number.isFinite(metric.value)) {
    return null;
  }
  return metric.value;
}

function isUnavailable(metric: MetricResult | undefined): boolean {
  if (!metric) {
    return true;
  }
  if (metric.value === null) {
    return true;
  }
  const quality = getMetricQuality(metric);
  return quality?.rawStatus === "insufficient_data";
}

function formatCount(value: number): string {
  return Number.isInteger(value) ? String(value) : String(value);
}

function inProgressItems(workItems: WorkItem[]): WorkItem[] {
  return workItems.filter((item) => item.status === "In Progress");
}

export function buildDeliveryBriefing(
  metrics: Record<string, MetricResult> | null,
  workItems: WorkItem[],
  historical: HistoricalMetricsResponse | null,
): DeliveryBriefing {
  const wip = numericValue(metrics, "wip");
  const throughput = numericValue(metrics, "throughput");
  const velocity = numericValue(metrics, "velocity");
  const commitment = numericValue(metrics, "commitment_vs_completed");
  const cycleTime = numericValue(metrics, "cycle_time");
  const leadTime = numericValue(metrics, "lead_time");

  const measurable = [wip, throughput, velocity, commitment, cycleTime, leadTime]
    .filter((value) => value !== null)
    .length;

  const active = inProgressItems(workItems);
  const concerns: DeliveryConcern[] = [];

  if (
    commitment !== null &&
    commitment < COMMITMENT_MEDIUM
  ) {
    concerns.push({
      id: "planning-risk",
      title:
        commitment < COMMITMENT_HIGH
          ? "Low completion of currently assigned work"
          : "Completion of currently assigned work is below 70%",
      detail: `${formatCount(commitment)}% of currently assigned story points are completed. This is a proxy based on current assignment, not sprint-start commitment.`,
    });
  }

  if (
    wip !== null &&
    throughput !== null &&
    throughput > 0 &&
    wip / throughput >= WIP_THROUGHPUT_RATIO
  ) {
    concerns.push({
      id: "wip-throughput",
      title: "In-progress work is high relative to completions",
      detail: `${formatCount(wip)} items are in progress against ${formatCount(throughput)} completed.`,
    });
  }

  if (
    historical?.metric === "velocity" &&
    velocity !== null &&
    historical.points.filter((point) => point.value !== null).length >= 2
  ) {
    const values = historical.points
      .map((point) => point.value)
      .filter((value): value is number => value !== null);
    const change = values[values.length - 1] - values[0];
    if (change < 0) {
      concerns.push({
        id: "velocity-trend",
        title: "Completed story points are lower in later iterations",
        detail: `Average completed volume is ${formatCount(velocity)} story points per iteration, and the loaded iteration series ends lower than it starts.`,
      });
    }
  }

  const facts: string[] = [];

  if (commitment !== null) {
    facts.push(
      `${formatCount(commitment)}% of currently assigned story points are completed (assignment proxy, not sprint-start commitment).`,
    );
  }

  if (wip !== null) {
    const ids = active
      .map((item) => item.id)
      .filter(Boolean)
      .slice(0, 5);
    if (wip > 0 && ids.length > 0 && ids.length === active.length) {
      facts.push(
        `${formatCount(wip)} work ${wip === 1 ? "item is" : "items are"} in progress (${ids.join(", ")}).`,
      );
    } else {
      facts.push(
        `${formatCount(wip)} work ${wip === 1 ? "item is" : "items are"} currently in progress.`,
      );
    }
  }

  if (velocity !== null) {
    facts.push(
      `Average completed volume is ${formatCount(velocity)} story points per iteration.`,
    );
  }

  if (throughput !== null) {
    facts.push(
      `${formatCount(throughput)} work ${throughput === 1 ? "item has" : "items have"} been completed.`,
    );
  }

  const supportingFacts = facts.slice(0, 3);

  const dataInsufficient = measurable === 0;

  if (dataInsufficient) {
    return {
      headline:
        "There is not enough measurable delivery data to brief the current situation.",
      facts: [
        "Loaded metrics do not yet provide a reliable delivery reading.",
      ],
      discussion:
        "Confirm that work items include status history, iterations, and story points before treating this project as briefable.",
      concerns: [],
      dataInsufficient: true,
    };
  }

  const primary = concerns[0];
  let headline: string;
  let discussion: string;

  if (primary?.id === "planning-risk") {
    headline =
      "A substantial share of currently assigned story points is still incomplete.";
    discussion =
      "Discuss whether the next iteration should take on less new work until in-progress and unfinished assigned work is understood.";
  } else if (primary?.id === "wip-throughput") {
    headline = "More work is sitting in progress than the team is finishing.";
    discussion =
      "Discuss finishing the oldest in-progress items before starting additional work.";
  } else if (primary?.id === "velocity-trend") {
    headline =
      "Later iterations completed fewer story points than earlier ones in the loaded series.";
    discussion =
      "Discuss spillover, blocked work, and item size before raising future commitments.";
  } else {
    headline =
      "Measurable delivery metrics are available and do not show a strong current-metric concern.";
    discussion =
      "Review whether in-progress work still matches the team's intended focus.";
  }

  return {
    headline,
    facts:
      supportingFacts.length > 0
        ? supportingFacts
        : ["Current metrics were loaded, but few numeric facts are available to list."],
    discussion,
    concerns,
    dataInsufficient: false,
  };
}

export function unavailableReason(metric: MetricResult): string {
  const quality = getMetricQuality(metric);
  const message = quality?.message?.trim() ?? metric.message?.trim() ?? "";

  if (message.includes("In Progress and Done")) {
    return "Needs work items that moved from In Progress to Done.";
  }
  if (message.includes("Done history")) {
    return "Needs completed work with a recorded Done date.";
  }
  if (message.includes("No work items available")) {
    return "No work items were loaded.";
  }
  if (message.includes("iteration or Story Point")) {
    return "Needs iteration and story point data.";
  }
  if (message.includes("committed Story Points")) {
    return "Needs iterations with assigned story points.";
  }
  if (message && message !== "Sufficient data available.") {
    return message;
  }
  return "Not enough history to measure this yet.";
}

export function isMetricUnavailable(metric: MetricResult): boolean {
  return isUnavailable(metric);
}
