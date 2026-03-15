import { Routes, Route } from "react-router-dom";
import AppShell from "./components/AppShell/AppShell";
import DashboardPage from "./pages/DashboardPage";
import AnalyticsPage from "./pages/AnalyticsPage";
import ReportPage from "./pages/ReportPage";

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
      </Route>
      <Route path="/report/:id" element={<ReportPage />} />
    </Routes>
  );
}
