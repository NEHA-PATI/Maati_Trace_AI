import { z } from "zod";

export function normaliseIndianPhone(value) {
  const compact = String(value || "").replace(/[\s()-]/g, "");
  let national = compact;
  if (national.startsWith("+91")) national = national.slice(3);
  else if (national.startsWith("91") && national.length === 12) national = national.slice(2);
  else if (national.startsWith("0") && national.length === 11) national = national.slice(1);
  if (!/^[6-9]\d{9}$/.test(national)) {
    throw new Error("Enter a valid 10-digit Indian mobile number.");
  }
  return `+91${national}`;
}

export function passwordScore(value) {
  const password = String(value || "");
  let score = 0;
  if (password.length >= 12) score += 1;
  if (password.length >= 16) score += 1;
  if (/\s/.test(password) || /[^A-Za-z0-9]/.test(password)) score += 1;
  if (/[A-Z]/.test(password) && /[a-z]/.test(password)) score += 1;
  if (/\d/.test(password)) score += 1;
  return Math.min(score, 4);
}

const phoneSchema = z.string().transform((value, context) => {
  try {
    return normaliseIndianPhone(value);
  } catch (error) {
    context.addIssue({ code: z.ZodIssueCode.custom, message: error.message });
    return z.NEVER;
  }
});

const passwordSchema = z
  .string()
  .min(12, "Use at least 12 characters.")
  .max(128, "Use no more than 128 characters.")
  .refine((value) => value.trim().length >= 12, "Use a longer passphrase, not only spaces.");

const optionalLocationCode = z.preprocess(
  (value) => (value === "" || value === null || value === undefined ? null : Number(value)),
  z.number().int().positive().nullable(),
);

export const signupAccountSchema = z
  .object({
    account_type: z.enum(["farmer", "fpo"]),
    full_name: z.string().trim().min(2, "Enter your full name.").max(200, "Name is too long."),
    email: z.string().trim().email("Enter a valid email address.").transform((value) => value.toLowerCase()),
    phone_number: phoneSchema,
    password: passwordSchema,
    confirm_password: z.string(),
    consent_terms: z.boolean().refine((value) => value === true, "Accept the terms and privacy notice."),
    authorised_fpo_representative: z.boolean(),
    organisation_name: z.string().trim().max(250),
    registration_type: z.enum(["producer_company", "cooperative_society", "other"]),
    registration_number: z.string().trim().max(100),
    state_code: optionalLocationCode,
    district_code: optionalLocationCode,
  })
  .superRefine((value, context) => {
    if (value.password !== value.confirm_password) {
      context.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["confirm_password"],
        message: "Passwords do not match.",
      });
    }
    if (value.account_type === "fpo") {
      if (value.organisation_name.length < 2) context.addIssue({ code: z.ZodIssueCode.custom, path: ["organisation_name"], message: "Enter the registered FPO name." });
      if (value.registration_number.length < 2) context.addIssue({ code: z.ZodIssueCode.custom, path: ["registration_number"], message: "Enter the registration number." });
      if (!value.state_code) context.addIssue({ code: z.ZodIssueCode.custom, path: ["state_code"], message: "Enter the state code." });
      if (!value.district_code) context.addIssue({ code: z.ZodIssueCode.custom, path: ["district_code"], message: "Enter the district code." });
      if (!value.authorised_fpo_representative) context.addIssue({ code: z.ZodIssueCode.custom, path: ["authorised_fpo_representative"], message: "Confirm your authority to register this FPO." });
    }
  });

export const loginSchema = z.object({
  identifier: z.string().trim().min(3, "Enter your email or mobile number."),
  password: z.string().min(1, "Enter your password."),
});

export const forgotPasswordSchema = z.object({
  email: z.string().trim().email("Enter a valid email address.").transform((value) => value.toLowerCase()),
});

export const resetPasswordSchema = z
  .object({ password: passwordSchema, confirm_password: z.string() })
  .superRefine((value, context) => {
    if (value.password !== value.confirm_password) {
      context.addIssue({ code: z.ZodIssueCode.custom, path: ["confirm_password"], message: "Passwords do not match." });
    }
  });

export const invitationAcceptSchema = z
  .object({
    full_name: z.string().trim().min(2, "Enter your full name.").max(200),
    phone_number: phoneSchema,
    password: passwordSchema,
    confirm_password: z.string(),
  })
  .superRefine((value, context) => {
    if (value.password !== value.confirm_password) {
      context.addIssue({ code: z.ZodIssueCode.custom, path: ["confirm_password"], message: "Passwords do not match." });
    }
  });
