import { Routes, Route } from "react-router-dom";
import AppShell from "./components/AppShell/AppShell";
import DashboardPage from "./pages/DashboardPage";
import AnalyticsPage from "./pages/AnalyticsPage";
import GraphPage from "./pages/GraphPage";
import ConfigPage from "./pages/ConfigPage";
import ReportPage from "./pages/ReportPage";
import PrototypePage from "./pages/PrototypePage";

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
        <Route path="/graph" element={<GraphPage />} />
        <Route path="/config" element={<ConfigPage />} />
      </Route>
      <Route path="/report/:id" element={<ReportPage />} />
      <Route path="/prototype" element={<PrototypePage />} />
    </Routes>
  );
}
