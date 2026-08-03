import { z } from "zod";

const INDIAN_PHONE =
  /^(\+91)?[6-9]\d{9}$/;

const PINCODE =
  /^[1-9]\d{5}$/;

function normalizedPhone(value) {
  return String(value || "")
    .replace(/[\s()-]/g, "");
}

const optionalPhone = z
  .string()
  .trim()
  .refine(
    (value) =>
      value === ""
      || INDIAN_PHONE.test(
        normalizedPhone(value),
      ),
    "Enter a valid Indian mobile number.",
  );

const requiredPhone = z
  .string()
  .trim()
  .min(
    1,
    "Enter a contact phone number.",
  )
  .refine(
    (value) =>
      INDIAN_PHONE.test(
        normalizedPhone(value),
      ),
    "Enter a valid Indian mobile number.",
  );

const optionalPincode = z
  .string()
  .trim()
  .refine(
    (value) =>
      value === ""
      || PINCODE.test(value),
    "Enter a valid six-digit pincode.",
  );

const optionalDate = z
  .string()
  .refine(
    (value) =>
      value === ""
      || /^\d{4}-\d{2}-\d{2}$/.test(
        value,
      ),
    "Enter a valid date.",
  );

const optionalPastDate =
  optionalDate.refine(
    (value) =>
      value === ""
      || new Date(`${value}T00:00:00`)
        <= new Date(),
    "Date cannot be in the future.",
  );

const optionalNumber = z.preprocess(
  (value) => {
    if (
      value === ""
      || value === null
      || value === undefined
    ) {
      return null;
    }

    return Number(value);
  },
  z
    .number()
    .min(
      0,
      "Value cannot be negative.",
    )
    .nullable(),
);

const optionalPositiveInteger =
  z.preprocess(
    (value) => {
      if (
        value === ""
        || value === null
        || value === undefined
      ) {
        return null;
      }

      return Number(value);
    },
    z
      .number()
      .int()
      .positive()
      .nullable(),
  );

const optionalNonNegativeInteger =
  z.preprocess(
    (value) => {
      if (
        value === ""
        || value === null
        || value === undefined
      ) {
        return null;
      }

      return Number(value);
    },
    z
      .number()
      .int()
      .min(
        0,
        "Value cannot be negative.",
      )
      .nullable(),
  );

export const farmerProfileSchema = z
  .object({
    full_name: z
      .string()
      .trim()
      .min(
        2,
        "Enter your full name.",
      )
      .max(200),

    phone_number: requiredPhone,

    gender: z.enum([
      "",
      "male",
      "female",
      "other",
      "prefer_not_to_say",
    ]),

    date_of_birth:
      optionalPastDate,

    preferred_language: z.enum([
      "en",
      "hi",
      "or",
    ]),

    aadhaar_last4: z
      .string()
      .trim()
      .refine(
        (value) =>
          value === ""
          || /^\d{4}$/.test(value),
        "Enter exactly four digits.",
      ),

    profile_image_url: z
      .string()
      .trim()
      .refine(
        (value) => {
          if (value === "") return true;

          try {
            new URL(value);
            return true;
          } catch {
            return false;
          }
        },
        "Enter a valid image URL.",
      ),

    state_name: z
      .string()
      .trim()
      .default("Odisha"),

    district_name:
      z.string().trim(),

    block_name:
      z.string().trim(),

    block_code:
      optionalPositiveInteger,

    village_name:
      z.string().trim(),

    gram_panchayat:
      z.string().trim(),

    pincode:
      optionalPincode,

    farmer_type:
      z.string().trim(),

    total_landholding_acres:
      optionalNumber,

    cultivated_area_acres:
      optionalNumber,

    primary_crop:
      z.string().trim(),

    irrigation_status:
      z.string().trim(),

    consent_location_use:
      z.boolean(),

    consent_data_processing: z
      .boolean()
      .refine(
        Boolean,
        "Data processing consent is required.",
      ),

    consent_advisory_messages:
      z.boolean(),

    consent_fpo_data_sharing:
      z.boolean(),
  })
  .superRefine(
    (values, context) => {
      if (
        values.total_landholding_acres !== null
        && values.cultivated_area_acres !== null
        && values.cultivated_area_acres
          > values.total_landholding_acres
      ) {
        context.addIssue({
          code:
            z.ZodIssueCode.custom,
          path: [
            "cultivated_area_acres",
          ],
          message:
            "Cultivated area cannot exceed total landholding.",
        });
      }

      if (
        values.block_code !== null
        && !values.district_name
      ) {
        context.addIssue({
          code:
            z.ZodIssueCode.custom,
          path: ["district_name"],
          message:
            "Select a district before selecting a block.",
        });
      }
    },
  );

export const fpoProfileSchema = z
  .object({
    fpo_name: z
      .string()
      .trim()
      .min(
        2,
        "Enter the FPO name.",
      )
      .max(200),

    registration_number: z
      .string()
      .trim()
      .max(100),

    registration_type:
      z.string().trim(),

    date_of_registration:
      optionalPastDate,

    promoted_by:
      z.string().trim(),

    promoting_institution_name:
      z.string().trim(),

    contact_person_name: z
      .string()
      .trim()
      .min(
        2,
        "Enter the contact person's name.",
      )
      .max(200),

    contact_person_designation:
      z.string().trim(),

    contact_phone:
      requiredPhone,

    alternate_phone:
      optionalPhone,

    contact_email: z
      .string()
      .trim()
      .email(
        "Enter a valid contact email.",
      ),

    profile_image_url: z
      .string()
      .trim()
      .refine(
        (value) => {
          if (value === "") return true;

          try {
            new URL(value);
            return true;
          } catch {
            return false;
          }
        },
        "Enter a valid image URL.",
      ),

    state_name: z
      .string()
      .trim()
      .default("Odisha"),

    district_name:
      z.string().trim(),

    block_name:
      z.string().trim(),

    block_code:
      optionalPositiveInteger,

    village_name:
      z.string().trim(),

    gram_panchayat:
      z.string().trim(),

    pincode:
      optionalPincode,

    office_address: z
      .string()
      .trim()
      .max(1000),

    main_commodities:
      z.string(),

    member_count:
      optionalNonNegativeInteger,

    active_member_count:
      optionalNonNegativeInteger,

    services_provided:
      z.string(),
  })
  .superRefine(
    (values, context) => {
      if (
        values.member_count !== null
        && values.active_member_count !== null
        && values.active_member_count
          > values.member_count
      ) {
        context.addIssue({
          code:
            z.ZodIssueCode.custom,
          path: [
            "active_member_count",
          ],
          message:
            "Active members cannot exceed total members.",
        });
      }
    },
  );
