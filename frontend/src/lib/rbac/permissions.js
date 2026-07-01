export const ROLES = {
  ADMIN: "admin",
  FPO: "fpo",
  FARMER: "farmer",
};

export const ROUTE_RULES = {
  adminDashboard: [ROLES.ADMIN],
  fpoDashboard: [ROLES.ADMIN, ROLES.FPO],
  myFpo: [ROLES.ADMIN, ROLES.FPO],
  farmerProfile: [ROLES.ADMIN, ROLES.FPO, ROLES.FARMER],
  landIntelligence: [ROLES.ADMIN, ROLES.FPO, ROLES.FARMER],
  farmRegister: [ROLES.ADMIN, ROLES.FPO, ROLES.FARMER],
  bulkUpload: [ROLES.ADMIN, ROLES.FPO],
  notifications: [ROLES.ADMIN, ROLES.FPO, ROLES.FARMER],
  publicInternal: [ROLES.ADMIN, ROLES.FPO, ROLES.FARMER],
};

const PATH_PERMISSION_MAP = {
  "/admin": "adminDashboard",
  "/fpo/me": "fpoDashboard",
  "/fpo/:fpoId": "fpoDashboard",
  "/my-fpo": "myFpo",
  "/farmer/me": "farmerProfile",
  "/farmers/:farmerId": "farmerProfile",
  "/land/:farmId": "landIntelligence",
  "/farm-register": "farmRegister",
  "/bulk-upload": "bulkUpload",
  "/notifications": "notifications",
  "/use-cases": "publicInternal",
  "/our-method": "publicInternal",
};

export function hasRole(user, allowedRoles) {
  if (!user) return false;
  return allowedRoles.includes(user.role);
}

export function canAccess(user, permission) {
  const key = PATH_PERMISSION_MAP[permission] || permission;
  return hasRole(user, ROUTE_RULES[key] || []);
}

export function canSeeFpoControls(user) {
  return user?.role === ROLES.ADMIN || user?.role === ROLES.FPO;
}

export function canSeeAdminControls(user) {
  return user?.role === ROLES.ADMIN;
}

export function canBulkUpload(user) {
  return user?.role === ROLES.ADMIN || user?.role === ROLES.FPO;
}

export function canEditFarm(user) {
  return !!user;
}

export function canViewTechnicalH3Layer(user) {
  return user?.role === ROLES.ADMIN || user?.role === ROLES.FPO;
}
