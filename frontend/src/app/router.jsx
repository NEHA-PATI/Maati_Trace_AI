import { createBrowserRouter, Navigate, Outlet } from "react-router-dom";

import ScrollToTop from "@/components/ScrollToTop";

import ProtectedRoute from "@/features/auth/components/ProtectedRoute";
import AcceptInvitationPage from "@/features/auth/pages/AcceptInvitationPage";
import ForgotPasswordPage from "@/features/auth/pages/ForgotPasswordPage";
import LoginPage from "@/features/auth/pages/LoginPage";
import RegisterPage from "@/features/auth/pages/RegisterPage";
import ResetPasswordPage from "@/features/auth/pages/ResetPasswordPage";
import FpoAccessRequestPage from "@/features/fpo-access/pages/FpoAccessRequestPage";
import FpoAccessAdminPage from "@/features/fpo-access/pages/FpoAccessAdminPage";
import {
  CropLanguagePage,
  CropStagePage,
  MyCropsPage,
  ObservationHistoryPage,
} from "@/features/crop-observation";
import {
  CropObservationAdminHubPage,
  CropConfigurationEditorPage,
  CropConfigurationPage,
  CropObservationRecordsPage,
} from "@/features/crop-observation-admin";
import { PlansPage } from "@/features/plans";
import { ProfileSettingsPage } from "@/features/profile";
import {
  FpoAppShell,
  FpoDashboardPage,
  FpoFarmerDirectoryPage,
} from "@/features/fpo";
import FpoVerificationPage from "@/features/fpo/dashboard/FpoVerificationPage";
import FpoFarmerDetailPage from "@/features/fpo/farmers/FpoFarmerDetailPage";
import FpoFarmIntelligencePage from "@/features/fpo/farmers/FpoFarmIntelligencePage";
import FpoAlertsPage from "@/features/fpo/dashboard/FpoAlertsPage";
import FpoReportsPage from "@/features/fpo/dashboard/FpoReportsPage";
import FpoMonitoringPage from "@/features/fpo/dashboard/FpoMonitoringPage";
import FpoGeographyPage from "@/features/fpo/dashboard/FpoGeographyPage";
import FpoCropPerformancePage from "@/features/fpo/dashboard/FpoCropPerformancePage";
import FpoImportsPage from "@/features/fpo/dashboard/FpoImportsPage";
import FpoDataQualityPage from "@/features/fpo/dashboard/FpoDataQualityPage";
import {
  FpoSegmentsPage,
  FpoSeasonsPage,
  FpoTasksPage,
} from "@/features/fpo/dashboard/FpoGrowthOperationsPages";
import FpoClassBMonitoringPage from "@/features/fpo/dashboard/FpoClassBMonitoringPage";
import FpoAdvisoriesPage from "@/features/fpo/dashboard/FpoAdvisoriesPage";
import {
  FpoInputsPage,
  FpoForecastsPage,
  FpoAdvancedReportsPage,
} from "@/features/fpo/dashboard/FpoB7Pages";
import FpoClassCCommercialPage from "@/features/fpo/dashboard/FpoClassCCommercialPage";
import FpoClassCOperationsPage from "@/features/fpo/dashboard/FpoClassCOperationsPage";
import FpoClassCExecutionPage from "@/features/fpo/dashboard/FpoClassCExecutionPage";
import FpoClassCCompliancePage from "@/features/fpo/dashboard/FpoClassCCompliancePage";
import FpoClassCIntegrationsPage from "@/features/fpo/dashboard/FpoClassCIntegrationsPage";
import FpoVerificationWorkspacePage from "@/pages/FpoVerificationWorkspacePage";
import FpoProvisioningRoute from "@/features/fpo/access/FpoProvisioningRoute";

import AdminDashboard from "@/pages/AdminDashboard";
import SystemManagementPage from "@/pages/SystemManagementPage";
import HistoricalAcquisitionPage from "@/pages/HistoricalAcquisitionPage";
import BulkUpload from "@/pages/BulkUpload";
import FarmRegister from "@/pages/FarmRegister";
import FarmerProfile from "@/pages/FarmerProfile";
import FpoAdminPage from "@/pages/FpoAdminPage";
import FarmerFpoPage from "@/pages/FarmerFpoPage";
import FarmerFarmFpoRelationshipPage from "@/pages/FarmerFarmFpoRelationshipPage";
import FarmerImportedOnboardingPage from "@/pages/FarmerImportedOnboardingPage";
import FpoRelationshipsPage from "@/pages/FpoRelationshipsPage";
import Home from "@/pages/Home";
import LandIntelligence from "@/pages/LandIntelligence";
import MyFpo from "@/pages/MyFpo";
import Notifications from "@/pages/Notifications";
import OurMethod from "@/pages/OurMethod";
import UseCases from "@/pages/UseCases";

function RouteLayout() {
  return (
    <>
      <ScrollToTop />
      <Outlet />
    </>
  );
}

export const router = createBrowserRouter(
  [
    {
      element: <RouteLayout />,
      children: [
        { path: "/", element: <Home /> },
        { path: "/login", element: <LoginPage /> },
        { path: "/register", element: <RegisterPage /> },
        { path: "/forgot-password", element: <ForgotPasswordPage /> },
        { path: "/reset-password", element: <ResetPasswordPage /> },
        { path: "/accept-invitation", element: <AcceptInvitationPage /> },
        { path: "/request-fpo-access", element: <FpoAccessRequestPage /> },
        { path: "/use-cases", element: <UseCases /> },
        { path: "/our-method", element: <OurMethod /> },
        { path: "/plans", element: <PlansPage /> },

        {
          element: <ProtectedRoute permission="adminDashboard" />,
          children: [
            { path: "/admin", element: <AdminDashboard /> },
            { path: "/admin/fpo-access", element: <FpoAccessAdminPage /> },
            { path: "/admin/fpo", element: <FpoAdminPage /> },
            {
              path: "/admin/fpo/verification",
              element: <FpoVerificationWorkspacePage />,
            },
            { path: "/admin/system", element: <SystemManagementPage /> },
            { path: "/admin/data-acquisition", element: <HistoricalAcquisitionPage /> },
            {
              path: "/admin/feature-processing",
              element: <SystemManagementPage />,
            },
          ],
        },
        {
          element: <ProtectedRoute permission="cropObservationAdmin" />,
          children: [
            {
              path: "/admin/crop-observation",
              element: <CropObservationAdminHubPage />,
            },
            {
              path: "/admin/crop-observation/config/:cropCode",
              element: <CropConfigurationEditorPage />,
            },
            {
              path: "/admin/crop-observations",
              element: <CropObservationRecordsPage />,
            },
            {
              path: "/admin/crop-observations/config",
              element: <CropConfigurationPage />,
            },
            {
              path: "/admin/crop-observations/config/:cropCode",
              element: <CropConfigurationEditorPage />,
            },
          ],
        },
        {
          element: <ProtectedRoute permission="fpoDashboard" />,
          children: [
            {
              path: "/fpo/me",
              element: <Navigate to="/fpo/overview" replace />,
            },
          ],
        },
        {
          element: <FpoProvisioningRoute />,
          children: [
            {
              element: <FpoAppShell />,
              children: [
                { path: "/fpo/overview", element: <FpoDashboardPage /> },
                {
                  path: "/fpo/dashboard",
                  element: <Navigate to="/fpo/overview" replace />,
                },
                { path: "/fpo/farmers", element: <FpoFarmerDirectoryPage /> },
                { path: "/fpo/farms", element: <FpoMonitoringPage /> },
                {
                  path: "/fpo/farmers/:farmerId",
                  element: <FpoFarmerDetailPage />,
                },
                {
                  path: "/fpo/farmers/:farmerId/farms/:farmId/intelligence",
                  element: <FpoFarmIntelligencePage />,
                },
                { path: "/fpo/alerts", element: <FpoAlertsPage /> },
                { path: "/fpo/reports", element: <FpoReportsPage /> },
                { path: "/fpo/monitoring", element: <FpoMonitoringPage /> },
                { path: "/fpo/geography", element: <FpoGeographyPage /> },
                { path: "/fpo/crops", element: <FpoCropPerformancePage /> },
                { path: "/fpo/imports", element: <FpoImportsPage /> },
                { path: "/fpo/data-quality", element: <FpoDataQualityPage /> },
                { path: "/fpo/farmers/segments", element: <FpoSegmentsPage /> },
                { path: "/fpo/seasons", element: <FpoSeasonsPage /> },
                { path: "/fpo/tasks", element: <FpoTasksPage /> },
                {
                  path: "/fpo/monitoring/rules",
                  element: <FpoClassBMonitoringPage />,
                },
                { path: "/fpo/advisories", element: <FpoAdvisoriesPage /> },
                { path: "/fpo/inputs", element: <FpoInputsPage /> },
                { path: "/fpo/forecasts", element: <FpoForecastsPage /> },
                {
                  path: "/fpo/reports/advanced",
                  element: <FpoAdvancedReportsPage />,
                },
                {
                  path: "/fpo/commercial",
                  element: <FpoClassCCommercialPage />,
                },
                {
                  path: "/fpo/operations",
                  element: <FpoClassCOperationsPage />,
                },
                { path: "/fpo/execution", element: <FpoClassCExecutionPage /> },
                {
                  path: "/fpo/compliance",
                  element: <FpoClassCCompliancePage />,
                },
                {
                  path: "/fpo/integrations",
                  element: <FpoClassCIntegrationsPage />,
                },
                { path: "/fpo/profile", element: <ProfileSettingsPage /> },
                { path: "/fpo/verification", element: <FpoVerificationPage /> },
                {
                  path: "/fpo/relationships",
                  element: <FpoRelationshipsPage />,
                },
              ],
            },
          ],
        },
        { path: "/fpo/me", element: <Navigate to="/fpo/overview" replace /> },
        {
          element: <ProtectedRoute permission="myFpo" />,
          children: [{ path: "/my-fpo", element: <MyFpo /> }],
        },
        {
          element: <ProtectedRoute permission="farmerSelfProfile" />,
          children: [
            { path: "/farmer/me", element: <FarmerProfile /> },
            { path: "/farmer/fpo", element: <FarmerFpoPage /> },
            { path: "/farmer/farms/:farmId/fpo/:relationshipId", element: <FarmerFarmFpoRelationshipPage /> },
            {
              path: "/farmer/imported-onboarding",
              element: <FarmerImportedOnboardingPage />,
            },
          ],
        },
        {
          element: <ProtectedRoute permission="farmerProfile" />,
          children: [{ path: "/farmers/:farmerId", element: <FarmerProfile /> }],
        },
        {
          element: <ProtectedRoute permission="landIntelligence" />,
          children: [{ path: "/land/:farmId", element: <LandIntelligence /> }],
        },
        {
          element: <ProtectedRoute permission="cropDiary" />,
          children: [
            { path: "/my-crops/language", element: <CropLanguagePage /> },
            { path: "/my-crops", element: <MyCropsPage /> },
            {
              path: "/my-crops/:farmId/:cropCycleId/history",
              element: <ObservationHistoryPage />,
            },
            {
              path: "/my-crops/:farmId/:cropCycleId/:stageCode",
              element: <CropStagePage />,
            },
          ],
        },
        {
          element: <ProtectedRoute permission="farmRegister" />,
          children: [{ path: "/farm-register", element: <FarmRegister /> }],
        },
        {
          element: <ProtectedRoute permission="bulkUpload" />,
          children: [{ path: "/bulk-upload", element: <BulkUpload /> }],
        },
        {
          element: <ProtectedRoute permission="notifications" />,
          children: [{ path: "/notifications", element: <Notifications /> }],
        },
        {
          element: <ProtectedRoute permission="settings" />,
          children: [{ path: "/settings", element: <ProfileSettingsPage /> }],
        },
        { path: "*", element: <Navigate to="/" replace /> },
      ],
    },
  ],
  {
    future: {
      v7_relativeSplatPath: true,
      v7_startTransition: true,
    },
  },
);
