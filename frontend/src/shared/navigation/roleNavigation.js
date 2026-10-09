import { ROLES } from "@/shared/rbac/permissions";

const PUBLIC_ITEMS = [
  { to: "/", label: "Home", end: true },
  { to: "/our-method", label: "Our Method" },
  { to: "/use-cases", label: "Use Cases" },
  { to: "/plans", label: "Plans" },
];

const ROLE_ITEMS = {
  [ROLES.FARMER]: [
    { to: "/farmer/me", label: "Dashboard", end: true },
    { to: "/my-crops/language", label: "My Crop" },
    { to: "/farmer/fpo", label: "FPOs" },
    { to: "/settings", label: "Profile", end: true },
    { to: "/farm-register", label: "Register" },
  ],
  [ROLES.FPO]: [
    { to: "/fpo/overview", label: "FPO Workspace" },
    { to: "/fpo/farmers", label: "Farmers" },
    { to: "/fpo/monitoring", label: "Monitoring" },
    { to: "/fpo/reports", label: "Reports" },
    { to: "/settings", label: "Profile", end: true },
  ],
  [ROLES.ADMIN]: [
    { to: "/admin", label: "Admin Dashboard", end: true },
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
