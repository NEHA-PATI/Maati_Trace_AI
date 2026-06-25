from pathlib import Path

# Expose backend/shared as the package path when running from the repo root.
_backend_shared = Path(__file__).resolve().parent.parent / "backend" / "shared"
__path__ = [str(_backend_shared)] if _backend_shared.exists() else []
