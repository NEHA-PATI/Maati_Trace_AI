export const DEFAULT_ROUTE_BY_ROLE = Object.freeze({
  admin: "/admin",
  fpo: "/fpo/me",
  farmer: "/farmer/me",
});

export function getDefaultRouteForRole(role) {
  return DEFAULT_ROUTE_BY_ROLE[String(role || "").toLowerCase()] || "/";
}

export const AUTH_ROUTES = Object.freeze({
  login: "/login",
  register: "/register",
  forgotPassword: "/forgot-password",
  resetPassword: "/reset-password",
  acceptInvitation: "/accept-invitation",
  requestFpoAccess: "/request-fpo-access",
  completeProfile: "/settings",
  registerLand: "/farm-register",
});
