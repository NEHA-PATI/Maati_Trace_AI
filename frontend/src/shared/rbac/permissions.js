export const ROLES = Object.freeze({
  ADMIN: "admin",
  FPO: "fpo",
  FARMER: "farmer",
});

export const ROUTE_RULES = Object.freeze({
  adminDashboard: [ROLES.ADMIN],

  fpoDashboard: [
    ROLES.ADMIN,
    ROLES.FPO,
  ],

  fpoAccessAdministration: [
    ROLES.ADMIN,
  ],

  myFpo: [
    ROLES.ADMIN,
    ROLES.FPO,
  ],

  farmerProfile: [
    ROLES.ADMIN,
    ROLES.FPO,
    ROLES.FARMER,
  ],

  landIntelligence: [
    ROLES.ADMIN,
    ROLES.FPO,
    ROLES.FARMER,
  ],

  farmRegister: [
    ROLES.ADMIN,
    ROLES.FPO,
    ROLES.FARMER,
  ],

  bulkUpload: [
    ROLES.ADMIN,
    ROLES.FPO,
  ],

  notifications: [
    ROLES.ADMIN,
    ROLES.FPO,
    ROLES.FARMER,
  ],

  settings: [
    ROLES.ADMIN,
    ROLES.FPO,
    ROLES.FARMER,
  ],

  publicInternal: [
    ROLES.ADMIN,
    ROLES.FPO,
    ROLES.FARMER,
  ],
});

const PATH_PERMISSION_MAP = Object.freeze({
  "/admin": "adminDashboard",

  "/admin/fpo-access":
    "fpoAccessAdministration",

  "/fpo/me": "fpoDashboard",
  "/fpo/:fpoId": "fpoDashboard",

  "/my-fpo": "myFpo",

  "/farmer/me": "farmerProfile",
  "/farmers/:farmerId": "farmerProfile",

  "/land/:farmId": "landIntelligence",

  "/farm-register": "farmRegister",

  "/bulk-upload": "bulkUpload",

  "/notifications": "notifications",

  "/settings": "settings",

  "/use-cases": "publicInternal",

  "/our-method": "publicInternal",

  "/plans": "publicInternal",
});

export function hasRole(user, allowedRoles = []) {
  if (!user?.role) {
    return false;
  }

  return allowedRoles.includes(user.role);
}

export function canAccess(user, permissionOrPath) {
  const permission =
    PATH_PERMISSION_MAP[permissionOrPath] ||
    permissionOrPath;

  const allowedRoles =
    ROUTE_RULES[permission] || [];

  return hasRole(user, allowedRoles);
}

export function canSeeFpoControls(user) {
  return (
    user?.role === ROLES.ADMIN ||
    user?.role === ROLES.FPO
  );
}

export function canSeeAdminControls(user) {
  return user?.role === ROLES.ADMIN;
}

export function canBulkUpload(user) {
  return (
    user?.role === ROLES.ADMIN ||
    user?.role === ROLES.FPO
  );
}

export function canEditFarm(user, farm = null) {
  if (!user) {
    return false;
  }

  if (user.role === ROLES.ADMIN) {
    return true;
  }

  if (!farm) {
    return true;
  }

  if (user.role === ROLES.FPO) {
    return Boolean(
      user.fpo_id &&
        farm.fpo_id &&
        user.fpo_id === farm.fpo_id,
    );
  }

  if (user.role === ROLES.FARMER) {
    return Boolean(
      user.farmer_id &&
        farm.farmer_id &&
        user.farmer_id === farm.farmer_id,
    );
  }

  return false;
}

export function canViewTechnicalH3Layer(user) {
  return (
    user?.role === ROLES.ADMIN ||
    user?.role === ROLES.FPO
  );
}
