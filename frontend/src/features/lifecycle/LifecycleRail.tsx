import type { Lifecycle } from "../../types";

export function LifecycleRail({
  lifecycle,
  compact = false,
}: {
  lifecycle: Lifecycle;
  compact?: boolean;
}) {
  const currentIndex = lifecycle.happy_path.findIndex((step) => step.value === lifecycle.current);
  return (
    <ol className={compact ? "rail rail-compact" : "rail"}>
      {lifecycle.happy_path.map((step, index) => {
        const state =
          currentIndex < 0 ? "upcoming" : index < currentIndex ? "done" : index === currentIndex ? "current" : "upcoming";
        return (
          <li key={step.value} className={`rail-step is-${state}`}>
            <span className="rail-mark" aria-hidden="true" />
            <span className="rail-copy">
              <strong>{step.label}</strong>
              {compact ? null : <em>{step.description}</em>}
            </span>
          </li>
        );
      })}
    </ol>
  );
}
