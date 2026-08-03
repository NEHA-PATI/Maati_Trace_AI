import {
  render,
  screen,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  describe,
  expect,
  it,
  vi,
} from "vitest";

import { FarmerProfileForm } from "@/features/profile/components/FarmerProfileForm";

vi.mock(
  "@/features/profile/hooks/useProfileLocations",
  () => ({
    useProfileLocations: () => ({
      states: [
        {
          state_name: "Odisha",
        },
      ],
      districts: [
        {
          district_code: 369,
          district_name: "Puri",
          state_name: "Odisha",
        },
        {
          district_code: 386,
          district_name: "Khordha",
          state_name: "Odisha",
        },
      ],
      blocks: [
        {
          block_code: 3546,
          block_name: "Satyabadi",
          district_name: "Puri",
          state_name: "Odisha",
        },
      ],
      loading: {
        states: false,
        districts: false,
        blocks: false,
      },
    }),
  }),
);

describe("FarmerProfileForm", () => {
  it("submits registered field values from custom profile controls", async () => {
    const user = userEvent.setup();
    const onSave = vi.fn(
      async (payload) => ({
        profile: {
          full_name:
            payload.full_name,
          phone_number:
            payload.phone_number,
          consent_data_processing:
            payload
              .consent_data_processing,
        },
      }),
    );

    render(
      <FarmerProfileForm
        user={{
          full_name: "Old Name",
          phone_number:
            "+919876543210",
          email:
            "farmer@example.com",
        }}
        profile={{
          full_name: "Old Name",
          phone_number:
            "+919876543210",
          preferred_language: "en",
          state_name: "Odisha",
          consent_location_use: false,
          consent_data_processing:
            false,
          consent_advisory_messages:
            false,
          consent_fpo_data_sharing:
            false,
        }}
        onSave={onSave}
        onExport={vi.fn()}
        saving={false}
        exporting={false}
        savedAt={null}
      />,
    );

    await user.clear(
      screen.getByLabelText(
        /Full name/i,
      ),
    );
    await user.type(
      screen.getByLabelText(
        /Full name/i,
      ),
      "Badal Farmer",
    );

    await user.clear(
      screen.getByLabelText(
        /Phone number/i,
      ),
    );
    await user.type(
      screen.getByLabelText(
        /Phone number/i,
      ),
      "9876543210",
    );

    await user.click(
      screen.getByLabelText(
        /Process profile data/i,
      ),
    );
    await user.click(
      screen.getByRole("button", {
        name: /Save profile/i,
      }),
    );

    expect(onSave).toHaveBeenCalledWith(
      expect.objectContaining({
        full_name: "Badal Farmer",
        phone_number: "9876543210",
        consent_data_processing:
          true,
      }),
    );
    expect(
      screen.queryByText(
        /expected string/i,
      ),
    ).not.toBeInTheDocument();
  });

  it("shows district and block names instead of repeating state names", () => {
    render(
      <FarmerProfileForm
        user={{
          full_name: "Old Name",
          phone_number:
            "+919876543210",
          email:
            "farmer@example.com",
        }}
        profile={{
          full_name: "Old Name",
          phone_number:
            "+919876543210",
          preferred_language: "en",
          state_name: "Odisha",
          district_name: "Puri",
          consent_location_use: false,
          consent_data_processing:
            true,
          consent_advisory_messages:
            false,
          consent_fpo_data_sharing:
            false,
        }}
        onSave={vi.fn()}
        onExport={vi.fn()}
        saving={false}
        exporting={false}
        savedAt={null}
      />,
    );

    expect(
      screen.getByRole("option", {
        name: "Puri",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("option", {
        name: "Khordha",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("option", {
        name: "Satyabadi",
      }),
    ).toBeInTheDocument();
  });
});
