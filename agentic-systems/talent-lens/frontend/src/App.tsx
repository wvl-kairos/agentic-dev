import { Routes, Route, Outlet } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import { DashboardPage } from "@/pages/DashboardPage";
import { CandidatesPage } from "@/pages/CandidatesPage";
import { AssessmentPage } from "@/pages/AssessmentPage";
import { RoleTemplatesPage } from "@/pages/RoleTemplatesPage";
import { InterviewsPage } from "@/pages/InterviewsPage";
import { PublicCandidatePage } from "@/pages/PublicCandidatePage";
import { SurveyPage } from "@/pages/SurveyPage";

function AppLayout() {
  return (
    <AppShell>
      <Outlet />
    </AppShell>
  );
}

export default function App() {
  return (
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
  );
}
