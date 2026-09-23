import {
  BookOpen,
  Bot,
  Boxes,
  FlaskConical,
  FolderKanban,
  GitBranch,
  GitPullRequest,
  LayoutDashboard,
  ListTree,
  Menu,
  Settings,
  X,
} from "lucide-react";
import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../hooks/useAuth";
import { useOrganization } from "../hooks/useOrganization";
import { initials } from "../services/format";
import { BrandMark } from "./BrandMark";
import { Modal } from "./Modal";
import { Field } from "./Field";
import { api, ApiError } from "../services/api";
import type { Organization } from "../types";

const NAV = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard, later: false },
  { to: "/projects", label: "Projects", icon: FolderKanban, later: false },
  { to: "/tasks", label: "Tasks", icon: ListTree, later: true },
  { to: "/wiki", label: "Wiki", icon: BookOpen, later: true },
  { to: "/architecture", label: "Architecture", icon: Boxes, later: true },
  { to: "/runs", label: "Agent Runs", icon: Bot, later: true },
  { to: "/repository", label: "Repository", icon: GitBranch, later: true },
  { to: "/pull-requests", label: "Pull Requests", icon: GitPullRequest, later: true },
  { to: "/tests", label: "Tests", icon: FlaskConical, later: true },
  { to: "/settings", label: "Settings", icon: Settings, later: false },
];

export function AppShell() {
  const { user, logout, refreshOrganizations } = useAuth();
  const { organization, organizations, setOrganizationId } = useOrganization();
  const [open, setOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    setOpen(false);
    setMenuOpen(false);
  }, [location.pathname]);

  return (
    <div className="shell">
      <aside className={open ? "sidebar is-open" : "sidebar"}>
        <div className="sidebar-brand">
          <BrandMark tone="paper" />
          <div>
            <strong>Orbit</strong>
            <span>0.1 · Registry</span>
          </div>
        </div>
        <nav className="side-nav" aria-label="Primary">
          {NAV.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink key={item.to} to={item.to} className={({ isActive }) => (isActive ? "nav-link is-active" : "nav-link")}>
                <Icon size={16} strokeWidth={1.75} />
                <span>{item.label}</span>
                {item.later ? <em>Later</em> : null}
              </NavLink>
            );
          })}
        </nav>
        <p className="sidebar-note">Generated products stay outside this application.</p>
      </aside>
      {open ? <button type="button" className="scrim" aria-label="Close navigation" onClick={() => setOpen(false)} /> : null}

      <div className="workspace">
        <header className="topbar">
          <button type="button" className="icon-btn mobile-only" onClick={() => setOpen(true)} aria-label="Open navigation">
            <Menu size={18} />
          </button>
          <OrgSwitcher
            organization={organization}
            organizations={organizations}
            open={menuOpen}
            onToggle={() => setMenuOpen((value) => !value)}
            onClose={() => setMenuOpen(false)}
            onSelect={(id) => {
              setOrganizationId(id);
              setMenuOpen(false);
              if (location.pathname.startsWith("/projects/")) navigate("/projects");
            }}
            onCreate={() => {
              setMenuOpen(false);
              setCreating(true);
            }}
          />
          <div className="topbar-spacer" />
          <div className="user-chip">
            <span className="avatar" aria-hidden="true">
              {initials(user?.full_name || user?.email || "?")}
            </span>
            <span className="user-chip-copy">
              <strong>{user?.full_name}</strong>
              <small>{user?.email}</small>
            </span>
          </div>
          <button
            type="button"
            className="btn btn-ghost btn-small"
            onClick={() => {
              void logout().then(() => navigate("/login"));
            }}
          >
            Sign out
          </button>
        </header>
        <main className="main">
          <Outlet />
        </main>
      </div>
      {creating ? (
        <CreateOrganization
          onClose={() => setCreating(false)}
          onCreated={async (created) => {
            await refreshOrganizations();
            setOrganizationId(created.id);
            setCreating(false);
          }}
        />
      ) : null}
    </div>
  );
}

function OrgSwitcher({
  organization,
  organizations,
  open,
  onToggle,
  onClose,
  onSelect,
  onCreate,
}: {
  organization: Organization | null;
  organizations: Organization[];
  open: boolean;
  onToggle: () => void;
  onClose: () => void;
  onSelect: (id: string) => void;
  onCreate: () => void;
}) {
  return (
    <div className="org-switcher">
      <button type="button" className="org-button" onClick={onToggle} aria-expanded={open} aria-haspopup="listbox">
        <span className="org-kicker">Organization</span>
        <strong>{organization?.name ?? "No workspace"}</strong>
      </button>
      {open ? (
        <div className="org-menu" role="listbox" aria-label="Organizations">
          {organizations.map((item) => (
            <button
              key={item.id}
              type="button"
              className={item.id === organization?.id ? "org-option is-current" : "org-option"}
              onClick={() => onSelect(item.id)}
            >
              <strong>{item.name}</strong>
              <small>
                {item.role} · {item.project_count} projects
              </small>
            </button>
          ))}
          <button type="button" className="org-option org-create" onClick={onCreate}>
            New organization
          </button>
          <button type="button" className="org-dismiss" onClick={onClose}>
            <X size={14} /> Close
          </button>
        </div>
      ) : null}
    </div>
  );
}

function CreateOrganization({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: (organization: Organization) => Promise<void>;
}) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setPending(true);
    setError("");
    try {
      const created = await api<Organization>("/organizations/", {
        method: "POST",
        body: JSON.stringify({ name, description }),
      });
      await onCreated(created);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not create the organization.");
    } finally {
      setPending(false);
    }
  }

  return (
    <Modal title="New organization" onClose={onClose}>
      <form className="stack" onSubmit={submit}>
        <Field label="Name" hint="This is the tenant boundary. Projects inside it stay isolated.">
          <input className="input" value={name} onChange={(event) => setName(event.target.value)} required minLength={2} />
        </Field>
        <Field label="Description" hint="Optional.">
          <textarea className="textarea" rows={3} value={description} onChange={(event) => setDescription(event.target.value)} />
        </Field>
        {error ? <p className="banner is-danger">{error}</p> : null}
        <div className="row-actions">
          <button type="button" className="btn btn-ghost" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={pending}>
            {pending ? "Creating" : "Create organization"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
