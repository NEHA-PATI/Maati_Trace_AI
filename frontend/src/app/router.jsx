import { createBrowserRouter, Navigate } from "react-router-dom";

import ProtectedRoute from "@/features/auth/components/ProtectedRoute";
import AcceptInvitationPage from "@/features/auth/pages/AcceptInvitationPage";
import ForgotPasswordPage from "@/features/auth/pages/ForgotPasswordPage";
import LoginPage from "@/features/auth/pages/LoginPage";
import RegisterPage from "@/features/auth/pages/RegisterPage";
import ResetPasswordPage from "@/features/auth/pages/ResetPasswordPage";
import FpoAccessRequestPage from "@/features/fpo-access/pages/FpoAccessRequestPage";
import FpoAccessAdminPage from "@/features/fpo-access/pages/FpoAccessAdminPage";

import AdminDashboard from "@/pages/AdminDashboard";
import BulkUpload from "@/pages/BulkUpload";
import FarmRegister from "@/pages/FarmRegister";
import FarmerProfile from "@/pages/FarmerProfile";
import FpoDashboard from "@/pages/FpoDashboard";
import Home from "@/pages/Home";
import LandIntelligence from "@/pages/LandIntelligence";
import MyFpo from "@/pages/MyFpo";
import Notifications from "@/pages/Notifications";
import OurMethod from "@/pages/OurMethod";
import Settings from "@/pages/Settings";
import UseCases from "@/pages/UseCases";

export const router = createBrowserRouter([
  { path: "/", element: <Home /> },
  { path: "/login", element: <LoginPage /> },
  { path: "/register", element: <RegisterPage /> },
  { path: "/forgot-password", element: <ForgotPasswordPage /> },
  { path: "/reset-password", element: <ResetPasswordPage /> },
  { path: "/accept-invitation", element: <AcceptInvitationPage /> },
  { path: "/request-fpo-access", element: <FpoAccessRequestPage /> },
  { path: "/use-cases", element: <UseCases /> },
  { path: "/our-method", element: <OurMethod /> },

  { element: <ProtectedRoute permission="adminDashboard" />, children: [
    { path: "/admin", element: <AdminDashboard /> },
    { path: "/admin/fpo-access", element: <FpoAccessAdminPage /> },
  ] },
  { element: <ProtectedRoute permission="fpoDashboard" />, children: [{ path: "/fpo/me", element: <FpoDashboard /> }] },
  { element: <ProtectedRoute permission="myFpo" />, children: [{ path: "/my-fpo", element: <MyFpo /> }] },
  {
    element: <ProtectedRoute permission="farmerProfile" />,
    children: [
      { path: "/farmer/me", element: <FarmerProfile /> },
      { path: "/farmers/:farmerId", element: <FarmerProfile /> },
    ],
  },
  { element: <ProtectedRoute permission="landIntelligence" />, children: [{ path: "/land/:farmId", element: <LandIntelligence /> }] },
  { element: <ProtectedRoute permission="farmRegister" />, children: [{ path: "/farm-register", element: <FarmRegister /> }] },
  { element: <ProtectedRoute permission="bulkUpload" />, children: [{ path: "/bulk-upload", element: <BulkUpload /> }] },
  { element: <ProtectedRoute permission="notifications" />, children: [{ path: "/notifications", element: <Notifications /> }] },
  { element: <ProtectedRoute permission="settings" />, children: [{ path: "/settings", element: <Settings /> }] },
  { path: "*", element: <Navigate to="/" replace /> },
]);
