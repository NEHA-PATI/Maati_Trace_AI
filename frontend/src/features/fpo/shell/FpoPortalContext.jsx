import { createContext, useContext } from "react";

export const FpoPortalContext = createContext({ bootstrap: null, entitlements: {} });

export function useFpoPortal() {
  return useContext(FpoPortalContext);
}
