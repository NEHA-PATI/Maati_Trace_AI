--
-- PostgreSQL database dump
--

-- Dumped from database version 17.5
-- Dumped by pg_dump version 17.5

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: fpo_access_requests; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.fpo_access_requests (request_id, organisation_name, registration_number, contact_person_name, contact_email, contact_phone, state_name, district_name, message, status, reviewed_by, reviewed_at, review_note, created_ip, device_id_hash, correlation_id, created_at, updated_at) VALUES ('de4be30b-cf44-45b7-999f-fee1c12e9149', 'Rani Sukadei FPO Cuttack', '3', 'Amir Faishal', 'amirfaishal484@gmail.com', '+916372440443', 'Odisha', 'Cuttack', 'I am the person responsible for the FPO rani sukadei', 'closed', '62f7885e-35c2-434c-afec-bb5b14428db9', '2026-09-25 13:06:07.52143+05:30', 'FPO invitation queued successfully.', '127.0.0.1', 'f4513304f8acd05c5812a2402ff3c790fe8f8bcad056cac383811c995facca99', '4ac913fe-1d1f-4217-b26a-030b083af1ef', '2026-09-25 12:01:01.989153+05:30', '2026-09-25 13:06:07.52143+05:30');
INSERT INTO public.fpo_access_requests (request_id, organisation_name, registration_number, contact_person_name, contact_email, contact_phone, state_name, district_name, message, status, reviewed_by, reviewed_at, review_note, created_ip, device_id_hash, correlation_id, created_at, updated_at) VALUES ('afbf8e78-5f34-462a-877a-85e445d6f765', 'FPO Satyabadi Puri', '2222222222', 'NEHA PATI', 'nehapati11122004@gmail.com', '+919665707987', 'Odisha', 'khordha', NULL, 'approved', '62f7885e-35c2-434c-afec-bb5b14428db9', '2026-09-25 13:06:13.015276+05:30', 'Approved for secure FPO invitation.', '127.0.0.1', 'f4513304f8acd05c5812a2402ff3c790fe8f8bcad056cac383811c995facca99', 'dfe4ae27-eecb-46f2-9c95-41a91f59dc7b', '2026-09-21 16:56:44.180229+05:30', '2026-09-25 13:06:13.015276+05:30');
INSERT INTO public.fpo_access_requests (request_id, organisation_name, registration_number, contact_person_name, contact_email, contact_phone, state_name, district_name, message, status, reviewed_by, reviewed_at, review_note, created_ip, device_id_hash, correlation_id, created_at, updated_at) VALUES ('6a32528c-16a5-412b-9525-1e0758851442', 'Rani Sukadei FPO Cuttack', '333333333333', 'Amir Faishal', 'amirfaishal484@gmail.com', '+916372440443', 'Odisha', 'khordha', 'I am representing the Rani Sukadei FPO', 'closed', '62f7885e-35c2-434c-afec-bb5b14428db9', '2026-09-25 13:53:04.807549+05:30', 'FPO invitation queued successfully.', '127.0.0.1', 'f4513304f8acd05c5812a2402ff3c790fe8f8bcad056cac383811c995facca99', 'a21e9c3d-baf8-4ea6-b64d-89383561978d', '2026-09-25 13:52:25.065112+05:30', '2026-09-25 13:53:04.807549+05:30');
INSERT INTO public.fpo_access_requests (request_id, organisation_name, registration_number, contact_person_name, contact_email, contact_phone, state_name, district_name, message, status, reviewed_by, reviewed_at, review_note, created_ip, device_id_hash, correlation_id, created_at, updated_at) VALUES ('6512731b-0c95-4bf1-887f-0a026bd63a60', 'Rani Sukadei FPO Cuttack', '333333333333', 'Amir Faishal', 'amirfaishal484@gmail.com', '+916372440443', 'Odisha', 'khordha', 'i am representing the fpo , kindly accept my request', 'closed', '62f7885e-35c2-434c-afec-bb5b14428db9', '2026-09-25 14:35:16.982941+05:30', 'FPO invitation queued successfully.', '127.0.0.1', 'f4513304f8acd05c5812a2402ff3c790fe8f8bcad056cac383811c995facca99', '24bab292-a836-447d-9fbb-f375eb1a3c7e', '2026-09-25 14:35:04.538087+05:30', '2026-09-25 14:35:16.982941+05:30');
INSERT INTO public.fpo_access_requests (request_id, organisation_name, registration_number, contact_person_name, contact_email, contact_phone, state_name, district_name, message, status, reviewed_by, reviewed_at, review_note, created_ip, device_id_hash, correlation_id, created_at, updated_at) VALUES ('7cc77847-cd07-43f4-a2e3-cacd55dcf717', 'Rani Sukadei FPO Cuttack', '333333333333', 'Amir Faishal', 'nehapati5357182@gmail.com', '+916372440443', 'Odisha', 'khordha', 'i am representing the fpo , accept my request', 'closed', '62f7885e-35c2-434c-afec-bb5b14428db9', '2026-09-25 15:14:10.729425+05:30', 'FPO invitation queued successfully.', '127.0.0.1', 'f4513304f8acd05c5812a2402ff3c790fe8f8bcad056cac383811c995facca99', '2bb73c14-a310-4dc6-bead-464393413c20', '2026-09-25 14:43:48.401304+05:30', '2026-09-25 15:14:10.729425+05:30');


--
-- Data for Name: fpos; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.fpos (fpo_id, fpo_name, registration_number, state_name, district_name, block_name, block_code, contact_phone, contact_email, is_active, created_at, updated_at, district_code, registration_type, date_of_registration, promoted_by, promoting_institution_name, contact_person_name, contact_person_designation, alternate_phone, village_name, gram_panchayat, pincode, office_address, main_commodities, member_count, active_member_count, services_provided, verification_status, profile_image_url, onboarding_completed_at, profile_version, legal_name, display_name, organisation_type, cin, pan_encrypted, gstin, website_url, organisation_description, operating_since_year, logo_object_key, logo_mime_type, logo_size_bytes, logo_checksum, registered_address_line_1, registered_address_line_2, women_member_count, small_marginal_member_count, declared_area_acres, profile_completion_percentage, verification_readiness_percentage) VALUES ('318efbab-4c24-47f7-9060-22bf91bad3a0', 'Jayadeva FPO Khordha', '4444444444', 'Odisha', 'Khordha', 'Chilika', 3462, '+916203771750', 'taniya3002@gmail.com', true, '2026-09-25 12:22:55.45348+05:30', '2026-09-25 12:25:28.831635+05:30', 362, 'cooperative_society', '2025-04-17', NULL, NULL, 'Taniya Ghosh', NULL, NULL, NULL, NULL, NULL, NULL, '{}', NULL, NULL, '{}', 'pending', NULL, '2026-09-25 12:25:28.831635+05:30', 2, 'Jayadeva FPO', 'Jayadeva FPO Khordha', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0, 0);
INSERT INTO public.fpos (fpo_id, fpo_name, registration_number, state_name, district_name, block_name, block_code, contact_phone, contact_email, is_active, created_at, updated_at, district_code, registration_type, date_of_registration, promoted_by, promoting_institution_name, contact_person_name, contact_person_designation, alternate_phone, village_name, gram_panchayat, pincode, office_address, main_commodities, member_count, active_member_count, services_provided, verification_status, profile_image_url, onboarding_completed_at, profile_version, legal_name, display_name, organisation_type, cin, pan_encrypted, gstin, website_url, organisation_description, operating_since_year, logo_object_key, logo_mime_type, logo_size_bytes, logo_checksum, registered_address_line_1, registered_address_line_2, women_member_count, small_marginal_member_count, declared_area_acres, profile_completion_percentage, verification_readiness_percentage) VALUES ('eec41b5a-d542-44fd-92a9-c3870578c125', 'FPO Satyabadi Puri', '1111111111', 'Odisha', 'Bargarh', 'Bijepur', 3316, '+918093669088', 'soumikbasu2003@gmail.com', true, '2026-09-21 13:02:33.51896+05:30', '2026-09-21 17:31:17.665154+05:30', 347, 'cooperative_society', '2026-09-01', NULL, NULL, 'SOUMIK FARMER', NULL, NULL, NULL, NULL, NULL, NULL, '{}', NULL, NULL, '{}', 'pending', NULL, '2026-09-21 13:02:33.51896+05:30', 3, 'Satyabadi Puri FPO', 'Satyabadi Puri FPO', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0, 0);
INSERT INTO public.fpos (fpo_id, fpo_name, registration_number, state_name, district_name, block_name, block_code, contact_phone, contact_email, is_active, created_at, updated_at, district_code, registration_type, date_of_registration, promoted_by, promoting_institution_name, contact_person_name, contact_person_designation, alternate_phone, village_name, gram_panchayat, pincode, office_address, main_commodities, member_count, active_member_count, services_provided, verification_status, profile_image_url, onboarding_completed_at, profile_version, legal_name, display_name, organisation_type, cin, pan_encrypted, gstin, website_url, organisation_description, operating_since_year, logo_object_key, logo_mime_type, logo_size_bytes, logo_checksum, registered_address_line_1, registered_address_line_2, women_member_count, small_marginal_member_count, declared_area_acres, profile_completion_percentage, verification_readiness_percentage) VALUES ('273f8c1d-ccd3-46fc-82ea-89908bc63930', 'Rani Sukadei FPO Cuttack', '333333333333', 'Odisha', 'Cuttack', 'Salepur', 3343, '+916372440443', 'nehapati5357182@gmail.com', true, '2026-09-25 15:15:23.812573+05:30', '2026-09-25 15:46:05.82182+05:30', 350, 'other', '2020-02-25', NULL, NULL, 'Amir Faishal', 'owner', NULL, NULL, NULL, '751028', 'CGEWHO kendriya vihar Phase 1 , B5/76', '{}', NULL, NULL, '{}', 'pending', NULL, '2026-09-25 15:46:05.82182+05:30', 2, 'Rani Sukadei FPO Cuttack', 'Rani Sukadei FPO Cuttack', 'corporate', NULL, NULL, NULL, NULL, NULL, 2020, NULL, NULL, NULL, NULL, 'CGEWHO kendriya vihar Phase 1 , B5/76', NULL, 2, 4, 6.0000, 0, 0);
INSERT INTO public.fpos (fpo_id, fpo_name, registration_number, state_name, district_name, block_name, block_code, contact_phone, contact_email, is_active, created_at, updated_at, district_code, registration_type, date_of_registration, promoted_by, promoting_institution_name, contact_person_name, contact_person_designation, alternate_phone, village_name, gram_panchayat, pincode, office_address, main_commodities, member_count, active_member_count, services_provided, verification_status, profile_image_url, onboarding_completed_at, profile_version, legal_name, display_name, organisation_type, cin, pan_encrypted, gstin, website_url, organisation_description, operating_since_year, logo_object_key, logo_mime_type, logo_size_bytes, logo_checksum, registered_address_line_1, registered_address_line_2, women_member_count, small_marginal_member_count, declared_area_acres, profile_completion_percentage, verification_readiness_percentage) VALUES ('d13cdfbe-857c-4d46-b3fe-c53329a6c95e', 'Demo MaatiTrace FPO', 'DEMO-FPO-2026-001', 'Odisha', 'Puri', 'Puri Sadar', NULL, '+919876543219', 'fpo.demo@maatitrace.local', true, '2026-09-16 11:35:10.141254+05:30', '2026-09-21 16:08:45.575264+05:30', NULL, 'FPO', '2026-09-16', 'Self Help Group', 'MaatiTrace Demo', 'Demo FPO Owner', 'Owner', NULL, 'Demo Village', 'Demo GP', '752001', 'Demo FPO Office, Puri, Odisha', '{Paddy,Mango,Vegetables}', 100, 80, '{farm_registration,crop_advisory,market_linkage}', 'verified', NULL, '2026-09-16 11:35:10.141254+05:30', 1, 'Demo MaatiTrace FPO', 'Demo MaatiTrace FPO', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0, 0);


--
-- Data for Name: fpo_organizations; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.fpo_organizations (fpo_id, auth_user_id, public_fpo_id, lifecycle_status, provisioning_status, verification_status, verification_level, commercial_status, discoverable, approved_at, approved_by, suspended_at, suspension_reason, version, created_at, updated_at, profile_fpo_id, provisioning_error) VALUES ('420e6f40-2d99-4fc5-93c4-2ce6fc869c85', '48bcc40d-6476-49b8-8981-fe5be90fd88b', 'MTFPO-OD-26-100414-Y', 'ACTIVE', 'READY', 'APPROVED', NULL, 'UNASSIGNED', true, '2026-09-25 13:48:28.036267+05:30', '62f7885e-35c2-434c-afec-bb5b14428db9', NULL, NULL, 4, '2026-09-25 12:22:55.45348+05:30', '2026-09-25 13:48:28.036267+05:30', '318efbab-4c24-47f7-9060-22bf91bad3a0', NULL);
INSERT INTO public.fpo_organizations (fpo_id, auth_user_id, public_fpo_id, lifecycle_status, provisioning_status, verification_status, verification_level, commercial_status, discoverable, approved_at, approved_by, suspended_at, suspension_reason, version, created_at, updated_at, profile_fpo_id, provisioning_error) VALUES ('f2828e93-d068-427b-9028-437aa358006f', '19f6d134-b0c5-4ea3-ae47-296bdc06b59d', 'MTFPO-S20-26-100413-X', 'ACTIVE', 'READY', 'APPROVED', NULL, 'UNASSIGNED', true, '2026-09-21 17:35:33.618091+05:30', '62f7885e-35c2-434c-afec-bb5b14428db9', NULL, NULL, 7, '2026-09-21 17:14:00.622471+05:30', '2026-09-21 17:35:33.618091+05:30', 'eec41b5a-d542-44fd-92a9-c3870578c125', NULL);
INSERT INTO public.fpo_organizations (fpo_id, auth_user_id, public_fpo_id, lifecycle_status, provisioning_status, verification_status, verification_level, commercial_status, discoverable, approved_at, approved_by, suspended_at, suspension_reason, version, created_at, updated_at, profile_fpo_id, provisioning_error) VALUES ('3c96b2f5-67e9-45f8-be75-d0f1cce6265f', '77fd988f-f9f3-48cb-b8bc-b7187c765f43', 'MTFPO-S00-26-100415-Z', 'ACTIVE', 'READY', 'APPROVED', NULL, 'UNASSIGNED', true, '2026-09-25 15:49:37.984651+05:30', '62f7885e-35c2-434c-afec-bb5b14428db9', NULL, NULL, 4, '2026-09-25 15:15:23.812573+05:30', '2026-09-25 15:49:37.984651+05:30', '273f8c1d-ccd3-46fc-82ea-89908bc63930', NULL);


--
-- Data for Name: fpo_advisory_templates; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_farmer_segments; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_advisory_campaigns; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_farmer_relationships; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.fpo_farmer_relationships (relationship_id, fpo_id, farmer_user_id, farmer_profile_id, relationship_type, status, initiated_by, farmer_consented_at, fpo_accepted_at, fpo_accepted_by, revoked_at, revoked_by, revocation_reason, created_at, updated_at, farm_id) VALUES ('2bef9eac-2715-4953-962e-1411e2291ec4', 'f2828e93-d068-427b-9028-437aa358006f', 'd52292d8-8ada-465b-bc28-98a60f315a2f', '8a8f1f13-a42b-4ff5-a3e5-08ac1603c1b3', 'PRIMARY', 'ACTIVE', 'FARMER', '2026-09-22 16:16:21.22231+05:30', '2026-09-22 16:16:21.708581+05:30', '19f6d134-b0c5-4ea3-ae47-296bdc06b59d', NULL, NULL, NULL, '2026-09-22 16:16:21.22231+05:30', '2026-09-22 16:16:21.708581+05:30', NULL);
INSERT INTO public.fpo_farmer_relationships (relationship_id, fpo_id, farmer_user_id, farmer_profile_id, relationship_type, status, initiated_by, farmer_consented_at, fpo_accepted_at, fpo_accepted_by, revoked_at, revoked_by, revocation_reason, created_at, updated_at, farm_id) VALUES ('24e8e3de-58d3-4382-9192-2d61d0212867', 'f2828e93-d068-427b-9028-437aa358006f', 'd52292d8-8ada-465b-bc28-98a60f315a2f', '8a8f1f13-a42b-4ff5-a3e5-08ac1603c1b3', 'PRIMARY', 'REJECTED', 'FARMER', '2026-09-26 23:47:32.160865+05:30', NULL, '19f6d134-b0c5-4ea3-ae47-296bdc06b59d', NULL, NULL, NULL, '2026-09-26 23:47:32.160865+05:30', '2026-09-27 00:15:29.472262+05:30', '89d9cf9f-6f27-43e7-85d5-ce76063f7699');
INSERT INTO public.fpo_farmer_relationships (relationship_id, fpo_id, farmer_user_id, farmer_profile_id, relationship_type, status, initiated_by, farmer_consented_at, fpo_accepted_at, fpo_accepted_by, revoked_at, revoked_by, revocation_reason, created_at, updated_at, farm_id) VALUES ('2a5aa3c1-523d-4439-8fa8-64bd8ccdb85e', '3c96b2f5-67e9-45f8-be75-d0f1cce6265f', 'd52292d8-8ada-465b-bc28-98a60f315a2f', '8a8f1f13-a42b-4ff5-a3e5-08ac1603c1b3', 'PRIMARY', 'ACTIVE', 'FARMER', '2026-09-27 00:19:55.925973+05:30', '2026-09-27 00:23:27.786523+05:30', '77fd988f-f9f3-48cb-b8bc-b7187c765f43', NULL, NULL, NULL, '2026-09-27 00:19:55.925973+05:30', '2026-09-27 00:23:27.786523+05:30', 'ce8ca015-3efe-47d7-b3bf-1e1dd8b8d73d');
INSERT INTO public.fpo_farmer_relationships (relationship_id, fpo_id, farmer_user_id, farmer_profile_id, relationship_type, status, initiated_by, farmer_consented_at, fpo_accepted_at, fpo_accepted_by, revoked_at, revoked_by, revocation_reason, created_at, updated_at, farm_id) VALUES ('de7850e0-d28a-47c8-a014-4968f356d586', '420e6f40-2d99-4fc5-93c4-2ce6fc869c85', 'd52292d8-8ada-465b-bc28-98a60f315a2f', '8a8f1f13-a42b-4ff5-a3e5-08ac1603c1b3', 'PRIMARY', 'ACTIVE', 'FARMER', '2026-09-27 21:00:30.289805+05:30', '2026-09-27 21:03:22.571268+05:30', '48bcc40d-6476-49b8-8981-fe5be90fd88b', NULL, NULL, NULL, '2026-09-27 21:00:30.289805+05:30', '2026-09-27 21:03:22.571268+05:30', 'ce8ca015-3efe-47d7-b3bf-1e1dd8b8d73d');


--
-- Data for Name: fpo_farmer_relationship_consents; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.fpo_farmer_relationship_consents (consent_id, relationship_id, policy_code, policy_version, purpose, scopes, language_code, capture_channel, consent_content_hash, captured_at, captured_by, revoked_at, revoked_by, revocation_reason, expires_at, evidence_metadata) VALUES ('de8c3d71-d381-47ab-b4fb-5b2d658ea175', '2bef9eac-2715-4953-962e-1411e2291ec4', 'FPO_DATA_SHARING', '2', 'Consent-backed FPO portfolio access', '{PROFILE_READ,CONTACT_MASKED_READ,FARM_READ,CROP_READ,OBSERVATION_READ,LAND_INTELLIGENCE_READ}', 'en', 'WEB', 'b5a544d3fa01f1bfaf4b36c5da97f91a6462b71b8d1b6be11c36cacc868fa268', '2026-09-22 16:16:21.22231+05:30', 'd52292d8-8ada-465b-bc28-98a60f315a2f', NULL, NULL, NULL, NULL, '{"ip_address": "127.0.0.1", "correlation_id": "fpo-e2e-57fa7bca-b595-4e9a-a434-03e10c624837", "capture_channel": "WEB", "policy_content_hash": "b5a544d3fa01f1bfaf4b36c5da97f91a6462b71b8d1b6be11c36cacc868fa268"}');
INSERT INTO public.fpo_farmer_relationship_consents (consent_id, relationship_id, policy_code, policy_version, purpose, scopes, language_code, capture_channel, consent_content_hash, captured_at, captured_by, revoked_at, revoked_by, revocation_reason, expires_at, evidence_metadata) VALUES ('4dd5ba28-1bf4-4190-b7fe-aa037708fc58', '24e8e3de-58d3-4382-9192-2d61d0212867', 'FPO_DATA_SHARING', '2', 'Consent-backed FPO portfolio access', '{PROFILE_READ,CONTACT_MASKED_READ,FARM_READ,CROP_READ,OBSERVATION_READ,LAND_INTELLIGENCE_READ}', 'en', 'WEB', 'b5a544d3fa01f1bfaf4b36c5da97f91a6462b71b8d1b6be11c36cacc868fa268', '2026-09-26 23:47:32.160865+05:30', 'd52292d8-8ada-465b-bc28-98a60f315a2f', NULL, NULL, NULL, NULL, '{"ip_address": "127.0.0.1", "correlation_id": "35ac0bde-7493-432e-9618-eea31a6f41c5", "capture_channel": "WEB", "policy_content_hash": "b5a544d3fa01f1bfaf4b36c5da97f91a6462b71b8d1b6be11c36cacc868fa268"}');
INSERT INTO public.fpo_farmer_relationship_consents (consent_id, relationship_id, policy_code, policy_version, purpose, scopes, language_code, capture_channel, consent_content_hash, captured_at, captured_by, revoked_at, revoked_by, revocation_reason, expires_at, evidence_metadata) VALUES ('12ffb70c-2910-4339-8b04-04df730e82c4', '2a5aa3c1-523d-4439-8fa8-64bd8ccdb85e', 'FPO_DATA_SHARING', '2', 'Consent-backed FPO portfolio access', '{PROFILE_READ,CONTACT_MASKED_READ,FARM_READ,CROP_READ,OBSERVATION_READ,LAND_INTELLIGENCE_READ}', 'en', 'WEB', 'b5a544d3fa01f1bfaf4b36c5da97f91a6462b71b8d1b6be11c36cacc868fa268', '2026-09-27 00:19:55.925973+05:30', 'd52292d8-8ada-465b-bc28-98a60f315a2f', NULL, NULL, NULL, NULL, '{"ip_address": "127.0.0.1", "correlation_id": "894d11d0-19ad-49fb-9c58-020e94e123b5", "capture_channel": "WEB", "policy_content_hash": "b5a544d3fa01f1bfaf4b36c5da97f91a6462b71b8d1b6be11c36cacc868fa268"}');
INSERT INTO public.fpo_farmer_relationship_consents (consent_id, relationship_id, policy_code, policy_version, purpose, scopes, language_code, capture_channel, consent_content_hash, captured_at, captured_by, revoked_at, revoked_by, revocation_reason, expires_at, evidence_metadata) VALUES ('7a81ea3c-0c1e-43ea-b053-21c7fc1b1d9d', 'de7850e0-d28a-47c8-a014-4968f356d586', 'FPO_DATA_SHARING', '2', 'Consent-backed FPO portfolio access', '{PROFILE_READ,CONTACT_MASKED_READ,FARM_READ,CROP_READ,OBSERVATION_READ,LAND_INTELLIGENCE_READ,ADVISORY_MESSAGE,CONTACT_DIRECT_READ,COMMERCIAL_PARTICIPATION}', 'en', 'WEB', 'b5a544d3fa01f1bfaf4b36c5da97f91a6462b71b8d1b6be11c36cacc868fa268', '2026-09-27 21:00:30.289805+05:30', 'd52292d8-8ada-465b-bc28-98a60f315a2f', NULL, NULL, NULL, NULL, '{"ip_address": "127.0.0.1", "correlation_id": "66bb0949-1772-4a28-af1e-04f546c2d1b6", "capture_channel": "WEB", "policy_content_hash": "b5a544d3fa01f1bfaf4b36c5da97f91a6462b71b8d1b6be11c36cacc868fa268"}');


--
-- Data for Name: fpo_advisory_recipients; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_procurement_plans; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_aggregation_lots; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_alert_metric_registry; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.fpo_alert_metric_registry (metric_key, display_name, description, unit, value_type, allowed_operators, minimum_threshold, maximum_threshold, supported_scopes, data_source, freshness_requirement, risk_level, status, created_at, updated_at) VALUES ('OBSERVATION_AGE_DAYS', 'Observation age', 'Days since the latest trusted observation.', 'days', 'NUMBER', '{GREATER_THAN,LESS_THAN}', NULL, NULL, '{PORTFOLIO,SEGMENT,CROP,GEOGRAPHY}', 'analytics', NULL, 'MEDIUM', 'ACTIVE', '2026-09-23 21:21:34.16814+05:30', '2026-09-23 21:41:58.922469+05:30');
INSERT INTO public.fpo_alert_metric_registry (metric_key, display_name, description, unit, value_type, allowed_operators, minimum_threshold, maximum_threshold, supported_scopes, data_source, freshness_requirement, risk_level, status, created_at, updated_at) VALUES ('OPEN_ALERT_COUNT', 'Open alerts', 'Number of unresolved operational alerts.', 'alerts', 'NUMBER', '{GREATER_THAN,EQUALS}', NULL, NULL, '{PORTFOLIO,SEGMENT,GEOGRAPHY}', 'fpo_management', NULL, 'MEDIUM', 'ACTIVE', '2026-09-23 21:21:34.16814+05:30', '2026-09-23 21:41:58.922469+05:30');
INSERT INTO public.fpo_alert_metric_registry (metric_key, display_name, description, unit, value_type, allowed_operators, minimum_threshold, maximum_threshold, supported_scopes, data_source, freshness_requirement, risk_level, status, created_at, updated_at) VALUES ('FARM_CONDITION_STATUS', 'Farm condition', 'Latest server-calculated farm condition status.', 'status', 'ENUM', '{EQUALS}', NULL, NULL, '{PORTFOLIO,SEGMENT,CROP,GEOGRAPHY}', 'analytics', NULL, 'HIGH', 'ACTIVE', '2026-09-23 21:21:34.16814+05:30', '2026-09-23 21:41:58.922469+05:30');
INSERT INTO public.fpo_alert_metric_registry (metric_key, display_name, description, unit, value_type, allowed_operators, minimum_threshold, maximum_threshold, supported_scopes, data_source, freshness_requirement, risk_level, status, created_at, updated_at) VALUES ('PORTFOLIO_AREA_ACRES', 'Portfolio area', 'Active relationship farm area.', 'acres', 'NUMBER', '{GREATER_THAN,LESS_THAN}', NULL, NULL, '{PORTFOLIO,GEOGRAPHY}', 'farm_registry', NULL, 'LOW', 'ACTIVE', '2026-09-23 21:21:34.16814+05:30', '2026-09-23 21:41:58.922469+05:30');


--
-- Data for Name: fpo_alert_rules; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_api_clients; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_audit_events; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.fpo_audit_events (audit_event_id, fpo_id, actor_user_id, action, target_type, target_id, metadata, created_at) VALUES ('b4100151-e4e3-4ff8-a36f-df79a264086d', 'f2828e93-d068-427b-9028-437aa358006f', '62f7885e-35c2-434c-afec-bb5b14428db9', 'FPO_CLASS_ASSIGNED', 'fpo_class_assignment', 'ff99d453-19d0-4f3d-b988-f80cb46c21e8', '{"class_code": "A", "configuration_version": 1}', '2026-09-21 17:35:25.457069+05:30');
INSERT INTO public.fpo_audit_events (audit_event_id, fpo_id, actor_user_id, action, target_type, target_id, metadata, created_at) VALUES ('4985163f-ec60-4351-990c-c229860787df', 'f2828e93-d068-427b-9028-437aa358006f', '62f7885e-35c2-434c-afec-bb5b14428db9', 'FPO_VERIFICATION_REVIEWED', 'verification_submission', '060db737-192e-4490-976a-9b3c676a05de', '{"note": "", "status": "APPROVED"}', '2026-09-21 17:35:33.618091+05:30');
INSERT INTO public.fpo_audit_events (audit_event_id, fpo_id, actor_user_id, action, target_type, target_id, metadata, created_at) VALUES ('f33a922a-e6ef-4fe9-9811-c782d128a36a', 'f2828e93-d068-427b-9028-437aa358006f', '19f6d134-b0c5-4ea3-ae47-296bdc06b59d', 'FPO_RELATIONSHIP_DECIDED', 'farmer_relationship', '2bef9eac-2715-4953-962e-1411e2291ec4', '{"decision": "ACTIVE", "farmer_user_id": "d52292d8-8ada-465b-bc28-98a60f315a2f"}', '2026-09-22 16:16:21.708581+05:30');
INSERT INTO public.fpo_audit_events (audit_event_id, fpo_id, actor_user_id, action, target_type, target_id, metadata, created_at) VALUES ('1eb4013f-f653-451d-8ef8-1d60f2dab4e7', NULL, '62f7885e-35c2-434c-afec-bb5b14428db9', 'FPO_RECONCILIATION_COMPLETED', 'reconciliation_run', '3f283863-23ce-4cb1-ad42-9abb890f64f4', '{"run_id": "3f283863-23ce-4cb1-ad42-9abb890f64f4", "status": "COMPLETED", "orphaned_organizations": 0, "organizations_refreshed": 1, "cleared_stale_projections": 0, "repaired_farmer_projections": 0}', '2026-09-22 16:16:22.176156+05:30');
INSERT INTO public.fpo_audit_events (audit_event_id, fpo_id, actor_user_id, action, target_type, target_id, metadata, created_at) VALUES ('f6ceeb6b-6b5c-45b3-9c93-1c9a95c25a7c', NULL, '62f7885e-35c2-434c-afec-bb5b14428db9', 'FPO_RECONCILIATION_COMPLETED', 'reconciliation_run', '336abb2f-1dcb-40a5-9b3e-170fc1caf827', '{"run_id": "336abb2f-1dcb-40a5-9b3e-170fc1caf827", "status": "COMPLETED", "orphaned_organizations": 0, "organizations_refreshed": 1, "cleared_stale_projections": 0, "repaired_farmer_projections": 0}', '2026-09-22 16:17:27.787758+05:30');
INSERT INTO public.fpo_audit_events (audit_event_id, fpo_id, actor_user_id, action, target_type, target_id, metadata, created_at) VALUES ('f2aaa501-a956-4916-b0f9-2a1baf9a5d88', '420e6f40-2d99-4fc5-93c4-2ce6fc869c85', '62f7885e-35c2-434c-afec-bb5b14428db9', 'FPO_VERIFICATION_CHECKLIST_UPDATED', 'verification_checklist', 'ab4fa747-f89d-4b84-9e6f-81951df8fdb2', '{"note": "Reviewed in FPO management: PASS", "result": "PASS"}', '2026-09-25 13:30:44.360648+05:30');
INSERT INTO public.fpo_audit_events (audit_event_id, fpo_id, actor_user_id, action, target_type, target_id, metadata, created_at) VALUES ('9f0c8196-5f14-4432-871b-7103dad612c9', '420e6f40-2d99-4fc5-93c4-2ce6fc869c85', '62f7885e-35c2-434c-afec-bb5b14428db9', 'FPO_VERIFICATION_CHECKLIST_UPDATED', 'verification_checklist', '7f40677f-d41c-44f6-a3e9-877d744f9780', '{"note": "Reviewed in FPO management: PASS", "result": "PASS"}', '2026-09-25 13:30:45.233851+05:30');
INSERT INTO public.fpo_audit_events (audit_event_id, fpo_id, actor_user_id, action, target_type, target_id, metadata, created_at) VALUES ('f87531a8-1f53-4a1e-b63a-337a41ea2dd6', '420e6f40-2d99-4fc5-93c4-2ce6fc869c85', '62f7885e-35c2-434c-afec-bb5b14428db9', 'FPO_VERIFICATION_CHECKLIST_UPDATED', 'verification_checklist', '5212bcab-c6b0-4c59-9476-87ad83c1081e', '{"note": "Reviewed in FPO management: PASS", "result": "PASS"}', '2026-09-25 13:30:46.746229+05:30');
INSERT INTO public.fpo_audit_events (audit_event_id, fpo_id, actor_user_id, action, target_type, target_id, metadata, created_at) VALUES ('5785e904-ad12-431a-87cd-619792d93ff7', '420e6f40-2d99-4fc5-93c4-2ce6fc869c85', '62f7885e-35c2-434c-afec-bb5b14428db9', 'FPO_VERIFICATION_CHECKLIST_UPDATED', 'verification_checklist', '22c092cc-5f5a-43c0-8d11-3693d4be6b95', '{"note": "Reviewed in FPO management: PASS", "result": "PASS"}', '2026-09-25 13:30:48.181145+05:30');
INSERT INTO public.fpo_audit_events (audit_event_id, fpo_id, actor_user_id, action, target_type, target_id, metadata, created_at) VALUES ('7d37f280-5c4e-428e-818d-5790f7695e60', '420e6f40-2d99-4fc5-93c4-2ce6fc869c85', '62f7885e-35c2-434c-afec-bb5b14428db9', 'FPO_VERIFICATION_CHECKLIST_UPDATED', 'verification_checklist', 'b988ec79-d75d-4191-a2e7-d1676bb16637', '{"note": "Reviewed in FPO management: PASS", "result": "PASS"}', '2026-09-25 13:30:49.26197+05:30');
INSERT INTO public.fpo_audit_events (audit_event_id, fpo_id, actor_user_id, action, target_type, target_id, metadata, created_at) VALUES ('cfb16865-a894-4d0e-b73d-fb2bea446e06', '420e6f40-2d99-4fc5-93c4-2ce6fc869c85', '62f7885e-35c2-434c-afec-bb5b14428db9', 'FPO_CLASS_ASSIGNED', 'fpo_class_assignment', '5b7005ae-3d55-4785-97bd-e0d0d4a28ca1', '{"class_code": "B", "configuration_version": 1}', '2026-09-25 13:38:17.942142+05:30');
INSERT INTO public.fpo_audit_events (audit_event_id, fpo_id, actor_user_id, action, target_type, target_id, metadata, created_at) VALUES ('2f95d3cc-2986-4bac-8e5c-0563ebea5165', '420e6f40-2d99-4fc5-93c4-2ce6fc869c85', '62f7885e-35c2-434c-afec-bb5b14428db9', 'FPO_DOCUMENT_VALIDATED', 'verification_document', 'c186f9c0-59c9-46e4-b72e-4f2a25159c6c', '{"reason": "Document reviewed and accepted.", "validation_status": "VALID"}', '2026-09-25 13:48:09.086556+05:30');
INSERT INTO public.fpo_audit_events (audit_event_id, fpo_id, actor_user_id, action, target_type, target_id, metadata, created_at) VALUES ('4e988eed-7670-40b6-ab9a-51d7b3490e0f', '420e6f40-2d99-4fc5-93c4-2ce6fc869c85', '62f7885e-35c2-434c-afec-bb5b14428db9', 'FPO_DOCUMENT_VALIDATED', 'verification_document', '9b05ad19-58cb-4883-a69b-cc3b796d9bb2', '{"reason": "Document reviewed and accepted.", "validation_status": "VALID"}', '2026-09-25 13:48:11.290245+05:30');
INSERT INTO public.fpo_audit_events (audit_event_id, fpo_id, actor_user_id, action, target_type, target_id, metadata, created_at) VALUES ('64203cb1-9390-428e-be3e-17fb59bb3093', '420e6f40-2d99-4fc5-93c4-2ce6fc869c85', '62f7885e-35c2-434c-afec-bb5b14428db9', 'FPO_DOCUMENT_VALIDATED', 'verification_document', '52b8c91b-f052-43b8-b976-b9a3a96d0340', '{"reason": "Document reviewed and accepted.", "validation_status": "VALID"}', '2026-09-25 13:48:13.130548+05:30');
INSERT INTO public.fpo_audit_events (audit_event_id, fpo_id, actor_user_id, action, target_type, target_id, metadata, created_at) VALUES ('0f1e2c91-8851-4d5d-b3c2-425732384719', '420e6f40-2d99-4fc5-93c4-2ce6fc869c85', '62f7885e-35c2-434c-afec-bb5b14428db9', 'FPO_VERIFICATION_REVIEWED', 'verification_submission', 'dcb93c6b-a263-4d66-9531-a1eb19b253ed', '{"note": "the documents are approved and visited", "status": "APPROVED"}', '2026-09-25 13:48:28.036267+05:30');
INSERT INTO public.fpo_audit_events (audit_event_id, fpo_id, actor_user_id, action, target_type, target_id, metadata, created_at) VALUES ('9f850ee3-66a7-455b-9353-7c35b5f3ad17', '3c96b2f5-67e9-45f8-be75-d0f1cce6265f', '62f7885e-35c2-434c-afec-bb5b14428db9', 'FPO_DOCUMENT_VALIDATED', 'verification_document', '815d8e68-8ad8-4e61-b004-17cb06709c6a', '{"reason": "Document reviewed and accepted.", "validation_status": "VALID"}', '2026-09-25 15:48:05.897489+05:30');
INSERT INTO public.fpo_audit_events (audit_event_id, fpo_id, actor_user_id, action, target_type, target_id, metadata, created_at) VALUES ('9cb0ad43-0182-4901-b821-3954d14d1e42', '3c96b2f5-67e9-45f8-be75-d0f1cce6265f', '62f7885e-35c2-434c-afec-bb5b14428db9', 'FPO_DOCUMENT_VALIDATED', 'verification_document', '971711fb-5a4d-47e3-805e-56c4477b559d', '{"reason": "Document reviewed and accepted.", "validation_status": "VALID"}', '2026-09-25 15:48:07.218305+05:30');
INSERT INTO public.fpo_audit_events (audit_event_id, fpo_id, actor_user_id, action, target_type, target_id, metadata, created_at) VALUES ('3e66bd16-6e94-4ac1-9e88-a87d8d68bc85', '3c96b2f5-67e9-45f8-be75-d0f1cce6265f', '62f7885e-35c2-434c-afec-bb5b14428db9', 'FPO_DOCUMENT_VALIDATED', 'verification_document', 'c2946ed2-8ec5-4858-bb1c-2aff40fdc6ae', '{"reason": "Document reviewed and accepted.", "validation_status": "VALID"}', '2026-09-25 15:48:08.738397+05:30');
INSERT INTO public.fpo_audit_events (audit_event_id, fpo_id, actor_user_id, action, target_type, target_id, metadata, created_at) VALUES ('2d895382-6dfb-4e19-b16b-9e88ef0e0769', '3c96b2f5-67e9-45f8-be75-d0f1cce6265f', '62f7885e-35c2-434c-afec-bb5b14428db9', 'FPO_VERIFICATION_REVIEWED', 'verification_submission', '49f45a17-773a-4c7a-b7f6-c7840c1864a7', '{"note": "request access functionality tested and proved ", "status": "APPROVED"}', '2026-09-25 15:49:37.984651+05:30');
INSERT INTO public.fpo_audit_events (audit_event_id, fpo_id, actor_user_id, action, target_type, target_id, metadata, created_at) VALUES ('f6ba6a67-ba97-41fe-8159-3234e714a4a9', '3c96b2f5-67e9-45f8-be75-d0f1cce6265f', '62f7885e-35c2-434c-afec-bb5b14428db9', 'FPO_CLASS_ASSIGNED', 'fpo_class_assignment', '7d5f83e1-81d5-40e0-b05f-a136a842e905', '{"class_code": "C", "configuration_version": 1}', '2026-09-25 15:57:36.625845+05:30');
INSERT INTO public.fpo_audit_events (audit_event_id, fpo_id, actor_user_id, action, target_type, target_id, metadata, created_at) VALUES ('dc0fe94d-8991-4404-a3f7-1f0650021bff', 'f2828e93-d068-427b-9028-437aa358006f', '19f6d134-b0c5-4ea3-ae47-296bdc06b59d', 'FPO_RELATIONSHIP_DECIDED', 'farmer_relationship', '24e8e3de-58d3-4382-9192-2d61d0212867', '{"decision": "REJECTED", "farmer_user_id": "d52292d8-8ada-465b-bc28-98a60f315a2f"}', '2026-09-27 00:15:29.472262+05:30');
INSERT INTO public.fpo_audit_events (audit_event_id, fpo_id, actor_user_id, action, target_type, target_id, metadata, created_at) VALUES ('e277498a-5b18-4481-a9ff-d3a367e5314f', '3c96b2f5-67e9-45f8-be75-d0f1cce6265f', '77fd988f-f9f3-48cb-b8bc-b7187c765f43', 'FPO_RELATIONSHIP_DECIDED', 'farmer_relationship', '2a5aa3c1-523d-4439-8fa8-64bd8ccdb85e', '{"decision": "ACTIVE", "farmer_user_id": "d52292d8-8ada-465b-bc28-98a60f315a2f"}', '2026-09-27 00:23:27.786523+05:30');
INSERT INTO public.fpo_audit_events (audit_event_id, fpo_id, actor_user_id, action, target_type, target_id, metadata, created_at) VALUES ('1969d830-6de0-43a1-b2e3-c1881c4d479c', '420e6f40-2d99-4fc5-93c4-2ce6fc869c85', '48bcc40d-6476-49b8-8981-fe5be90fd88b', 'FPO_RELATIONSHIP_DECIDED', 'farmer_relationship', 'de7850e0-d28a-47c8-a014-4968f356d586', '{"note": "", "decision": "ACTIVE", "farmer_user_id": "d52292d8-8ada-465b-bc28-98a60f315a2f"}', '2026-09-27 21:03:22.571268+05:30');


--
-- Data for Name: fpo_bulk_import_jobs; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.fpo_bulk_import_jobs (import_job_id, fpo_id, import_type, source_format, original_filename, object_key, file_checksum, template_version, mode, status, total_rows, valid_rows, invalid_rows, created_rows, updated_rows, skipped_rows, failed_rows, configuration_snapshot, requested_by, started_at, completed_at, expires_at, error_code, error_message, version, created_at, updated_at, staged_rows) VALUES ('21df3c8f-8ab5-40f4-a184-1e39d89faf7b', 'f2828e93-d068-427b-9028-437aa358006f', 'FARMERS', 'CSV', 'class-b-smoke.csv', 'fpo-imports/f2828e93-d068-427b-9028-437aa358006f/21df3c8f-8ab5-40f4-a184-1e39d89faf7b/class-b-smoke.csv', '5b813cd3ab663f3b7205bea39688d536a228cfc7293712f497602d75fa073e8b', 1, 'DRY_RUN', 'CANCELLED', 2, 1, 1, 0, 0, 0, 0, '{"allowed_formats": ["CSV", "XLSX"], "require_dry_run": true, "max_jobs_per_day": 10, "max_rows_per_job": 5000, "artifact_retention_days": 30}', '19f6d134-b0c5-4ea3-ae47-296bdc06b59d', NULL, NULL, '2026-10-23 19:27:24.348859+05:30', NULL, NULL, 1, '2026-09-23 19:27:24.348859+05:30', '2026-09-23 19:27:24.41373+05:30', 0);


--
-- Data for Name: fpo_bulk_import_rows; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.fpo_bulk_import_rows (import_row_id, import_job_id, row_number, external_reference, raw_payload, normalized_payload, row_status, error_items, farmer_id, farm_id, idempotency_key, processed_at, created_at) VALUES ('ad7796e8-4001-49a5-a186-24ad4cef2b97', '21df3c8f-8ab5-40f4-a184-1e39d89faf7b', 2, NULL, '{"phone": "9999999999", "state_name": "Odisha", "farmer_name": "Smoke Farmer", "village_name": "Test Village", "district_name": "Khordha"}', '{"phone": "9999999999", "state_name": "Odisha", "farmer_name": "Smoke Farmer", "village_name": "Test Village", "district_name": "Khordha"}', 'VALID', '[]', NULL, NULL, 'c4dc238b8f58f65fe93ba709c1fd04d5c12dfe22a244a935b27eeade70276633', NULL, '2026-09-23 19:27:24.377606+05:30');
INSERT INTO public.fpo_bulk_import_rows (import_row_id, import_job_id, row_number, external_reference, raw_payload, normalized_payload, row_status, error_items, farmer_id, farm_id, idempotency_key, processed_at, created_at) VALUES ('a9e0a2de-56ae-4689-929e-0d48c2957fe9', '21df3c8f-8ab5-40f4-a184-1e39d89faf7b', 3, NULL, '{"phone": "999", "state_name": "Odisha", "farmer_name": "=bad", "village_name": "Test", "district_name": "Khordha"}', NULL, 'INVALID', '[{"code": "FORMULA_CELL", "field": "farmer_name", "message": "Formula-like cells are not accepted"}]', NULL, NULL, '680b9d18fa0d8b0dff67fb58ebdf4bb94a0421ed1e180aa41f64424bd564e310', NULL, '2026-09-23 19:27:24.377606+05:30');


--
-- Data for Name: fpo_bulk_staged_records; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_certifications; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_class_assignments; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.fpo_class_assignments (assignment_id, fpo_id, class_code, configuration_version, assigned_by, assigned_at, expires_at, is_active) VALUES ('191059c4-19b8-424f-91ee-5353c5fe9cf9', 'f2828e93-d068-427b-9028-437aa358006f', 'A', 1, '62f7885e-35c2-434c-afec-bb5b14428db9', '2026-09-21 17:19:09.403037+05:30', NULL, false);
INSERT INTO public.fpo_class_assignments (assignment_id, fpo_id, class_code, configuration_version, assigned_by, assigned_at, expires_at, is_active) VALUES ('ff99d453-19d0-4f3d-b988-f80cb46c21e8', 'f2828e93-d068-427b-9028-437aa358006f', 'A', 2, '62f7885e-35c2-434c-afec-bb5b14428db9', '2026-09-21 17:35:25.457069+05:30', NULL, true);
INSERT INTO public.fpo_class_assignments (assignment_id, fpo_id, class_code, configuration_version, assigned_by, assigned_at, expires_at, is_active) VALUES ('5b7005ae-3d55-4785-97bd-e0d0d4a28ca1', '420e6f40-2d99-4fc5-93c4-2ce6fc869c85', 'B', 2, '62f7885e-35c2-434c-afec-bb5b14428db9', '2026-09-25 13:38:17.942142+05:30', NULL, true);
INSERT INTO public.fpo_class_assignments (assignment_id, fpo_id, class_code, configuration_version, assigned_by, assigned_at, expires_at, is_active) VALUES ('e292db6d-6087-4ebe-abbc-946adf8ad20a', '3c96b2f5-67e9-45f8-be75-d0f1cce6265f', 'A', 2, '62f7885e-35c2-434c-afec-bb5b14428db9', '2026-09-25 15:49:37.984651+05:30', NULL, false);
INSERT INTO public.fpo_class_assignments (assignment_id, fpo_id, class_code, configuration_version, assigned_by, assigned_at, expires_at, is_active) VALUES ('7d5f83e1-81d5-40e0-b05f-a136a842e905', '3c96b2f5-67e9-45f8-be75-d0f1cce6265f', 'C', 2, '62f7885e-35c2-434c-afec-bb5b14428db9', '2026-09-25 15:57:36.625845+05:30', NULL, true);


--
-- Data for Name: fpo_plan_versions; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.fpo_plan_versions (plan_version_id, class_code, version, status, name, description, effective_from, effective_until, created_by, created_at, published_by, published_at, publication_reason, release_state) VALUES ('29acae86-a902-4ec5-8f4a-0b81b80e7dff', 'A', 2, 'PUBLISHED', 'Foundation v2', 'Class A foundation plan', '2026-09-22 12:55:49.778049+05:30', NULL, NULL, '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30', 'Corrected Class A entitlement baseline', 'DRAFT');
INSERT INTO public.fpo_plan_versions (plan_version_id, class_code, version, status, name, description, effective_from, effective_until, created_by, created_at, published_by, published_at, publication_reason, release_state) VALUES ('ed40d438-f9ee-46a8-aaa9-4669f97d9068', 'B', 2, 'PUBLISHED', 'Growth v2', 'Class A plus Growth capabilities', '2026-09-22 12:55:49.778049+05:30', NULL, NULL, '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30', 'Class inheritance correction', 'DRAFT');
INSERT INTO public.fpo_plan_versions (plan_version_id, class_code, version, status, name, description, effective_from, effective_until, created_by, created_at, published_by, published_at, publication_reason, release_state) VALUES ('7a9a7d83-f27f-44db-80b9-b3844334ba6e', 'C', 2, 'PUBLISHED', 'Enterprise v2', 'Class A plus Growth and Enterprise capabilities', '2026-09-22 12:55:49.778049+05:30', NULL, NULL, '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30', 'Class inheritance correction', 'DRAFT');
INSERT INTO public.fpo_plan_versions (plan_version_id, class_code, version, status, name, description, effective_from, effective_until, created_by, created_at, published_by, published_at, publication_reason, release_state) VALUES ('1d25dc3c-0cd5-4f0a-ba94-b9ea64a87fd8', 'B', 3, 'DRAFT', 'Growth Operations v3', 'Class A inheritance plus controlled Class B operations.', NULL, NULL, NULL, '2026-09-23 19:24:22.889404+05:30', NULL, NULL, 'Class B foundation and bulk onboarding implemented; awaiting remaining Class B release gates.', 'DRAFT');
INSERT INTO public.fpo_plan_versions (plan_version_id, class_code, version, status, name, description, effective_from, effective_until, created_by, created_at, published_by, published_at, publication_reason, release_state) VALUES ('fbacea16-8460-4ea9-9e6a-ee2765ef67e9', 'C', 4, 'DRAFT', 'Commercial Enterprise v4', 'Class A and B inheritance plus governed commercial and enterprise operations.', NULL, NULL, NULL, '2026-09-25 01:05:06.397714+05:30', NULL, NULL, 'Class C implementation foundation; pending C0-C9 release gates', 'DRAFT');


--
-- Data for Name: fpo_class_b_release_checks; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.fpo_class_b_release_checks (check_id, plan_version_id, check_key, status, evidence, checked_by, checked_at) VALUES ('872c4de8-04b6-4b24-8f72-d7de4dc6efe3', '1d25dc3c-0cd5-4f0a-ba94-b9ea64a87fd8', 'CLASS_B_FEATURE_CONFIGURATION', 'PASS', '{"enabled_feature_count": 35}', '62f7885e-35c2-434c-afec-bb5b14428db9', '2026-09-25 00:40:57.759124+05:30');
INSERT INTO public.fpo_class_b_release_checks (check_id, plan_version_id, check_key, status, evidence, checked_by, checked_at) VALUES ('0b24d4bc-d431-4c9a-b39c-bf07d3d17ecb', '1d25dc3c-0cd5-4f0a-ba94-b9ea64a87fd8', 'CLASS_A_PLAN_PUBLISHED', 'PASS', '{}', '62f7885e-35c2-434c-afec-bb5b14428db9', '2026-09-25 00:40:57.759124+05:30');
INSERT INTO public.fpo_class_b_release_checks (check_id, plan_version_id, check_key, status, evidence, checked_by, checked_at) VALUES ('a150fa46-c0e9-4dd5-be81-5631902e2c9d', '1d25dc3c-0cd5-4f0a-ba94-b9ea64a87fd8', 'IMPORT_CONTRACT', 'PASS', '{}', '62f7885e-35c2-434c-afec-bb5b14428db9', '2026-09-25 00:40:57.759124+05:30');
INSERT INTO public.fpo_class_b_release_checks (check_id, plan_version_id, check_key, status, evidence, checked_by, checked_at) VALUES ('54fbbb6b-9bb3-4f55-835f-2e122a4f2875', '1d25dc3c-0cd5-4f0a-ba94-b9ea64a87fd8', 'REPORT_CONTRACT', 'PASS', '{}', '62f7885e-35c2-434c-afec-bb5b14428db9', '2026-09-25 00:40:57.759124+05:30');
INSERT INTO public.fpo_class_b_release_checks (check_id, plan_version_id, check_key, status, evidence, checked_by, checked_at) VALUES ('0e389844-6f9d-4c16-ac1e-f9369f4493e4', '1d25dc3c-0cd5-4f0a-ba94-b9ea64a87fd8', 'ADVISORY_GOVERNANCE', 'PASS', '{}', '62f7885e-35c2-434c-afec-bb5b14428db9', '2026-09-25 00:40:57.759124+05:30');


--
-- Data for Name: fpo_class_c_release_checks; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_feature_catalogue; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('BULK_FARM_REGISTRATION', 'Bulk onboarding', 'Upload farmers and farms through dry-run-first controlled imports.', 'CLASS_B', true, '2026-09-21 15:45:16.940498+05:30', '2026-09-23 20:19:56.08862+05:30', '{"type": "object", "required": ["max_rows_per_job", "require_dry_run", "allowed_formats"]}', '{FARMER_DIRECTORY,FARM_PORTFOLIO_READ}', 'HIGH', 'imports', 150);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('ADVANCED_DIRECTORY_FILTERS', 'Advanced farmer filters', 'Filter the consented farmer portfolio by operational attributes.', 'CLASS_B', true, '2026-09-23 19:24:22.889404+05:30', '2026-09-23 20:19:56.08862+05:30', '{}', '{FARMER_DIRECTORY}', 'LOW', 'farmers', 160);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('PORTFOLIO_TRENDS', 'Portfolio trends', 'View time-series portfolio trends.', 'CLASS_B', true, '2026-09-23 19:24:22.889404+05:30', '2026-09-23 20:19:56.08862+05:30', '{}', '{PORTFOLIO_OVERVIEW}', 'LOW', 'overview', 190);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('COHORT_COMPARISON', 'Cohort comparison', 'Compare governed farmer cohorts.', 'CLASS_B', true, '2026-09-23 19:24:22.889404+05:30', '2026-09-23 20:19:56.08862+05:30', '{}', '{FARMER_SEGMENTATION}', 'MEDIUM', 'analytics', 200);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('FPO_PROFILE_MANAGEMENT', 'FPO profile management', 'Manage the organization profile and verification readiness.', 'CLASS_A', true, '2026-09-22 12:55:49.778049+05:30', '2026-09-22 12:55:49.778049+05:30', '{}', '{}', 'LOW', 'profile', 10);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('FPO_PUBLIC_ID', 'Public FPO ID', 'View and share the immutable public FPO identifier.', 'CLASS_A', true, '2026-09-22 12:55:49.778049+05:30', '2026-09-22 12:55:49.778049+05:30', '{}', '{}', 'LOW', 'profile', 20);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('PORTFOLIO_OVERVIEW', 'Portfolio overview', 'View server-maintained portfolio KPIs.', 'CLASS_A', true, '2026-09-22 12:55:49.778049+05:30', '2026-09-22 12:55:49.778049+05:30', '{}', '{}', 'LOW', 'overview', 30);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('RELATIONSHIP_INBOX', 'Relationship inbox', 'Review consent-backed farmer requests.', 'CLASS_A', true, '2026-09-22 12:55:49.778049+05:30', '2026-09-22 12:55:49.778049+05:30', '{}', '{}', 'LOW', 'relationships', 40);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('FARMER_DIRECTORY', 'Farmer directory', 'View farmers with an active consented relationship.', 'CLASS_A', true, '2026-09-21 15:45:16.940498+05:30', '2026-09-21 15:45:16.940498+05:30', '{}', '{}', 'LOW', 'farmers', 50);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('FARMER_DETAIL', 'Farmer detail', 'View consented farmer profile details.', 'CLASS_A', true, '2026-09-21 15:45:16.940498+05:30', '2026-09-21 15:45:16.940498+05:30', '{}', '{}', 'LOW', 'farmers', 60);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('FARM_PORTFOLIO_READ', 'Farm portfolio', 'View farms attached to active relationships.', 'CLASS_A', true, '2026-09-22 12:55:49.778049+05:30', '2026-09-22 12:55:49.778049+05:30', '{}', '{}', 'LOW', 'farms', 70);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('FARM_MAP', 'Farm map', 'View farms belonging to active FPO relationships.', 'CLASS_A', true, '2026-09-21 15:45:16.940498+05:30', '2026-09-21 15:45:16.940498+05:30', '{}', '{}', 'LOW', 'farms', 80);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('LAND_INTELLIGENCE_BASIC', 'Basic land intelligence', 'View permitted land intelligence.', 'CLASS_A', true, '2026-09-22 12:55:49.778049+05:30', '2026-09-22 12:55:49.778049+05:30', '{}', '{}', 'LOW', 'monitoring', 90);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('CROP_PORTFOLIO_BASIC', 'Basic crop portfolio', 'View crop and season portfolio summaries.', 'CLASS_A', true, '2026-09-22 12:55:49.778049+05:30', '2026-09-22 12:55:49.778049+05:30', '{}', '{}', 'LOW', 'crops', 100);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('COVERAGE_ANALYTICS_BASIC', 'Basic coverage', 'View district and block coverage counts.', 'CLASS_A', true, '2026-09-22 12:55:49.778049+05:30', '2026-09-22 12:55:49.778049+05:30', '{}', '{}', 'LOW', 'coverage', 110);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('BASIC_ALERTS', 'Basic alerts', 'Receive operational alerts for the FPO portfolio.', 'CLASS_A', true, '2026-09-21 15:45:16.940498+05:30', '2026-09-21 15:45:16.940498+05:30', '{}', '{}', 'LOW', 'alerts', 120);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('BASIC_REPORTS', 'Basic reports', 'Generate basic portfolio reports.', 'CLASS_A', true, '2026-09-21 15:45:16.940498+05:30', '2026-09-21 15:45:16.940498+05:30', '{}', '{}', 'LOW', 'reports', 130);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('ACTIVITY_FEED', 'Activity feed', 'View recent portfolio activity.', 'CLASS_A', true, '2026-09-22 12:55:49.778049+05:30', '2026-09-22 12:55:49.778049+05:30', '{}', '{}', 'LOW', 'overview', 140);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('CROP_PORTFOLIO_ADVANCED', 'Advanced crop portfolio', 'View advanced crop portfolio summaries.', 'CLASS_B', true, '2026-09-23 19:24:22.889404+05:30', '2026-09-23 20:19:56.08862+05:30', '{}', '{CROP_PORTFOLIO_BASIC}', 'MEDIUM', 'crops', 210);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('LAND_INTELLIGENCE', 'Land intelligence', 'View delegated land and satellite intelligence.', 'CLASS_A', false, '2026-09-21 15:45:16.940498+05:30', '2026-09-22 16:04:31.691947+05:30', '{}', '{}', 'LOW', NULL, 100);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('FARMER_SEGMENTATION', 'Farmer segments', 'Create governed dynamic and static farmer segments.', 'CLASS_B', true, '2026-09-23 19:24:22.889404+05:30', '2026-09-23 21:19:10.259661+05:30', '{}', '{FARMER_DIRECTORY}', 'MEDIUM', 'segments', 170);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('FARMER_NOTES_AND_FOLLOWUPS', 'Farmer notes and follow-ups', 'Keep private operational notes and follow-ups for the FPO owner.', 'CLASS_B', true, '2026-09-23 19:24:22.889404+05:30', '2026-09-23 21:19:10.259661+05:30', '{}', '{FARMER_DETAIL}', 'HIGH', 'farmers', 180);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('PROCUREMENT_PLANNING', 'Procurement planning', 'Plan commercial procurement by season, crop, geography and segment.', 'CLASS_C', true, '2026-09-25 01:05:06.397714+05:30', '2026-09-25 01:05:08.463856+05:30', '{}', '{SEASON_PLANNING,YIELD_FORECASTS_STANDARD}', 'HIGH', 'procurement', 400);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('LAND_INTELLIGENCE_COMPARE', 'Land intelligence comparison', 'Compare delegated land intelligence observations.', 'CLASS_B', true, '2026-09-23 19:24:22.889404+05:30', '2026-09-23 20:19:56.08862+05:30', '{}', '{LAND_INTELLIGENCE_BASIC}', 'MEDIUM', 'monitoring', 230);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('PORTFOLIO_MONITORING_ADVANCED', 'Advanced monitoring', 'Operate governed portfolio monitoring queues.', 'CLASS_B', true, '2026-09-23 19:24:22.889404+05:30', '2026-09-23 20:19:56.08862+05:30', '{}', '{BASIC_ALERTS,FARM_MAP}', 'MEDIUM', 'monitoring', 240);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('ALERT_RULE_MANAGEMENT', 'Alert rule management', 'Create versioned metric-backed alert rules.', 'CLASS_B', true, '2026-09-23 19:24:22.889404+05:30', '2026-09-23 20:19:56.08862+05:30', '{}', '{PORTFOLIO_MONITORING_ADVANCED}', 'HIGH', 'monitoring', 250);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('PRODUCE_AGGREGATION_LOTS', 'Produce aggregation lots', 'Receive approved farmer contributions into traceable lots.', 'CLASS_C', true, '2026-09-25 01:05:06.397714+05:30', '2026-09-25 01:05:08.463856+05:30', '{}', '{PROCUREMENT_PLANNING}', 'HIGH', 'lots', 410);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('ADVISORY_WORKBENCH', 'Advisory workbench', 'Compose approved agronomy advisories.', 'CLASS_B', true, '2026-09-23 19:24:22.889404+05:30', '2026-09-23 20:19:56.08862+05:30', '{}', '{CROP_PORTFOLIO_ADVANCED}', 'HIGH', 'advisories', 270);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('COMMUNICATION_BROADCAST', 'Farmer communication campaigns', 'Plan consent-aware farmer campaigns.', 'CLASS_B', true, '2026-09-23 19:24:22.889404+05:30', '2026-09-23 20:19:56.08862+05:30', '{}', '{ADVISORY_WORKBENCH}', 'HIGH', 'advisories', 280);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('NUTRIENT_PLANNING', 'Nutrient planning', 'Use approved nutrient recommendations.', 'CLASS_B', true, '2026-09-23 19:24:22.889404+05:30', '2026-09-23 20:19:56.08862+05:30', '{}', '{ADVISORY_WORKBENCH}', 'HIGH', 'advisories', 290);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('CROP_PROTECTION_MONITORING', 'Crop protection planning', 'Use approved crop-protection recommendations.', 'CLASS_B', true, '2026-09-23 19:24:22.889404+05:30', '2026-09-23 20:19:56.08862+05:30', '{}', '{ADVISORY_WORKBENCH}', 'HIGH', 'advisories', 300);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('INPUT_REQUIREMENT_PLANNING', 'Input demand planning', 'Aggregate governed season input requirements.', 'CLASS_B', true, '2026-09-23 19:24:22.889404+05:30', '2026-09-23 20:19:56.08862+05:30', '{}', '{SEASON_PLANNING}', 'MEDIUM', 'inputs', 310);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('YIELD_FORECASTS_STANDARD', 'Standard yield forecasts', 'View versioned standard yield forecasts.', 'CLASS_B', true, '2026-09-23 19:24:22.889404+05:30', '2026-09-23 20:19:56.08862+05:30', '{}', '{CROP_PORTFOLIO_ADVANCED}', 'MEDIUM', 'forecasts', 320);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('ADVANCED_REPORTS', 'Advanced reports', 'Generate governed operational reports.', 'CLASS_B', true, '2026-09-23 19:24:22.889404+05:30', '2026-09-23 20:19:56.08862+05:30', '{}', '{BASIC_REPORTS}', 'MEDIUM', 'reports', 330);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('DATA_EXPORT', 'Data export', 'Export governed FPO data asynchronously.', 'CLASS_B', true, '2026-09-23 19:24:22.889404+05:30', '2026-09-23 20:19:56.08862+05:30', '{}', '{ADVANCED_REPORTS}', 'HIGH', 'reports', 340);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('DATA_QUALITY_WORKBENCH', 'Data quality workbench', 'Review and resolve portfolio data-quality issues.', 'CLASS_B', true, '2026-09-23 19:24:22.889404+05:30', '2026-09-23 20:19:56.08862+05:30', '{}', '{PORTFOLIO_OVERVIEW}', 'MEDIUM', 'data-quality', 350);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('QUALITY_GRADING', 'Quality and grading', 'Inspect and grade aggregated produce with governed schemas.', 'CLASS_C', true, '2026-09-25 01:05:06.397714+05:30', '2026-09-25 01:05:08.463856+05:30', '{}', '{PRODUCE_AGGREGATION_LOTS}', 'HIGH', 'quality', 420);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('END_TO_END_TRACEABILITY', 'End-to-end traceability', 'Maintain internal lot lineage and minimized traceability views.', 'CLASS_C', true, '2026-09-25 01:05:06.397714+05:30', '2026-09-25 01:05:08.463856+05:30', '{}', '{PRODUCE_AGGREGATION_LOTS,QUALITY_GRADING}', 'HIGH', 'traceability', 430);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('SEASON_PLANNING', 'Season planning', 'Plan season crop targets without mutating farmer crop cycles.', 'CLASS_B', true, '2026-09-23 19:24:22.889404+05:30', '2026-09-23 21:19:10.259661+05:30', '{}', '{CROP_PORTFOLIO_ADVANCED}', 'MEDIUM', 'seasons', 220);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('FIELD_ACTIVITY_PLANNING', 'Tasks and field follow-ups', 'Plan and track FPO owner field work.', 'CLASS_B', true, '2026-09-23 19:24:22.889404+05:30', '2026-09-23 21:19:10.259661+05:30', '{}', '{FARMER_DETAIL}', 'MEDIUM', 'tasks', 260);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('WAREHOUSE_INVENTORY', 'Warehouse and inventory', 'Operate warehouses and append-only inventory ledgers.', 'CLASS_C', true, '2026-09-25 01:05:06.397714+05:30', '2026-09-25 01:05:08.463856+05:30', '{}', '{PRODUCE_AGGREGATION_LOTS}', 'HIGH', 'inventory', 440);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('BUYER_EXPORTER_CRM', 'Buyers and exporters', 'Manage governed counterparty records and due diligence.', 'CLASS_C', true, '2026-09-25 01:05:06.397714+05:30', '2026-09-25 01:05:08.463856+05:30', '{}', '{FPO_PROFILE_MANAGEMENT}', 'HIGH', 'counterparties', 450);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('MARKET_OPPORTUNITIES', 'Market opportunities', 'Manage qualified commercial opportunity pipelines.', 'CLASS_C', true, '2026-09-25 01:05:06.397714+05:30', '2026-09-25 01:05:08.463856+05:30', '{}', '{BUYER_EXPORTER_CRM}', 'MEDIUM', 'opportunities', 460);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('CONTRACT_AND_ORDER_MANAGEMENT', 'Contracts and orders', 'Track commercial contracts, orders and fulfillment.', 'CLASS_C', true, '2026-09-25 01:05:06.397714+05:30', '2026-09-25 01:05:08.463856+05:30', '{}', '{MARKET_OPPORTUNITIES}', 'HIGH', 'orders', 470);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('LOGISTICS_COORDINATION', 'Logistics and dispatch', 'Coordinate compatible-stock allocations and dispatches.', 'CLASS_C', true, '2026-09-25 01:05:06.397714+05:30', '2026-09-25 01:05:08.463856+05:30', '{}', '{WAREHOUSE_INVENTORY,CONTRACT_AND_ORDER_MANAGEMENT}', 'HIGH', 'logistics', 480);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('PRICE_INTELLIGENCE', 'Price intelligence', 'View source-aware price observations with freshness.', 'CLASS_C', true, '2026-09-25 01:05:06.397714+05:30', '2026-09-25 01:05:08.463856+05:30', '{}', '{CROP_PORTFOLIO_ADVANCED}', 'MEDIUM', 'prices', 490);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('YIELD_FORECASTING_ADVANCED', 'Advanced production forecasting', 'Use provenance-aware advanced yield and surplus forecasts.', 'CLASS_C', true, '2026-09-25 01:05:06.397714+05:30', '2026-09-25 01:05:08.463856+05:30', '{}', '{YIELD_FORECASTS_STANDARD}', 'MEDIUM', 'forecasts', 500);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('COMPLIANCE_AND_CERTIFICATIONS', 'Compliance and certifications', 'Track compliance requirements, certificates and expiry.', 'CLASS_C', true, '2026-09-25 01:05:06.397714+05:30', '2026-09-25 01:05:08.463856+05:30', '{}', '{FPO_PROFILE_MANAGEMENT}', 'HIGH', 'compliance', 510);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('EXPORT_DOCUMENT_PACKS', 'Export document packs', 'Generate governed export-ready document packs.', 'CLASS_C', true, '2026-09-25 01:05:06.397714+05:30', '2026-09-25 01:05:08.463856+05:30', '{}', '{COMPLIANCE_AND_CERTIFICATIONS,CONTRACT_AND_ORDER_MANAGEMENT}', 'HIGH', 'exports', 520);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('FINANCE_INSURANCE_DATA_PACKS', 'Finance and insurance data packs', 'Generate consent-bound minimized finance or insurance data packs.', 'CLASS_C', true, '2026-09-25 01:05:06.397714+05:30', '2026-09-25 01:05:08.463856+05:30', '{}', '{ADVANCED_REPORTS}', 'CRITICAL', 'data-packs', 530);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('SUSTAINABILITY_ANALYTICS', 'Sustainability and impact', 'Calculate coverage-aware sustainability indicators.', 'CLASS_C', true, '2026-09-25 01:05:06.397714+05:30', '2026-09-25 01:05:08.463856+05:30', '{}', '{PORTFOLIO_TRENDS}', 'MEDIUM', 'sustainability', 540);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('CUSTOM_DASHBOARDS', 'Custom dashboards', 'Configure governed commercial dashboards.', 'CLASS_C', true, '2026-09-25 01:05:06.397714+05:30', '2026-09-25 01:05:08.463856+05:30', '{}', '{ADVANCED_REPORTS}', 'MEDIUM', 'dashboards', 550);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('SCHEDULED_REPORTS', 'Scheduled reports', 'Schedule governed commercial reports.', 'CLASS_C', true, '2026-09-25 01:05:06.397714+05:30', '2026-09-25 01:05:08.463856+05:30', '{}', '{ADVANCED_REPORTS,DATA_EXPORT}', 'HIGH', 'reports', 560);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('ENTERPRISE_API_ACCESS', 'Enterprise API access', 'Expose approved scoped integrations through the gateway.', 'CLASS_C', true, '2026-09-25 01:05:06.397714+05:30', '2026-09-25 01:05:08.463856+05:30', '{}', '{END_TO_END_TRACEABILITY}', 'CRITICAL', 'integrations', 570);
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, is_active, created_at, updated_at, configuration_schema, dependencies, risk_level, navigation_key, sort_order) VALUES ('OUTBOUND_WEBHOOKS', 'Outbound webhooks', 'Deliver approved domain events to governed destinations.', 'CLASS_C', true, '2026-09-25 01:05:06.397714+05:30', '2026-09-25 01:05:08.463856+05:30', '{}', '{ENTERPRISE_API_ACCESS}', 'CRITICAL', 'integrations', 580);


--
-- Data for Name: fpo_class_feature_versions; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('4fc3d710-57fc-4921-be9e-de3110124116', 'A', 1, 'FARMER_DIRECTORY', true, '{}', '2026-09-21 15:45:16.940498+05:30', NULL, '2026-09-21 15:45:16.940498+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('c126b20e-73b5-4b31-8ec5-0ffe5ee22965', 'A', 1, 'FARMER_DETAIL', true, '{}', '2026-09-21 15:45:16.940498+05:30', NULL, '2026-09-21 15:45:16.940498+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('d1e9d317-efc2-41ca-8dd5-6da4f6cc3929', 'A', 1, 'FARM_MAP', true, '{}', '2026-09-21 15:45:16.940498+05:30', NULL, '2026-09-21 15:45:16.940498+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('9dfa33c3-6eb3-4f26-aa69-6247ea2d5637', 'A', 1, 'LAND_INTELLIGENCE', true, '{}', '2026-09-21 15:45:16.940498+05:30', NULL, '2026-09-21 15:45:16.940498+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('e53f015d-f9ed-45a8-ac05-ab7bc86522a3', 'A', 1, 'BASIC_ALERTS', true, '{}', '2026-09-21 15:45:16.940498+05:30', NULL, '2026-09-21 15:45:16.940498+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('504f4fce-9579-44ec-805c-b7eceea6f623', 'A', 1, 'BASIC_REPORTS', true, '{}', '2026-09-21 15:45:16.940498+05:30', NULL, '2026-09-21 15:45:16.940498+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('386b05e2-0a90-4c3b-a333-14f5fc0ca6a7', 'A', 1, 'BULK_FARM_REGISTRATION', true, '{}', '2026-09-21 15:45:16.940498+05:30', NULL, '2026-09-21 15:45:16.940498+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('70b6b7ef-7d3f-4c78-a831-53b87f5d896c', 'B', 1, 'FARMER_DIRECTORY', false, '{}', '2026-09-21 15:45:16.940498+05:30', NULL, '2026-09-21 15:45:16.940498+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('8539e496-3315-41dd-9399-19751020d3c3', 'C', 1, 'FARMER_DIRECTORY', false, '{}', '2026-09-21 15:45:16.940498+05:30', NULL, '2026-09-21 15:45:16.940498+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('76010cc6-c6d6-4edb-adfe-c960e7a35779', 'B', 1, 'FARMER_DETAIL', false, '{}', '2026-09-21 15:45:16.940498+05:30', NULL, '2026-09-21 15:45:16.940498+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('cf7a1378-bc5e-4d25-9ca6-84ec7493f8da', 'C', 1, 'FARMER_DETAIL', false, '{}', '2026-09-21 15:45:16.940498+05:30', NULL, '2026-09-21 15:45:16.940498+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('719d0027-50e7-4e9f-982f-2c3e7b154d2a', 'B', 1, 'FARM_MAP', false, '{}', '2026-09-21 15:45:16.940498+05:30', NULL, '2026-09-21 15:45:16.940498+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('fa007607-cb5d-4ce8-86fe-89e4017e05ef', 'C', 1, 'FARM_MAP', false, '{}', '2026-09-21 15:45:16.940498+05:30', NULL, '2026-09-21 15:45:16.940498+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('d5ad77e2-0aeb-476b-9c70-fb4d3eb5e240', 'B', 1, 'LAND_INTELLIGENCE', false, '{}', '2026-09-21 15:45:16.940498+05:30', NULL, '2026-09-21 15:45:16.940498+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('82998cef-f10b-4fa2-9e3d-034352b7ca1a', 'C', 1, 'LAND_INTELLIGENCE', false, '{}', '2026-09-21 15:45:16.940498+05:30', NULL, '2026-09-21 15:45:16.940498+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('9b7df6b7-089c-4ee3-9757-91e2b4b6f155', 'B', 1, 'BASIC_ALERTS', false, '{}', '2026-09-21 15:45:16.940498+05:30', NULL, '2026-09-21 15:45:16.940498+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('d804e9dd-58e2-405c-8c4c-0eb3c59d5570', 'C', 1, 'BASIC_ALERTS', false, '{}', '2026-09-21 15:45:16.940498+05:30', NULL, '2026-09-21 15:45:16.940498+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('b3173e64-b2c4-407c-8a44-51d870e2ef7a', 'B', 1, 'BASIC_REPORTS', false, '{}', '2026-09-21 15:45:16.940498+05:30', NULL, '2026-09-21 15:45:16.940498+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('cbba78ee-7319-4392-9f90-54eae2f4bb0a', 'C', 1, 'BASIC_REPORTS', false, '{}', '2026-09-21 15:45:16.940498+05:30', NULL, '2026-09-21 15:45:16.940498+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('293fa8a5-5b72-40d7-ab15-ec9e471c35c2', 'B', 1, 'BULK_FARM_REGISTRATION', false, '{}', '2026-09-21 15:45:16.940498+05:30', NULL, '2026-09-21 15:45:16.940498+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('f8c86351-7eab-4f26-bfa4-40928ef43b5d', 'C', 1, 'BULK_FARM_REGISTRATION', false, '{}', '2026-09-21 15:45:16.940498+05:30', NULL, '2026-09-21 15:45:16.940498+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('8cf2bdcf-53c6-4570-bd5c-6a8862f39695', 'A', 2, 'LAND_INTELLIGENCE', true, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('786fc5b3-fe56-45a7-b67c-28b487e3aa42', 'B', 2, 'LAND_INTELLIGENCE', true, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('840157ce-5a9e-4069-9664-1bf8486daa3e', 'C', 2, 'LAND_INTELLIGENCE', true, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('8cf3fcff-698d-4c50-afa5-492c22a6b280', 'A', 2, 'FPO_PROFILE_MANAGEMENT', true, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('5327d5eb-a2db-4b15-858c-bcd2b337e182', 'B', 2, 'FPO_PROFILE_MANAGEMENT', true, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('883bb5e7-1c6b-4e9f-97d4-fd07839168d9', 'C', 2, 'FPO_PROFILE_MANAGEMENT', true, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('811eec6f-2885-4a71-a317-9000a3d08b7d', 'A', 2, 'FPO_PUBLIC_ID', true, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('ec8616aa-2ecc-4f41-8e5f-b5518fda38ba', 'B', 2, 'FPO_PUBLIC_ID', true, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('09d9b547-4da6-4a13-b34f-291a85c8a530', 'C', 2, 'FPO_PUBLIC_ID', true, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('f08a0c5e-8420-4658-971c-e1ee866ded85', 'A', 2, 'PORTFOLIO_OVERVIEW', true, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('1e5272c2-3b5b-4f3f-a4d8-f874cf00aff8', 'B', 2, 'PORTFOLIO_OVERVIEW', true, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('db8b95c7-7665-43da-a021-42687138e6b3', 'C', 2, 'PORTFOLIO_OVERVIEW', true, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('73aed8e0-e3e8-446b-869c-7755e82f9a20', 'A', 2, 'RELATIONSHIP_INBOX', true, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('27d3fcd9-b653-4070-8f33-1c3a59c5fa38', 'B', 2, 'RELATIONSHIP_INBOX', true, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('b4840d80-bce2-4b43-a2a7-0022159334c1', 'C', 2, 'RELATIONSHIP_INBOX', true, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('b133f7be-ad23-41b3-9c8a-c23b809e7d40', 'A', 2, 'FARMER_DIRECTORY', true, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('28619a0c-ded2-4bed-b5d4-092c0be41799', 'B', 2, 'FARMER_DIRECTORY', true, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('df8a3562-eacc-4089-acf1-712bd1fa1ed1', 'C', 2, 'FARMER_DIRECTORY', true, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('1e112ff5-c7bb-4475-8121-537c8b1b3ee1', 'A', 2, 'FARMER_DETAIL', true, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('5471f0fa-6968-49e6-9ffc-b65c8a9cebd4', 'B', 2, 'FARMER_DETAIL', true, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('6201db71-3df4-4cc9-83c2-bd71b77b3557', 'C', 2, 'FARMER_DETAIL', true, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('31ecd541-686d-4e11-8901-441e264b1157', 'A', 2, 'FARM_PORTFOLIO_READ', true, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('8c0b5846-23d1-48bd-a0f7-e3d0a78acdbe', 'B', 2, 'FARM_PORTFOLIO_READ', true, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('83006224-1698-4997-8b04-ed2ae5c81ab6', 'C', 2, 'FARM_PORTFOLIO_READ', true, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('2e0463dc-2ed3-4e7d-8d31-50ffff9c63b2', 'A', 2, 'FARM_MAP', true, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('9e1ea21c-a218-492e-ae3f-6e63e18dc428', 'B', 2, 'FARM_MAP', true, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('0204e207-23d0-49a4-9bd6-3943c38151c6', 'C', 2, 'FARM_MAP', true, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('7fe8d195-0d84-4ae8-81a1-c7db996fed58', 'A', 2, 'LAND_INTELLIGENCE_BASIC', true, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('cfb04ac1-699b-4b3c-a568-5295275812fe', 'B', 2, 'LAND_INTELLIGENCE_BASIC', true, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('fb591a0e-d571-425c-99de-05a0d7a0ea94', 'C', 2, 'LAND_INTELLIGENCE_BASIC', true, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('c3b3e115-55dd-4d2e-9656-c1138b1fc18e', 'A', 2, 'CROP_PORTFOLIO_BASIC', true, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('601d8314-fd40-4659-a94c-eb7887c31870', 'B', 2, 'CROP_PORTFOLIO_BASIC', true, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('18ea3145-7068-4656-a571-f6836d8163b8', 'C', 2, 'CROP_PORTFOLIO_BASIC', true, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('e70c3d96-5fe7-4dee-bf5e-5ba06fbc01c1', 'A', 2, 'COVERAGE_ANALYTICS_BASIC', true, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('bd3de535-6eac-44c3-8818-0a19458d41f8', 'B', 2, 'COVERAGE_ANALYTICS_BASIC', true, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('428f8136-2cf5-4049-8e26-705637276dc2', 'C', 2, 'COVERAGE_ANALYTICS_BASIC', true, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('c558e013-6526-4481-80c2-6a818e9dfcb1', 'A', 2, 'BASIC_ALERTS', true, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('2c77818e-0be2-4bd2-a603-17850613db03', 'B', 2, 'BASIC_ALERTS', true, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('39df5ad4-ef5e-486f-86f3-4e6f3620f358', 'C', 2, 'BASIC_ALERTS', true, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('2c5f0a94-6a3f-4a22-a609-3e0b6a9ff5cb', 'A', 2, 'BASIC_REPORTS', true, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('14716666-5b99-4c24-b15f-2fba45a7ca65', 'B', 2, 'BASIC_REPORTS', true, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('36ce1844-9f67-4e57-a6d8-3c4d11d60db4', 'C', 2, 'BASIC_REPORTS', true, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('f8d70d3f-a7e8-47f9-9b5d-18101482a2b2', 'A', 2, 'ACTIVITY_FEED', true, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('334fdc8f-3604-482d-9971-8eccbf3cf035', 'B', 2, 'ACTIVITY_FEED', true, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('16c5d794-d3c5-472f-b995-3ff3487c06bc', 'C', 2, 'ACTIVITY_FEED', true, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('55b5d8f1-dbd5-4909-a29e-7fa4c6c2af2a', 'B', 3, 'FPO_PROFILE_MANAGEMENT', true, '{}', '2026-09-23 19:24:22.889404+05:30', NULL, '2026-09-23 19:24:22.889404+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('b6e7b6a0-4242-45ee-9679-670a12f6d698', 'B', 3, 'FPO_PUBLIC_ID', true, '{}', '2026-09-23 19:24:22.889404+05:30', NULL, '2026-09-23 19:24:22.889404+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('c521b620-6136-4306-b02e-60f03abf0d02', 'B', 3, 'PORTFOLIO_OVERVIEW', true, '{}', '2026-09-23 19:24:22.889404+05:30', NULL, '2026-09-23 19:24:22.889404+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('04bb1f45-bf66-4e48-a598-b2d72c23cf7d', 'A', 2, 'BULK_FARM_REGISTRATION', false, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('c9f082a5-28e3-4fbd-9017-0ac21f183997', 'B', 2, 'BULK_FARM_REGISTRATION', true, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('914e0483-930d-48fe-82be-ecded43ba4ba', 'C', 2, 'BULK_FARM_REGISTRATION', true, '{}', '2026-09-22 12:55:49.778049+05:30', NULL, '2026-09-22 12:55:49.778049+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('53e86cf5-2761-4902-a648-84c4cd6dc799', 'B', 3, 'RELATIONSHIP_INBOX', true, '{}', '2026-09-23 19:24:22.889404+05:30', NULL, '2026-09-23 19:24:22.889404+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('269c1be7-7e42-49a5-8f29-9215f2eb794f', 'B', 3, 'FARMER_DIRECTORY', true, '{}', '2026-09-23 19:24:22.889404+05:30', NULL, '2026-09-23 19:24:22.889404+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('e2c2839e-e172-4cce-9f3b-e785878c6e49', 'B', 3, 'FARMER_DETAIL', true, '{}', '2026-09-23 19:24:22.889404+05:30', NULL, '2026-09-23 19:24:22.889404+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('e54c3da9-93b5-48a4-8190-3c18ed39100b', 'B', 3, 'FARM_PORTFOLIO_READ', true, '{}', '2026-09-23 19:24:22.889404+05:30', NULL, '2026-09-23 19:24:22.889404+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('5de5de35-7583-4e3d-8aeb-87c327a2d9ec', 'B', 3, 'FARM_MAP', true, '{}', '2026-09-23 19:24:22.889404+05:30', NULL, '2026-09-23 19:24:22.889404+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('34058c6e-a51e-4ae8-b209-11b70d3cecf8', 'B', 3, 'LAND_INTELLIGENCE_BASIC', true, '{}', '2026-09-23 19:24:22.889404+05:30', NULL, '2026-09-23 19:24:22.889404+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('cf475c49-6a93-411f-ad04-b297256022fa', 'B', 3, 'CROP_PORTFOLIO_BASIC', true, '{}', '2026-09-23 19:24:22.889404+05:30', NULL, '2026-09-23 19:24:22.889404+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('ca9b258c-9210-48b7-ba08-fcb688659403', 'B', 3, 'COVERAGE_ANALYTICS_BASIC', true, '{}', '2026-09-23 19:24:22.889404+05:30', NULL, '2026-09-23 19:24:22.889404+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('e7fe13e1-7975-45d1-b508-1cd06d2baa74', 'B', 3, 'BASIC_ALERTS', true, '{}', '2026-09-23 19:24:22.889404+05:30', NULL, '2026-09-23 19:24:22.889404+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('91a7d9f0-659f-446a-a449-2967bdada3f3', 'B', 3, 'BASIC_REPORTS', true, '{}', '2026-09-23 19:24:22.889404+05:30', NULL, '2026-09-23 19:24:22.889404+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('d298c421-b046-46e8-85f8-402c85b71cfd', 'B', 3, 'ACTIVITY_FEED', true, '{}', '2026-09-23 19:24:22.889404+05:30', NULL, '2026-09-23 19:24:22.889404+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('2fa96223-64bc-4993-91a8-1d51877ffc9f', 'B', 3, 'BULK_FARM_REGISTRATION', true, '{"allowed_formats": ["CSV", "XLSX"], "require_dry_run": true, "max_jobs_per_day": 10, "max_rows_per_job": 5000, "artifact_retention_days": 30}', '2026-09-23 19:24:22.889404+05:30', NULL, '2026-09-23 19:24:22.889404+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('7a31c352-339b-4fec-a3ca-c1f12b44ec4a', 'B', 3, 'ADVANCED_DIRECTORY_FILTERS', true, '{}', '2026-09-23 19:24:22.889404+05:30', NULL, '2026-09-23 19:24:22.889404+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('3d19dadc-c5d5-466f-900c-723e01ce0187', 'B', 3, 'FARMER_SEGMENTATION', true, '{}', '2026-09-23 19:24:22.889404+05:30', NULL, '2026-09-23 19:24:22.889404+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('64274661-417f-4efc-b251-19ce85c381b0', 'B', 3, 'FARMER_NOTES_AND_FOLLOWUPS', true, '{}', '2026-09-23 19:24:22.889404+05:30', NULL, '2026-09-23 19:24:22.889404+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('b2074b29-c0d6-4f12-86c5-a3f726a0d161', 'B', 3, 'PORTFOLIO_TRENDS', true, '{}', '2026-09-23 19:24:22.889404+05:30', NULL, '2026-09-23 19:24:22.889404+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('ee842238-8627-41b0-adb4-0bb07fa54c3f', 'B', 3, 'COHORT_COMPARISON', true, '{}', '2026-09-23 19:24:22.889404+05:30', NULL, '2026-09-23 19:24:22.889404+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('bcc97a71-f33d-4f07-849c-be05a0cf982c', 'B', 3, 'CROP_PORTFOLIO_ADVANCED', true, '{}', '2026-09-23 19:24:22.889404+05:30', NULL, '2026-09-23 19:24:22.889404+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('6b3fd033-1ae8-406d-a716-5d7281b6457d', 'B', 3, 'SEASON_PLANNING', true, '{}', '2026-09-23 19:24:22.889404+05:30', NULL, '2026-09-23 19:24:22.889404+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('ed2e205e-bef6-4336-a793-aa14ccf31ac4', 'B', 3, 'LAND_INTELLIGENCE_COMPARE', true, '{}', '2026-09-23 19:24:22.889404+05:30', NULL, '2026-09-23 19:24:22.889404+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('76d20ea5-0f9b-4e99-8e0a-1d72066eb71d', 'B', 3, 'PORTFOLIO_MONITORING_ADVANCED', true, '{}', '2026-09-23 19:24:22.889404+05:30', NULL, '2026-09-23 19:24:22.889404+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('3b76dcae-bb72-463c-9f47-6de538b98ca2', 'B', 3, 'ALERT_RULE_MANAGEMENT', true, '{}', '2026-09-23 19:24:22.889404+05:30', NULL, '2026-09-23 19:24:22.889404+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('4634730c-5312-44ab-8872-90807bee869e', 'B', 3, 'FIELD_ACTIVITY_PLANNING', true, '{}', '2026-09-23 19:24:22.889404+05:30', NULL, '2026-09-23 19:24:22.889404+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('076452bf-341b-4047-bce1-4164cfe26227', 'B', 3, 'ADVISORY_WORKBENCH', true, '{}', '2026-09-23 19:24:22.889404+05:30', NULL, '2026-09-23 19:24:22.889404+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('68e1700e-1c83-46ff-ae83-ef50408abb16', 'B', 3, 'COMMUNICATION_BROADCAST', true, '{}', '2026-09-23 19:24:22.889404+05:30', NULL, '2026-09-23 19:24:22.889404+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('e7a30447-b843-47c7-826c-b857de2dddf7', 'B', 3, 'NUTRIENT_PLANNING', true, '{}', '2026-09-23 19:24:22.889404+05:30', NULL, '2026-09-23 19:24:22.889404+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('55ec2d42-c5a5-4f64-ba3d-06c758cb8320', 'B', 3, 'CROP_PROTECTION_MONITORING', true, '{}', '2026-09-23 19:24:22.889404+05:30', NULL, '2026-09-23 19:24:22.889404+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('3e132295-b605-43e2-a678-1d2d488078f8', 'B', 3, 'INPUT_REQUIREMENT_PLANNING', true, '{}', '2026-09-23 19:24:22.889404+05:30', NULL, '2026-09-23 19:24:22.889404+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('1f92e365-c8ac-4abe-885b-07a9324a2564', 'B', 3, 'YIELD_FORECASTS_STANDARD', true, '{}', '2026-09-23 19:24:22.889404+05:30', NULL, '2026-09-23 19:24:22.889404+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('7ce35c7f-8019-4c2d-8804-bb313d3755da', 'B', 3, 'ADVANCED_REPORTS', true, '{}', '2026-09-23 19:24:22.889404+05:30', NULL, '2026-09-23 19:24:22.889404+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('c9cd580f-9acd-49a3-ba6b-3329a7cbe0a0', 'B', 3, 'DATA_EXPORT', true, '{}', '2026-09-23 19:24:22.889404+05:30', NULL, '2026-09-23 19:24:22.889404+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('797055dc-ecf5-4364-a674-6b206b757e35', 'B', 3, 'DATA_QUALITY_WORKBENCH', true, '{}', '2026-09-23 19:24:22.889404+05:30', NULL, '2026-09-23 19:24:22.889404+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('0a0ee16f-2a7c-40e7-a6b5-1772c65fd067', 'C', 4, 'BULK_FARM_REGISTRATION', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('9c01cd39-c7c2-4ffe-aa01-5cc3bdf1a96c', 'C', 4, 'ADVANCED_DIRECTORY_FILTERS', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('5843bee9-0d45-418b-b685-324f94700e75', 'C', 4, 'PORTFOLIO_TRENDS', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('7861a72e-5e74-4121-b6e4-8b1143cf1b64', 'C', 4, 'COHORT_COMPARISON', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('9b33d499-ae1c-4088-872f-fd4ad01fc5cc', 'C', 4, 'FPO_PROFILE_MANAGEMENT', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('d0dd709f-1854-452f-b9b7-bc92242328be', 'C', 4, 'FPO_PUBLIC_ID', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('021ea07b-974d-4317-b46d-05c1b08cd191', 'C', 4, 'PORTFOLIO_OVERVIEW', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('1947bb2a-86bf-4057-bd18-87f0bf0f9ce8', 'C', 4, 'RELATIONSHIP_INBOX', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('14fab0c7-38ab-4625-8967-0b40b4d8779b', 'C', 4, 'FARMER_DIRECTORY', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('6e0a6436-0cca-4df3-a042-c2334b3b3fc3', 'C', 4, 'FARMER_DETAIL', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('25530824-c63f-40a0-8820-9c7cd25b5bff', 'C', 4, 'FARM_PORTFOLIO_READ', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('9ba982b7-6959-4e77-a3ce-9486a63e1eca', 'C', 4, 'FARM_MAP', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('8f392175-96f1-47c7-871b-548f02fd6559', 'C', 4, 'LAND_INTELLIGENCE_BASIC', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('5faaf6fc-4c5c-44aa-b6ea-f0797f3570bf', 'C', 4, 'CROP_PORTFOLIO_BASIC', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('912c39a6-ac9d-4f52-b487-a67484294722', 'C', 4, 'COVERAGE_ANALYTICS_BASIC', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('0ba7a650-be40-4b8e-a023-0cab3a524d51', 'C', 4, 'BASIC_ALERTS', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('88978541-8a30-4036-8cdf-2096b677f596', 'C', 4, 'BASIC_REPORTS', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('219a4d33-5a8e-44f7-bd8d-b80c0782723f', 'C', 4, 'ACTIVITY_FEED', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('94391fd8-90e3-4509-b195-48fb61c0a18d', 'C', 4, 'CROP_PORTFOLIO_ADVANCED', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('5b6548f5-cdb5-450a-898e-cde210a6fa5f', 'C', 4, 'FARMER_SEGMENTATION', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('e89805d7-9a57-45c4-9101-eebc8ffe1d1d', 'C', 4, 'FARMER_NOTES_AND_FOLLOWUPS', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('93503114-b3c7-423b-bf3d-64a14a3777a0', 'C', 4, 'LAND_INTELLIGENCE_COMPARE', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('25f6a536-a346-4bbc-b11f-b8f13cfb82ab', 'C', 4, 'PORTFOLIO_MONITORING_ADVANCED', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('cf791007-5886-48e4-bdbe-57e0f1ada385', 'C', 4, 'ALERT_RULE_MANAGEMENT', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('fe4ffa8e-3677-46db-ba33-000c944a35c8', 'C', 4, 'ADVISORY_WORKBENCH', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('4979e6d7-d5df-4c3b-b609-022752c18355', 'C', 4, 'COMMUNICATION_BROADCAST', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('ddb8b225-4f43-4cc2-bc2c-2067db2d04cf', 'C', 4, 'NUTRIENT_PLANNING', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('ca17582b-e11b-4f72-a0c3-63412904484a', 'C', 4, 'CROP_PROTECTION_MONITORING', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('c0e9b3ab-ed38-4392-b190-5575ad3cff3f', 'C', 4, 'INPUT_REQUIREMENT_PLANNING', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('55ac116a-5e39-4576-8b2f-4da3431a8b0b', 'C', 4, 'YIELD_FORECASTS_STANDARD', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('e691b8e8-2105-4be0-a59f-e0a31e46b048', 'C', 4, 'ADVANCED_REPORTS', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('7649ee61-df34-440a-86b7-5594ab273089', 'C', 4, 'DATA_EXPORT', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('2ba2011b-8b28-4b6e-bb35-9f4c3ced00c7', 'C', 4, 'DATA_QUALITY_WORKBENCH', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('b46cf8b6-c61b-4a87-881e-6b45ddd41ad1', 'C', 4, 'SEASON_PLANNING', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('aadf5aa2-c649-4aee-b96f-e1c07f55054f', 'C', 4, 'FIELD_ACTIVITY_PLANNING', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('ce298add-e207-4112-b622-1644a1db3923', 'C', 4, 'PROCUREMENT_PLANNING', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('a59ac235-c3cc-4449-9e46-8d0e09b740e7', 'C', 4, 'PRODUCE_AGGREGATION_LOTS', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('5c237bee-83f1-4e6b-953a-b25478bc14ca', 'C', 4, 'QUALITY_GRADING', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('6f7b3a8c-9766-4dd5-8505-7dce7a7a539c', 'C', 4, 'END_TO_END_TRACEABILITY', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('44277d92-9d60-4321-94c5-52822cbc3b32', 'C', 4, 'WAREHOUSE_INVENTORY', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('aff9cc42-ff72-43ad-be3e-a3fa54cd3d2f', 'C', 4, 'BUYER_EXPORTER_CRM', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('76110c2c-d45b-4bc8-8e39-1b259964f3c6', 'C', 4, 'MARKET_OPPORTUNITIES', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('11d99a4a-1a53-41a4-acae-09f92890784c', 'C', 4, 'CONTRACT_AND_ORDER_MANAGEMENT', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('117c1d13-4c68-4b43-9812-acb5c16ee528', 'C', 4, 'LOGISTICS_COORDINATION', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('92e5c0e8-ea58-4a82-b262-b1a6dbfd3ca2', 'C', 4, 'PRICE_INTELLIGENCE', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('9a8d8a76-c568-4210-86b5-0c37e1590bf2', 'C', 4, 'YIELD_FORECASTING_ADVANCED', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('4571c470-ad49-40c6-ad64-26aa25ca5be9', 'C', 4, 'COMPLIANCE_AND_CERTIFICATIONS', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('ff34e33a-a84b-4e44-8714-ab6c2fe59bd5', 'C', 4, 'EXPORT_DOCUMENT_PACKS', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('568979de-7bb2-4400-954b-5d253560cfc9', 'C', 4, 'FINANCE_INSURANCE_DATA_PACKS', true, '{"enabled": false, "require_destination_grant": true}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('2f42255f-c018-4358-94f1-c17ac8dab33d', 'C', 4, 'SUSTAINABILITY_ANALYTICS', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('4cdcd8dd-cc39-4fe3-89cf-f105765de486', 'C', 4, 'CUSTOM_DASHBOARDS', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('b3011aff-00f9-4541-968c-ebe32eb17fc8', 'C', 4, 'SCHEDULED_REPORTS', true, '{}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('f1014445-90df-4f9c-aee1-8379d2aae387', 'C', 4, 'ENTERPRISE_API_ACCESS', true, '{"enabled": false, "emergency_disable": true, "default_rate_limit_per_minute": 60}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');
INSERT INTO public.fpo_class_feature_versions (class_feature_version_id, class_code, version, feature_key, enabled, configuration, published_at, created_by, created_at) VALUES ('390a60b5-d74e-4349-90e1-6a91eac6e47d', 'C', 4, 'OUTBOUND_WEBHOOKS', true, '{"enabled": false, "emergency_disable": true}', NULL, NULL, '2026-09-25 01:05:06.397714+05:30');


--
-- Data for Name: fpo_commercial_audit_events; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_counterparties; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_market_opportunities; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_quality_grading_schemas; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_commercial_contracts; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_compliance_documents; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_compliance_requirements; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_consent_policies; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.fpo_consent_policies (policy_id, policy_code, version, status, language_code, title, content, content_hash, mandatory_scopes, optional_scopes, effective_from, effective_until, created_by, created_at) VALUES ('71792de9-3339-4a21-a57b-57bdb4bd4cd0', 'FPO_DATA_SHARING', '2', 'PUBLISHED', 'en', 'FPO portfolio data sharing consent', 'I consent to the selected FPO accessing my permitted farmer, farm, crop, observation and land-intelligence information for the stated purpose. I can revoke this consent at any time.', 'b5a544d3fa01f1bfaf4b36c5da97f91a6462b71b8d1b6be11c36cacc868fa268', '{PROFILE_READ,CONTACT_MASKED_READ,FARM_READ,CROP_READ,OBSERVATION_READ,LAND_INTELLIGENCE_READ}', '{ADVISORY_MESSAGE,CONTACT_DIRECT_READ,COMMERCIAL_PARTICIPATION}', '2026-09-22 16:04:31.691947+05:30', NULL, NULL, '2026-09-22 16:04:31.691947+05:30');


--
-- Data for Name: fpo_consent_scope_catalogue; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.fpo_consent_scope_catalogue (scope_code, display_name, description, is_mandatory, is_active, created_at) VALUES ('PROFILE_READ', 'Farmer profile', 'Read the consented farmer profile.', true, true, '2026-09-22 16:04:31.691947+05:30');
INSERT INTO public.fpo_consent_scope_catalogue (scope_code, display_name, description, is_mandatory, is_active, created_at) VALUES ('CONTACT_MASKED_READ', 'Masked contact', 'Read a masked phone number.', true, true, '2026-09-22 16:04:31.691947+05:30');
INSERT INTO public.fpo_consent_scope_catalogue (scope_code, display_name, description, is_mandatory, is_active, created_at) VALUES ('FARM_READ', 'Farm records', 'Read farms owned by the farmer.', true, true, '2026-09-22 16:04:31.691947+05:30');
INSERT INTO public.fpo_consent_scope_catalogue (scope_code, display_name, description, is_mandatory, is_active, created_at) VALUES ('CROP_READ', 'Crop portfolio', 'Read crop and crop-cycle information.', true, true, '2026-09-22 16:04:31.691947+05:30');
INSERT INTO public.fpo_consent_scope_catalogue (scope_code, display_name, description, is_mandatory, is_active, created_at) VALUES ('OBSERVATION_READ', 'Observations', 'Read consented crop observations.', true, true, '2026-09-22 16:04:31.691947+05:30');
INSERT INTO public.fpo_consent_scope_catalogue (scope_code, display_name, description, is_mandatory, is_active, created_at) VALUES ('LAND_INTELLIGENCE_READ', 'Land intelligence', 'Read delegated land intelligence.', true, true, '2026-09-22 16:04:31.691947+05:30');
INSERT INTO public.fpo_consent_scope_catalogue (scope_code, display_name, description, is_mandatory, is_active, created_at) VALUES ('ADVISORY_MESSAGE', 'Advisory messages', 'Send approved advisory messages.', false, true, '2026-09-22 16:04:31.691947+05:30');
INSERT INTO public.fpo_consent_scope_catalogue (scope_code, display_name, description, is_mandatory, is_active, created_at) VALUES ('CONTACT_DIRECT_READ', 'Direct contact', 'Read direct contact details.', false, true, '2026-09-22 16:04:31.691947+05:30');
INSERT INTO public.fpo_consent_scope_catalogue (scope_code, display_name, description, is_mandatory, is_active, created_at) VALUES ('COMMERCIAL_PARTICIPATION', 'Commercial participation', 'Use data for commercial workflows.', false, true, '2026-09-22 16:04:31.691947+05:30');


--
-- Data for Name: fpo_counterparty_contacts; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_data_pack_schemas; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_data_pack_requests; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_data_quality_issues; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_data_sharing_grants; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_orders; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_warehouses; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_dispatches; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_inventory_lots; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_order_lines; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_dispatch_items; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_event_inbox; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.fpo_event_inbox (inbox_id, consumer_name, event_id, event_type, event_version, subject_id, payload_hash, status, attempts, available_at, locked_at, processed_at, last_error, created_at, updated_at) VALUES ('13c10c1f-11fe-47bf-8b96-8c2ee99f0274', 'fpo_management_service', 'a6b5ba42-c7af-4083-8254-8a28fd5e9a76', 'auth.user.created', 1, '48bcc40d-6476-49b8-8981-fe5be90fd88b', '1db4dc81fc6038fc3494d51cf99c47ed18ebfc7164857160983c903ae9236064', 'PROCESSED', 1, '2026-09-25 12:22:55.45348+05:30', NULL, '2026-09-25 12:22:55.45348+05:30', NULL, '2026-09-25 12:22:55.45348+05:30', '2026-09-25 12:22:55.45348+05:30');
INSERT INTO public.fpo_event_inbox (inbox_id, consumer_name, event_id, event_type, event_version, subject_id, payload_hash, status, attempts, available_at, locked_at, processed_at, last_error, created_at, updated_at) VALUES ('db58423a-f09a-4a12-8abc-da83b0484b8d', 'fpo_management_service', '866893b7-eeb7-46df-a186-ed515829b631', 'auth.user.created', 1, '77fd988f-f9f3-48cb-b8bc-b7187c765f43', '4c874f09e5cdbe8768c36113b5062ebf9c3ea0e7bd949fb94ac864c80564e556', 'PROCESSED', 1, '2026-09-25 15:15:23.812573+05:30', NULL, '2026-09-25 15:15:23.812573+05:30', NULL, '2026-09-25 15:15:23.812573+05:30', '2026-09-25 15:15:23.812573+05:30');


--
-- Data for Name: fpo_export_packs; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_farmer_notes; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_farmer_portfolio; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.fpo_farmer_portfolio (fpo_id, farmer_id, farmer_name, phone_masked, district_code, district_name, block_code, block_name, village_name, farm_count, area_acres, active_crop_codes, condition_status, highest_alert_severity, open_alert_count, latest_observation_at, latest_analysis_date, relationship_status, updated_at) VALUES ('420e6f40-2d99-4fc5-93c4-2ce6fc869c85', '8a8f1f13-a42b-4ff5-a3e5-08ac1603c1b3', 'Ram Kumar', '*********7977', 362, 'Khordha', 3463, 'Jatni', 'badaraghunathpur', 1, 4.1472, '{kala_jeera}', 'UNKNOWN', NULL, 0, NULL, NULL, 'ACTIVE', '2026-09-27 21:03:58.434704+05:30');


--
-- Data for Name: fpo_farmer_relationship_events; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.fpo_farmer_relationship_events (relationship_event_id, relationship_id, event_type, actor_user_id, metadata, created_at) VALUES ('d24e7ec5-aa44-4cff-b188-a48d11927a2e', '2bef9eac-2715-4953-962e-1411e2291ec4', 'REQUESTED', 'd52292d8-8ada-465b-bc28-98a60f315a2f', '{}', '2026-09-22 16:16:21.22231+05:30');
INSERT INTO public.fpo_farmer_relationship_events (relationship_event_id, relationship_id, event_type, actor_user_id, metadata, created_at) VALUES ('d7f5a883-5fec-4886-8368-f48657068162', '2bef9eac-2715-4953-962e-1411e2291ec4', 'CONSENT_RECORDED', 'd52292d8-8ada-465b-bc28-98a60f315a2f', '{}', '2026-09-22 16:16:21.22231+05:30');
INSERT INTO public.fpo_farmer_relationship_events (relationship_event_id, relationship_id, event_type, actor_user_id, metadata, created_at) VALUES ('ce8688de-dfab-4d5c-840a-ad45032fb36a', '2bef9eac-2715-4953-962e-1411e2291ec4', 'ACCEPTED', '19f6d134-b0c5-4ea3-ae47-296bdc06b59d', '{}', '2026-09-22 16:16:21.708581+05:30');
INSERT INTO public.fpo_farmer_relationship_events (relationship_event_id, relationship_id, event_type, actor_user_id, metadata, created_at) VALUES ('7f33f309-41f3-431e-a898-63e1f030775b', '24e8e3de-58d3-4382-9192-2d61d0212867', 'REQUESTED', 'd52292d8-8ada-465b-bc28-98a60f315a2f', '{}', '2026-09-26 23:47:32.160865+05:30');
INSERT INTO public.fpo_farmer_relationship_events (relationship_event_id, relationship_id, event_type, actor_user_id, metadata, created_at) VALUES ('6dbf8823-2a78-4e23-a509-dd2839a335bd', '24e8e3de-58d3-4382-9192-2d61d0212867', 'CONSENT_RECORDED', 'd52292d8-8ada-465b-bc28-98a60f315a2f', '{}', '2026-09-26 23:47:32.160865+05:30');
INSERT INTO public.fpo_farmer_relationship_events (relationship_event_id, relationship_id, event_type, actor_user_id, metadata, created_at) VALUES ('205208e8-0447-4093-b89b-9ad92fd43dc0', '24e8e3de-58d3-4382-9192-2d61d0212867', 'REJECTED', '19f6d134-b0c5-4ea3-ae47-296bdc06b59d', '{}', '2026-09-27 00:15:29.472262+05:30');
INSERT INTO public.fpo_farmer_relationship_events (relationship_event_id, relationship_id, event_type, actor_user_id, metadata, created_at) VALUES ('9b1f0cb3-29a1-4d3c-91b6-a9cdaabce63f', '2a5aa3c1-523d-4439-8fa8-64bd8ccdb85e', 'REQUESTED', 'd52292d8-8ada-465b-bc28-98a60f315a2f', '{}', '2026-09-27 00:19:55.925973+05:30');
INSERT INTO public.fpo_farmer_relationship_events (relationship_event_id, relationship_id, event_type, actor_user_id, metadata, created_at) VALUES ('953de330-7bde-4b9d-b4b5-5c816c026730', '2a5aa3c1-523d-4439-8fa8-64bd8ccdb85e', 'CONSENT_RECORDED', 'd52292d8-8ada-465b-bc28-98a60f315a2f', '{}', '2026-09-27 00:19:55.925973+05:30');
INSERT INTO public.fpo_farmer_relationship_events (relationship_event_id, relationship_id, event_type, actor_user_id, metadata, created_at) VALUES ('2ea04bc2-0455-498b-9bf5-0fe7c4f670f0', '2a5aa3c1-523d-4439-8fa8-64bd8ccdb85e', 'ACCEPTED', '77fd988f-f9f3-48cb-b8bc-b7187c765f43', '{}', '2026-09-27 00:23:27.786523+05:30');
INSERT INTO public.fpo_farmer_relationship_events (relationship_event_id, relationship_id, event_type, actor_user_id, metadata, created_at) VALUES ('27768db7-720a-4391-9e4b-27515945cf11', 'de7850e0-d28a-47c8-a014-4968f356d586', 'REQUESTED', 'd52292d8-8ada-465b-bc28-98a60f315a2f', '{}', '2026-09-27 21:00:30.289805+05:30');
INSERT INTO public.fpo_farmer_relationship_events (relationship_event_id, relationship_id, event_type, actor_user_id, metadata, created_at) VALUES ('bb56e67c-a1fc-4188-9fd1-2766414fa734', 'de7850e0-d28a-47c8-a014-4968f356d586', 'CONSENT_RECORDED', 'd52292d8-8ada-465b-bc28-98a60f315a2f', '{}', '2026-09-27 21:00:30.289805+05:30');
INSERT INTO public.fpo_farmer_relationship_events (relationship_event_id, relationship_id, event_type, actor_user_id, metadata, created_at) VALUES ('33866789-ad71-447a-b70a-c87f22d9b066', 'de7850e0-d28a-47c8-a014-4968f356d586', 'ACCEPTED', '48bcc40d-6476-49b8-8981-fe5be90fd88b', '{"note": ""}', '2026-09-27 21:03:22.571268+05:30');


--
-- Data for Name: fpo_farmer_segment_members; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_farmer_tags; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_farmer_tag_assignments; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_feature_overrides; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_field_tasks; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_field_task_events; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_season_plans; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_input_demand_plans; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_input_demand_items; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_inventory_ledger; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_inventory_reconciliation_runs; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_inventory_reservations; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_lot_events; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_lot_sources; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_operational_alerts; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_organization_status_events; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_portfolio_summary; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.fpo_portfolio_summary (fpo_id, active_farmer_count, pending_farmer_count, active_farm_count, registered_area_acres, active_crop_count, district_count, block_count, village_count, open_alert_count, attention_farm_count, critical_farm_count, data_through, calculation_version, updated_at) VALUES ('f2828e93-d068-427b-9028-437aa358006f', 0, 0, 0, 0.0000, 0, 0, 0, 0, 0, 0, 0, '2026-09-27 13:02:55.599352+05:30', 'fpo-portfolio-v1', '2026-09-27 13:02:55.599352+05:30');
INSERT INTO public.fpo_portfolio_summary (fpo_id, active_farmer_count, pending_farmer_count, active_farm_count, registered_area_acres, active_crop_count, district_count, block_count, village_count, open_alert_count, attention_farm_count, critical_farm_count, data_through, calculation_version, updated_at) VALUES ('420e6f40-2d99-4fc5-93c4-2ce6fc869c85', 1, 0, 1, 4.1472, 1, 1, 1, 1, 0, 0, 0, '2026-09-27 21:03:58.434704+05:30', 'fpo-portfolio-v1', '2026-09-27 21:03:58.434704+05:30');


--
-- Data for Name: fpo_procurement_plan_items; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_profile_commodities; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_profile_service_areas; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_profile_services; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_projection_refresh_queue; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_quality_inspections; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_quality_test_results; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_reconciliation_runs; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.fpo_reconciliation_runs (run_id, started_by, status, repaired_farmer_projections, cleared_stale_projections, orphaned_organizations, completed_at, error_message, created_at) VALUES ('3f283863-23ce-4cb1-ad42-9abb890f64f4', '62f7885e-35c2-434c-afec-bb5b14428db9', 'COMPLETED', 0, 0, 0, '2026-09-22 16:16:22.176156+05:30', NULL, '2026-09-22 16:16:22.176156+05:30');
INSERT INTO public.fpo_reconciliation_runs (run_id, started_by, status, repaired_farmer_projections, cleared_stale_projections, orphaned_organizations, completed_at, error_message, created_at) VALUES ('336abb2f-1dcb-40a5-9b3e-170fc1caf827', '62f7885e-35c2-434c-afec-bb5b14428db9', 'COMPLETED', 0, 0, 0, '2026-09-22 16:17:27.787758+05:30', NULL, '2026-09-22 16:17:27.787758+05:30');


--
-- Data for Name: fpo_report_jobs; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_report_artifacts; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_required_document_policies; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.fpo_required_document_policies (registration_type, document_type, is_required, created_at) VALUES ('DEFAULT', 'REGISTRATION_CERTIFICATE', true, '2026-09-22 16:04:31.691947+05:30');
INSERT INTO public.fpo_required_document_policies (registration_type, document_type, is_required, created_at) VALUES ('DEFAULT', 'AUTHORIZED_REPRESENTATIVE_DECLARATION', true, '2026-09-22 16:04:31.691947+05:30');
INSERT INTO public.fpo_required_document_policies (registration_type, document_type, is_required, created_at) VALUES ('DEFAULT', 'ADDRESS_PROOF', true, '2026-09-22 16:04:31.691947+05:30');


--
-- Data for Name: fpo_season_crop_targets; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_sensitive_access_events; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.fpo_sensitive_access_events (access_event_id, fpo_id, actor_user_id, farmer_id, farm_id, operation, scopes, correlation_id, created_at) VALUES ('ff5594b0-1c5a-4b0f-b6c5-15e1cfa19e75', 'f2828e93-d068-427b-9028-437aa358006f', '19f6d134-b0c5-4ea3-ae47-296bdc06b59d', '8a8f1f13-a42b-4ff5-a3e5-08ac1603c1b3', NULL, 'FARM_LIST_READ', '{PROFILE_READ,CONTACT_MASKED_READ,FARM_READ,CROP_READ,OBSERVATION_READ,LAND_INTELLIGENCE_READ}', NULL, '2026-09-22 16:23:24.539195+05:30');
INSERT INTO public.fpo_sensitive_access_events (access_event_id, fpo_id, actor_user_id, farmer_id, farm_id, operation, scopes, correlation_id, created_at) VALUES ('0bcc5864-9e55-4efb-8566-32710527689c', 'f2828e93-d068-427b-9028-437aa358006f', '19f6d134-b0c5-4ea3-ae47-296bdc06b59d', '8a8f1f13-a42b-4ff5-a3e5-08ac1603c1b3', NULL, 'FARM_INTELLIGENCE_READ', '{PROFILE_READ,CONTACT_MASKED_READ,FARM_READ,CROP_READ,OBSERVATION_READ,LAND_INTELLIGENCE_READ}', NULL, '2026-09-22 16:23:24.78095+05:30');
INSERT INTO public.fpo_sensitive_access_events (access_event_id, fpo_id, actor_user_id, farmer_id, farm_id, operation, scopes, correlation_id, created_at) VALUES ('e0847a5c-08be-45b3-96e2-00c5ce7c3219', 'f2828e93-d068-427b-9028-437aa358006f', '19f6d134-b0c5-4ea3-ae47-296bdc06b59d', '8a8f1f13-a42b-4ff5-a3e5-08ac1603c1b3', NULL, 'FARM_LIST_READ', '{PROFILE_READ,CONTACT_MASKED_READ,FARM_READ,CROP_READ,OBSERVATION_READ,LAND_INTELLIGENCE_READ}', NULL, '2026-09-22 16:24:34.465777+05:30');
INSERT INTO public.fpo_sensitive_access_events (access_event_id, fpo_id, actor_user_id, farmer_id, farm_id, operation, scopes, correlation_id, created_at) VALUES ('b7078e7c-8648-449c-b292-5e6ba9f89b19', 'f2828e93-d068-427b-9028-437aa358006f', '19f6d134-b0c5-4ea3-ae47-296bdc06b59d', '8a8f1f13-a42b-4ff5-a3e5-08ac1603c1b3', NULL, 'FARM_INTELLIGENCE_READ', '{PROFILE_READ,CONTACT_MASKED_READ,FARM_READ,CROP_READ,OBSERVATION_READ,LAND_INTELLIGENCE_READ}', NULL, '2026-09-22 16:24:34.691912+05:30');
INSERT INTO public.fpo_sensitive_access_events (access_event_id, fpo_id, actor_user_id, farmer_id, farm_id, operation, scopes, correlation_id, created_at) VALUES ('5b9e3a20-bdfa-4a90-8cb7-813cc216469d', 'f2828e93-d068-427b-9028-437aa358006f', '19f6d134-b0c5-4ea3-ae47-296bdc06b59d', '8a8f1f13-a42b-4ff5-a3e5-08ac1603c1b3', NULL, 'FARM_LIST_READ', '{PROFILE_READ,CONTACT_MASKED_READ,FARM_READ,CROP_READ,OBSERVATION_READ,LAND_INTELLIGENCE_READ}', NULL, '2026-09-23 19:31:17.324921+05:30');
INSERT INTO public.fpo_sensitive_access_events (access_event_id, fpo_id, actor_user_id, farmer_id, farm_id, operation, scopes, correlation_id, created_at) VALUES ('0ebcc28f-6a3c-4010-8921-e90d2c79a1ab', 'f2828e93-d068-427b-9028-437aa358006f', '19f6d134-b0c5-4ea3-ae47-296bdc06b59d', '8a8f1f13-a42b-4ff5-a3e5-08ac1603c1b3', NULL, 'FARM_INTELLIGENCE_READ', '{PROFILE_READ,CONTACT_MASKED_READ,FARM_READ,CROP_READ,OBSERVATION_READ,LAND_INTELLIGENCE_READ}', NULL, '2026-09-23 19:31:17.671755+05:30');
INSERT INTO public.fpo_sensitive_access_events (access_event_id, fpo_id, actor_user_id, farmer_id, farm_id, operation, scopes, correlation_id, created_at) VALUES ('1406a612-3249-4986-9618-9a99f547ed40', 'f2828e93-d068-427b-9028-437aa358006f', '19f6d134-b0c5-4ea3-ae47-296bdc06b59d', '8a8f1f13-a42b-4ff5-a3e5-08ac1603c1b3', NULL, 'FARMER_DETAIL_READ', '{PROFILE_READ,CONTACT_MASKED_READ,FARM_READ,CROP_READ,OBSERVATION_READ,LAND_INTELLIGENCE_READ}', NULL, '2026-09-25 12:07:06.797047+05:30');
INSERT INTO public.fpo_sensitive_access_events (access_event_id, fpo_id, actor_user_id, farmer_id, farm_id, operation, scopes, correlation_id, created_at) VALUES ('1bf95d5f-4a0e-4a6d-9da5-a3e3f1c9d6ab', 'f2828e93-d068-427b-9028-437aa358006f', '19f6d134-b0c5-4ea3-ae47-296bdc06b59d', '8a8f1f13-a42b-4ff5-a3e5-08ac1603c1b3', NULL, 'FARM_LIST_READ', '{PROFILE_READ,CONTACT_MASKED_READ,FARM_READ,CROP_READ,OBSERVATION_READ,LAND_INTELLIGENCE_READ}', NULL, '2026-09-25 12:07:07.060087+05:30');
INSERT INTO public.fpo_sensitive_access_events (access_event_id, fpo_id, actor_user_id, farmer_id, farm_id, operation, scopes, correlation_id, created_at) VALUES ('4d5f66cb-3a34-4de2-b9d3-5ea95ea1f4fd', 'f2828e93-d068-427b-9028-437aa358006f', '19f6d134-b0c5-4ea3-ae47-296bdc06b59d', '8a8f1f13-a42b-4ff5-a3e5-08ac1603c1b3', NULL, 'FARM_INTELLIGENCE_READ', '{PROFILE_READ,CONTACT_MASKED_READ,FARM_READ,CROP_READ,OBSERVATION_READ,LAND_INTELLIGENCE_READ}', NULL, '2026-09-25 12:07:27.359887+05:30');
INSERT INTO public.fpo_sensitive_access_events (access_event_id, fpo_id, actor_user_id, farmer_id, farm_id, operation, scopes, correlation_id, created_at) VALUES ('1562e97a-2fac-4a2f-b390-c21645f35dcd', 'f2828e93-d068-427b-9028-437aa358006f', '19f6d134-b0c5-4ea3-ae47-296bdc06b59d', '8a8f1f13-a42b-4ff5-a3e5-08ac1603c1b3', NULL, 'FARMER_DETAIL_READ', '{PROFILE_READ,CONTACT_MASKED_READ,FARM_READ,CROP_READ,OBSERVATION_READ,LAND_INTELLIGENCE_READ}', NULL, '2026-09-27 00:02:23.626153+05:30');
INSERT INTO public.fpo_sensitive_access_events (access_event_id, fpo_id, actor_user_id, farmer_id, farm_id, operation, scopes, correlation_id, created_at) VALUES ('303caa53-efe3-44b9-84aa-fadaea8b3031', '420e6f40-2d99-4fc5-93c4-2ce6fc869c85', '48bcc40d-6476-49b8-8981-fe5be90fd88b', '8a8f1f13-a42b-4ff5-a3e5-08ac1603c1b3', NULL, 'FARM_INTELLIGENCE_READ', '{PROFILE_READ,CONTACT_MASKED_READ,FARM_READ,CROP_READ,OBSERVATION_READ,LAND_INTELLIGENCE_READ,ADVISORY_MESSAGE,CONTACT_DIRECT_READ,COMMERCIAL_PARTICIPATION}', NULL, '2026-09-27 21:03:36.268872+05:30');
INSERT INTO public.fpo_sensitive_access_events (access_event_id, fpo_id, actor_user_id, farmer_id, farm_id, operation, scopes, correlation_id, created_at) VALUES ('867e66f6-ea12-4006-8b13-905d440b5a0b', '420e6f40-2d99-4fc5-93c4-2ce6fc869c85', '48bcc40d-6476-49b8-8981-fe5be90fd88b', '8a8f1f13-a42b-4ff5-a3e5-08ac1603c1b3', NULL, 'FARMER_DETAIL_READ', '{PROFILE_READ,CONTACT_MASKED_READ,FARM_READ,CROP_READ,OBSERVATION_READ,LAND_INTELLIGENCE_READ,ADVISORY_MESSAGE,CONTACT_DIRECT_READ,COMMERCIAL_PARTICIPATION}', NULL, '2026-09-27 21:04:07.900674+05:30');
INSERT INTO public.fpo_sensitive_access_events (access_event_id, fpo_id, actor_user_id, farmer_id, farm_id, operation, scopes, correlation_id, created_at) VALUES ('22152716-5262-4041-8f12-bc88b9e2a28f', '420e6f40-2d99-4fc5-93c4-2ce6fc869c85', '48bcc40d-6476-49b8-8981-fe5be90fd88b', '8a8f1f13-a42b-4ff5-a3e5-08ac1603c1b3', NULL, 'FARM_LIST_READ', '{PROFILE_READ,CONTACT_MASKED_READ,FARM_READ,CROP_READ,OBSERVATION_READ,LAND_INTELLIGENCE_READ,ADVISORY_MESSAGE,CONTACT_DIRECT_READ,COMMERCIAL_PARTICIPATION}', NULL, '2026-09-27 21:04:08.174012+05:30');
INSERT INTO public.fpo_sensitive_access_events (access_event_id, fpo_id, actor_user_id, farmer_id, farm_id, operation, scopes, correlation_id, created_at) VALUES ('410a88d4-e06c-497e-8d38-be33b3a6ebad', '420e6f40-2d99-4fc5-93c4-2ce6fc869c85', '48bcc40d-6476-49b8-8981-fe5be90fd88b', '8a8f1f13-a42b-4ff5-a3e5-08ac1603c1b3', NULL, 'FARM_INTELLIGENCE_READ', '{PROFILE_READ,CONTACT_MASKED_READ,FARM_READ,CROP_READ,OBSERVATION_READ,LAND_INTELLIGENCE_READ,ADVISORY_MESSAGE,CONTACT_DIRECT_READ,COMMERCIAL_PARTICIPATION}', NULL, '2026-09-27 21:04:28.052169+05:30');


--
-- Data for Name: fpo_support_tickets; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_sustainability_methodologies; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_sustainability_metrics; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_traceability_views; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_users; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.fpo_users (fpo_user_id, fpo_id, user_id, fpo_role, is_active, created_at, role, updated_at) VALUES ('efe736c3-8409-4f14-99db-8bee67a7475d', 'd13cdfbe-857c-4d46-b3fe-c53329a6c95e', 'ba6d8474-48f8-454e-a04c-f5bd4231f6fa', 'owner', true, '2026-09-16 11:35:10.141254+05:30', 'owner', '2026-09-21 13:16:40.595675+05:30');
INSERT INTO public.fpo_users (fpo_user_id, fpo_id, user_id, fpo_role, is_active, created_at, role, updated_at) VALUES ('6c7e4e39-0096-497d-91a9-4e44d8259619', 'eec41b5a-d542-44fd-92a9-c3870578c125', '19f6d134-b0c5-4ea3-ae47-296bdc06b59d', 'owner', true, '2026-09-21 13:02:33.51896+05:30', 'owner', '2026-09-21 13:16:40.595675+05:30');
INSERT INTO public.fpo_users (fpo_user_id, fpo_id, user_id, fpo_role, is_active, created_at, role, updated_at) VALUES ('1ef3f185-deb1-4103-a40b-fdf4b3f84e19', '318efbab-4c24-47f7-9060-22bf91bad3a0', '48bcc40d-6476-49b8-8981-fe5be90fd88b', 'owner', true, '2026-09-25 12:22:55.45348+05:30', 'owner', '2026-09-25 12:22:55.45348+05:30');
INSERT INTO public.fpo_users (fpo_user_id, fpo_id, user_id, fpo_role, is_active, created_at, role, updated_at) VALUES ('4ff7fad3-4fb9-48a6-9add-3f8dba49e775', '273f8c1d-ccd3-46fc-82ea-89908bc63930', '77fd988f-f9f3-48cb-b8bc-b7187c765f43', 'owner', true, '2026-09-25 15:15:23.812573+05:30', 'owner', '2026-09-25 15:15:23.812573+05:30');


--
-- Data for Name: fpo_verification_submissions; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.fpo_verification_submissions (submission_id, fpo_id, submitted_by, status, profile_snapshot, reviewer_user_id, reviewer_note, reviewed_at, created_at, updated_at) VALUES ('060db737-192e-4490-976a-9b3c676a05de', 'f2828e93-d068-427b-9028-437aa358006f', '19f6d134-b0c5-4ea3-ae47-296bdc06b59d', 'APPROVED', '{"fpo_name": "FPO Satyabadi Puri", "state_name": "Odisha", "member_count": null, "contact_email": "soumikbasu2003@gmail.com", "contact_phone": "+918093669088", "district_code": 334, "district_name": "Pending", "main_commodities": [], "registration_type": "cooperative_society", "services_provided": [], "contact_person_name": "SOUMIK FARMER", "registration_number": "1111111111"}', '62f7885e-35c2-434c-afec-bb5b14428db9', '', '2026-09-21 17:35:33.618091+05:30', '2026-09-21 17:30:40.177028+05:30', '2026-09-21 17:35:33.618091+05:30');
INSERT INTO public.fpo_verification_submissions (submission_id, fpo_id, submitted_by, status, profile_snapshot, reviewer_user_id, reviewer_note, reviewed_at, created_at, updated_at) VALUES ('dcb93c6b-a263-4d66-9531-a1eb19b253ed', '420e6f40-2d99-4fc5-93c4-2ce6fc869c85', '48bcc40d-6476-49b8-8981-fe5be90fd88b', 'APPROVED', '{"fpo_name": "Jayadeva FPO Khordha", "state_name": "Odisha", "member_count": null, "contact_email": "taniya3002@gmail.com", "contact_phone": "+916203771750", "district_code": 362, "district_name": "Khordha", "main_commodities": [], "registration_type": "cooperative_society", "services_provided": [], "contact_person_name": "Taniya Ghosh", "registration_number": "4444444444"}', '62f7885e-35c2-434c-afec-bb5b14428db9', 'the documents are approved and visited', '2026-09-25 13:48:28.036267+05:30', '2026-09-25 13:21:51.86015+05:30', '2026-09-25 13:48:28.036267+05:30');
INSERT INTO public.fpo_verification_submissions (submission_id, fpo_id, submitted_by, status, profile_snapshot, reviewer_user_id, reviewer_note, reviewed_at, created_at, updated_at) VALUES ('49f45a17-773a-4c7a-b7f6-c7840c1864a7', '3c96b2f5-67e9-45f8-be75-d0f1cce6265f', '77fd988f-f9f3-48cb-b8bc-b7187c765f43', 'APPROVED', '{"fpo_name": "Rani Sukadei FPO Cuttack", "state_name": "Odisha", "member_count": null, "contact_email": "nehapati5357182@gmail.com", "contact_phone": "+916372440443", "district_code": 350, "district_name": "Cuttack", "main_commodities": [], "registration_type": "other", "services_provided": [], "contact_person_name": "Amir Faishal", "registration_number": "333333333333"}', '62f7885e-35c2-434c-afec-bb5b14428db9', 'request access functionality tested and proved ', '2026-09-25 15:49:37.984651+05:30', '2026-09-25 15:46:08.838625+05:30', '2026-09-25 15:49:37.984651+05:30');


--
-- Data for Name: fpo_verification_cases; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.fpo_verification_cases (case_id, fpo_id, submission_id, status, priority, assigned_reviewer_id, checklist_policy_version, sla_due_at, created_at, updated_at) VALUES ('1c77e63a-8f6f-4928-8e3f-e34a2e691b16', '420e6f40-2d99-4fc5-93c4-2ce6fc869c85', 'dcb93c6b-a263-4d66-9531-a1eb19b253ed', 'APPROVED', 'NORMAL', '62f7885e-35c2-434c-afec-bb5b14428db9', 'class-a-v1', NULL, '2026-09-25 13:21:51.86015+05:30', '2026-09-25 13:48:28.036267+05:30');
INSERT INTO public.fpo_verification_cases (case_id, fpo_id, submission_id, status, priority, assigned_reviewer_id, checklist_policy_version, sla_due_at, created_at, updated_at) VALUES ('8ee1b47c-783b-4a4b-b70d-1d7eb770a9b2', '3c96b2f5-67e9-45f8-be75-d0f1cce6265f', '49f45a17-773a-4c7a-b7f6-c7840c1864a7', 'APPROVED', 'NORMAL', '62f7885e-35c2-434c-afec-bb5b14428db9', 'class-a-v1', NULL, '2026-09-25 15:46:08.838625+05:30', '2026-09-25 15:49:37.984651+05:30');


--
-- Data for Name: fpo_verification_case_events; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_verification_checklist_results; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.fpo_verification_checklist_results (checklist_result_id, case_id, checklist_key, result, note, checked_by, checked_at) VALUES ('ab4fa747-f89d-4b84-9e6f-81951df8fdb2', '1c77e63a-8f6f-4928-8e3f-e34a2e691b16', 'CONTACT', 'PASS', 'Reviewed in FPO management: PASS', '62f7885e-35c2-434c-afec-bb5b14428db9', '2026-09-25 13:30:44.360648+05:30');
INSERT INTO public.fpo_verification_checklist_results (checklist_result_id, case_id, checklist_key, result, note, checked_by, checked_at) VALUES ('7f40677f-d41c-44f6-a3e9-877d744f9780', '1c77e63a-8f6f-4928-8e3f-e34a2e691b16', 'GEOGRAPHY', 'PASS', 'Reviewed in FPO management: PASS', '62f7885e-35c2-434c-afec-bb5b14428db9', '2026-09-25 13:30:45.233851+05:30');
INSERT INTO public.fpo_verification_checklist_results (checklist_result_id, case_id, checklist_key, result, note, checked_by, checked_at) VALUES ('5212bcab-c6b0-4c59-9476-87ad83c1081e', '1c77e63a-8f6f-4928-8e3f-e34a2e691b16', 'IDENTITY', 'PASS', 'Reviewed in FPO management: PASS', '62f7885e-35c2-434c-afec-bb5b14428db9', '2026-09-25 13:30:46.746229+05:30');
INSERT INTO public.fpo_verification_checklist_results (checklist_result_id, case_id, checklist_key, result, note, checked_by, checked_at) VALUES ('22c092cc-5f5a-43c0-8d11-3693d4be6b95', '1c77e63a-8f6f-4928-8e3f-e34a2e691b16', 'OPERATIONS', 'PASS', 'Reviewed in FPO management: PASS', '62f7885e-35c2-434c-afec-bb5b14428db9', '2026-09-25 13:30:48.181145+05:30');
INSERT INTO public.fpo_verification_checklist_results (checklist_result_id, case_id, checklist_key, result, note, checked_by, checked_at) VALUES ('b988ec79-d75d-4191-a2e7-d1676bb16637', '1c77e63a-8f6f-4928-8e3f-e34a2e691b16', 'REGISTRATION', 'PASS', 'Reviewed in FPO management: PASS', '62f7885e-35c2-434c-afec-bb5b14428db9', '2026-09-25 13:30:49.26197+05:30');
INSERT INTO public.fpo_verification_checklist_results (checklist_result_id, case_id, checklist_key, result, note, checked_by, checked_at) VALUES ('99592b2e-ba6b-4bdd-bcb0-1de5c13071b4', '8ee1b47c-783b-4a4b-b70d-1d7eb770a9b2', 'IDENTITY', 'PENDING', NULL, NULL, NULL);
INSERT INTO public.fpo_verification_checklist_results (checklist_result_id, case_id, checklist_key, result, note, checked_by, checked_at) VALUES ('e2502031-91a8-4688-b26d-5700d19ef0ab', '8ee1b47c-783b-4a4b-b70d-1d7eb770a9b2', 'REGISTRATION', 'PENDING', NULL, NULL, NULL);
INSERT INTO public.fpo_verification_checklist_results (checklist_result_id, case_id, checklist_key, result, note, checked_by, checked_at) VALUES ('2c04c2b6-cb6b-4e6b-8bbc-a094bed6e050', '8ee1b47c-783b-4a4b-b70d-1d7eb770a9b2', 'CONTACT', 'PENDING', NULL, NULL, NULL);
INSERT INTO public.fpo_verification_checklist_results (checklist_result_id, case_id, checklist_key, result, note, checked_by, checked_at) VALUES ('6fd10bee-7a12-46c7-9d41-49cfbdbd8252', '8ee1b47c-783b-4a4b-b70d-1d7eb770a9b2', 'GEOGRAPHY', 'PENDING', NULL, NULL, NULL);
INSERT INTO public.fpo_verification_checklist_results (checklist_result_id, case_id, checklist_key, result, note, checked_by, checked_at) VALUES ('008edc9b-92aa-43c7-919d-dfcf26e46582', '8ee1b47c-783b-4a4b-b70d-1d7eb770a9b2', 'OPERATIONS', 'PENDING', NULL, NULL, NULL);


--
-- Data for Name: fpo_verification_documents; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.fpo_verification_documents (document_id, fpo_id, submission_id, document_type, object_key, original_filename, mime_type, size_bytes, checksum, uploaded_by, created_at, upload_status, scan_status, validation_status, validated_by, validated_at, validation_reason, storage_version, deleted_at, updated_at, scan_attempts, scan_next_attempt_at, scan_error, scanned_at, verified_checksum, scan_locked_at, scan_worker_id, scan_lease_expires_at, scan_max_attempts) VALUES ('fdb68c20-8fee-4de9-bd42-df23947ee736', '420e6f40-2d99-4fc5-93c4-2ce6fc869c85', NULL, 'REGISTRATION_CERTIFICATE', 'fpo/420e6f40-2d99-4fc5-93c4-2ce6fc869c85/verification/ff17bee1-c804-42b9-b360-f0b0c932d601/Provisional_Degree_Certificate.pdf', 'Provisional_Degree_Certificate.pdf', 'application/pdf', 153287, '494509a0ce0ef839eb18ee6c7f51cdbbc7d85b3ce783ed7ce1ce1fc77788516a', '48bcc40d-6476-49b8-8981-fe5be90fd88b', '2026-09-25 12:35:58.121362+05:30', 'AVAILABLE', 'NOT_REQUIRED', 'PENDING', NULL, NULL, NULL, 2, '2026-09-25 13:20:11.997113+05:30', '2026-09-25 13:20:11.997113+05:30', 0, '2026-09-25 12:35:58.121362+05:30', NULL, NULL, NULL, NULL, NULL, NULL, 5);
INSERT INTO public.fpo_verification_documents (document_id, fpo_id, submission_id, document_type, object_key, original_filename, mime_type, size_bytes, checksum, uploaded_by, created_at, upload_status, scan_status, validation_status, validated_by, validated_at, validation_reason, storage_version, deleted_at, updated_at, scan_attempts, scan_next_attempt_at, scan_error, scanned_at, verified_checksum, scan_locked_at, scan_worker_id, scan_lease_expires_at, scan_max_attempts) VALUES ('43521740-9177-4993-bd4d-7a24e62686ff', '420e6f40-2d99-4fc5-93c4-2ce6fc869c85', NULL, 'REGISTRATION_CERTIFICATE', 'fpo/420e6f40-2d99-4fc5-93c4-2ce6fc869c85/verification/4101f40b-5ceb-4b63-8efb-021c2e809ef0/TRAIN.pdf', 'TRAIN.pdf', 'application/pdf', 1790575, '4a2000a138d010903a8182ab0a65ec0a5c4640098a0243f7089be98bf7fc215f', '48bcc40d-6476-49b8-8981-fe5be90fd88b', '2026-09-25 12:34:52.636331+05:30', 'AVAILABLE', 'NOT_REQUIRED', 'PENDING', NULL, NULL, NULL, 2, '2026-09-25 13:20:14.516864+05:30', '2026-09-25 13:20:14.516864+05:30', 0, '2026-09-25 12:34:52.636331+05:30', NULL, NULL, NULL, NULL, NULL, NULL, 5);
INSERT INTO public.fpo_verification_documents (document_id, fpo_id, submission_id, document_type, object_key, original_filename, mime_type, size_bytes, checksum, uploaded_by, created_at, upload_status, scan_status, validation_status, validated_by, validated_at, validation_reason, storage_version, deleted_at, updated_at, scan_attempts, scan_next_attempt_at, scan_error, scanned_at, verified_checksum, scan_locked_at, scan_worker_id, scan_lease_expires_at, scan_max_attempts) VALUES ('c186f9c0-59c9-46e4-b72e-4f2a25159c6c', '420e6f40-2d99-4fc5-93c4-2ce6fc869c85', NULL, 'ADDRESS_PROOF', 'fpo/420e6f40-2d99-4fc5-93c4-2ce6fc869c85/verification/8e4cef95-5322-4cd0-8289-e9a721aaf893/Aadhar_Card_Online_Berhampur_Neha_Pati.pdf', 'Aadhar_Card_Online_Berhampur_Neha_Pati.pdf', 'application/pdf', 885148, 'ef1900b50ca34054ada7422835842d221d46e0a96f1212ff696325b22f91baf9', '48bcc40d-6476-49b8-8981-fe5be90fd88b', '2026-09-25 13:21:44.781773+05:30', 'AVAILABLE', 'NOT_REQUIRED', 'VALID', '62f7885e-35c2-434c-afec-bb5b14428db9', '2026-09-25 13:48:09.086556+05:30', 'Document reviewed and accepted.', 2, NULL, '2026-09-25 13:48:09.086556+05:30', 0, '2026-09-25 13:21:44.781773+05:30', NULL, NULL, NULL, NULL, NULL, NULL, 5);
INSERT INTO public.fpo_verification_documents (document_id, fpo_id, submission_id, document_type, object_key, original_filename, mime_type, size_bytes, checksum, uploaded_by, created_at, upload_status, scan_status, validation_status, validated_by, validated_at, validation_reason, storage_version, deleted_at, updated_at, scan_attempts, scan_next_attempt_at, scan_error, scanned_at, verified_checksum, scan_locked_at, scan_worker_id, scan_lease_expires_at, scan_max_attempts) VALUES ('9b05ad19-58cb-4883-a69b-cc3b796d9bb2', '420e6f40-2d99-4fc5-93c4-2ce6fc869c85', NULL, 'AUTHORIZED_REPRESENTATIVE_DECLARATION', 'fpo/420e6f40-2d99-4fc5-93c4-2ce6fc869c85/verification/34daa603-a4ce-4817-aadb-53ee3238ff8c/10th_Marksheet_and_Pass_Certificate_Neha_Pati.pdf', '10th_Marksheet_and_Pass_Certificate_Neha_Pati.pdf', 'application/pdf', 8226223, '4c73e6aa3b95f312aeec5e73fcb0d11bb182e2f6ebf2b560d33639397a83b52a', '48bcc40d-6476-49b8-8981-fe5be90fd88b', '2026-09-25 13:21:29.401036+05:30', 'AVAILABLE', 'NOT_REQUIRED', 'VALID', '62f7885e-35c2-434c-afec-bb5b14428db9', '2026-09-25 13:48:11.290245+05:30', 'Document reviewed and accepted.', 2, NULL, '2026-09-25 13:48:11.290245+05:30', 0, '2026-09-25 13:21:29.401036+05:30', NULL, NULL, NULL, NULL, NULL, NULL, 5);
INSERT INTO public.fpo_verification_documents (document_id, fpo_id, submission_id, document_type, object_key, original_filename, mime_type, size_bytes, checksum, uploaded_by, created_at, upload_status, scan_status, validation_status, validated_by, validated_at, validation_reason, storage_version, deleted_at, updated_at, scan_attempts, scan_next_attempt_at, scan_error, scanned_at, verified_checksum, scan_locked_at, scan_worker_id, scan_lease_expires_at, scan_max_attempts) VALUES ('52b8c91b-f052-43b8-b976-b9a3a96d0340', '420e6f40-2d99-4fc5-93c4-2ce6fc869c85', NULL, 'REGISTRATION_CERTIFICATE', 'fpo/420e6f40-2d99-4fc5-93c4-2ce6fc869c85/verification/f4ee4e50-34b2-45f7-a8d7-70b59a430f62/NEHA_PATI__1_.pdf', 'NEHA_PATI__1_.pdf', 'application/pdf', 51138, 'dc792d44993c0dc0a174a54c4782502be12359fd51e57aa0ff3560c7584c713a', '48bcc40d-6476-49b8-8981-fe5be90fd88b', '2026-09-25 13:20:40.977173+05:30', 'AVAILABLE', 'NOT_REQUIRED', 'VALID', '62f7885e-35c2-434c-afec-bb5b14428db9', '2026-09-25 13:48:13.130548+05:30', 'Document reviewed and accepted.', 2, NULL, '2026-09-25 13:48:13.130548+05:30', 0, '2026-09-25 13:20:40.977173+05:30', NULL, NULL, NULL, NULL, NULL, NULL, 5);
INSERT INTO public.fpo_verification_documents (document_id, fpo_id, submission_id, document_type, object_key, original_filename, mime_type, size_bytes, checksum, uploaded_by, created_at, upload_status, scan_status, validation_status, validated_by, validated_at, validation_reason, storage_version, deleted_at, updated_at, scan_attempts, scan_next_attempt_at, scan_error, scanned_at, verified_checksum, scan_locked_at, scan_worker_id, scan_lease_expires_at, scan_max_attempts) VALUES ('815d8e68-8ad8-4e61-b004-17cb06709c6a', '3c96b2f5-67e9-45f8-be75-d0f1cce6265f', NULL, 'ADDRESS_PROOF', 'fpo/3c96b2f5-67e9-45f8-be75-d0f1cce6265f/verification/6e2d9226-a834-4132-a565-95a3a9727d6a/Jee_Mains_Rank_Card_Neha_Pati.pdf', 'Jee_Mains_Rank_Card_Neha_Pati.pdf', 'application/pdf', 281229, '71e8a89de66dca3cf80c7d79c504727c83de3c878972170c0444354cc8b3d0d7', '77fd988f-f9f3-48cb-b8bc-b7187c765f43', '2026-09-25 15:41:51.776271+05:30', 'AVAILABLE', 'NOT_REQUIRED', 'VALID', '62f7885e-35c2-434c-afec-bb5b14428db9', '2026-09-25 15:48:05.897489+05:30', 'Document reviewed and accepted.', 2, NULL, '2026-09-25 15:48:05.897489+05:30', 0, '2026-09-25 15:41:51.776271+05:30', NULL, NULL, NULL, NULL, NULL, NULL, 5);
INSERT INTO public.fpo_verification_documents (document_id, fpo_id, submission_id, document_type, object_key, original_filename, mime_type, size_bytes, checksum, uploaded_by, created_at, upload_status, scan_status, validation_status, validated_by, validated_at, validation_reason, storage_version, deleted_at, updated_at, scan_attempts, scan_next_attempt_at, scan_error, scanned_at, verified_checksum, scan_locked_at, scan_worker_id, scan_lease_expires_at, scan_max_attempts) VALUES ('971711fb-5a4d-47e3-805e-56c4477b559d', '3c96b2f5-67e9-45f8-be75-d0f1cce6265f', NULL, 'AUTHORIZED_REPRESENTATIVE_DECLARATION', 'fpo/3c96b2f5-67e9-45f8-be75-d0f1cce6265f/verification/4be9a9c5-7a91-430b-b4e2-c2d7129ae781/Candidate_Profile.pdf', 'Candidate_Profile.pdf', 'application/pdf', 64706, 'de8175bea6914145d5607977e90e5b1581946e2f5fed2423d3137649db93d098', '77fd988f-f9f3-48cb-b8bc-b7187c765f43', '2026-09-25 15:41:40.942961+05:30', 'AVAILABLE', 'NOT_REQUIRED', 'VALID', '62f7885e-35c2-434c-afec-bb5b14428db9', '2026-09-25 15:48:07.218305+05:30', 'Document reviewed and accepted.', 2, NULL, '2026-09-25 15:48:07.218305+05:30', 0, '2026-09-25 15:41:40.942961+05:30', NULL, NULL, NULL, NULL, NULL, NULL, 5);
INSERT INTO public.fpo_verification_documents (document_id, fpo_id, submission_id, document_type, object_key, original_filename, mime_type, size_bytes, checksum, uploaded_by, created_at, upload_status, scan_status, validation_status, validated_by, validated_at, validation_reason, storage_version, deleted_at, updated_at, scan_attempts, scan_next_attempt_at, scan_error, scanned_at, verified_checksum, scan_locked_at, scan_worker_id, scan_lease_expires_at, scan_max_attempts) VALUES ('c2946ed2-8ec5-4858-bb1c-2aff40fdc6ae', '3c96b2f5-67e9-45f8-be75-d0f1cce6265f', NULL, 'REGISTRATION_CERTIFICATE', 'fpo/3c96b2f5-67e9-45f8-be75-d0f1cce6265f/verification/10118526-eb60-427c-93fd-2e9a7eba3f8e/Nativity_Certificate_Neha_Pati.pdf', 'Nativity_Certificate_Neha_Pati.pdf', 'application/pdf', 134877, '404f4e75280ff669745e84fa1f5b31584ed56a869e1913f228377be310e6efc9', '77fd988f-f9f3-48cb-b8bc-b7187c765f43', '2026-09-25 15:41:27.73813+05:30', 'AVAILABLE', 'NOT_REQUIRED', 'VALID', '62f7885e-35c2-434c-afec-bb5b14428db9', '2026-09-25 15:48:08.738397+05:30', 'Document reviewed and accepted.', 2, NULL, '2026-09-25 15:48:08.738397+05:30', 0, '2026-09-25 15:41:27.73813+05:30', NULL, NULL, NULL, NULL, NULL, NULL, 5);


--
-- Data for Name: fpo_verification_submission_documents; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.fpo_verification_submission_documents (submission_id, document_id, storage_version, checksum, linked_at) VALUES ('dcb93c6b-a263-4d66-9531-a1eb19b253ed', '52b8c91b-f052-43b8-b976-b9a3a96d0340', 2, 'dc792d44993c0dc0a174a54c4782502be12359fd51e57aa0ff3560c7584c713a', '2026-09-25 13:21:51.86015+05:30');
INSERT INTO public.fpo_verification_submission_documents (submission_id, document_id, storage_version, checksum, linked_at) VALUES ('dcb93c6b-a263-4d66-9531-a1eb19b253ed', '9b05ad19-58cb-4883-a69b-cc3b796d9bb2', 2, '4c73e6aa3b95f312aeec5e73fcb0d11bb182e2f6ebf2b560d33639397a83b52a', '2026-09-25 13:21:51.86015+05:30');
INSERT INTO public.fpo_verification_submission_documents (submission_id, document_id, storage_version, checksum, linked_at) VALUES ('dcb93c6b-a263-4d66-9531-a1eb19b253ed', 'c186f9c0-59c9-46e4-b72e-4f2a25159c6c', 2, 'ef1900b50ca34054ada7422835842d221d46e0a96f1212ff696325b22f91baf9', '2026-09-25 13:21:51.86015+05:30');
INSERT INTO public.fpo_verification_submission_documents (submission_id, document_id, storage_version, checksum, linked_at) VALUES ('49f45a17-773a-4c7a-b7f6-c7840c1864a7', 'c2946ed2-8ec5-4858-bb1c-2aff40fdc6ae', 2, '404f4e75280ff669745e84fa1f5b31584ed56a869e1913f228377be310e6efc9', '2026-09-25 15:46:08.838625+05:30');
INSERT INTO public.fpo_verification_submission_documents (submission_id, document_id, storage_version, checksum, linked_at) VALUES ('49f45a17-773a-4c7a-b7f6-c7840c1864a7', '971711fb-5a4d-47e3-805e-56c4477b559d', 2, 'de8175bea6914145d5607977e90e5b1581946e2f5fed2423d3137649db93d098', '2026-09-25 15:46:08.838625+05:30');
INSERT INTO public.fpo_verification_submission_documents (submission_id, document_id, storage_version, checksum, linked_at) VALUES ('49f45a17-773a-4c7a-b7f6-c7840c1864a7', '815d8e68-8ad8-4e61-b004-17cb06709c6a', 2, '71e8a89de66dca3cf80c7d79c504727c83de3c878972170c0444354cc8b3d0d7', '2026-09-25 15:46:08.838625+05:30');


--
-- Data for Name: fpo_webhook_subscriptions; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_webhook_deliveries; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: fpo_yield_forecasts; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Name: fpo_public_number_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.fpo_public_number_seq', 100415, true);


--
-- PostgreSQL database dump complete
--

