import { ROLES } from "@/shared/rbac/permissions";

const PUBLIC_ITEMS = [
  { to: "/", label: "Home", labelKey: "home", end: true },
  { to: "/our-method", label: "Our Method", labelKey: "ourMethod" },
  { to: "/use-cases", label: "Use Cases", labelKey: "useCases" },
  { to: "/plans", label: "Plans", labelKey: "plans" },
];

const ROLE_ITEMS = {
  [ROLES.FARMER]: [
    { to: "/farmer/me", label: "Dashboard", labelKey: "dashboard", end: true },
    { to: "/my-crops/language", label: "My Crop", labelKey: "myCrop" },
    { to: "/farmer/fpo", label: "FPOs", labelKey: "fpos" },
    { to: "/settings", label: "Profile", labelKey: "profile", end: true },
    { to: "/farm-register", label: "Register", labelKey: "register" },
  ],
  [ROLES.FPO]: [
    { to: "/fpo/overview", label: "FPO Workspace", labelKey: "fpoWorkspace" },
    { to: "/fpo/farmers", label: "Farmers", labelKey: "farmers" },
    { to: "/fpo/monitoring", label: "Monitoring", labelKey: "monitoring" },
    { to: "/fpo/reports", label: "Reports", labelKey: "reports" },
    { to: "/settings", label: "Profile", labelKey: "profile", end: true },
  ],
  [ROLES.ADMIN]: [
    { to: "/admin", label: "Admin Dashboard", labelKey: "adminDashboard", end: true },
  ],
};

export function getRoleNavigation(role) {
  return ROLE_ITEMS[role] || ROLE_ITEMS[ROLES.FARMER];
}

export function getAuthenticatedNavigation(role) {
  return role === ROLES.ADMIN
    ? getRoleNavigation(role)
    : [...getRoleNavigation(role), ...PUBLIC_ITEMS];
}

export function isNavigationItemActive(pathname, item) {
  if (item.end || item.to === "/") return pathname === item.to;
  return pathname === item.to || pathname.startsWith(`${item.to}/`);
}

export { PUBLIC_ITEMS };
