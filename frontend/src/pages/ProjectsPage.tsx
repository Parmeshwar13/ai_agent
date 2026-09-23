import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { EmptyState } from "../components/EmptyState";
import { StatusBadge } from "../components/StatusBadge";
import { useOrganization } from "../hooks/useOrganization";
import { useTitle } from "../hooks/useTitle";
import { api } from "../services/api";
import { formatWhen } from "../services/format";
import type { Lifecycle, Page, Project } from "../types";

export function ProjectsPage() {
  useTitle("Projects");
  const { organization } = useOrganization();
  const [page, setPage] = useState<Page<Project> | null>(null);
  const [lifecycle, setLifecycle] = useState<Lifecycle | null>(null);
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");
  const [includeArchived, setIncludeArchived] = useState(false);
  const [pageNumber, setPageNumber] = useState(1);
  const [error, setError] = useState("");

  useEffect(() => {
    const handle = window.setTimeout(() => setQuery(search.trim()), 250);
    return () => window.clearTimeout(handle);
  }, [search]);

  useEffect(() => {
    let cancelled = false;
    api<Lifecycle>("/projects/lifecycle/")
      .then((graph) => {
        if (!cancelled) setLifecycle(graph);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!organization) return;
    let cancelled = false;
    const params = new URLSearchParams({ organization: organization.id });
    if (query) params.set("search", query);
    if (status) params.set("status", status);
    if (includeArchived) params.set("include_archived", "true");
    params.set("page", String(pageNumber));
    api<Page<Project>>(`/projects/?${params.toString()}`)
      .then((result) => {
        if (!cancelled) {
          setPage(result);
          setError("");
        }
      })
      .catch(() => {
        if (!cancelled) setError("Could not load projects.");
      });
    return () => {
      cancelled = true;
    };
  }, [organization, query, status, includeArchived, pageNumber]);

  const stages = lifecycle
    ? [...lifecycle.happy_path, ...lifecycle.failure_path].filter(
        (step, index, all) => all.findIndex((item) => item.value === step.value) === index,
      )
    : [];

  return (
    <section className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Registry</p>
          <h1>Projects</h1>
          <p className="lede">Each row is an independent product. Search stays inside the current organization.</p>
        </div>
        <Link className="btn btn-primary" to="/projects/new">
          New project
        </Link>
      </header>

      <div className="toolbar">
        <input
          className="input"
          placeholder="Search name, key, or description"
          value={search}
          onChange={(event) => {
            setSearch(event.target.value);
            setPageNumber(1);
          }}
          aria-label="Search projects"
        />
        <select
          className="select"
          value={status}
          onChange={(event) => {
            setStatus(event.target.value);
            setPageNumber(1);
          }}
          aria-label="Filter by status"
        >
          <option value="">All stages</option>
          {stages.map((step) => (
            <option key={step.value} value={step.value}>
              {step.label}
            </option>
          ))}
        </select>
        <label className="check">
          <input
            type="checkbox"
            checked={includeArchived}
            onChange={(event) => {
              setIncludeArchived(event.target.checked);
              setPageNumber(1);
            }}
          />
          Include archived
        </label>
      </div>

      {error ? <p className="banner is-danger">{error}</p> : null}

      <section className="panel">
        {!organization ? (
          <EmptyState title="Choose an organization" body="Projects are listed only for a workspace you belong to." />
        ) : !page ? (
          <p className="quiet">Loading projects</p>
        ) : page.results.length === 0 ? (
          <EmptyState
            title="Nothing matches"
            body="No project in this organization fits the current filters."
            action={
              <Link className="btn btn-primary" to="/projects/new">
                Register a product
              </Link>
            }
          />
        ) : (
          <div className="project-list">
            {page?.results.map((project) => (
              <Link key={project.id} to={`/projects/${project.id}`} className="project-row">
                <span className="key">{project.key}</span>
                <span className="project-row-main">
                  <strong>{project.name}</strong>
                  <small>{project.summary || "No summary"}</small>
                </span>
                <StatusBadge status={project.status} label={project.status_label} />
                <time>{formatWhen(project.updated_at)}</time>
              </Link>
            ))}
          </div>
        )}
        {page && page.count > page.results.length ? (
          <p className="panel-note">Showing {page.results.length} of {page.count}. Narrow the search to see a specific product.</p>
        ) : null}
      </section>
    </section>
  );
}
