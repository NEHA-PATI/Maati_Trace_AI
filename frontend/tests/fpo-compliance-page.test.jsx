import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  getFpoComplianceDocuments,
  getFpoComplianceReadiness,
  getFpoDataPackSchemas,
  getFpoExportPacks,
  getFpoSustainabilityMetrics,
} from "@/features/fpo/api/fpoPortalApi";
import FpoClassCCompliancePage from "@/features/fpo/dashboard/FpoClassCCompliancePage";

vi.mock("@/features/fpo/api/fpoPortalApi", () => ({
  getFpoComplianceDocuments: vi.fn(),
  getFpoComplianceReadiness: vi.fn(),
  getFpoDataPackSchemas: vi.fn(),
  getFpoExportPacks: vi.fn(),
  getFpoSustainabilityMetrics: vi.fn(),
}));

describe("FPO compliance page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getFpoComplianceDocuments.mockResolvedValue([
      { compliance_document_id: "document-1", document_type_code: "REGISTRATION_CERTIFICATE", review_status: "APPROVED" },
    ]);
    getFpoComplianceReadiness.mockResolvedValue({ complete: 1, under_review: 0, expired: 0 });
    getFpoDataPackSchemas.mockResolvedValue([
      { data_pack_schema_id: "schema-1", name: "Traceability pack", schema_key: "TRACE", version: 1, purpose_code: "BUYER" },
    ]);
    getFpoExportPacks.mockResolvedValue([
      { export_pack_id: "pack-1", pack_code: "EXPORT-1", status: "READY" },
    ]);
    getFpoSustainabilityMetrics.mockResolvedValue([
      { metric_id: "metric-1", metric_code: "SOIL_CARBON", metric_value: 12, unit_code: "t/ha" },
    ]);
  });

  it("keeps successful sections visible and reports a failed section instead of showing false zeros", async () => {
    getFpoComplianceReadiness.mockRejectedValue(new Error("Internal Server Error"));

    render(<FpoClassCCompliancePage />);

    expect(await screen.findByText("REGISTRATION_CERTIFICATE")).toBeInTheDocument();
    expect(screen.getByText("EXPORT-1")).toBeInTheDocument();
    expect(screen.getByText("Traceability pack")).toBeInTheDocument();
    expect(screen.getByText("SOIL_CARBON")).toBeInTheDocument();
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Compliance readiness is unavailable: Internal Server Error",
    );
    expect(screen.queryByText("No compliance documents are recorded.")).not.toBeInTheDocument();
    expect(getFpoComplianceReadiness).toHaveBeenCalled();
  });
});
