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
  Check,
  FileText,
  MapPin,
  Shield,
  User,
  Wheat,
} from "lucide-react";

import {
  applyApiFieldErrors,
  buildFarmerPayload,
  toFarmerForm,
} from "@/features/profile/profileMappers";
import { farmerProfileSchema } from "@/features/profile/profileSchemas";
import { useProfileLocations } from "@/features/profile/hooks/useProfileLocations";
import { ProfileControls } from "@/features/profile/components/ProfileControls";
import { ProfilePlansSection } from "@/features/profile/components/ProfilePlansSection";
import {
  ProfileCheckbox,
  ProfileGrid,
  ProfileInput,
  ProfileSection,
  ProfileSelect,
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

export function FarmerProfileForm({
  user,
  profile,
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
      farmerProfileSchema,
    ),
    defaultValues: toFarmerForm(
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
      toFarmerForm(
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
      buildFarmerPayload(
        values,
        dirtyFields,
      );

    if (
      Object.keys(payload).length === 0
    ) {
      setSubmitError(
        "No changed profile fields to save.",
      );
      return;
    }

    try {
      const nextEnvelope =
        await onSave(payload);

      reset(
        toFarmerForm(
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
          || "Profile could not be saved.",
        );
      }
    }
  };

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="space-y-5"
    >
      {submitError ? (
        <div className="mt-pop flex items-center gap-3 rounded-[1.25rem] border border-rose-100 bg-[color:var(--mt-rose-soft)] px-4 py-3 text-sm font-semibold text-[color:var(--mt-rose)]">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {submitError}
        </div>
      ) : null}

      <ProfileSection
        id="account"
        title="Account"
        eyebrow="Required basics"
        icon={User}
      >
        <ProfileGrid>
          <ProfileInput
            label="Full name"
            required
            error={errors.full_name}
            {...register("full_name")}
          />
          <ProfileInput
            label="Phone number"
            required
            error={errors.phone_number}
            {...register("phone_number")}
          />
          <ProfileSelect
            label="Preferred language"
            error={
              errors.preferred_language
            }
            {...register(
              "preferred_language",
            )}
          >
            <option value="en">
              English
            </option>
            <option value="hi">
              Hindi
            </option>
            <option value="or">
              Odia
            </option>
          </ProfileSelect>
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
        id="identity"
        title="Identity"
        eyebrow="Optional KYC context"
        icon={Shield}
      >
        <ProfileGrid>
          <ProfileSelect
            label="Gender"
            error={errors.gender}
            {...register("gender")}
          >
            <option value="">
              Not specified
            </option>
            <option value="male">
              Male
            </option>
            <option value="female">
              Female
            </option>
            <option value="other">
              Other
            </option>
            <option value="prefer_not_to_say">
              Prefer not to say
            </option>
          </ProfileSelect>
          <ProfileInput
            type="date"
            label="Date of birth"
            error={
              errors.date_of_birth
            }
            {...register(
              "date_of_birth",
            )}
          />
          <ProfileInput
            label="Aadhaar last 4"
            error={
              errors.aadhaar_last4
            }
            maxLength={4}
            {...register(
              "aadhaar_last4",
            )}
          />
        </ProfileGrid>
      </ProfileSection>

      <ProfileSection
        id="location"
        title="Location"
        eyebrow="Optional geography"
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
      </ProfileSection>

      <ProfileSection
        id="role"
        title="Role Details"
        eyebrow="Optional farm context"
        icon={Wheat}
      >
        <ProfileGrid>
          <ProfileInput
            label="Farmer type"
            error={
              errors.farmer_type
            }
            {...register(
              "farmer_type",
            )}
          />
          <ProfileInput
            type="number"
            step="0.01"
            label="Total landholding acres"
            error={
              errors
                .total_landholding_acres
            }
            {...register(
              "total_landholding_acres",
            )}
          />
          <ProfileInput
            type="number"
            step="0.01"
            label="Cultivated area acres"
            error={
              errors
                .cultivated_area_acres
            }
            {...register(
              "cultivated_area_acres",
            )}
          />
          <ProfileInput
            label="Primary crop"
            error={
              errors.primary_crop
            }
            {...register(
              "primary_crop",
            )}
          />
          <ProfileInput
            label="Irrigation status"
            error={
              errors.irrigation_status
            }
            {...register(
              "irrigation_status",
            )}
          />
        </ProfileGrid>
      </ProfileSection>

      <ProfileSection
        id="consent"
        title="Consent"
        eyebrow="Privacy controls"
        icon={Check}
      >
        <div className="grid gap-3">
          <ProfileCheckbox
            label="Use location for farm services"
            description="Optional permission for location-aware recommendations."
            error={
              errors.consent_location_use
            }
            {...register(
              "consent_location_use",
            )}
          />
          <ProfileCheckbox
            label="Process profile data"
            description="Required so MaatiTrace can maintain your account profile."
            error={
              errors.consent_data_processing
            }
            {...register(
              "consent_data_processing",
            )}
          />
          <ProfileCheckbox
            label="Advisory messages"
            description="Optional consent for advisory communications."
            error={
              errors
                .consent_advisory_messages
            }
            {...register(
              "consent_advisory_messages",
            )}
          />
          <ProfileCheckbox
            label="FPO data sharing"
            description="Optional consent for sharing profile context with linked FPOs."
            error={
              errors
                .consent_fpo_data_sharing
            }
            {...register(
              "consent_fpo_data_sharing",
            )}
          />
        </div>
      </ProfileSection>

      <ProfilePlansSection />

      <ProfileSection
        id="export"
        title="Export"
        eyebrow="Data portability"
        icon={FileText}
      >
        <p className="rounded-[1.25rem] border border-dashed border-slate-200 bg-slate-50 p-4 text-sm leading-6 text-slate-600">
          Export returns the profile-service representation of your
          current account profile through the gateway.
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
