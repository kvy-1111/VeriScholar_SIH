import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { useAuth } from "./contexts/AuthContext";
import { AuditPage } from "./pages/AuditPage";
import { CasesPage } from "./pages/CasesPage";
import { CompliancePage } from "./pages/CompliancePage";
import { DashboardPage } from "./pages/DashboardPage";
import { LoginPage } from "./pages/LoginPage";
import { QRPage } from "./pages/QRPage";
import { StudentsPage } from "./pages/StudentsPage";

function ProtectedRoutes() {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/students" element={<StudentsPage />} />
        <Route path="/compliance" element={<CompliancePage />} />
        <Route path="/cases" element={<CasesPage />} />
        <Route path="/audit" element={<AuditPage />} />
        <Route path="/qr" element={<QRPage />} />
      </Route>
    </Routes>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/*" element={<ProtectedRoutes />} />
    </Routes>
  );
}
