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
import Register from "@/pages/Register";
import ForgotPassword from "@/pages/ForgotPassword";
import ResetPassword from "@/pages/ResetPassword";
import MyFpo from "@/pages/MyFpo";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />
        <Route path="/use-cases" element={<UseCases />} />
        <Route path="/our-method" element={<OurMethod />} />
        <Route element={<ProtectedRoute permission="/admin" />}>
          <Route path="/admin" element={<AdminDashboard />} />
        </Route>
        <Route element={<ProtectedRoute permission="/fpo/me" />}>
          <Route path="/fpo/me" element={<FpoDashboard />} />
          <Route path="/my-fpo" element={<MyFpo />} />
          <Route path="/fpo/:fpoId" element={<FpoDashboard />} />
        </Route>
        <Route element={<ProtectedRoute permission="/farmer/me" />}>
          <Route path="/farmer/me" element={<FarmerProfile />} />
        </Route>
        <Route element={<ProtectedRoute permission="/farmers/:farmerId" />}>
          <Route path="/farmers/:farmerId" element={<FarmerProfile />} />
        </Route>
        <Route element={<ProtectedRoute permission="/land/:farmId" />}>
          <Route path="/land/:farmId" element={<LandIntelligence />} />
        </Route>
        <Route element={<ProtectedRoute permission="/farm-register" />}>
          <Route path="/farm-register" element={<FarmRegister />} />
        </Route>
        <Route element={<ProtectedRoute permission="/bulk-upload" />}>
          <Route path="/bulk-upload" element={<BulkUpload />} />
        </Route>
        <Route element={<ProtectedRoute permission="/notifications" />}>
          <Route path="/notifications" element={<Notifications />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
