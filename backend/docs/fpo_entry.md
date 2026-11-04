REQUEST ACCESS PATH                         DIRECT SIGNUP PATH

Request FPO access form                     Signup as FPO
        |                                           |
        v                                           v
fpo_access_requests row                    Signup OTP session
status = pending                                    |
        |                                           v
        v                                  Email OTP verification
Admin approves request                                |
        |                                           v
        v                                  User account creation
Invitation created                                   |
        |                                           |
        v                                           |
Invitation email                                     |
        |                                           |
        v                                           |
User accepts invitation                               |
        |                                           |
        +-------------------+-----------------------+
                            |
                            v
              users row created with role = fpo
                            |
                            v
                 auth.user.created event
                            |
                            v
                 FPO provisioning worker
                            |
                            v
              FPO organization/profile created
                            |
                            v
                 FPO profile completion
                            |
                            v
                    Document upload
                            |
                            v
                Verification submission
                            |
                            v
                  Admin FPO verification
                            |
                            v
                 Admin class assignment


FPO-01 provisioning delivery
----------------------------

Auth and FPO Management each own their side of event delivery:

Auth user + outbox
        |
        v
Auth publisher (services.auth_service.app.fpo_event_worker)
        |
        v
Authenticated FPO event inbox + idempotent worker
        |
        v
FPO organization + stable public FPO ID
        |
        v
Authenticated Profile Service provisioning
        |
        v
Profile + owner membership + organization link
        |
        v
READY -> profile completion -> document upload -> verification

Apply `backend/data_contracts/sql/fpo_sql/20261102_39_fpo_provisioning_delivery.sql`
after the existing FPO migrations. Run the Auth event publisher separately from the
Auth API and keep `services.fpo_management_service.worker` running. Configure the
same `FPO_EVENT_DELIVERY_TOKEN` for Auth and FPO Management, and the same
`PROFILE_INTERNAL_SERVICE_TOKEN` for FPO Management and Profile Service. The browser
does not receive either internal token. See [the FPO API contract](../../docs/fpo-api-contract.md)
for the status response, admin recovery endpoints, and runtime configuration.

FPO access request lifecycle
----------------------------

`fpo_access_requests` stores the applicant's request and its review status.
`account_invitations` stores each single-use invitation and its expiry/acceptance
timestamps; `fpo_access_request_id` links it to the request with a foreign key.
`email_outbox` stores queued acknowledgement and invitation messages.
`users` is created only after the invite is accepted. Provisioning then creates
the organization records in `fpo_organizations`, `fpo_users`, and `fpos`.

Repeat submissions for an email reuse its pending/approved request or its
invitation-linked request. Expired or revoked invitations remain auditable and
are shown to administrators as resendable; they do not require a second request.
The database migration `20261102_40_fpo_access_request_idempotency.sql` cleans up
older active duplicates and enforces one pending/approved request per email.
From `backend/`, apply it with:

```powershell
psql $env:DATABASE_URL -v ON_ERROR_STOP=1 -f data_contracts/sql/20261102_40_fpo_access_request_idempotency.sql
```









Farmer opens a farm's Land Intelligence page
              |
              v
System checks whether this farm has an active FPO relationship
              |
              +── Active relationship
              |       |
              |       v
              |   Show FPO-linked intelligence
              |
              +── No relationship
                      |
                      v
             Show "Connect with FPO"
                      |
                      v
             Farmer selects approved FPO
                      |
                      v
             Farmer accepts data-sharing consent
                      |
                      v
Farm-level relationship created
status = PENDING_FPO_ACCEPTANCE
                      |
                      v
FPO reviews request
                /             \
             Reject           Accept
               |                |
               v                v
           REJECTED          ACTIVE
                                |
                                v
            FPO can access only this specific farm
            with valid consent and enabled entitlements