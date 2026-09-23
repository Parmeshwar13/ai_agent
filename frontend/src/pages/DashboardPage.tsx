import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { EmptyState } from "../components/EmptyState";
import { StatusBadge } from "../components/StatusBadge";
import { LifecycleRail } from "../features/lifecycle/LifecycleRail";
import { useAuth } from "../hooks/useAuth";
import { useOrganization } from "../hooks/useOrganization";
import { useTitle } from "../hooks/useTitle";
import { api } from "../services/api";
import { formatWhen } from "../services/format";
import type { Lifecycle, Page, Project } from "../types";

export function DashboardPage() {
  useTitle("Dashboard");
  const { user } = useAuth();
  const { organization } = useOrganization();
  const [projects, setProjects] = useState<Page<Project> | null>(null);
  const [lifecycle, setLifecycle] = useState<Lifecycle | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      if (!organization) {
        setProjects(null);
        return;
      }
      try {
        const [page, graph] = await Promise.all([
          api<Page<Project>>(`/projects/?organization=${organization.id}&page_size=5`),
          api<Lifecycle>("/projects/lifecycle/"),
        ]);
        if (!cancelled) {
          setProjects(page);
          setLifecycle(graph);
          setError("");
        }
      } catch {
        if (!cancelled) setError("Could not load this workspace.");
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, [organization]);

  if (!organization) {
    return (
      <section className="page">
        <EmptyState
          title="No organization yet"
          body="Create a workspace from the organization switcher. Every project you register will belong to it."
        />
      </section>
    );
  }

  return (
    <section className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">{organization.name}</p>
          <h1>Welcome back, {user?.first_name || "there"}.</h1>
          <p className="lede">
            This workspace registers independent software products. Orbit does not implement them in this release.
          </p>
        </div>
        <Link className="btn btn-primary" to="/projects/new">
          New project
        </Link>
      </header>

      <div className="stat-grid">
        <article className="stat">
          <span>Open projects</span>
          <strong>{projects?.count ?? "–"}</strong>
        </article>
        <article className="stat">
          <span>People</span>
          <strong>{organization.member_count}</strong>
        </article>
        <article className="stat">
          <span>Your role</span>
          <strong className="stat-text">{organization.role}</strong>
        </article>
      </div>

      {error ? <p className="banner is-danger">{error}</p> : null}

      <section className="panel">
        <header className="panel-header">
          <h2>Projects</h2>
          <Link to="/projects">View all</Link>
        </header>
        {!projects ? (
          <p className="quiet">Loading projects</p>
        ) : projects.results.length === 0 ? (
          <EmptyState
            title="No products registered yet"
            body="A project is a software product Orbit will later specify and implement. It is not a module of Orbit itself."
            action={
              <Link className="btn btn-primary" to="/projects/new">
                Register a product
              </Link>
            }
          />
        ) : (
          <div className="project-list">
            {projects?.results.map((project) => (
              <Link key={project.id} to={`/projects/${project.id}`} className="project-row">
                <span className="key">{project.key}</span>
                <span className="project-row-main">
                  <strong>{project.name}</strong>
                  <small>{project.summary || project.product_description}</small>
                </span>
                <StatusBadge status={project.status} label={project.status_label} />
                <time>{formatWhen(project.updated_at)}</time>
              </Link>
            ))}
          </div>
        )}
      </section>

      {lifecycle ? (
        <section className="panel">
          <header className="panel-header">
            <h2>Lifecycle</h2>
            <span className="quiet">Automation off</span>
          </header>
          <p className="panel-note">{lifecycle.note}</p>
          <LifecycleRail lifecycle={lifecycle} compact />
          <p className="failure-note">
            Failure path, not active: {lifecycle.failure_path.map((step) => step.label).join(" → ")}. Exceeding later
            retry limits stops at Human review required. Orbit will not loop forever, and it will not claim a test
            passed without running it.
          </p>
        </section>
      ) : null}
    </section>
  );
}
