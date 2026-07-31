import { z } from "zod";
import { normaliseIndianPhone } from "@/features/auth/authValidation";

export const fpoAccessSchema = z.object({
  organisation_name: z.string().trim().min(2, "Enter the FPO name.").max(250),
  registration_number: z.string().trim().max(100).optional().or(z.literal("")),
  contact_person_name: z.string().trim().min(2, "Enter the contact person's name.").max(200),
  contact_email: z.string().trim().email("Enter a valid email address.").transform((value) => value.toLowerCase()),
  contact_phone: z.string().transform((value, context) => {
    try {
      return normaliseIndianPhone(value);
    } catch (error) {
      context.addIssue({ code: z.ZodIssueCode.custom, message: error.message });
      return z.NEVER;
    }
  }),
  state_name: z.string().trim().max(100).default("Odisha"),
  district_name: z.string().trim().max(100).optional().or(z.literal("")),
  message: z.string().trim().max(2000, "Message is too long.").optional().or(z.literal("")),
});
