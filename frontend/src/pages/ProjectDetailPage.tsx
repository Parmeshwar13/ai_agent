import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { Field } from "../components/Field";
import { StatusBadge } from "../components/StatusBadge";
import { LifecycleRail } from "../features/lifecycle/LifecycleRail";
import { useTitle } from "../hooks/useTitle";
import { useToast } from "../hooks/useToast";
import { api, ApiError } from "../services/api";
import { fieldError, type FieldErrors } from "../services/errors";
import { formatWhen, initials, roleLabel } from "../services/format";
import type { Lifecycle, Page, Project, ProjectEvent, ProjectMember, ProjectRole } from "../types";

export function ProjectDetailPage() {
  const { projectId = "" } = useParams();
  const navigate = useNavigate();
  const toast = useToast();
  const [project, setProject] = useState<Project | null>(null);
  const [lifecycle, setLifecycle] = useState<Lifecycle | null>(null);
  const [members, setMembers] = useState<ProjectMember[]>([]);
  const [events, setEvents] = useState<ProjectEvent[]>([]);
  const [missing, setMissing] = useState(false);
  const [editing, setEditing] = useState(false);
  const [error, setError] = useState("");

  useTitle(project ? project.name : "Project");

  async function reload() {
    const [nextProject, nextLifecycle, nextMembers, nextEvents] = await Promise.all([
      api<Project>(`/projects/${projectId}/`),
      api<Lifecycle>(`/projects/${projectId}/lifecycle/`),
      api<ProjectMember[]>(`/projects/${projectId}/members/`),
      api<Page<ProjectEvent>>(`/projects/${projectId}/events/`),
    ]);
    setProject(nextProject);
    setLifecycle(nextLifecycle);
    setMembers(nextMembers);
    setEvents(nextEvents.results);
    setMissing(false);
  }

  useEffect(() => {
    let cancelled = false;
    reload()
      .catch((err: unknown) => {
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 404) setMissing(true);
        else setError("Could not load this project.");
      });
    return () => {
      cancelled = true;
    };
    // reload is recreated each render; the id is the dependency that matters.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  if (missing) {
    return (
      <section className="page">
        <div className="empty">
          <h2>Project not found</h2>
          <p>It does not exist, or it belongs to an organization you are not in. Orbit does not reveal which.</p>
          <Link className="btn btn-primary" to="/projects">
            Back to projects
          </Link>
        </div>
      </section>
    );
  }

  if (!project || !lifecycle) {
    return (
      <section className="page">
        <p className="quiet">{error || "Loading project"}</p>
      </section>
    );
  }

  return (
    <section className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">
            <Link to="/projects">Projects</Link> / {project.organization.name}
          </p>
          <div className="title-row">
            <span className="key key-lg">{project.key}</span>
            <h1>{project.name}</h1>
            <StatusBadge status={project.status} label={project.status_label} />
          </div>
          <p className="lede">{project.summary || "No summary yet."}</p>
        </div>
        <div className="row-actions">
          {project.can_edit ? (
            <button type="button" className="btn btn-ghost" onClick={() => setEditing((value) => !value)}>
              {editing ? "Close editor" : "Edit details"}
            </button>
          ) : null}
          {project.can_archive ? (
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => {
                const path = project.is_archived ? "unarchive" : "archive";
                void api<Project>(`/projects/${project.id}/${path}/`, { method: "POST" })
                  .then((updated) => {
                    setProject(updated);
                    toast(updated.is_archived ? "Project archived." : "Project restored.");
                    return reload();
                  })
                  .catch((err: unknown) => {
                    toast(err instanceof ApiError ? err.detail : "Could not update archive state.", "danger");
                  });
              }}
            >
              {project.is_archived ? "Restore" : "Archive"}
            </button>
          ) : null}
        </div>
      </header>

      <div className="detail-grid">
        <div className="stack">
          <section className="panel">
            <header className="panel-header">
              <h2>Product description</h2>
              <span className="quiet">Source text</span>
            </header>
            {editing ? (
              <EditForm
                project={project}
                onCancel={() => setEditing(false)}
                onSaved={(updated) => {
                  setProject(updated);
                  setEditing(false);
                  toast("Project details saved.");
                  void reload();
                }}
              />
            ) : (
              <p className="prose">{project.product_description}</p>
            )}
          </section>

          <section className="panel">
            <header className="panel-header">
              <h2>Lifecycle</h2>
              <span className="quiet">{lifecycle.allowed_transitions.length} open transitions</span>
            </header>
            <p className="panel-note">{lifecycle.note}</p>
            <LifecycleRail lifecycle={lifecycle} />
          </section>

          <section className="panel">
            <header className="panel-header">
              <h2>Activity</h2>
            </header>
            {events.length === 0 ? (
              <p className="quiet">No events yet.</p>
            ) : (
              <ol className="timeline">
                {events.map((event) => (
                  <li key={event.id}>
                    <time>{formatWhen(event.created_at)}</time>
                    <p>{event.message}</p>
                  </li>
                ))}
              </ol>
            )}
          </section>
        </div>

        <aside className="stack">
          <section className="panel">
            <header className="panel-header">
              <h2>Members</h2>
            </header>
            <ul className="people">
              {members.map((member) => (
                <li key={member.id}>
                  <span className="avatar" aria-hidden="true">
                    {initials(member.user.full_name)}
                  </span>
                  <span>
                    <strong>{member.user.full_name}</strong>
                    <small>{member.user.email}</small>
                  </span>
                  <em>{roleLabel(member.role)}</em>
                </li>
              ))}
            </ul>
            {project.can_manage_members ? (
              <AddMember projectId={project.id} onAdded={() => void reload().then(() => toast("Member added."))} />
            ) : (
              <p className="quiet">Organization admins can read this project. Write access is limited to maintainers and owners.</p>
            )}
          </section>

          <section className="panel meta-panel">
            <h2>Record</h2>
            <dl>
              <div>
                <dt>Slug</dt>
                <dd>{project.slug}</dd>
              </div>
              <div>
                <dt>Created</dt>
                <dd>{formatWhen(project.created_at)}</dd>
              </div>
              <div>
                <dt>Created by</dt>
                <dd>{project.created_by.full_name}</dd>
              </div>
              <div>
                <dt>Your access</dt>
                <dd>{roleLabel(project.role)}</dd>
              </div>
            </dl>
            {project.can_delete ? (
              <button
                type="button"
                className="btn btn-danger btn-small"
                onClick={() => {
                  const confirmed = window.confirm(
                    "Permanently delete this project and its history? Archive keeps the record.",
                  );
                  if (!confirmed) return;
                  void api(`/projects/${project.id}/?confirm=true`, { method: "DELETE" })
                    .then(() => {
                      toast("Project deleted.");
                      navigate("/projects");
                    })
                    .catch((err: unknown) => {
                      toast(err instanceof ApiError ? err.detail : "Could not delete the project.", "danger");
                    });
                }}
              >
                Delete permanently
              </button>
            ) : null}
          </section>
        </aside>
      </div>
    </section>
  );
}

function EditForm({
  project,
  onCancel,
  onSaved,
}: {
  project: Project;
  onCancel: () => void;
  onSaved: (project: Project) => void;
}) {
  const [name, setName] = useState(project.name);
  const [summary, setSummary] = useState(project.summary);
  const [description, setDescription] = useState(project.product_description);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [pending, setPending] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setPending(true);
    try {
      const updated = await api<Project>(`/projects/${project.id}/`, {
        method: "PATCH",
        body: JSON.stringify({ name, summary, product_description: description }),
      });
      onSaved(updated);
    } catch (err) {
      if (err instanceof ApiError) setErrors(err.errors);
    } finally {
      setPending(false);
    }
  }

  return (
    <form className="stack" onSubmit={submit}>
      <Field label="Name" error={fieldError(errors, "name")}>
        <input className="input" value={name} onChange={(event) => setName(event.target.value)} required />
      </Field>
      <Field label="Summary" error={fieldError(errors, "summary")}>
        <input className="input" value={summary} onChange={(event) => setSummary(event.target.value)} />
      </Field>
      <Field label="Product description" error={fieldError(errors, "product_description")}>
        <textarea className="textarea" rows={7} value={description} onChange={(event) => setDescription(event.target.value)} />
      </Field>
      <div className="row-actions">
        <button type="button" className="btn btn-ghost" onClick={onCancel}>
          Cancel
        </button>
        <button type="submit" className="btn btn-primary" disabled={pending}>
          Save
        </button>
      </div>
    </form>
  );
}

function AddMember({ projectId, onAdded }: { projectId: string; onAdded: () => void }) {
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<ProjectRole>("viewer");
  const [error, setError] = useState("");

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    try {
      await api(`/projects/${projectId}/members/`, {
        method: "POST",
        body: JSON.stringify({ email, role }),
      });
      setEmail("");
      onAdded();
    } catch (err) {
      setError(err instanceof ApiError ? err.errors.email?.[0] || err.detail : "Could not add member.");
    }
  }

  return (
    <form className="inline-form" onSubmit={submit}>
      <input
        className="input"
        type="email"
        placeholder="Email in this organization"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
        required
        aria-label="Member email"
      />
      <select className="select" value={role} onChange={(event) => setRole(event.target.value as ProjectRole)} aria-label="Project role">
        <option value="viewer">Viewer</option>
        <option value="maintainer">Maintainer</option>
        <option value="owner">Owner</option>
      </select>
      <button type="submit" className="btn btn-primary btn-small">
        Add
      </button>
      {error ? <p className="field-error">{error}</p> : null}
    </form>
  );
}
