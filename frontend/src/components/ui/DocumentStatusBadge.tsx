import { Badge } from "./Badge";

const STATUS_LABELS: Record<string, string> = {
  pending: "Pending",
  processing: "Processing",
  ready: "Ready",
  failed: "Failed",
};

export function DocumentStatusBadge({ status }: { status: string }) {
  const tone =
    status === "ready"
      ? "success"
      : status === "failed"
        ? "muted"
        : "neutral";

  return <Badge tone={tone}>{STATUS_LABELS[status] ?? status}</Badge>;
}
