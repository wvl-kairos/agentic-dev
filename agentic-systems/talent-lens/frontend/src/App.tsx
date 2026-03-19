import { Component, type ReactNode } from "react";
import { Routes, Route, Outlet } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import { DashboardPage } from "@/pages/DashboardPage";
import { CandidatesPage } from "@/pages/CandidatesPage";
import { AssessmentPage } from "@/pages/AssessmentPage";
import { RoleTemplatesPage } from "@/pages/RoleTemplatesPage";
import { InterviewsPage } from "@/pages/InterviewsPage";
import { PublicCandidatePage } from "@/pages/PublicCandidatePage";
import { SurveyPage } from "@/pages/SurveyPage";

class ErrorBoundary extends Component<
  { children: ReactNode },
  { error: Error | null }
> {
  constructor(props: { children: ReactNode }) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  render() {
    if (this.state.error) {
      return (
        <div style={{ padding: 32, fontFamily: "monospace" }}>
          <h2 style={{ color: "red" }}>Something went wrong</h2>
          <pre style={{ whiteSpace: "pre-wrap", color: "#333" }}>
            {this.state.error.message}
          </pre>
          <pre style={{ whiteSpace: "pre-wrap", color: "#666", fontSize: 12 }}>
            {this.state.error.stack}
          </pre>
        </div>
      );
    }
    return this.props.children;
  }
}

function AppLayout() {
  return (
    <AppShell>
      <ErrorBoundary>
        <Outlet />
      </ErrorBoundary>
    </AppShell>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <Routes>
        {/* Public pages — no AppShell */}
        <Route path="/shared/:token" element={<PublicCandidatePage />} />
        <Route path="/survey/:roleTemplateId" element={<SurveyPage />} />

        {/* App pages — with AppShell layout */}
        <Route element={<AppLayout />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/candidates" element={<CandidatesPage />} />
          <Route path="/assessment/:id" element={<AssessmentPage />} />
          <Route path="/role-templates" element={<RoleTemplatesPage />} />
          <Route path="/interviews" element={<InterviewsPage />} />
        </Route>
      </Routes>
    </ErrorBoundary>
  );
}
