import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { useAuth } from "./useAuth";
import type { Organization } from "../types";

type OrgContextValue = {
  organization: Organization | null;
  organizations: Organization[];
  setOrganizationId: (id: string) => void;
};

const OrgContext = createContext<OrgContextValue | null>(null);
const STORAGE_KEY = "orbit.org";

export function OrganizationProvider({ children }: { children: ReactNode }) {
  const { organizations } = useAuth();
  const [organizationId, setOrganizationIdState] = useState<string | null>(
    () => localStorage.getItem(STORAGE_KEY),
  );

  useEffect(() => {
    if (organizations.length === 0) {
      setOrganizationIdState(null);
      localStorage.removeItem(STORAGE_KEY);
      return;
    }
    const stillThere = organizations.some((organization) => organization.id === organizationId);
    if (!stillThere) {
      setOrganizationIdState(organizations[0].id);
      localStorage.setItem(STORAGE_KEY, organizations[0].id);
    }
  }, [organizations, organizationId]);

  const setOrganizationId = (id: string) => {
    setOrganizationIdState(id);
    localStorage.setItem(STORAGE_KEY, id);
  };

  const organization = organizations.find((item) => item.id === organizationId) ?? organizations[0] ?? null;

  const value = useMemo(
    () => ({ organization, organizations, setOrganizationId }),
    [organization, organizations],
  );

  return <OrgContext.Provider value={value}>{children}</OrgContext.Provider>;
}

export function useOrganization() {
  const context = useContext(OrgContext);
  if (!context) throw new Error("useOrganization must be used within OrganizationProvider");
  return context;
}
