import {
  useEffect,
  useState,
} from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  useForm,
} from "react-hook-form";
import {
  AlertCircle,
  Building2,
  FileText,
  Info,
  MapPin,
  Shield,
  User,
  Wheat,
} from "lucide-react";

import {
  applyApiFieldErrors,
  buildFpoPayload,
  toFpoForm,
} from "@/features/profile/profileMappers";
import { fpoProfileSchema } from "@/features/profile/profileSchemas";
import { useProfileLocations } from "@/features/profile/hooks/useProfileLocations";
import { ProfileControls } from "@/features/profile/components/ProfileControls";
import {
  ProfileGrid,
  ProfileInput,
  ProfileSection,
  ProfileSelect,
  ProfileTextarea,
  ReadOnlyValue,
} from "@/features/profile/components/ProfileSection";

function getStateName(item) {
  return (
    item?.name
    || item?.state_name
    || String(item || "")
  );
}

function getDistrictName(item) {
  return (
    item?.district_name
    || item?.name
    || String(item || "")
  );
}

function getBlockName(item) {
  return (
    item?.block_name
    || item?.name
    || String(item || "")
  );
}

function itemCode(item) {
  return (
    item?.block_code
    ?? item?.code
    ?? ""
  );
}

export function FpoProfileForm({
  user,
  profile,
  setupRequired,
  onSave,
  onExport,
  saving,
  exporting,
  savedAt,
}) {
  const [submitError, setSubmitError] =
    useState(null);

  const form = useForm({
    resolver: zodResolver(
      fpoProfileSchema,
    ),
    defaultValues: toFpoForm(
      profile,
      user,
    ),
  });

  const {
    register,
    handleSubmit,
    reset,
    setError,
    setValue,
    watch,
    formState: {
      errors,
      dirtyFields,
    },
  } = form;

  useEffect(() => {
    reset(
      toFpoForm(
        profile,
        user,
      ),
    );
  }, [profile, reset, user]);

  const stateName =
    watch("state_name")
    || "Odisha";
  const districtName =
    watch("district_name")
    || "";

  const {
    states,
    districts,
    blocks,
    loading: locationLoading,
  } = useProfileLocations({
    stateName,
    districtName,
  });

  const stateField =
    register("state_name");
  const districtField =
    register("district_name");

  const onSubmit = async (values) => {
    setSubmitError(null);

    const payload =
      buildFpoPayload(
        values,
        dirtyFields,
        setupRequired,
      );

    if (
      !setupRequired
      && Object.keys(payload).length
        === 0
    ) {
      setSubmitError(
        "No changed profile fields to save.",
      );
      return;
    }

    try {
      const nextEnvelope =
        await onSave(
          payload,
          setupRequired,
        );

      reset(
        toFpoForm(
          nextEnvelope?.profile,
          user,
        ),
      );
    } catch (error) {
      if (
        !applyApiFieldErrors(
          error,
          setError,
        )
      ) {
        setSubmitError(
          error?.message
          || "FPO profile could not be saved.",
        );
      }
    }
  };

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="space-y-5"
    >
      {setupRequired ? (
        <div className="mt-fade-up flex items-start gap-3 rounded-[1.25rem] border border-amber-200 bg-[color:var(--mt-harvest-soft)] p-4 text-sm leading-6 text-amber-950">
          <Info className="mt-0.5 h-4 w-4 shrink-0" />
          <span>
            This account is not linked to an FPO profile yet. Fill the
            required organisation and contact fields to create it.
          </span>
        </div>
      ) : null}

      {submitError ? (
        <div className="mt-pop flex items-center gap-3 rounded-[1.25rem] border border-rose-100 bg-[color:var(--mt-rose-soft)] px-4 py-3 text-sm font-semibold text-[color:var(--mt-rose)]">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {submitError}
        </div>
      ) : null}

      <ProfileSection
        id="organisation"
        title="Organisation"
        eyebrow="Required identity"
        icon={Building2}
      >
        <ProfileGrid>
          <ProfileInput
            label="FPO name"
            required
            error={errors.fpo_name}
            {...register("fpo_name")}
          />
          <ProfileInput
            label="Registration number"
            error={
              errors.registration_number
            }
            {...register(
              "registration_number",
            )}
          />
          <ProfileInput
            label="Registration type"
            error={
              errors.registration_type
            }
            {...register(
              "registration_type",
            )}
          />
          <ProfileInput
            type="date"
            label="Date of registration"
            error={
              errors.date_of_registration
            }
            {...register(
              "date_of_registration",
            )}
          />
          <ProfileInput
            label="Promoted by"
            error={errors.promoted_by}
            {...register(
              "promoted_by",
            )}
          />
          <ProfileInput
            label="Promoting institution"
            error={
              errors
                .promoting_institution_name
            }
            {...register(
              "promoting_institution_name",
            )}
          />
        </ProfileGrid>
      </ProfileSection>

      <ProfileSection
        id="contact"
        title="Contact"
        eyebrow="Required contact"
        icon={User}
      >
        <ProfileGrid>
          <ProfileInput
            label="Contact person"
            required
            error={
              errors.contact_person_name
            }
            {...register(
              "contact_person_name",
            )}
          />
          <ProfileInput
            label="Designation"
            error={
              errors
                .contact_person_designation
            }
            {...register(
              "contact_person_designation",
            )}
          />
          <ProfileInput
            label="Contact phone"
            required
            error={errors.contact_phone}
            {...register(
              "contact_phone",
            )}
          />
          <ProfileInput
            label="Alternate phone"
            error={
              errors.alternate_phone
            }
            {...register(
              "alternate_phone",
            )}
          />
          <ProfileInput
            type="email"
            label="Contact email"
            required
            error={errors.contact_email}
            {...register(
              "contact_email",
            )}
          />
          <ProfileInput
            label="Profile image URL"
            error={
              errors.profile_image_url
            }
            {...register(
              "profile_image_url",
            )}
          />
        </ProfileGrid>
      </ProfileSection>

      <ProfileSection
        id="location"
        title="Location"
        eyebrow="Optional office geography"
        icon={MapPin}
      >
        <ProfileGrid>
          <ProfileSelect
            label="State"
            error={errors.state_name}
            {...stateField}
            onChange={(event) => {
              stateField.onChange(event);
              setValue(
                "district_name",
                "",
                {
                  shouldDirty: true,
                  shouldValidate: true,
                },
              );
              setValue(
                "block_code",
                "",
                {
                  shouldDirty: true,
                },
              );
              setValue(
                "block_name",
                "",
                {
                  shouldDirty: true,
                },
              );
            }}
          >
            <option value="Odisha">
              Odisha
            </option>
            {states.map((state) => {
              const name =
                getStateName(state);

              if (name === "Odisha") {
                return null;
              }

              return (
                <option
                  key={name}
                  value={name}
                >
                  {name}
                </option>
              );
            })}
          </ProfileSelect>
          <ProfileSelect
            label={
              locationLoading.districts
                ? "District loading..."
                : "District"
            }
            error={errors.district_name}
            {...districtField}
            onChange={(event) => {
              districtField.onChange(event);
              setValue(
                "block_code",
                "",
                {
                  shouldDirty: true,
                },
              );
              setValue(
                "block_name",
                "",
                {
                  shouldDirty: true,
                },
              );
            }}
          >
            <option value="">
              Select later
            </option>
            {districts.map((district) => {
              const name =
                getDistrictName(district);

              return (
                <option
                  key={name}
                  value={name}
                >
                  {name}
                </option>
              );
            })}
          </ProfileSelect>
          <ProfileSelect
            label={
              locationLoading.blocks
                ? "Block loading..."
                : "Block"
            }
            error={errors.block_code}
            value={
              watch("block_code")
              || ""
            }
            onChange={(event) => {
              const block = blocks.find(
                (item) =>
                  String(itemCode(item))
                  === event.target.value,
              );

              setValue(
                "block_code",
                event.target.value
                  ? Number(
                    event.target.value,
                  )
                  : "",
                {
                  shouldDirty: true,
                  shouldValidate: true,
                },
              );
              setValue(
                "block_name",
                block
                  ? getBlockName(block)
                  : "",
                {
                  shouldDirty: true,
                },
              );
            }}
          >
            <option value="">
              Select later
            </option>
            {blocks.map((block) => {
              const code =
                itemCode(block);
              const name =
                getBlockName(block);

              return (
                <option
                  key={code || name}
                  value={code}
                >
                  {name}
                </option>
              );
            })}
          </ProfileSelect>
          <ProfileInput
            label="Village"
            error={
              errors.village_name
            }
            {...register(
              "village_name",
            )}
          />
          <ProfileInput
            label="Gram panchayat"
            error={
              errors.gram_panchayat
            }
            {...register(
              "gram_panchayat",
            )}
          />
          <ProfileInput
            label="Pincode"
            error={errors.pincode}
            {...register("pincode")}
          />
        </ProfileGrid>
        <ProfileTextarea
          label="Office address"
          error={
            errors.office_address
          }
          {...register(
            "office_address",
          )}
        />
      </ProfileSection>

      <ProfileSection
        id="operations"
        title="Operations"
        eyebrow="Optional services"
        icon={Wheat}
      >
        <ProfileGrid>
          <ProfileInput
            label="Main commodities"
            placeholder="Paddy, Millet, Pulses"
            error={
              errors.main_commodities
            }
            {...register(
              "main_commodities",
            )}
          />
          <ProfileInput
            label="Services provided"
            placeholder="Input supply, aggregation, advisory"
            error={
              errors.services_provided
            }
            {...register(
              "services_provided",
            )}
          />
          <ProfileInput
            type="number"
            label="Member count"
            error={
              errors.member_count
            }
            {...register(
              "member_count",
            )}
          />
          <ProfileInput
            type="number"
            label="Active member count"
            error={
              errors
                .active_member_count
            }
            {...register(
              "active_member_count",
            )}
          />
        </ProfileGrid>
      </ProfileSection>

      <ProfileSection
        id="verification"
        title="Verification"
        eyebrow="Read only status"
        icon={Shield}
      >
        <ProfileGrid>
          <ReadOnlyValue
            label="Verification status"
            value={
              profile
                ?.verification_status
              || "pending"
            }
          />
          <ReadOnlyValue
            label="Current user role"
            value={
              profile
                ?.current_user_fpo_role
              || "owner"
            }
          />
        </ProfileGrid>
      </ProfileSection>

      <ProfileSection
        id="export"
        title="Export"
        eyebrow="Data portability"
        icon={FileText}
      >
        <p className="rounded-[1.25rem] border border-dashed border-slate-200 bg-slate-50 p-4 text-sm leading-6 text-slate-600">
          Export returns the profile-service representation of the
          current FPO profile through the gateway.
        </p>
      </ProfileSection>

      <ProfileControls
        saving={saving}
        exporting={exporting}
        savedAt={savedAt}
        onExport={onExport}
      />
    </form>
  );
}
