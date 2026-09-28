import { useFpoPortal } from "@/features/fpo/shell/FpoPortalContext";

export default function FpoFeatureGate({ feature, fallback = null, children }) {
  const { entitlements } = useFpoPortal();
  return entitlements?.[feature]?.enabled ? children : fallback;
}
