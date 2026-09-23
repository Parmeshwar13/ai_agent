import { Navigate, Route, Routes } from "react-router-dom";

import { AppShell } from "./components/AppShell";
import { BrandMark } from "./components/BrandMark";
import { useAuth } from "./hooks/useAuth";
import { OrganizationProvider } from "./hooks/useOrganization";
import { ToastProvider } from "./hooks/useToast";
import { DashboardPage } from "./pages/DashboardPage";
import { LoginPage } from "./pages/LoginPage";
import { ProjectCreatePage } from "./pages/ProjectCreatePage";
import { ProjectDetailPage } from "./pages/ProjectDetailPage";
import { ProjectsPage } from "./pages/ProjectsPage";
import { RegisterPage } from "./pages/RegisterPage";
import { SettingsPage } from "./pages/SettingsPage";
import { UpcomingPage } from "./pages/UpcomingPage";

function BootScreen() {
  return (
    <div className="boot">
      <BrandMark size={40} />
      <p>Opening Orbit</p>
    </div>
  );
}

function RequireAuth() {
  const { user, ready } = useAuth();
  if (!ready) return <BootScreen />;
  if (!user) return <Navigate to="/login" replace />;
  return (
    <OrganizationProvider>
      <ToastProvider>
        <AppShell />
      </ToastProvider>
    </OrganizationProvider>
  );
}

function GuestOnly({ children }: { children: JSX.Element }) {
  const { user, ready } = useAuth();
  if (!ready) return <BootScreen />;
  if (user) return <Navigate to="/dashboard" replace />;
  return children;
}

export function App() {
  return (
    <Routes>
      <Route
        path="/login"
        element={
          <GuestOnly>
            <LoginPage />
          </GuestOnly>
        }
      />
      <Route
        path="/register"
        element={
          <GuestOnly>
            <RegisterPage />
          </GuestOnly>
        }
      />
      <Route element={<RequireAuth />}>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/projects" element={<ProjectsPage />} />
        <Route path="/projects/new" element={<ProjectCreatePage />} />
        <Route path="/projects/:projectId" element={<ProjectDetailPage />} />
        <Route path="/tasks" element={<UpcomingPage module="Tasks" />} />
        <Route path="/wiki" element={<UpcomingPage module="Wiki" />} />
        <Route path="/architecture" element={<UpcomingPage module="Architecture" />} />
        <Route path="/runs" element={<UpcomingPage module="Agent Runs" />} />
        <Route path="/repository" element={<UpcomingPage module="Repository" />} />
        <Route path="/pull-requests" element={<UpcomingPage module="Pull Requests" />} />
        <Route path="/tests" element={<UpcomingPage module="Tests" />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
