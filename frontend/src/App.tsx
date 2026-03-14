import { Routes, Route } from "react-router-dom";
import DashboardPage from "./pages/DashboardPage";
import ReportPage from "./pages/ReportPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<DashboardPage />} />
      <Route path="/report/:id" element={<ReportPage />} />
    </Routes>
  );
}
