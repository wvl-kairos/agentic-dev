import { Routes, Route } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import { DashboardPage } from "@/pages/DashboardPage";
import { CandidatesPage } from "@/pages/CandidatesPage";
import { AssessmentPage } from "@/pages/AssessmentPage";
import { RoleTemplatesPage } from "@/pages/RoleTemplatesPage";

export default function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/candidates" element={<CandidatesPage />} />
        <Route path="/assessment/:id" element={<AssessmentPage />} />
        <Route path="/role-templates" element={<RoleTemplatesPage />} />
      </Routes>
    </AppShell>
  );
}
