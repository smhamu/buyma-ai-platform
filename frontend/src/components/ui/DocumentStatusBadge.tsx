import { Badge } from "./Badge";

const STATUS_LABELS: Record<string, string> = {
  pending: "処理待ち",
  processing: "処理中",
  ready: "準備完了",
  failed: "失敗",
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
