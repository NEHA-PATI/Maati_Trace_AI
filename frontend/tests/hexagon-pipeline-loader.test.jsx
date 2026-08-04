import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import HexagonPipelineLoader from "@/components/ui-custom/HexagonPipelineLoader";

const steps = [
  "Validating location",
  "Previewing H3 cells",
  "Registering land boundary",
  "Saving farm polygon",
  "Starting satellite search",
];

describe("HexagonPipelineLoader", () => {
  it("shows the real active pipeline stage", () => {
    render(
      <HexagonPipelineLoader
        open
        title="Land registration pipeline"
        steps={steps}
        currentStep={2}
        status="Registering farm..."
        details={[]}
      />,
    );

    expect(screen.getByRole("status", {
      name: "Land registration pipeline",
    })).toBeInTheDocument();
    expect(screen.getByText("Registering land boundary")).toBeInTheDocument();
    expect(screen.getByText("Registering farm...")).toBeInTheDocument();
    expect(screen.queryByText(/H3 res:/i)).not.toBeInTheDocument();
  });

  it("renders nothing while the pipeline is closed", () => {
    render(
      <HexagonPipelineLoader
        open={false}
        steps={steps}
      />,
    );

    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });
});
