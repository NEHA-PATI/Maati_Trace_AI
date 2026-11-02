import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import FpoMobileNavigation from "@/features/fpo/shell/FpoMobileNavigation";
import { FpoPortalContext } from "@/features/fpo/shell/FpoPortalContext";
import {
  FPO_NAV_GROUPS,
  getVisibleFpoNavGroups,
} from "@/features/fpo/shell/fpoNavigation";

const enabledEntitlements = Object.fromEntries(
  FPO_NAV_GROUPS.flatMap((group) => group.items)
    .filter((item) => item.feature)
    .map((item) => [item.feature, { enabled: true }]),
);

describe("FPO navigation", () => {
  it("uses one canonical route for farms and monitoring and includes crop performance", () => {
    const items = FPO_NAV_GROUPS.flatMap((group) => group.items);
    const routes = items.map((item) => item.to);

    expect(new Set(routes).size).toBe(routes.length);
    expect(routes).not.toContain("/fpo/farms");
    expect(routes).toContain("/fpo/monitoring");
    expect(routes).toContain("/fpo/crops");
  });

  it("uses the same entitlement keys as the gated pages", () => {
    const items = FPO_NAV_GROUPS.flatMap((group) => group.items);
    const alertRules = items.find((item) => item.to === "/fpo/monitoring/rules");
    const monitoring = items.find((item) => item.to === "/fpo/monitoring");

    expect(alertRules.feature).toBe("PORTFOLIO_MONITORING_ADVANCED");
    expect(monitoring.feature).toBe("FARM_MAP");
    expect(
      getVisibleFpoNavGroups({
        PORTFOLIO_MONITORING_ADVANCED: { enabled: false },
        FARM_MAP: { enabled: true },
      }).flatMap((group) => group.items).map((item) => item.to),
    ).not.toContain("/fpo/monitoring/rules");
  });

  it("exposes non-shortcut features from the mobile More menu", () => {
    render(
      <MemoryRouter>
        <FpoPortalContext.Provider value={{ entitlements: enabledEntitlements }}>
          <FpoMobileNavigation />
        </FpoPortalContext.Provider>
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByRole("button", { name: /More/ }));

    expect(screen.getByRole("navigation", { name: "All FPO features" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Farm requests" })).toHaveAttribute(
      "href",
      "/fpo/relationships",
    );
    expect(screen.getByRole("link", { name: "Crop performance" })).toHaveAttribute(
      "href",
      "/fpo/crops",
    );
    expect(screen.getByRole("link", { name: "Profile" })).toHaveAttribute(
      "href",
      "/fpo/profile",
    );
    fireEvent.click(screen.getByRole("link", { name: "Crop performance" }));
    expect(screen.queryByRole("navigation", { name: "All FPO features" })).not.toBeInTheDocument();
  });
});
