import { useTitle } from "../hooks/useTitle";

const COPY: Record<string, { phase: string; body: string; rules: string[] }> = {
  Tasks: {
    phase: "Phase 3",
    body: "Tasks will be a dependency graph from epic to subtask, not a flat to-do list. The planner is not running.",
    rules: ["Dependencies will be explicit.", "A task will not be marked done because a model said so."],
  },
  Wiki: {
    phase: "Phase 2",
    body: "Every project will have a versioned wiki: overview, personas, requirements, architecture, and known issues. Documents are not generated in this release.",
    rules: ["Knowledge will be versioned.", "Only affected documents will be updated."],
  },
  Architecture: {
    phase: "Phase 3",
    body: "Architecture decisions will be ADR-style records. Orbit will not force one stack onto every generated product.",
    rules: ["Decision, reason, alternatives, consequences, status.", "No assumed Django backend for generated apps."],
  },
  "Agent Runs": {
    phase: "Phase 5",
    body: "Coding runs will be tool calls inside a sandbox, with every step stored. There is no agent loop in this release, and nothing here executes on the Orbit host.",
    rules: ["Bounded retries.", "Resumable runs.", "No infinite autonomy."],
  },
  Repository: {
    phase: "Phase 4",
    body: "GitHub repository creation and a code index come later. Orbit will not clone or modify a repository from this screen.",
    rules: ["Main is never the working branch.", "Secrets stay out of generated repositories."],
  },
  "Pull Requests": {
    phase: "Phase 6",
    body: "Pull requests will be opened from task branches after tests actually run. This page does not create a pull request.",
    rules: ["PR text will cite the task.", "Status will follow the GitHub pull request, not a local guess."],
  },
  Tests: {
    phase: "Phase 6",
    body: "Sandbox test runs, lint, and type checks are not available yet. Orbit will not report a pass it did not execute.",
    rules: ["Command output is the evidence.", "Failures return to analysis, then a bounded fix."],
  },
};

export function UpcomingPage({ module }: { module: string }) {
  useTitle(module);
  const copy = COPY[module] ?? {
    phase: "Later",
    body: "This module is part of the Orbit map and is not implemented.",
    rules: [],
  };

  return (
    <section className="page narrow">
      <header className="page-header">
        <div>
          <p className="eyebrow">{copy.phase}</p>
          <h1>{module}</h1>
          <p className="lede">{copy.body}</p>
        </div>
      </header>
      <section className="panel">
        <h2>Not in this release</h2>
        <ul className="plain-list">
          {copy.rules.map((rule) => (
            <li key={rule}>{rule}</li>
          ))}
        </ul>
        <p className="panel-note">
          Phase 1 is the registry: users, organizations, and projects, with tenant isolation enforced on the server.
        </p>
      </section>
    </section>
  );
}
