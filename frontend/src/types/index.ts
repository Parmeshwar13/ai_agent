export type User = {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  created_at: string;
  updated_at: string;
};

export type OrganizationRole = "owner" | "admin" | "member";
export type ProjectRole = "owner" | "maintainer" | "viewer";

export type Organization = {
  id: string;
  name: string;
  slug: string;
  description: string;
  role: OrganizationRole | null;
  member_count: number;
  project_count: number;
  created_at: string;
  updated_at: string;
};

export type OrganizationMember = {
  id: string;
  user: User;
  role: OrganizationRole;
  created_at: string;
  updated_at: string;
};

export type OrganizationEvent = {
  id: string;
  event_type: string;
  message: string;
  metadata: Record<string, unknown>;
  actor: User | null;
  created_at: string;
};

export type Project = {
  id: string;
  organization: { id: string; name: string; slug: string };
  name: string;
  slug: string;
  key: string;
  summary: string;
  product_description: string;
  status: string;
  status_label: string;
  is_archived: boolean;
  archived_at: string | null;
  created_by: User;
  member_count: number;
  role: ProjectRole | null;
  can_edit: boolean;
  can_manage_members: boolean;
  can_archive: boolean;
  can_delete: boolean;
  created_at: string;
  updated_at: string;
};

export type ProjectMember = {
  id: string;
  user: User;
  role: ProjectRole;
  created_at: string;
  updated_at: string;
};

export type ProjectEvent = {
  id: string;
  event_type: string;
  message: string;
  metadata: Record<string, unknown>;
  actor: User | null;
  created_at: string;
};

export type Page<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

export type LifecycleStep = {
  value: string;
  label: string;
  description: string;
};

export type Lifecycle = {
  current: string;
  automation: string;
  phase: number;
  note: string;
  allowed_transitions: string[];
  happy_path: LifecycleStep[];
  failure_path: LifecycleStep[];
  terminal: string[];
};

export type SessionResponse = {
  access: string;
  refresh: string;
  user: User;
  organizations: Organization[];
};
