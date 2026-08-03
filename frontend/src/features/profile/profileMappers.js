const LOCATION_FIELDS =
  new Set([
    "state_name",
    "district_name",
    "block_name",
    "block_code",
    "village_name",
  ]);

function blankToNull(value) {
  if (
    value === undefined
    || value === null
  ) {
    return null;
  }

  if (typeof value === "string") {
    const cleaned = value.trim();

    return cleaned === ""
      ? null
      : cleaned;
  }

  return value;
}

function commaList(value) {
  return String(value || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean)
    .filter(
      (item, index, items) =>
        items.findIndex(
          (candidate) =>
            candidate.toLowerCase()
            === item.toLowerCase(),
        ) === index,
    );
}

function dateOnly(value) {
  if (!value) return "";

  return String(value).slice(0, 10);
}

function numberFormValue(value) {
  return value === null
    || value === undefined
      ? ""
      : value;
}

export function toFarmerForm(
  profile,
  user,
) {
  return {
    full_name:
      profile?.full_name
      || user?.full_name
      || "",
    phone_number:
      profile?.phone_number
      || user?.phone_number
      || "",
    gender:
      profile?.gender || "",
    date_of_birth:
      dateOnly(
        profile?.date_of_birth,
      ),
    preferred_language:
      profile?.preferred_language
      || "en",
    aadhaar_last4:
      profile?.aadhaar_last4 || "",
    profile_image_url:
      profile?.profile_image_url
      || "",
    state_name:
      profile?.state_name
      || "Odisha",
    district_name:
      profile?.district_name
      || "",
    block_name:
      profile?.block_name
      || "",
    block_code:
      numberFormValue(
        profile?.block_code,
      ),
    village_name:
      profile?.village_name
      || "",
    gram_panchayat:
      profile?.gram_panchayat
      || "",
    pincode:
      profile?.pincode || "",
    farmer_type:
      profile?.farmer_type
      || "",
    total_landholding_acres:
      numberFormValue(
        profile
          ?.total_landholding_acres,
      ),
    cultivated_area_acres:
      numberFormValue(
        profile
          ?.cultivated_area_acres,
      ),
    primary_crop:
      profile?.primary_crop || "",
    irrigation_status:
      profile?.irrigation_status
      || "",
    consent_location_use:
      Boolean(
        profile
          ?.consent_location_use,
      ),
    consent_data_processing:
      Boolean(
        profile
          ?.consent_data_processing,
      ),
    consent_advisory_messages:
      Boolean(
        profile
          ?.consent_advisory_messages,
      ),
    consent_fpo_data_sharing:
      Boolean(
        profile
          ?.consent_fpo_data_sharing,
      ),
  };
}

export function toFpoForm(
  profile,
  user,
) {
  return {
    fpo_name:
      profile?.fpo_name || "",
    registration_number:
      profile
        ?.registration_number
      || "",
    registration_type:
      profile?.registration_type
      || "",
    date_of_registration:
      dateOnly(
        profile
          ?.date_of_registration,
      ),
    promoted_by:
      profile?.promoted_by || "",
    promoting_institution_name:
      profile
        ?.promoting_institution_name
      || "",
    contact_person_name:
      profile
        ?.contact_person_name
      || user?.full_name
      || "",
    contact_person_designation:
      profile
        ?.contact_person_designation
      || "",
    contact_phone:
      profile?.contact_phone
      || user?.phone_number
      || "",
    alternate_phone:
      profile?.alternate_phone
      || "",
    contact_email:
      profile?.contact_email
      || user?.email
      || "",
    profile_image_url:
      profile?.profile_image_url
      || "",
    state_name:
      profile?.state_name
      || "Odisha",
    district_name:
      profile?.district_name
      || "",
    block_name:
      profile?.block_name
      || "",
    block_code:
      numberFormValue(
        profile?.block_code,
      ),
    village_name:
      profile?.village_name
      || "",
    gram_panchayat:
      profile?.gram_panchayat
      || "",
    pincode:
      profile?.pincode || "",
    office_address:
      profile?.office_address
      || "",
    main_commodities:
      Array.isArray(
        profile?.main_commodities,
      )
        ? profile.main_commodities
          .join(", ")
        : profile
          ?.main_commodities
          || "",
    member_count:
      numberFormValue(
        profile?.member_count,
      ),
    active_member_count:
      numberFormValue(
        profile
          ?.active_member_count,
      ),
    services_provided:
      Array.isArray(
        profile?.services_provided,
      )
        ? profile.services_provided
          .join(", ")
        : profile
          ?.services_provided
          || "",
  };
}

function dirtyKeys(dirtyFields) {
  return new Set(
    Object.keys(dirtyFields || {}),
  );
}

function locationWasChanged(keys) {
  return [...LOCATION_FIELDS].some(
    (field) => keys.has(field),
  );
}

export function buildFarmerPayload(
  values,
  dirtyFields,
) {
  const keys = dirtyKeys(dirtyFields);
  const payload = {};

  const normalFields = [
    "full_name",
    "phone_number",
    "gender",
    "date_of_birth",
    "preferred_language",
    "aadhaar_last4",
    "profile_image_url",
    "gram_panchayat",
    "pincode",
    "farmer_type",
    "total_landholding_acres",
    "cultivated_area_acres",
    "primary_crop",
    "irrigation_status",
    "consent_location_use",
    "consent_data_processing",
    "consent_advisory_messages",
    "consent_fpo_data_sharing",
  ];

  normalFields.forEach((field) => {
    if (!keys.has(field)) return;

    payload[field] =
      typeof values[field] === "string"
        ? blankToNull(values[field])
        : values[field];
  });

  if (locationWasChanged(keys)) {
    if (values.district_name) {
      payload.state_name =
        values.state_name
        || "Odisha";
      payload.district_name =
        values.district_name;
      payload.block_name =
        blankToNull(
          values.block_name,
        );
      payload.block_code =
        blankToNull(
          values.block_code,
        );
      payload.village_name =
        blankToNull(
          values.village_name,
        );
    }
  }

  return payload;
}

export function buildFpoPayload(
  values,
  dirtyFields,
  setupRequired,
) {
  const keys = dirtyKeys(dirtyFields);
  const payload = {};

  const shouldInclude = (field) =>
    setupRequired || keys.has(field);

  const fields = [
    "fpo_name",
    "registration_number",
    "registration_type",
    "date_of_registration",
    "promoted_by",
    "promoting_institution_name",
    "contact_person_name",
    "contact_person_designation",
    "contact_phone",
    "alternate_phone",
    "contact_email",
    "profile_image_url",
    "gram_panchayat",
    "pincode",
    "office_address",
    "member_count",
    "active_member_count",
  ];

  fields.forEach((field) => {
    if (!shouldInclude(field)) {
      return;
    }

    payload[field] =
      typeof values[field] === "string"
        ? blankToNull(values[field])
        : values[field];
  });

  if (
    shouldInclude(
      "main_commodities",
    )
  ) {
    payload.main_commodities =
      commaList(
        values.main_commodities,
      );
  }

  if (
    shouldInclude(
      "services_provided",
    )
  ) {
    payload.services_provided =
      commaList(
        values.services_provided,
      );
  }

  if (
    setupRequired
    || locationWasChanged(keys)
  ) {
    payload.state_name =
      values.state_name || "Odisha";
    payload.district_name =
      blankToNull(
        values.district_name,
      );
    payload.block_name =
      blankToNull(values.block_name);
    payload.block_code =
      blankToNull(values.block_code);
    payload.village_name =
      blankToNull(
        values.village_name,
      );
  }

  return payload;
}

export function applyApiFieldErrors(
  error,
  setError,
) {
  let applied = false;

  for (
    const item
    of error?.fields || []
  ) {
    const location =
      Array.isArray(item?.loc)
        ? item.loc
        : [];

    const field = [...location]
      .reverse()
      .find(
        (part) =>
          typeof part === "string"
          && ![
            "body",
            "query",
            "path",
            "response",
          ].includes(part),
      );

    if (!field) continue;

    setError(field, {
      type: "server",
      message:
        item?.msg
        || "Check this value.",
    });

    applied = true;
  }

  return applied;
}

export function downloadProfileJson(
  payload,
) {
  const blob = new Blob(
    [
      JSON.stringify(
        payload,
        null,
        2,
      ),
    ],
    {
      type: "application/json",
    },
  );

  const url =
    URL.createObjectURL(blob);

  const link =
    document.createElement("a");

  link.href = url;
  link.download =
    `maatitrace-${
      payload?.profile_type
      || "profile"
    }-profile.json`;

  document.body.appendChild(link);
  link.click();
  link.remove();

  URL.revokeObjectURL(url);
}

export function readableFieldName(
  field,
) {
  return String(field || "")
    .replaceAll("_", " ")
    .replace(
      /\b\w/g,
      (character) =>
        character.toUpperCase(),
    );
}
