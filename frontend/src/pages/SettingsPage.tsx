import { useEffect, useState } from "react";

import { Field } from "../components/Field";
import { useAuth } from "../hooks/useAuth";
import { useOrganization } from "../hooks/useOrganization";
import { useTitle } from "../hooks/useTitle";
import { useToast } from "../hooks/useToast";
import { api, ApiError } from "../services/api";
import { fieldError, type FieldErrors } from "../services/errors";
import { formatWhen, initials } from "../services/format";
import type { OrganizationEvent, OrganizationMember, OrganizationRole, User } from "../types";

type Tab = "profile" | "organization" | "people";

export function SettingsPage() {
  useTitle("Settings");
  const [tab, setTab] = useState<Tab>("profile");

  return (
    <section className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Account</p>
          <h1>Settings</h1>
          <p className="lede">Profile, organization, and the people who can see its projects.</p>
        </div>
      </header>
      <div className="tabs" role="tablist">
        {(
          [
            ["profile", "Profile"],
            ["organization", "Organization"],
            ["people", "People"],
          ] as const
        ).map(([id, label]) => (
          <button key={id} type="button" className={tab === id ? "tab is-active" : "tab"} onClick={() => setTab(id)}>
            {label}
          </button>
        ))}
      </div>
      {tab === "profile" ? <ProfileSettings /> : null}
      {tab === "organization" ? <OrganizationSettings /> : null}
      {tab === "people" ? <PeopleSettings /> : null}
    </section>
  );
}

function ProfileSettings() {
  const { user, setUser } = useAuth();
  const toast = useToast();
  const [firstName, setFirstName] = useState(user?.first_name ?? "");
  const [lastName, setLastName] = useState(user?.last_name ?? "");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [errors, setErrors] = useState<FieldErrors>({});

  useEffect(() => {
    setFirstName(user?.first_name ?? "");
    setLastName(user?.last_name ?? "");
  }, [user]);

  async function saveProfile(event: React.FormEvent) {
    event.preventDefault();
    try {
      const updated = await api<User>("/auth/me/", {
        method: "PATCH",
        body: JSON.stringify({ first_name: firstName, last_name: lastName }),
      });
      setUser(updated);
      toast("Profile saved.");
    } catch (err) {
      toast(err instanceof ApiError ? err.detail : "Could not save profile.", "danger");
    }
  }

  async function savePassword(event: React.FormEvent) {
    event.preventDefault();
    setErrors({});
    try {
      await api("/auth/password/", {
        method: "POST",
        body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
      });
      setCurrentPassword("");
      setNewPassword("");
      toast("Password updated.");
    } catch (err) {
      if (err instanceof ApiError) setErrors(err.errors);
      toast("Password was not changed.", "danger");
    }
  }

  return (
    <div className="settings-grid">
      <form className="panel stack" onSubmit={saveProfile}>
        <h2>Profile</h2>
        <Field label="Email">
          <input className="input" value={user?.email ?? ""} disabled />
        </Field>
        <Field label="First name">
          <input className="input" value={firstName} onChange={(event) => setFirstName(event.target.value)} required />
        </Field>
        <Field label="Last name">
          <input className="input" value={lastName} onChange={(event) => setLastName(event.target.value)} />
        </Field>
        <button type="submit" className="btn btn-primary">
          Save profile
        </button>
      </form>
      <form className="panel stack" onSubmit={savePassword}>
        <h2>Password</h2>
        <Field label="Current password" error={fieldError(errors, "current_password")}>
          <input
            className="input"
            type="password"
            value={currentPassword}
            onChange={(event) => setCurrentPassword(event.target.value)}
            required
          />
        </Field>
        <Field label="New password" hint="At least 10 characters." error={fieldError(errors, "new_password")}>
          <input
            className="input"
            type="password"
            value={newPassword}
            onChange={(event) => setNewPassword(event.target.value)}
            required
            minLength={10}
          />
        </Field>
        <button type="submit" className="btn btn-primary">
          Update password
        </button>
      </form>
    </div>
  );
}

function OrganizationSettings() {
  const { organization, setOrganizationId } = useOrganization();
  const { refreshOrganizations } = useAuth();
  const toast = useToast();
  const [name, setName] = useState(organization?.name ?? "");
  const [description, setDescription] = useState(organization?.description ?? "");
  const [confirmSlug, setConfirmSlug] = useState("");
  const [events, setEvents] = useState<OrganizationEvent[]>([]);
  const canManage = organization?.role === "owner" || organization?.role === "admin";

  useEffect(() => {
    setName(organization?.name ?? "");
    setDescription(organization?.description ?? "");
    if (!organization) return;
    api<OrganizationEvent[]>(`/organizations/${organization.id}/events/`)
      .then(setEvents)
      .catch(() => setEvents([]));
  }, [organization]);

  if (!organization) return <p className="quiet">Create an organization before editing settings.</p>;

  async function save(event: React.FormEvent) {
    event.preventDefault();
    try {
      await api(`/organizations/${organization!.id}/`, {
        method: "PATCH",
        body: JSON.stringify({ name, description }),
      });
      await refreshOrganizations();
      toast("Organization updated.");
    } catch (err) {
      toast(err instanceof ApiError ? err.detail : "Could not update the organization.", "danger");
    }
  }

  async function remove(event: React.FormEvent) {
    event.preventDefault();
    try {
      await api(`/organizations/${organization!.id}/`, {
        method: "DELETE",
        body: JSON.stringify({ confirm_slug: confirmSlug }),
      });
      const remaining = await refreshOrganizations();
      setOrganizationId(remaining[0]?.id ?? "");
      toast("Organization deleted.");
    } catch (err) {
      toast(err instanceof ApiError ? err.errors.confirm_slug?.[0] || err.detail : "Could not delete.", "danger");
    }
  }

  return (
    <div className="settings-grid">
      <form className="panel stack" onSubmit={save}>
        <h2>{organization.name}</h2>
        <p className="quiet">Slug {organization.slug}. Slugs stay stable so links do not break when the name changes.</p>
        <Field label="Name">
          <input className="input" value={name} onChange={(event) => setName(event.target.value)} disabled={!canManage} />
        </Field>
        <Field label="Description">
          <textarea
            className="textarea"
            rows={4}
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            disabled={!canManage}
          />
        </Field>
        {canManage ? (
          <button type="submit" className="btn btn-primary">
            Save organization
          </button>
        ) : (
          <p className="quiet">Only owners and admins can edit the organization.</p>
        )}
      </form>
      <div className="stack">
        <section className="panel">
          <h2>Recent organization activity</h2>
          <ol className="timeline">
            {events.map((event) => (
              <li key={event.id}>
                <time>{formatWhen(event.created_at)}</time>
                <p>{event.message}</p>
              </li>
            ))}
          </ol>
        </section>
        {organization.role === "owner" ? (
          <form className="panel stack danger-zone" onSubmit={remove}>
            <h2>Delete organization</h2>
            <p>This permanently removes the organization and its projects. Type the slug to confirm.</p>
            <Field label="Slug confirmation">
              <input className="input" value={confirmSlug} onChange={(event) => setConfirmSlug(event.target.value)} />
            </Field>
            <button type="submit" className="btn btn-danger" disabled={confirmSlug !== organization.slug}>
              Delete {organization.slug}
            </button>
          </form>
        ) : null}
      </div>
    </div>
  );
}

function PeopleSettings() {
  const { organization } = useOrganization();
  const { refreshOrganizations } = useAuth();
  const toast = useToast();
  const [members, setMembers] = useState<OrganizationMember[]>([]);
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<OrganizationRole>("member");
  const [error, setError] = useState("");
  const canManage = organization?.role === "owner" || organization?.role === "admin";

  async function load() {
    if (!organization) return;
    const rows = await api<OrganizationMember[]>(`/organizations/${organization.id}/members/`);
    setMembers(rows);
  }

  useEffect(() => {
    void load().catch(() => setMembers([]));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [organization?.id]);

  if (!organization) return <p className="quiet">No organization selected.</p>;

  async function add(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    try {
      await api(`/organizations/${organization!.id}/members/`, {
        method: "POST",
        body: JSON.stringify({ email, role }),
      });
      setEmail("");
      await load();
      await refreshOrganizations();
      toast("Member added.");
    } catch (err) {
      setError(err instanceof ApiError ? err.errors.email?.[0] || err.detail : "Could not add member.");
    }
  }

  return (
    <section className="panel stack">
      <h2>People in {organization.name}</h2>
      <p className="quiet">
        Someone must already have an Orbit account. This release does not send invitation email. A user outside this
        organization cannot see its projects, even if they know the id.
      </p>
      <ul className="people people-wide">
        {members.map((member) => (
          <li key={member.id}>
            <span className="avatar" aria-hidden="true">
              {initials(member.user.full_name)}
            </span>
            <span>
              <strong>{member.user.full_name}</strong>
              <small>{member.user.email}</small>
            </span>
            {canManage ? (
              <select
                className="select"
                value={member.role}
                aria-label={`Role for ${member.user.full_name}`}
                onChange={(event) => {
                  const next = event.target.value as OrganizationRole;
                  void api(`/organizations/${organization.id}/members/${member.id}/`, {
                    method: "PATCH",
                    body: JSON.stringify({ role: next }),
                  })
                    .then(() => load())
                    .then(() => refreshOrganizations())
                    .then(() => toast("Role updated."))
                    .catch((err: unknown) => {
                      toast(err instanceof ApiError ? err.detail : "Role was not changed.", "danger");
                    });
                }}
              >
                <option value="member">Member</option>
                <option value="admin">Admin</option>
                <option value="owner">Owner</option>
              </select>
            ) : (
              <em>{member.role}</em>
            )}
            {canManage ? (
              <button
                type="button"
                className="btn btn-ghost btn-small"
                onClick={() => {
                  void api(`/organizations/${organization.id}/members/${member.id}/`, { method: "DELETE" })
                    .then(() => load())
                    .then(() => refreshOrganizations())
                    .then(() => toast("Member removed."))
                    .catch((err: unknown) => {
                      toast(err instanceof ApiError ? err.detail : "Could not remove member.", "danger");
                    });
                }}
              >
                Remove
              </button>
            ) : null}
          </li>
        ))}
      </ul>
      {canManage ? (
        <form className="inline-form" onSubmit={add}>
          <input
            className="input"
            type="email"
            placeholder="ada@example.com"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
            aria-label="Email to add"
          />
          <select className="select" value={role} onChange={(event) => setRole(event.target.value as OrganizationRole)} aria-label="Organization role">
            <option value="member">Member</option>
            <option value="admin">Admin</option>
            {organization.role === "owner" ? <option value="owner">Owner</option> : null}
          </select>
          <button type="submit" className="btn btn-primary btn-small">
            Add person
          </button>
          {error ? <p className="field-error">{error}</p> : null}
        </form>
      ) : null}
    </section>
  );
}
