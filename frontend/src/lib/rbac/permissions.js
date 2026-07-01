const ROUTE_RULES = {
  "/admin": ["admin"],
  "/fpo/me": ["admin", "fpo"],
  "/fpo/:fpoId": ["admin", "fpo"],
  "/my-fpo": ["admin", "fpo"],
  "/farmer/me": ["farmer"],
  "/farmers/:farmerId": ["admin", "fpo", "farmer"],
  "/land/:farmId": ["admin", "fpo", "farmer"],
  "/farm-register": ["admin", "fpo", "farmer"],
  "/bulk-upload": ["admin", "fpo"],
  "/notifications": ["admin", "fpo", "farmer"],
  "/use-cases": ["admin", "fpo", "farmer"],
  "/our-method": ["admin", "fpo", "farmer"],
};
export const canAccess = (user, permission) => !!user && ROUTE_RULES[permission]?.includes(user.role);
export const canSeeAdminControls = (user) => user?.role === "admin";
export const canSeeFpoControls = (user) => user?.role === "admin" || user?.role === "fpo";
export const canBulkUpload = (user) => user?.role === "admin" || user?.role === "fpo";
export const canEditFarm = (user) => !!user;
export const canViewTechnicalH3Layer = (user) => user?.role === "admin" || user?.role === "fpo";
