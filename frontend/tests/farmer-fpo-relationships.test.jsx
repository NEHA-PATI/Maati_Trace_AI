import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import FarmerFpoPage from "@/pages/FarmerFpoPage";

const api = vi.hoisted(() => ({
  getFarms: vi.fn(),
  createFpoSupportTicket: vi.fn(),
  discoverFpos: vi.fn(),
  getFarmerFpoRelationships: vi.fn(),
  getFpoRelationshipConsentPolicy: vi.fn(),
  requestFarmerFpoRelationship: vi.fn(),
  revokeFarmerFpoRelationship: vi.fn(),
  cancelFarmerFpoRelationship: vi.fn(),
}));

vi.mock("@/lib/api/farm", () => ({ getFarms: api.getFarms }));
vi.mock("@/lib/api/fpo", () => api);

describe("farmer farm-to-FPO connection flow", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.getFarms.mockResolvedValue([{ farm_id: "farm-1", farm_name: "North field", area_acres: 2.5, village_name: "Kantabania", district_name: "Puri", is_active: true }]);
    api.discoverFpos.mockResolvedValue([{ fpo_id: "fpo-1", fpo_name: "Coastal Growers", public_fpo_id: "MTFPO-1", district_name: "Puri", state_name: "Odisha" }]);
    api.getFarmerFpoRelationships.mockResolvedValue([]);
    api.getFpoRelationshipConsentPolicy.mockResolvedValue({
      policy_code: "FPO_DATA_SHARING",
      policy_version: "7",
      title: "Farm information sharing",
      content: "This FPO may access the selected farm only.",
      mandatory_scopes: ["FARM_READ", "LAND_INTELLIGENCE_READ"],
      optional_scopes: ["ADVISORY_MESSAGE"],
    });
    api.requestFarmerFpoRelationship.mockResolvedValue({ relationship_id: "rel-1" });
  });

  it("requires explicit policy consent and submits only the selected farm and published policy", async () => {
    const user = userEvent.setup();
    render(<MemoryRouter><FarmerFpoPage /></MemoryRouter>);

    await screen.findByRole("heading", { name: "FPOs" });
    await user.click(await screen.findByRole("button", { name: "Connect this farm" }));

    expect(await screen.findByText("This FPO may access the selected farm only.")).toBeInTheDocument();
    const submit = screen.getByRole("button", { name: "Confirm and send request" });
    expect(submit).toBeDisabled();

    await user.click(screen.getByLabelText(/I have read this policy/));
    expect(submit).toBeEnabled();
    await user.click(submit);

    await waitFor(() => expect(api.requestFarmerFpoRelationship).toHaveBeenCalledWith("farm-1", "fpo-1", {
      accepted: true,
      policy_code: "FPO_DATA_SHARING",
      policy_version: "7",
      selected_optional_scopes: [],
    }));
    expect(await screen.findByRole("status")).toHaveTextContent("Your farm request was sent to Coastal Growers");
  });

  it("shows an already-pending request as refreshed instead of an error", async () => {
    const user = userEvent.setup();
    api.requestFarmerFpoRelationship.mockResolvedValue({ relationship_id: "rel-1", already_requested: true });
    render(<MemoryRouter><FarmerFpoPage /></MemoryRouter>);

    await screen.findByRole("heading", { name: "FPOs" });
    await user.click(await screen.findByRole("button", { name: "Connect this farm" }));
    await user.click(screen.getByLabelText(/I have read this policy/));
    await user.click(screen.getByRole("button", { name: "Confirm and send request" }));

    expect(await screen.findByRole("status")).toHaveTextContent("A request to this FPO was already pending");
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("explains duplicate connection to the same FPO and reloads connection state", async () => {
    const user = userEvent.setup();
    api.requestFarmerFpoRelationship.mockRejectedValue({ status: 409, code: "FPO_ALREADY_CONNECTED", message: "conflict" });
    render(<MemoryRouter><FarmerFpoPage /></MemoryRouter>);

    await screen.findByRole("heading", { name: "FPOs" });
    await user.click(await screen.findByRole("button", { name: "Connect this farm" }));
    await user.click(screen.getByLabelText(/I have read this policy/));
    await user.click(screen.getByRole("button", { name: "Confirm and send request" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("This farm is already connected to this FPO. You can connect it to other FPOs separately.");
    expect(api.getFarmerFpoRelationships).toHaveBeenCalledTimes(2);
  });
});
