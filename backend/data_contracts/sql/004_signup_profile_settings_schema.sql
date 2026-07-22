ALTER TABLE IF EXISTS farmer_profiles
  ADD COLUMN IF NOT EXISTS date_of_birth DATE,
  ADD COLUMN IF NOT EXISTS preferred_language TEXT,
  ADD COLUMN IF NOT EXISTS aadhaar_last4 TEXT,
  ADD COLUMN IF NOT EXISTS kisan_pehchan_patra_document_url TEXT,
  ADD COLUMN IF NOT EXISTS gram_panchayat TEXT,
  ADD COLUMN IF NOT EXISTS pincode TEXT,
  ADD COLUMN IF NOT EXISTS farmer_type TEXT,
  ADD COLUMN IF NOT EXISTS total_landholding_acres DOUBLE PRECISION,
  ADD COLUMN IF NOT EXISTS cultivated_area_acres DOUBLE PRECISION,
  ADD COLUMN IF NOT EXISTS primary_crop TEXT,
  ADD COLUMN IF NOT EXISTS irrigation_status TEXT,
  ADD COLUMN IF NOT EXISTS kyc_status TEXT DEFAULT 'pending',
  ADD COLUMN IF NOT EXISTS address_verification_status TEXT DEFAULT 'self_declared',
  ADD COLUMN IF NOT EXISTS verification_status TEXT DEFAULT 'pending',
  ADD COLUMN IF NOT EXISTS consent_location_use BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS consent_data_processing BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS consent_advisory_messages BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS consent_fpo_data_sharing BOOLEAN DEFAULT FALSE;

ALTER TABLE IF EXISTS fpos
  ADD COLUMN IF NOT EXISTS registration_type TEXT,
  ADD COLUMN IF NOT EXISTS date_of_registration DATE,
  ADD COLUMN IF NOT EXISTS promoted_by TEXT,
  ADD COLUMN IF NOT EXISTS promoting_institution_name TEXT,
  ADD COLUMN IF NOT EXISTS contact_person_name TEXT,
  ADD COLUMN IF NOT EXISTS contact_person_designation TEXT,
  ADD COLUMN IF NOT EXISTS alternate_phone TEXT,
  ADD COLUMN IF NOT EXISTS village_name TEXT,
  ADD COLUMN IF NOT EXISTS pincode TEXT,
  ADD COLUMN IF NOT EXISTS office_address TEXT,
  ADD COLUMN IF NOT EXISTS main_commodities TEXT[],
  ADD COLUMN IF NOT EXISTS member_count INTEGER,
  ADD COLUMN IF NOT EXISTS active_member_count INTEGER,
  ADD COLUMN IF NOT EXISTS services_provided TEXT[],
  ADD COLUMN IF NOT EXISTS onboarding_status TEXT DEFAULT 'pending',
  ADD COLUMN IF NOT EXISTS verification_status TEXT DEFAULT 'pending';

CREATE TABLE IF NOT EXISTS farmer_documents (
  document_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  farmer_id UUID NOT NULL REFERENCES farmer_profiles(farmer_id),
  document_type TEXT NOT NULL,
  document_name TEXT,
  document_url TEXT,
  verification_status TEXT DEFAULT 'pending',
  uploaded_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS user_profile_audit_logs (
  audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID,
  entity_type TEXT NOT NULL,
  entity_id UUID,
  action TEXT NOT NULL,
  changed_fields JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS signup_otp_sessions (
  signup_session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  full_name TEXT NOT NULL,
  phone_number TEXT NOT NULL,
  email TEXT,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL,
  fpo_id TEXT,
  invite_code TEXT,
  otp_hash TEXT NOT NULL,
  otp_expires_at TIMESTAMPTZ NOT NULL,
  verified_at TIMESTAMPTZ,
  attempts INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT now(),
  completed_at TIMESTAMPTZ
);
