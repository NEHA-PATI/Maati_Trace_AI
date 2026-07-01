import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import Home from "@/pages/Home";
import OurMethod from "@/pages/OurMethod";
import UseCases from "@/pages/UseCases";
import Login from "@/pages/Login";
import ProtectedRoute from "@/components/ProtectedRoute";
import AdminDashboard from "@/pages/AdminDashboard";
import FpoDashboard from "@/pages/FpoDashboard";
import FarmerProfile from "@/pages/FarmerProfile";
import LandIntelligence from "@/pages/LandIntelligence";
import FarmRegister from "@/pages/FarmRegister";
import BulkUpload from "@/pages/BulkUpload";
import Notifications from "@/pages/Notifications";

const Placeholder = ({ title }) => <div className="min-h-screen p-10 text-3xl font-black">{title}</div>;

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Placeholder title="Register" />} />
        <Route path="/forgot-password" element={<Placeholder title="Forgot Password" />} />
        <Route path="/reset-password" element={<Placeholder title="Reset Password" />} />
        <Route path="/use-cases" element={<UseCases />} />
        <Route path="/our-method" element={<OurMethod />} />
        <Route element={<ProtectedRoute permission="/admin" />}>
          <Route path="/admin" element={<AdminDashboard />} />
        </Route>
        <Route element={<ProtectedRoute permission="/fpo/me" />}>
          <Route path="/fpo/me" element={<FpoDashboard />} />
          <Route path="/my-fpo" element={<FpoDashboard />} />
          <Route path="/fpo/:fpoId" element={<FpoDashboard />} />
        </Route>
        <Route element={<ProtectedRoute permission="/farmer/me" />}>
          <Route path="/farmer/me" element={<FarmerProfile />} />
          <Route path="/farmers/:farmerId" element={<FarmerProfile />} />
          <Route path="/land/:farmId" element={<LandIntelligence />} />
          <Route path="/farm-register" element={<FarmRegister />} />
          <Route path="/bulk-upload" element={<BulkUpload />} />
          <Route path="/notifications" element={<Notifications />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
