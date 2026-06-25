from pathlib import Path

# Expose backend/services as the package path when running from the repo root.
_backend_services = Path(__file__).resolve().parent.parent / "backend" / "services"
__path__ = [str(_backend_services)] if _backend_services.exists() else []

