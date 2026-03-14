import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Layout from "./Layout";
import PatientSelect from "./pages/PatientSelect";
import Dashboard from "./pages/Dashboard";
import Medications from "./pages/Medications";
import MedicationLogs from "./pages/MedicationLogs";
import Symptoms from "./pages/Symptoms";
import Vitals from "./pages/Vitals";
import VitalsAdd from "./pages/VitalsAdd";
import Export from "./pages/Export";
import Recommendations from "./pages/Recommendations";

const API = import.meta.env.VITE_API_URL || "/api";

export { API };

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<PatientSelect />} />
          <Route path="patient/:patientId" element={<Dashboard />} />
          <Route path="patient/:patientId/medications" element={<Medications />} />
          <Route path="patient/:patientId/medications/logs" element={<MedicationLogs />} />
          <Route path="patient/:patientId/symptoms" element={<Symptoms />} />
          <Route path="patient/:patientId/vitals" element={<Vitals />} />
          <Route path="patient/:patientId/vitals/add" element={<VitalsAdd />} />
          <Route path="patient/:patientId/export" element={<Export />} />
          <Route path="patient/:patientId/recommendations" element={<Recommendations />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
