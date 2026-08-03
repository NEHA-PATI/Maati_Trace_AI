import {
  describe,
  expect,
  it,
} from "vitest";

import {
  farmerProfileSchema,
  fpoProfileSchema,
} from "@/features/profile/profileSchemas";

const validFarmer = {
  full_name: "Kalia Farmer",
  phone_number: "9876543210",
  gender: "",
  date_of_birth: "",
  preferred_language: "en",
  aadhaar_last4: "",
  profile_image_url: "",
  state_name: "Odisha",
  district_name: "",
  block_name: "",
  block_code: "",
  village_name: "",
  gram_panchayat: "",
  pincode: "",
  farmer_type: "",
  total_landholding_acres: "",
  cultivated_area_acres: "",
  primary_crop: "",
  irrigation_status: "",
  consent_location_use: false,
  consent_data_processing: true,
  consent_advisory_messages: false,
  consent_fpo_data_sharing: false,
};

const validFpo = {
  fpo_name: "Green FPO",
  registration_number: "",
  registration_type: "",
  date_of_registration: "",
  promoted_by: "",
  promoting_institution_name: "",
  contact_person_name: "Manager",
  contact_person_designation: "",
  contact_phone: "9876543210",
  alternate_phone: "",
  contact_email:
    "manager@example.com",
  profile_image_url: "",
  state_name: "Odisha",
  district_name: "",
  block_name: "",
  block_code: "",
  village_name: "",
  gram_panchayat: "",
  pincode: "",
  office_address: "",
  main_commodities: "",
  member_count: "",
  active_member_count: "",
  services_provided: "",
};

describe("profileSchemas", () => {
  it("accepts a farmer with only core required fields", () => {
    expect(
      farmerProfileSchema.safeParse(
        validFarmer,
      ).success,
    ).toBe(true);
  });

  it("requires farmer data processing consent", () => {
    expect(
      farmerProfileSchema.safeParse({
        ...validFarmer,
        consent_data_processing:
          false,
      }).success,
    ).toBe(false);
  });

  it("rejects cultivated area greater than total landholding", () => {
    expect(
      farmerProfileSchema.safeParse({
        ...validFarmer,
        total_landholding_acres: 2,
        cultivated_area_acres: 3,
      }).success,
    ).toBe(false);
  });

  it("rejects invalid farmer phone number", () => {
    expect(
      farmerProfileSchema.safeParse({
        ...validFarmer,
        phone_number: "12345",
      }).success,
    ).toBe(false);
  });

  it("accepts an FPO with only core required fields", () => {
    expect(
      fpoProfileSchema.safeParse(
        validFpo,
      ).success,
    ).toBe(true);
  });

  it("rejects active member count greater than member count", () => {
    expect(
      fpoProfileSchema.safeParse({
        ...validFpo,
        member_count: 10,
        active_member_count: 12,
      }).success,
    ).toBe(false);
  });
});
