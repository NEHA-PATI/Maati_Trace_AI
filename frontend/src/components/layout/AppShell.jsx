import AppTopbar from "./AppTopbar";
import MobileTabBar from "./MobileTabBar";
import AdminSidebar from "./AdminSidebar";
import { useAuth } from "@/features/auth/context/useAuth";
import { useLocation } from "react-router-dom";

export default function AppShell({ children }) {
  const { user } = useAuth();
  const location = useLocation();
  const isAdminArea = String(user?.role || "").toLowerCase() === "admin" && location.pathname.startsWith("/admin");

  return (
    <div className="min-h-screen bg-background text-foreground">
      <AppTopbar />
      {isAdminArea ? <AdminSidebar /> : null}
      <div className={`w-full px-[0.4cm] pt-16 md:pt-16 ${isAdminArea ? "lg:pl-64" : ""}`}>
        <main className="app-main mt-tabbar-safe min-h-[calc(100vh-4rem)] w-full">
          {children}
        </main>
      </div>
      <MobileTabBar />
    </div>
  );
}
