const TONE: Record<string, string> = {
  created: "copper",
  discovery: "moss",
  specification: "moss",
  architecture: "moss",
  planning: "moss",
  ready: "moss",
  implementing: "ink",
  testing: "ink",
  reviewing: "ink",
  pr_created: "ink",
  completed: "moss",
  failed: "danger",
  analyzing_failure: "danger",
  fixing: "danger",
  human_review_required: "warning",
};

export function StatusBadge({ status, label }: { status: string; label: string }) {
  return <span className={`badge is-${TONE[status] ?? "ink"}`}>{label}</span>;
}
