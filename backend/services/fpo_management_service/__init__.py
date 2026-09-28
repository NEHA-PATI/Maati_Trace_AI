"""FPO organization provisioning and lifecycle service."""

from pathlib import Path

from dotenv import load_dotenv


# This service intentionally has its own environment contract. Load it before
# importing shared.db.postgres or shared.security.local_auth, because those
# modules construct settings at import time.
load_dotenv(
    Path(__file__).resolve().parent / ".env",
    override=True,
)
