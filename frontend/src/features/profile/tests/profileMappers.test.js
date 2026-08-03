import {
  describe,
  expect,
  it,
} from "vitest";

import {
  buildFarmerPayload,
  buildFpoPayload,
  toFarmerForm,
  toFpoForm,
} from "@/features/profile/profileMappers";

describe("profileMappers", () => {
  it("maps pending farmer location placeholders to blank form values", () => {
    const form = toFarmerForm(
      {
        full_name: "Kalia Farmer",
        phone_number:
          "+919876543210",
        state_name: "Odisha",
        district_name: null,
        block_code: null,
      },
      {
        full_name: "Fallback",
      },
    );

    expect(form.full_name).toBe(
      "Kalia Farmer",
    );
    expect(form.district_name).toBe(
      "",
    );
    expect(form.block_code).toBe(
      "",
    );
  });

  it("builds farmer payload from only dirty editable fields", () => {
    const payload =
      buildFarmerPayload(
        {
          full_name: "New Name",
          preferred_language: "or",
          email:
            "not-editable@example.com",
        },
        {
          preferred_language: true,
        },
      );

    expect(payload).toEqual({
      preferred_language: "or",
    });
  });

  it("builds FPO setup payload with optional blank location as null", () => {
    const payload = buildFpoPayload(
      toFpoForm(
        null,
        {
          full_name: "Manager",
          email:
            "manager@example.com",
          phone_number:
            "+919876543210",
        },
      ),
      {},
      true,
    );

    expect(payload).toMatchObject({
      contact_person_name:
        "Manager",
      contact_email:
        "manager@example.com",
      contact_phone:
        "+919876543210",
      state_name: "Odisha",
      district_name: null,
      block_code: null,
    });
  });

  it("deduplicates comma-separated FPO lists", () => {
    const payload = buildFpoPayload(
      {
        main_commodities:
          "Paddy, Millet, paddy",
        services_provided:
          "Advisory, advisory, Input supply",
      },
      {
        main_commodities: true,
        services_provided: true,
      },
      false,
    );

    expect(
      payload.main_commodities,
    ).toEqual([
      "Paddy",
      "Millet",
    ]);
    expect(
      payload.services_provided,
    ).toEqual([
      "Advisory",
      "Input supply",
    ]);
  });
});
