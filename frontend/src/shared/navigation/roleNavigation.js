import { ROLES } from "@/shared/rbac/permissions";

const PUBLIC_ITEMS = [
  { to: "/", labelKey: "home", label: "Home", end: true },
  { to: "/our-method", labelKey: "ourMethod", label: "Our Method" },
  { to: "/use-cases", labelKey: "useCases", label: "Use Cases" },
  { to: "/plans", labelKey: "plans", label: "Plans" },
];

const ROLE_ITEMS = {
  [ROLES.FARMER]: [
    { to: "/farmer/me", labelKey: "dashboard", label: "Dashboard", end: true },
    { to: "/my-crops/language", labelKey: "myCrop", label: "My Crop" },
    { to: "/farmer/fpo", labelKey: "fpos", label: "FPOs" },
    { to: "/settings", labelKey: "profile", label: "Profile", end: true },
    { to: "/farm-register", labelKey: "register", label: "Register" },
  ],
  [ROLES.FPO]: [
    { to: "/fpo/overview", labelKey: "fpoWorkspace", label: "FPO Workspace" },
    { to: "/fpo/farmers", labelKey: "farmers", label: "Farmers" },
    { to: "/fpo/monitoring", labelKey: "monitoring", label: "Monitoring" },
    { to: "/fpo/reports", labelKey: "reports", label: "Reports" },
    { to: "/settings", labelKey: "profile", label: "Profile", end: true },
  ],
  [ROLES.ADMIN]: [
    { to: "/admin", labelKey: "adminDashboard", label: "Admin Dashboard", end: true },
    { to: "/admin/fpo-access", labelKey: "fpoAccess", label: "FPO Access" },
    { to: "/admin/fpo", labelKey: "fpoManagement", label: "FPO Management" },
    { to: "/admin/crop-observation", labelKey: "cropOperations", label: "Crop Operations" },
    { to: "/admin/system", labelKey: "system", label: "System" },
    { to: "/settings", labelKey: "profile", label: "Profile", end: true },
  ],
};

export function getRoleNavigation(role) {
  return ROLE_ITEMS[role] || ROLE_ITEMS[ROLES.FARMER];
}

export function getAuthenticatedNavigation(role) {
  return [...getRoleNavigation(role), ...PUBLIC_ITEMS];
}

export function isNavigationItemActive(pathname, item) {
  if (item.end || item.to === "/") return pathname === item.to;
  return pathname === item.to || pathname.startsWith(`${item.to}/`);
}

export { PUBLIC_ITEMS };
